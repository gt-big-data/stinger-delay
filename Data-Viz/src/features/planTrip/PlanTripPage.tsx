import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import styles from "./PlanTripPage.module.css";
import { Route } from "@/types/route";
import { Stop } from "@/types/stop";
import { mockRoutes } from "../../lib/mocks/mockTripData";

interface RouteSegment {
  route: Route;
  fromStop: Stop;
  toStop: Stop;
  stops: Stop[];
}

interface RouteResult {
  segments: RouteSegment[];
  totalStops: number;
  transfers: number;
  startStop: Stop;
  endStop: Stop;
  walkingDistanceStart: number;
  walkingDistanceEnd: number;
}

const PlanTripPage: React.FC = () => {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [fromLocation, setFromLocation] = useState<string>("");
  const [toLocation, setToLocation] = useState<string>("");
  const [fromCoords, setFromCoords] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [toCoords, setToCoords] = useState<{ lat: number; lng: number } | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  const [result, setResult] = useState<RouteResult | null>(null);
  const [error, setError] = useState<string>("");

  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const routeLineRef = useRef<L.Polyline[]>([]);

  const GT_CENTER: [number, number] = [33.7756, -84.3963];

  const startIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
    shadowUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const endIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
    shadowUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const transferIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png",
    shadowUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const boardIcon = L.icon({
    iconUrl:
      "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png",
    shadowUrl:
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  useEffect(() => {
    setRoutes(mockRoutes);
    const allStops: Stop[] = [];
    const stopKey = new Set<string>();
    mockRoutes.forEach((route) => {
      route.stops.forEach((stop) => {
        if (!stopKey.has(stop.id)) {
          stopKey.add(stop.id);
          allStops.push(stop);
        }
      });
    });
    setStops(allStops);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (mapRef.current && !mapInstanceRef.current && stops.length > 0)
      initMap();
  }, [stops]);

  useEffect(() => {
    if (result && mapInstanceRef.current) updateMap();
  }, [result]);

  function getStopByName(name: string): Stop | undefined {
    return stops.find((s) => s.name === name);
  }

  function handleFromLocationSelect(e: React.ChangeEvent<HTMLSelectElement>) {
    const stopName = e.target.value;
    setFromLocation(stopName);
    const stop = getStopByName(stopName);
    if (stop) setFromCoords({ lat: stop.latitude, lng: stop.longitude });
  }

  function handleToLocationSelect(e: React.ChangeEvent<HTMLSelectElement>) {
    const stopName = e.target.value;
    setToLocation(stopName);
    const stop = getStopByName(stopName);
    if (stop) setToCoords({ lat: stop.latitude, lng: stop.longitude });
  }

  const calculateDistance = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number => {
    const toRadian = (angle: number) => (Math.PI / 180) * angle;
    const R = 6371;
    const dLat = toRadian(lat2 - lat1);
    const dLon = toRadian(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRadian(lat1)) *
        Math.cos(toRadian(lat2)) *
        Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  const clearMarkers = () => {
    if (!mapInstanceRef.current) return;
    markersRef.current.forEach((marker) => {
      if (marker) mapInstanceRef.current!.removeLayer(marker);
    });
    markersRef.current = [];
    routeLineRef.current.forEach((line) => {
      if (line) mapInstanceRef.current!.removeLayer(line);
    });
    routeLineRef.current = [];
  };

  const initMap = () => {
    if (!mapRef.current || mapInstanceRef.current) return;
    const map = L.map(mapRef.current).setView(GT_CENTER, 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    mapInstanceRef.current = map;
  };

  const updateMap = () => {
    if (!result || !mapInstanceRef.current) return;
    clearMarkers();

    const allCoordinates: [number, number][] = [];

    if (result.transfers === -1) {
      if (fromCoords && toCoords) {
        allCoordinates.push(
          [fromCoords.lat, fromCoords.lng],
          [toCoords.lat, toCoords.lng]
        );

        markersRef.current.push(
          L.marker([fromCoords.lat, fromCoords.lng], { icon: startIcon })
            .bindPopup(`<strong>🏁 START</strong><br>${fromLocation}`)
            .addTo(mapInstanceRef.current)
        );

        markersRef.current.push(
          L.marker([toCoords.lat, toCoords.lng], { icon: endIcon })
            .bindPopup(`<strong>🎯 DESTINATION</strong><br>${toLocation}`)
            .addTo(mapInstanceRef.current)
        );

        routeLineRef.current.push(
          L.polyline(
            [
              [fromCoords.lat, fromCoords.lng],
              [toCoords.lat, toCoords.lng],
            ],
            {
              color: "#22c55e",
              weight: 5,
              opacity: 0.8,
              dashArray: "10, 10",
              lineCap: "round",
            }
          ).addTo(mapInstanceRef.current)
        );
      }
    } else {
      if (fromCoords) {
        allCoordinates.push([fromCoords.lat, fromCoords.lng]);
        markersRef.current.push(
          L.marker([fromCoords.lat, fromCoords.lng], { icon: startIcon })
            .bindPopup(`<strong>🏁 START</strong><br>${fromLocation}`)
            .addTo(mapInstanceRef.current)
        );
      }

      result.segments.forEach((segment, index) => {
        const coordinates: [number, number][] = segment.stops.map((s) => [
          s.latitude,
          s.longitude,
        ]);
        allCoordinates.push(...coordinates);

        routeLineRef.current.push(
          L.polyline(coordinates, {
            color: segment.route.color || "#3B82F6",
            weight: 6,
            opacity: 0.7,
            lineCap: "round",
            lineJoin: "round",
            smoothFactor: 1,
          }).addTo(mapInstanceRef.current!)
        );

        if (index > 0) {
          const transferStop = segment.stops[0];
          markersRef.current.push(
            L.marker([transferStop.latitude, transferStop.longitude], {
              icon: transferIcon,
            })
              .bindPopup(
                `<strong>🔄 TRANSFER</strong><br>${transferStop.name}<br>Switch to ${segment.route.name}`
              )
              .addTo(mapInstanceRef.current!)
          );
        } else {
          const boardStop = segment.stops[0];
          markersRef.current.push(
            L.marker([boardStop.latitude, boardStop.longitude], {
              icon: boardIcon,
            })
              .bindPopup(
                `<strong>🚌 BOARD</strong><br>${boardStop.name}<br>${segment.route.name}`
              )
              .addTo(mapInstanceRef.current!)
          );
        }
      });

      if (toCoords) {
        allCoordinates.push([toCoords.lat, toCoords.lng]);
        markersRef.current.push(
          L.marker([toCoords.lat, toCoords.lng], { icon: endIcon })
            .bindPopup(`<strong>🎯 DESTINATION</strong><br>${toLocation}`)
            .addTo(mapInstanceRef.current)
        );
      }
    }

    if (allCoordinates.length > 0) {
      const bounds = L.latLngBounds(allCoordinates);
      mapInstanceRef.current.fitBounds(bounds, { padding: [80, 80] });
    }
  };

  const findRouteWithBFS = (
    startStopId: string,
    endStopId: string
  ): Omit<
    RouteResult,
    "startStop" | "endStop" | "walkingDistanceStart" | "walkingDistanceEnd"
  > | null => {
    interface BFSNode {
      stopId: string;
      routeId: string;
      segments: RouteSegment[];
      visitedKey: string;
    }

    const queue: BFSNode[] = [];
    const visited = new Set<string>();

    routes.forEach((route) => {
      const startIdx = route.stops.findIndex((s) => s.id === startStopId);
      if (startIdx !== -1) {
        const key = `${startStopId}:${route.id}`;
        queue.push({
          stopId: startStopId,
          routeId: route.id,
          segments: [],
          visitedKey: key,
        });
        visited.add(key);
      }
    });

    let iterations = 0;
    while (queue.length > 0 && iterations < 10000) {
      iterations++;
      const current = queue.shift()!;
      const route = routes.find((r) => r.id === current.routeId);
      if (!route) continue;

      const currentIdx = route.stops.findIndex((s) => s.id === current.stopId);
      if (currentIdx === -1) continue;

      for (const direction of [1, -1]) {
        let i = currentIdx + direction;

        while (i >= 0 && i < route.stops.length) {
          const nextStop = route.stops[i];

          if (nextStop.id === endStopId) {
            const finalSegment: RouteSegment = {
              route,
              fromStop: route.stops[currentIdx],
              toStop: nextStop,
              stops:
                direction > 0
                  ? route.stops.slice(currentIdx, i + 1)
                  : route.stops.slice(i, currentIdx + 1).reverse(),
            };
            return {
              segments: [...current.segments, finalSegment],
              totalStops: [...current.segments, finalSegment].reduce(
                (sum, seg) => sum + seg.stops.length,
                0
              ),
              transfers: current.segments.length,
            };
          }

          routes.forEach((transferRoute) => {
            if (transferRoute.id === route.id) return;

            const transferIdx = transferRoute.stops.findIndex(
              (s) => s.id === nextStop.id
            );
            if (transferIdx !== -1) {
              const transferKey = `${nextStop.id}:${transferRoute.id}`;
              if (!visited.has(transferKey)) {
                visited.add(transferKey);

                const segmentToTransfer: RouteSegment = {
                  route,
                  fromStop: route.stops[currentIdx],
                  toStop: nextStop,
                  stops:
                    direction > 0
                      ? route.stops.slice(currentIdx, i + 1)
                      : route.stops.slice(i, currentIdx + 1).reverse(),
                };

                queue.push({
                  stopId: nextStop.id,
                  routeId: transferRoute.id,
                  segments: [...current.segments, segmentToTransfer],
                  visitedKey: transferKey,
                });
              }
            }
          });

          i += direction;
        }
      }
    }

    return null;
  };

  const findOptimalRoute = () => {
    if (!fromLocation || !toLocation) {
      setError("Please select both locations.");
      return;
    }
    if (fromLocation === toLocation) {
      setError("Starting location and destination cannot be the same.");
      return;
    }

    const fromStop = getStopByName(fromLocation);
    const toStop = getStopByName(toLocation);

    if (!fromStop || !toStop) {
      setError("Selected stop not found.");
      return;
    }

    const walkDistStart = fromCoords
      ? calculateDistance(
          fromCoords.lat,
          fromCoords.lng,
          fromStop.latitude,
          fromStop.longitude
        )
      : 0;
    const walkDistEnd = toCoords
      ? calculateDistance(
          toCoords.lat,
          toCoords.lng,
          toStop.latitude,
          toStop.longitude
        )
      : 0;

    const directWalkDistance = calculateDistance(
      fromStop.latitude,
      fromStop.longitude,
      toStop.latitude,
      toStop.longitude
    );

    const WALKING_THRESHOLD_KM = 0.8;
    const AVERAGE_WALKING_SPEED_KMH = 5;
    const walkingTimeMinutes =
      (directWalkDistance / AVERAGE_WALKING_SPEED_KMH) * 60;

    setSearching(true);
    setError("");
    setResult(null);

    setTimeout(() => {
      const routeResult = findRouteWithBFS(fromStop.id, toStop.id);

      let busTripTimeMinutes = 0;
      if (routeResult) {
        busTripTimeMinutes =
          5 + routeResult.totalStops * 2 + routeResult.transfers * 5;
      }

      if (
        directWalkDistance < WALKING_THRESHOLD_KM &&
        (!routeResult || walkingTimeMinutes < busTripTimeMinutes + 5)
      ) {
        setResult({
          segments: [],
          totalStops: 0,
          transfers: -1,
          startStop: fromStop,
          endStop: toStop,
          walkingDistanceStart: 0,
          walkingDistanceEnd: directWalkDistance,
        });
        setSearching(false);
        return;
      }

      if (routeResult) {
        setResult({
          ...routeResult,
          startStop: fromStop,
          endStop: toStop,
          walkingDistanceStart: walkDistStart,
          walkingDistanceEnd: walkDistEnd,
        });
      } else {
        if (directWalkDistance < 3) {
          setResult({
            segments: [],
            totalStops: 0,
            transfers: -1,
            startStop: fromStop,
            endStop: toStop,
            walkingDistanceStart: 0,
            walkingDistanceEnd: directWalkDistance,
          });
        } else {
          setError("No routes found and distance is too far to walk.");
        }
      }
      setSearching(false);
    }, 200);
  };

  if (loading) {
    return (
      <div className={styles.center}>
        <h2>🚌 Loading GT Bus Data...</h2>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h1 style={{ color: "#ffffff" }}>Plan Trip</h1>
      <p>Select your starting point and destination</p>

      <div className={styles.topSection}>
        <div className={styles.selectionBox}>
          <div className={styles.selectGroup}>
            <label>From</label>
            <select
              value={fromLocation}
              onChange={handleFromLocationSelect}
              className={styles.select}
            >
              <option value="">Select starting stop</option>
              {stops.map((stop) => (
                <option key={stop.id} value={stop.name}>
                  {stop.name}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.selectGroup}>
            <label>To</label>
            <select
              value={toLocation}
              onChange={handleToLocationSelect}
              className={styles.select}
            >
              <option value="">Select destination</option>
              {stops.map((stop) => (
                <option key={stop.id} value={stop.name}>
                  {stop.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={findOptimalRoute}
            disabled={searching}
            className={styles.findButton}
          >
            {searching ? "Finding Route..." : "Find Route"}
          </button>

          {error && <p className={styles.error}>{error}</p>}
        </div>

        {result && (
          <div className={styles.routeBox}>
            {result.transfers === -1 ? (
              <>
                <div className={styles.routeHeader}>
                  <h2>🚶 Walking Recommended</h2>
                  <p className={styles.subtitle}>Faster than taking the bus!</p>
                </div>
                <div className={styles.routeDetails}>
                  <div className={styles.detailRow}>
                    <span className={styles.label}>Distance:</span>
                    <span className={styles.value}>
                      {(result.walkingDistanceEnd * 1000).toFixed(0)}m
                    </span>
                  </div>
                  <div className={styles.detailRow}>
                    <span className={styles.label}>Time:</span>
                    <span className={styles.value}>
                      {((result.walkingDistanceEnd / 5) * 60).toFixed(0)} min
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className={styles.routeHeader}>
                  <h2>✅ Route Found</h2>
                  <p className={styles.subtitle}>
                    {result.transfers === 0
                      ? "Direct route"
                      : `${result.transfers} transfer${
                          result.transfers > 1 ? "s" : ""
                        }`}
                  </p>
                </div>
                <div className={styles.routeSteps}>
                  <div className={styles.step}>
                    <div className={styles.stepIcon}>🚶</div>
                    <div className={styles.stepContent}>
                      <strong>Walk to {result.startStop.name}</strong>
                      <span>
                        {(result.walkingDistanceStart * 1000).toFixed(0)}m
                      </span>
                    </div>
                  </div>

                  {result.segments.map((segment, index) => (
                    <div key={index} className={styles.step}>
                      <div
                        className={styles.stepIcon}
                        style={{ backgroundColor: segment.route.color }}
                      >
                        🚌
                      </div>
                      <div className={styles.stepContent}>
                        <strong>{segment.route.name}</strong>
                        <span>Board at {segment.fromStop.name}</span>
                        <span>Exit at {segment.toStop.name}</span>
                        <span className={styles.stopsCount}>
                          {segment.stops.length - 1} stops
                        </span>
                      </div>
                    </div>
                  ))}

                  <div className={styles.step}>
                    <div className={styles.stepIcon}>🎯</div>
                    <div className={styles.stepContent}>
                      <strong>Arrive at destination</strong>
                      <span>
                        Walk {(result.walkingDistanceEnd * 1000).toFixed(0)}m
                      </span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <div className={styles.mapContainer}>
        <div ref={mapRef} className={styles.map}></div>
      </div>

      <Link to="/" className={styles.linkButton}>
        ← Back to Home
      </Link>
    </div>
  );
};

export default PlanTripPage;
