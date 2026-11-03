#!/usr/bin/env python3
"""Build segment run times and ETA-slip stats from recorded Stinger CSVs.

Normalization (replay):
  - timestamps parsed to America/New_York (naive Green/Gold stamps are local)
  - eta_s = estimated_time_arrival - snapshot_time
  - Red stores that difference already, as eta_seconds
  - exact duplicate rows dropped
  - rows with eta_s < -30 dropped

segments.json
  Median seconds between consecutive stops on the loop in stops.json.
  An arrival is the closest approach (minimum ETA) during a stretch where
  that stop is the vehicle's next stop. The segment is the gap to the next
  stop's arrival when the pair is consecutive on the loop.

slip_stats.json
  Keyed slip_stats[route_id][hour]. For each vehicle, consecutive snapshots
  (<= 90s apart, same next stop) contribute
    slip_s = (eta_now - eta_prev) + elapsed_s
  which is how far the predicted arrival moved later.
  Buckets: on_time < 2 min, slightly_late 2–5 min, significantly_late > 5 min.
  slip_buffer_s is the 80th percentile of slip_s (never negative).
  share_eta_grew is the fraction of those pairs whose raw ETA seconds rose.

Routes: Red=20, Green=17, Gold=29.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
STINGER_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STINGER_ROOT.parent
STOPS_PATH = STINGER_ROOT / "app" / "data" / "stops.json"
SEGMENTS_PATH = STINGER_ROOT / "app" / "data" / "segments.json"
SLIP_PATH = STINGER_ROOT / "app" / "data" / "slip_stats.json"

NY = ZoneInfo("America/New_York")
ROUTES = (20, 17, 29)
ON_TIME_S = 120.0
SLIGHT_S = 300.0
MAX_PAIR_GAP_S = 90.0
MAX_RUN_GAP_S = 180.0
MIN_SEGMENT_S = 15.0
MAX_SEGMENT_S = 1200.0

CSV_SOURCES = {
    20: [REPO_ROOT / "Platform" / "red_line" / "data" / "red_line_data.csv"],
    17: sorted((REPO_ROOT / "Analysis" / "green_bus_data").glob("*.csv")),
    29: sorted((REPO_ROOT / "Analysis" / "bus_data").glob("gt_gold_bus_data_*.csv")),
}


def _num(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=NY)
    return dt.astimezone(NY)


def eta_and_snapshot(row: dict[str, str]) -> tuple[float | None, datetime | None]:
    """ETA seconds and snapshot time in America/New_York."""
    raw_eta = (row.get("estimated_time_arrival") or "").strip()
    snap = parse_ts(row.get("snapshot_time") or row.get("snapshot_time_utc"))
    looks_like_clock = "T" in raw_eta or (len(raw_eta) >= 19 and raw_eta[4:5] == "-")
    if looks_like_clock:
        eta_dt = parse_ts(raw_eta)
        if eta_dt is not None and snap is not None:
            return (eta_dt - snap).total_seconds(), snap
    seconds = _num(row.get("eta_seconds"))
    if seconds is None:
        seconds = _num(raw_eta)
    return seconds, snap


def load_stop_sequences() -> dict[int, list[int]]:
    rows = json.loads(STOPS_PATH.read_text(encoding="utf-8"))
    grouped: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["route_id"])].append((int(row["seq"]), int(row["route_stop_id"])))
    sequences = {}
    for route_id, pairs in grouped.items():
        sequences[route_id] = [sid for _seq, sid in sorted(pairs)]
    missing = [rid for rid in ROUTES if rid not in sequences or len(sequences[rid]) < 2]
    if missing:
        raise SystemExit(f"stops.json is missing a loop for routes {missing}")
    return sequences


def load_observations(route_id: int) -> list[tuple[str, datetime, int, float]]:
    """(vehicle_id, snapshot, route_stop_id, eta_s) after dedupe and eta filter."""
    files = CSV_SOURCES[route_id]
    if not files:
        raise FileNotFoundError(f"no CSVs for route {route_id}")
    seen: set[tuple[str, ...]] = set()
    rows: list[tuple[str, datetime, int, float]] = []
    for path in files:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = tuple(row.get(col, "") for col in row)
                if key in seen:
                    continue
                seen.add(key)
                sid_raw = (row.get("route_stop_id") or "").strip()
                vid = (row.get("vehicle_id") or "").strip()
                if not sid_raw or not vid:
                    continue
                try:
                    sid = int(float(sid_raw))
                except ValueError:
                    continue
                eta, snap = eta_and_snapshot(row)
                if eta is None or snap is None or eta < -30:
                    continue
                rows.append((vid, snap, sid, eta))
    return rows


def next_stop_snapshots(
    rows: list[tuple[str, datetime, int, float]],
) -> dict[str, list[tuple[datetime, int, float]]]:
    """Per vehicle, time-ordered (snapshot, next_stop_id, eta_s)."""
    grouped: dict[tuple[str, datetime], dict[int, float]] = defaultdict(dict)
    for vid, snap, sid, eta in rows:
        grouped[(vid, snap)][sid] = eta
    by_vehicle: dict[str, list[tuple[datetime, int, float]]] = defaultdict(list)
    for (vid, snap), stops in grouped.items():
        positive = [(eta, sid) for sid, eta in stops.items() if eta >= 0]
        if positive:
            eta, sid = min(positive)
        else:
            eta, sid = min((eta, sid) for sid, eta in stops.items())
        by_vehicle[vid].append((snap, sid, eta))
    for samples in by_vehicle.values():
        samples.sort()
    return by_vehicle


def split_runs(
    samples: list[tuple[datetime, int, float]],
) -> list[list[tuple[datetime, int, float]]]:
    if not samples:
        return []
    runs: list[list[tuple[datetime, int, float]]] = [[samples[0]]]
    for prev, cur in zip(samples, samples[1:]):
        gap = (cur[0] - prev[0]).total_seconds()
        if gap <= 0 or gap > MAX_RUN_GAP_S:
            runs.append([cur])
        else:
            runs[-1].append(cur)
    return runs


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[int(pos)]
    weight = pos - lo
    return ordered[lo] * (1 - weight) + ordered[hi] * weight


def accumulate(
    by_vehicle: dict[str, list[tuple[datetime, int, float]]],
    sequence: list[int],
) -> tuple[dict[int, list[float]], dict[int, int], dict[tuple[int, int], list[float]]]:
    successor = {sequence[i]: sequence[(i + 1) % len(sequence)] for i in range(len(sequence))}
    slips: dict[int, list[float]] = defaultdict(list)
    grew: dict[int, int] = defaultdict(int)
    segments: dict[tuple[int, int], list[float]] = defaultdict(list)

    for samples in by_vehicle.values():
        for run in split_runs(samples):
            for prev, cur in zip(run, run[1:]):
                t0, stop0, eta0 = prev
                t1, stop1, eta1 = cur
                if stop0 != stop1 or eta0 < 0 or eta1 < 0:
                    continue
                elapsed = (t1 - t0).total_seconds()
                if elapsed <= 0 or elapsed > MAX_PAIR_GAP_S:
                    continue
                hour = t1.hour
                slips[hour].append((eta1 - eta0) + elapsed)
                if eta1 > eta0:
                    grew[hour] += 1

            arrivals: list[tuple[datetime, int, float]] = []
            i = 0
            while i < len(run):
                j = i
                while j + 1 < len(run) and run[j + 1][1] == run[i][1]:
                    j += 1
                window = run[i : j + 1]
                arrivals.append(min(window, key=lambda sample: sample[2]))
                i = j + 1
            for prev, cur in zip(arrivals, arrivals[1:]):
                if successor.get(prev[1]) != cur[1]:
                    continue
                elapsed = (cur[0] - prev[0]).total_seconds()
                if MIN_SEGMENT_S <= elapsed <= MAX_SEGMENT_S:
                    segments[(prev[1], cur[1])].append(elapsed)
    return slips, grew, segments


def slip_payload(
    slips: dict[int, list[float]], grew: dict[int, int]
) -> dict[str, dict]:
    payload: dict[str, dict] = {}
    for hour in range(24):
        values = slips.get(hour)
        if not values:
            continue
        n = len(values)
        on_time = sum(1 for value in values if value < ON_TIME_S)
        slight = sum(1 for value in values if ON_TIME_S <= value < SLIGHT_S)
        significant = n - on_time - slight
        buffer = max(0.0, percentile(values, 0.8))
        if buffer < ON_TIME_S:
            slip_class = "on_time"
        elif buffer < SLIGHT_S:
            slip_class = "slightly_late"
        else:
            slip_class = "significantly_late"
        payload[str(hour)] = {
            "n": n,
            "share_eta_grew": round(grew.get(hour, 0) / n, 4),
            "on_time": round(on_time / n, 4),
            "slightly_late": round(slight / n, 4),
            "significantly_late": round(significant / n, 4),
            "slip_buffer_s": round(buffer, 1),
            "slip_class": slip_class,
        }
    return payload


def segment_payload(
    sequence: list[int], observed: dict[tuple[int, int], list[float]]
) -> list[dict]:
    measured: dict[tuple[int, int], tuple[float, int]] = {}
    for pair, samples in observed.items():
        measured[pair] = (float(statistics.median(samples)), len(samples))
    route_medians = [median for median, _n in measured.values()]
    fallback = float(statistics.median(route_medians)) if route_medians else None
    payload = []
    for i, origin in enumerate(sequence):
        dest = sequence[(i + 1) % len(sequence)]
        if (origin, dest) in measured:
            median_s, n = measured[(origin, dest)]
        elif fallback is not None:
            median_s, n = fallback, 0
        else:
            continue
        payload.append(
            {
                "from_route_stop_id": origin,
                "to_route_stop_id": dest,
                "median_s": round(median_s, 1),
                "n": n,
            }
        )
    return payload


def build() -> tuple[dict, dict]:
    sequences = load_stop_sequences()
    segments: dict[str, list[dict]] = {}
    slip: dict[str, dict] = {}
    for route_id in ROUTES:
        rows = load_observations(route_id)
        by_vehicle = next_stop_snapshots(rows)
        slips, grew, observed = accumulate(by_vehicle, sequences[route_id])
        segments[str(route_id)] = segment_payload(sequences[route_id], observed)
        slip[str(route_id)] = slip_payload(slips, grew)
        print(
            f"route {route_id}: observations={len(rows)} "
            f"segments={len(segments[str(route_id)])} hours={len(slip[str(route_id)])}",
            file=sys.stderr,
        )
    return segments, slip


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments", type=Path, default=SEGMENTS_PATH)
    parser.add_argument("--slip", type=Path, default=SLIP_PATH)
    args = parser.parse_args()
    segments, slip = build()
    args.segments.parent.mkdir(parents=True, exist_ok=True)
    args.segments.write_text(json.dumps(segments, indent=2) + "\n", encoding="utf-8")
    args.slip.write_text(json.dumps(slip, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.segments}")
    print(f"wrote {args.slip}")


if __name__ == "__main__":
    main()
