import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import styles from "./PlanTripPage.module.css";

interface Stop {
  stop_id: string;
  name: string;
  location: {
    lat: number;
    lng: number;
  };
}

interface Route {
  route_id: string;
  long_name: string;
  short_name?: string;
  stops?: string[];
  minutesAway?: number;
  nextArrival?: string;
}

interface RouteResult {
  route: Route;
  fromStop: Stop;
  toStop: Stop;
  allRoutes: Route[];
  routeStops: Stop[];
}

const PlanTripPage: React.FC = () => {
  const [stops, setStops] = useState<Stop[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [fromStop, setFromStop] = useState<string>("");
  const [toStop, setToStop] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  const [result, setResult] = useState<RouteResult | null>(null);
  const [error, setError] = useState<string>("");

  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const routeLineRef = useRef<L.Polyline | null>(null);

  const AGENCY_ID = "607";
  const API_BASE = "https://transloc-api-1-2.p.rapidapi.com";
  const API_KEY: string = process.env.REACT_APP_TRANSLOC_API_KEY || "";
  const GT_CENTER: [number, number] = [33.7756, -84.3963];

  // Custom marker icons
  const startIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const endIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const stopIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [20, 33],
    iconAnchor: [10, 33],
    popupAnchor: [1, -28],
    shadowSize: [33, 33]
  });

  const defaultIcon = L.icon({
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  useEffect(() => {
    fetchStopsAndRoutes();
  }, []);

  useEffect(() => {
    if (mapRef.current && !mapInstanceRef.current && stops.length > 0) {
      initMap();
    }
  }, [stops]);

  useEffect(() => {
    if (result && mapInstanceRef.current) {
      updateMap();
    }
  }, [result]);

  const fetchStopsAndRoutes = async () => {
    try {
      setLoading(true);

      const headers: Record<string, string> = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "transloc-api-1-2.p.rapidapi.com",
      };

      const [stopsRes, routesRes] = await Promise.all([
        fetch(`${API_BASE}/stops.json?agencies=${AGENCY_ID}`, { headers }),
        fetch(`${API_BASE}/routes.json?agencies=${AGENCY_ID}`, { headers }),
      ]);

      const stopsData = await stopsRes.json();
      const routesData = await routesRes.json();

      setStops(Object.values(stopsData.data?.[AGENCY_ID] || {}));
      setRoutes(Object.values(routesData.data?.[AGENCY_ID] || {}));
    } catch (err) {
      setError("⚠️ Failed to load bus data. Please check your API key.");
    } finally {
      setLoading(false);
    }
  };

  const initMap = () => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current).setView(GT_CENTER, 15);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    mapInstanceRef.current = map;

    // Add all stops to map initially
    stops.forEach(stop => {
      const marker = L.marker([stop.location.lat, stop.location.lng], { icon: defaultIcon })
        .bindPopup(`<strong>${stop.name}</strong>`)
        .addTo(map);
      markersRef.current.push(marker);
    });
  };

  const clearMarkers = () => {
    if (!mapInstanceRef.current) return;

    markersRef.current.forEach(marker => mapInstanceRef.current?.removeLayer(marker));
    markersRef.current = [];
    
    if (routeLineRef.current) {
      mapInstanceRef.current.removeLayer(routeLineRef.current);
      routeLineRef.current = null;
    }
  };

  const updateMap = () => {
    if (!result || !mapInstanceRef.current) return;

    clearMarkers();

    const { fromStop, toStop, routeStops } = result;

    // Add start marker
    const startMarker = L.marker([fromStop.location.lat, fromStop.location.lng], { icon: startIcon })
      .bindPopup(`<strong>🟢 START</strong><br>${fromStop.name}`)
      .addTo(mapInstanceRef.current);
    markersRef.current.push(startMarker);

    // Add end marker
    const endMarker = L.marker([toStop.location.lat, toStop.location.lng], { icon: endIcon })
      .bindPopup(`<strong>🔴 DESTINATION</strong><br>${toStop.name}`)
      .addTo(mapInstanceRef.current);
    markersRef.current.push(endMarker);

    // Add intermediate stops
    routeStops
      .filter(s => s.stop_id !== fromStop.stop_id && s.stop_id !== toStop.stop_id)
      .forEach(stop => {
        const marker = L.marker([stop.location.lat, stop.location.lng], { icon: stopIcon })
          .bindPopup(`<strong>${stop.name}</strong>`)
          .addTo(mapInstanceRef.current!);
        markersRef.current.push(marker);
      });

    // Draw route line
    const coordinates: [number, number][] = routeStops.map(s => [s.location.lat, s.location.lng]);
    routeLineRef.current = L.polyline(coordinates, {
      color: '#3B82F6',
      weight: 4,
      opacity: 0.7
    }).addTo(mapInstanceRef.current);

    // Fit map to route
    const bounds = L.latLngBounds(coordinates);
    mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
  };

  const findOptimalRoute = async () => {
    if (!fromStop || !toStop) {
      setError("Please select both origin and destination stops.");
      return;
    }

    if (fromStop === toStop) {
      setError("Origin and destination cannot be the same.");
      return;
    }

    setSearching(true);
    setError("");
    setResult(null);

    try {
      const commonRoutes = routes.filter((route) => {
        const stopIds = route.stops || [];
        return stopIds.includes(fromStop) && stopIds.includes(toStop);
      });

      if (commonRoutes.length === 0) {
        setError("No direct routes found. Transfer may be required.");
        return;
      }

      const arrivalsRes = await fetch(
        `${API_BASE}/arrival-estimates.json?agencies=${AGENCY_ID}&stops=${fromStop}`,
        {
          headers: {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "transloc-api-1-2.p.rapidapi.com",
          } as Record<string, string>,
        }
      );
      const arrivalsData = await arrivalsRes.json();

      let bestRoute: Route | null = null;
      let earliestTime = Infinity;

      for (const route of commonRoutes) {
        const arrivals = arrivalsData.data?.[0]?.arrivals || [];
        const routeArrivals = arrivals.filter(
          (a: any) => a.route_id === route.route_id
        );
        if (routeArrivals.length > 0) {
          const nextArrival = new Date(routeArrivals[0].arrival_at).getTime();
          if (nextArrival < earliestTime) {
            earliestTime = nextArrival;
            bestRoute = {
              ...route,
              nextArrival: routeArrivals[0].arrival_at,
              minutesAway: Math.round((nextArrival - Date.now()) / 60000),
            };
          }
        }
      }

      const selectedRoute = bestRoute || commonRoutes[0];
      const fromStopData = stops.find((s) => s.stop_id === fromStop)!;
      const toStopData = stops.find((s) => s.stop_id === toStop)!;

      // Get all stops on the route between origin and destination
      const routeStopIds = selectedRoute.stops || [];
      const fromIndex = routeStopIds.indexOf(fromStop);
      const toIndex = routeStopIds.indexOf(toStop);
      
      const relevantStopIds = fromIndex < toIndex 
        ? routeStopIds.slice(fromIndex, toIndex + 1)
        : routeStopIds.slice(toIndex, fromIndex + 1).reverse();

      const routeStops = relevantStopIds
        .map(id => stops.find(s => s.stop_id === id))
        .filter((s): s is Stop => s !== undefined);

      setResult({
        route: selectedRoute,
        fromStop: fromStopData,
        toStop: toStopData,
        allRoutes: commonRoutes,
        routeStops,
      });
    } catch (err) {
      setError("⚠️ Failed to find route. Please try again.");
    } finally {
      setSearching(false);
    }
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
      <h1>🚌 Plan Your GT Trip</h1>
      <p>Find the best bus route between two GT stops with visual map.</p>

      <div className={styles.gridContainer}>
        <div className={styles.formPanel}>
          <h2>Plan Your Route</h2>

          <div className={styles.form}>
            <label>🟢 Starting Location</label>
            <select
              value={fromStop}
              onChange={(e) => setFromStop(e.target.value)}
              className={styles.select}
            >
              <option value="">Select origin stop</option>
              {stops.map((stop) => (
                <option key={stop.stop_id} value={stop.stop_id}>
                  {stop.name}
                </option>
              ))}
            </select>

            <label>🔴 Destination</label>
            <select
              value={toStop}
              onChange={(e) => setToStop(e.target.value)}
              className={styles.select}
            >
              <option value="">Select destination stop</option>
              {stops.map((stop) => (
                <option key={stop.stop_id} value={stop.stop_id}>
                  {stop.name}
                </option>
              ))}
            </select>

            <button onClick={findOptimalRoute} disabled={searching}>
              {searching ? "Finding Route..." : "Find Best Route"}
            </button>

            {error && <p className={styles.error}>{error}</p>}
          </div>

          {result && (
            <div className={styles.result}>
              <h2>✅ Best Route: {result.route.long_name}</h2>
              {result.route.minutesAway !== undefined && (
                <p className={styles.highlight}>🕒 Next bus in {result.route.minutesAway} min</p>
              )}
              <p>
                🟢 From: <strong>{result.fromStop.name}</strong>
              </p>
              <p>
                🔴 To: <strong>{result.toStop.name}</strong>
              </p>
              <p className={styles.stats}>
                📍 Stops on route: {result.routeStops.length}
              </p>
              
              {result.allRoutes.length > 1 && (
                <div className={styles.alternatives}>
                  <p><strong>Alternative routes:</strong></p>
                  {result.allRoutes
                    .filter(r => r.route_id !== result.route.route_id)
                    .map(r => (
                      <p key={r.route_id}>• {r.long_name}</p>
                    ))
                  }
                </div>
              )}
            </div>
          )}
        </div>

        <div className={styles.mapPanel}>
          <div ref={mapRef} className={styles.map}></div>
        </div>
      </div>

      <Link to="/" className={styles.linkButton}>
        ← Return Home
      </Link>
    </div>
  );
};

export default PlanTripPage;