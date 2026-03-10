# Red Line Collector — Run Manual

## Environment

| Item | Value |
|---|---|
| Script | `Platform/red_line/red_line_collector.py` |
| Output CSV | `Platform/red_line/data/red_line_data.csv` |
| Log file | `Platform/red_line/data/red_line_collector.log` |
| Python env | conda `General_env` (Python 3.11) |
| Route | Red — routeID **20** |
| Poll interval | 30 s (configurable via `POLL_INTERVAL` in the script) |

---

## Step 0 — Prerequisites check

Run once before starting:

```bash
# Confirm General_env exists and has required packages
conda activate General_env
python -c "import requests, pytz; print('OK')"
```

Expected output: `OK`

If packages are missing:
```bash
pip install "requests>=2.28.0" "pytz>=2023.3"
```

---

## Step 1 — 30-minute dry run (mandatory before full run)

Open a terminal at the repo root and run:

```bash
conda activate General_env
python "Platform/red_line/red_line_collector.py"
```

Let it run for **at least 30 minutes**, then verify:

| Check | How |
|---|---|
| Ticks firing consistently every 30 s | Watch terminal heartbeat timestamps |
| CSV is growing | `wc -l Platform/red_line/data/red_line_data.csv` |
| All route_id values are 20 | `cut -d, -f3 Platform/red_line/data/red_line_data.csv \| sort -u` |
| No flood of `ERROR` lines in log | `grep ERROR Platform/red_line/data/red_line_collector.log` |

Stop with `Ctrl+C` once verified.

---

## Step 2 — Full 3-day run with tmux

```bash
# Start a named tmux session
tmux new -s redscrape

# Inside the session:
conda activate General_env
cd "/home/hty/Documents/Working Projects/stinger-delay"
python "Platform/red_line/red_line_collector.py"
```

Detach without stopping: `Ctrl+b`, then `d`

Reattach any time:
```bash
tmux attach -t redscrape
```

Alternative (no tmux — nohup):
```bash
conda run -n General_env nohup python \
  "Platform/red_line/red_line_collector.py" \
  > "Platform/red_line/data/nohup.log" 2>&1 &
echo "PID: $!"
```

---

## Step 3 — Monitoring while running

Check every few hours:

```bash
# 1. Is the process alive?
pgrep -a python | grep red_line_collector

# 2. Is the CSV growing? (row count)
wc -l "Platform/red_line/data/red_line_data.csv"

# 3. What was the latest tick? (should be within ~30s of now)
tail -2 "Platform/red_line/data/red_line_data.csv"

# 4. Any errors accumulating?
grep -c "ERROR" "Platform/red_line/data/red_line_collector.log"

# 5. Last heartbeat log entry
tail -5 "Platform/red_line/data/red_line_collector.log"
```

**Normal heartbeat line looks like:**
```
2024-03-04 14:00:30  INFO      HEARTBEAT | snapshot=2024-03-04 14:00:30 | vehicles=3 | rows=3 | errors=0
```

**"0 vehicles" is normal** outside Red Line operating hours (nights, weekends).

---

## Step 4 — Stopping the run

In the tmux session: `Ctrl+C`

Or kill by PID:
```bash
kill <PID>
```

The CSV is always in a valid state — each tick is flushed before the sleep.

---

## Step 5 — End-of-run QA checklist

After 3 days, open a Python shell or notebook and run:

```python
import pandas as pd

df = pd.read_csv("Platform/red_line/data/red_line_data.csv")
df["snapshot_time_utc"] = pd.to_datetime(df["snapshot_time_utc"], utc=True)

# 1. Timestamp span — must cover >= 3 full weekdays
print(df["snapshot_time_utc"].min(), "→", df["snapshot_time_utc"].max())

# 2. Route filter — all must be 20
print("Unique route_ids:", df["route_id"].unique())

# 3. Missing values per column
print(df.isnull().mean().round(3))

# 4. Duplicate rows
dupes = df.duplicated(subset=["snapshot_time_utc", "vehicle_id"])
print("Duplicate rows:", dupes.sum())

# 5. Row count
print("Total rows:", len(df))
# Expected: ~8,640 rows/day × 3 days ≈ 25,920 (at 30s polling, 3 vehicles avg)
```

---

## Known limitations

| Limitation | Notes |
|---|---|
| SSL certificate | `requests` verifies `bus.gatech.edu` by default. If the cert is expired/invalid at run time the script will log SSL errors and all ticks will fail. Check with `curl -v https://bus.gatech.edu` before starting. |
| Night / weekend gaps | Red Line does not run outside service hours. Gaps in the CSV during those periods are expected and logged as `0 vehicles`. |
| API key expiry | Key `8882812681` is hard-coded. If the API starts returning non-JSON or HTTP errors, the key may have been rotated. Update `API_KEY` in the script. |
| Restart data loss | Restarting the script does not recover any ticks missed while it was stopped. Plan accordingly (do not stop unless necessary). |

---

## File layout

```
Platform/red_line/
  red_line_collector.py   ← collector script
  requirements.txt        ← Python dependencies
  RUN_MANUAL.md           ← this file
  data/
    red_line_data.csv     ← output (created on first run)
    red_line_collector.log← heartbeat + error log (created on first run)
```
