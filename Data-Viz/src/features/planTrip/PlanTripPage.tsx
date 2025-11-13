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
  const [fromCoords, setFromCoords] = useState<{lat: number, lng: number} | null>(null);
  const [toCoords, setToCoords] = useState<{lat: number, lng: number} | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searching, setSearching] = useState<boolean>(false);
  const [result, setResult] = useState<RouteResult | null>(null);
  const [error, setError] = useState<string>("");

  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const routeLineRef = useRef<L.Polyline[]>([]);

  const GT_CENTER: [number, number] = [33.7756, -84.3963];

  // Expanded list of GT locations
  const popularLocations = [
    { name: "Student Center", lat: 33.7738, lng: -84.3986 },
    { name: "Klaus Advanced Computing Building", lat: 33.7772, lng: -84.3956 },
    { name: "Tech Square", lat: 33.7764, lng: -84.3889 },
    { name: "Campus Recreation Center (CRC)", lat: 33.7758, lng: -84.4025 },
    { name: "Price Gilbert Library", lat: 33.7746, lng: -84.3967 },
    { name: "Bobby Dodd Stadium", lat: 33.7722, lng: -84.3922 },
    { name: "Midtown MARTA Station", lat: 33.7812, lng: -84.3867 },
    { name: "College of Computing", lat: 33.7778, lng: -84.3975 },
    { name: "Clough Undergraduate Learning Commons", lat: 33.7751, lng: -84.3963 },
    { name: "Kendeda Building", lat: 33.7773, lng: -84.4005 },
    { name: "Van Leer Building", lat: 33.7758, lng: -84.3968 },
    { name: "Howey Physics Building", lat: 33.7775, lng: -84.3990 },
    { name: "Molecular Science Building", lat: 33.7783, lng: -84.3994 },
    { name: "Instructional Center", lat: 33.7754, lng: -84.3982 },
    { name: "Skiles Classroom Building", lat: 33.7741, lng: -84.3955 },
    { name: "Weber Space Science Building", lat: 33.7725, lng: -84.3951 },
    { name: "Ferst Center for the Arts", lat: 33.7732, lng: -84.3977 },
    { name: "North Avenue Apartments", lat: 33.7780, lng: -84.4035 },
    { name: "East Campus Apartments", lat: 33.7705, lng: -84.3880 },
    { name: "Georgia Tech Hotel", lat: 33.7763, lng: -84.3878 },
    { name: "GTRI Research Building", lat: 33.7820, lng: -84.3870 },
    { name: "Techwood Drive Apartments", lat: 33.7695, lng: -84.3850 },
    { name: "Curran Parking Deck", lat: 33.7795, lng: -84.4010 },
    { name: "Fifth Street Bridge", lat: 33.7775, lng: -84.3910 },
    { name: "Manufacture Building", lat: 33.7765, lng: -84.4015 },
  ];

  // Custom marker icons (same as before)
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

  const transferIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
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

  useEffect(() => {
    loadMockData();
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

  const loadMockData = () => {
    setLoading(true);
    setRoutes(mockRoutes);

    const allStops: Stop[] = [];
    const stopIds = new Set<string>();

    mockRoutes.forEach(route => {
      route.stops.forEach(stop => {
        if (!stopIds.has(stop.id)) {
          stopIds.add(stop.id);
          allStops.push(stop);
        }
      });
    });

    setStops(allStops);
    setLoading(false);
  };

  const initMap = () => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current).setView(GT_CENTER, 15);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    mapInstanceRef.current = map;
  };

  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const toRadian = (angle: number) => (Math.PI / 180) * angle;
    const R = 6371;
    
    const dLat = toRadian(lat2 - lat1);
    const dLon = toRadian(lon2 - lon1);
    
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRadian(lat1)) * Math.cos(toRadian(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    return distance;
  };

  const findNearestStop = (lat: number, lng: number): Stop => {
    let nearestStop = stops[0];
    let minDistance = calculateDistance(lat, lng, stops[0].latitude, stops[0].longitude);

    stops.forEach(stop => {
      const distance = calculateDistance(lat, lng, stop.latitude, stop.longitude);
      if (distance < minDistance) {
        minDistance = distance;
        nearestStop = stop;
      }
    });

    return nearestStop;
  };

  const handleFromLocationSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const locationName = e.target.value;
    setFromLocation(locationName);
    
    const location = popularLocations.find(loc => loc.name === locationName);
    if (location) {
      setFromCoords({ lat: location.lat, lng: location.lng });
    }
  };

  const handleToLocationSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const locationName = e.target.value;
    setToLocation(locationName);
    
    const location = popularLocations.find(loc => loc.name === locationName);
    if (location) {
      setToCoords({ lat: location.lat, lng: location.lng });
    }
  };

  const clearMarkers = () => {
    if (!mapInstanceRef.current) return;

    if (markersRef.current && markersRef.current.length > 0) {
      markersRef.current.forEach(marker => {
        if (marker && mapInstanceRef.current) {
          mapInstanceRef.current.removeLayer(marker);
        }
      });
    }
    markersRef.current = [];
    
    if (routeLineRef.current && routeLineRef.current.length > 0) {
      routeLineRef.current.forEach(line => {
        if (line && mapInstanceRef.current) {
          mapInstanceRef.current.removeLayer(line);
        }
      });
    }
    routeLineRef.current = [];
  };

  const updateMap = () => {
    if (!result || !mapInstanceRef.current) return;

    clearMarkers();

    const allCoordinates: [number, number][] = [];
    const colors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EC4899'];

    if (fromCoords) {
      allCoordinates.push([fromCoords.lat, fromCoords.lng]);
      const marker = L.marker([fromCoords.lat, fromCoords.lng], { icon: startIcon })
        .bindPopup(`<strong>🏁 YOUR LOCATION</strong><br>${fromLocation}<br>Walk to ${result.startStop.name}`)
        .addTo(mapInstanceRef.current);
      markersRef.current.push(marker);

      const walkLine = L.polyline([
        [fromCoords.lat, fromCoords.lng],
        [result.startStop.latitude, result.startStop.longitude]
      ], {
        color: '#6B7280',
        weight: 3,
        opacity: 0.6,
        dashArray: '5, 10'
      }).addTo(mapInstanceRef.current);
      routeLineRef.current.push(walkLine);
    }

    result.segments.forEach((segment, index) => {
      const coordinates: [number, number][] = segment.stops.map(s => [s.latitude, s.longitude]);
      allCoordinates.push(...coordinates);

      const line = L.polyline(coordinates, {
        color: colors[index % colors.length],
        weight: 4,
        opacity: 0.7
      }).addTo(mapInstanceRef.current!);
      routeLineRef.current.push(line);

      segment.stops.forEach((stop, stopIndex) => {
        let icon = stopIcon;
        let popupText = `<strong>${stop.name}</strong>`;

        if (stopIndex === 0 && index > 0) {
          icon = transferIcon;
          popupText = `<strong>🔄 TRANSFER ${index}</strong><br>${stop.name}<br>Switch to ${segment.route.name}`;
        } else if (stopIndex === segment.stops.length - 1 && index < result.segments.length - 1) {
          icon = transferIcon;
          popupText = `<strong>🔄 TRANSFER ${index + 1}</strong><br>${stop.name}<br>Switch to ${result.segments[index + 1].route.name}`;
        }

        const marker = L.marker([stop.latitude, stop.longitude], { icon })
          .bindPopup(popupText)
          .addTo(mapInstanceRef.current!);
        markersRef.current.push(marker);
      });
    });

    if (toCoords) {
      allCoordinates.push([toCoords.lat, toCoords.lng]);
      const marker = L.marker([toCoords.lat, toCoords.lng], { icon: endIcon })
        .bindPopup(`<strong>🎯 DESTINATION</strong><br>${toLocation}<br>Walk from ${result.endStop.name}`)
        .addTo(mapInstanceRef.current);
      markersRef.current.push(marker);

      const walkLine = L.polyline([
        [result.endStop.latitude, result.endStop.longitude],
        [toCoords.lat, toCoords.lng]
      ], {
        color: '#6B7280',
        weight: 3,
        opacity: 0.6,
        dashArray: '5, 10'
      }).addTo(mapInstanceRef.current);
      routeLineRef.current.push(walkLine);
    }

    if (allCoordinates.length > 0) {
      const bounds = L.latLngBounds(allCoordinates);
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
    }
  };

  const findOptimalRoute = () => {
    if (!fromCoords || !toCoords) {
      setError("Please select both starting location and destination.");
      return;
    }

    if (fromLocation === toLocation) {
      setError("Starting location and destination cannot be the same.");
      return;
    }

    setSearching(true);
    setError("");
    setResult(null);

    setTimeout(() => {
      try {
        const startStop = findNearestStop(fromCoords.lat, fromCoords.lng);
        const endStop = findNearestStop(toCoords.lat, toCoords.lng);

        const walkDistStart = calculateDistance(fromCoords.lat, fromCoords.lng, startStop.latitude, startStop.longitude);
        const walkDistEnd = calculateDistance(toCoords.lat, toCoords.lng, endStop.latitude, endStop.longitude);

        console.log(`Nearest start stop: ${startStop.name} (${(walkDistStart * 1000).toFixed(0)}m away)`);
        console.log(`Nearest end stop: ${endStop.name} (${(walkDistEnd * 1000).toFixed(0)}m away)`);

        const result = findRouteWithBFS(startStop.id, endStop.id);
        
        if (result) {
          setResult({
            ...result,
            startStop,
            endStop,
            walkingDistanceStart: walkDistStart,
            walkingDistanceEnd: walkDistEnd
          });
        } else {
          setError("No routes found between these locations. Try different locations.");
        }
      } catch (err) {
        setError("⚠️ Failed to find route. Please try again.");
        console.error(err);
      } finally {
        setSearching(false);
      }
    }, 500);
  };

  // Fixed BFS algorithm
  const findRouteWithBFS = (startStopId: string, endStopId: string): Omit<RouteResult, 'startStop' | 'endStop' | 'walkingDistanceStart' | 'walkingDistanceEnd'> | null => {
    console.log('=== Starting BFS from', startStopId, 'to', endStopId, '===');

    if (startStopId === endStopId) {
      console.log('Start and end are the same!');
      return null;
    }

    interface PathNode {
      stopId: string;
      routeId: string;
      segments: RouteSegment[];
      visitedStops: Set<string>;
    }

    const queue: PathNode[] = [];
    const visited = new Map<string, Set<string>>();

    // Initialize: Find all routes that have the start stop
    routes.forEach(route => {
      const stopIdx = route.stops.findIndex(s => s.id === startStopId);
      if (stopIdx !== -1) {
        console.log(`Found start stop in route: ${route.name}`);
        queue.push({
          stopId: startStopId,
          routeId: route.id,
          segments: [],
          visitedStops: new Set([startStopId])
        });
      }
    });

    console.log(`Starting with ${queue.length} routes`);

    let iterations = 0;
    const maxIterations = 1000;

    while (queue.length > 0 && iterations < maxIterations) {
      iterations++;
      const current = queue.shift()!;

      // Mark as visited
      const key = `${current.stopId}-${current.routeId}`;
      if (visited.has(current.stopId)) {
        if (visited.get(current.stopId)!.has(current.routeId)) {
          continue;
        }
        visited.get(current.stopId)!.add(current.routeId);
      } else {
        visited.set(current.stopId, new Set([current.routeId]));
      }

      const currentRoute = routes.find(r => r.id === current.routeId);
      if (!currentRoute) continue;

      const currentStopIdx = currentRoute.stops.findIndex(s => s.id === current.stopId);
      if (currentStopIdx === -1) continue;

      // Explore all stops forward on this route
      for (let i = currentStopIdx + 1; i < currentRoute.stops.length; i++) {
        const nextStop = currentRoute.stops[i];

        // Found the destination!
        if (nextStop.id === endStopId) {
          const finalSegment: RouteSegment = {
            route: currentRoute,
            fromStop: currentRoute.stops[currentStopIdx],
            toStop: nextStop,
            stops: currentRoute.stops.slice(currentStopIdx, i + 1)
          };

          const allSegments = [...current.segments, finalSegment];
          console.log(`✅ Found route with ${allSegments.length} segments!`);

          return {
            segments: allSegments,
            totalStops: allSegments.reduce((sum, seg) => sum + seg.stops.length, 0),
            transfers: allSegments.length - 1
          };
        }

        // Skip already visited stops
        if (current.visitedStops.has(nextStop.id)) continue;

        // Check for transfer opportunities at this stop
        routes.forEach(transferRoute => {
          if (transferRoute.id === currentRoute.id) return;

          const transferStopIdx = transferRoute.stops.findIndex(
            s => s.id === nextStop.id || s.name === nextStop.name
          );

          if (transferStopIdx !== -1) {
            // Create segment to this transfer point
            const segmentToTransfer: RouteSegment = {
              route: currentRoute,
              fromStop: currentRoute.stops[currentStopIdx],
              toStop: nextStop,
              stops: currentRoute.stops.slice(currentStopIdx, i + 1)
            };

            const newVisited = new Set(current.visitedStops);
            newVisited.add(nextStop.id);

            queue.push({
              stopId: nextStop.id,
              routeId: transferRoute.id,
              segments: [...current.segments, segmentToTransfer],
              visitedStops: newVisited
            });
          }
        });
      }
    }

    console.log(`❌ No route found after ${iterations} iterations`);
    return null;
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
      <p>Enter your location and destination - we'll find the best route with unlimited transfers!</p>

      <div className={styles.gridContainer}>
        <div className={styles.formPanel}>
          <h2>Plan Your Route</h2>

          <div className={styles.form}>
            <label>🏁 Starting Location</label>
            <select
              value={fromLocation}
              onChange={handleFromLocationSelect}
              className={styles.select}
            >
              <option value="">Select starting location</option>
              {popularLocations.map((loc) => (
                <option key={loc.name} value={loc.name}>
                  {loc.name}
                </option>
              ))}
            </select>

            <label>🎯 Destination</label>
            <select
              value={toLocation}
              onChange={handleToLocationSelect}
              className={styles.select}
            >
              <option value="">Select destination</option>
              {popularLocations.map((loc) => (
                <option key={loc.name} value={loc.name}>
                  {loc.name}
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
              <h2>✅ Route Found</h2>
              <p className={styles.highlight}>
                {result.transfers === 0 ? (
                  <>🚌 Direct route - No transfers needed!</>
                ) : (
                  <>🔄 {result.transfers} transfer{result.transfers > 1 ? 's' : ''} required</>
                )}
              </p>
              
              <div className={styles.walking}>
                <p>🚶 Walk {(result.walkingDistanceStart * 1000).toFixed(0)}m to <strong>{result.startStop.name}</strong></p>
              </div>

              {result.segments.map((segment, index) => (
                <div key={index} className={styles.segment}>
                  <h3>
                    {index === 0 ? '🟢' : '🔄'} {segment.route.name}
                  </h3>
                  <p>Board at: <strong>{segment.fromStop.name}</strong></p>
                  <p>Ride {segment.stops.length - 1} stop{segment.stops.length > 2 ? 's' : ''}</p>
                  <p>Exit at: <strong>{segment.toStop.name}</strong></p>
                  {index < result.segments.length - 1 && (
                    <p className={styles.transfer}>
                      ↓ Transfer to {result.segments[index + 1].route.name}
                    </p>
                  )}
                </div>
              ))}

              <div className={styles.walking}>
                <p>🚶 Walk {(result.walkingDistanceEnd * 1000).toFixed(0)}m to destination</p>
              </div>
              
              <p className={styles.stats}>
                Total: {result.totalStops} bus stops + {((result.walkingDistanceStart + result.walkingDistanceEnd) * 1000).toFixed(0)}m walking
              </p>
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
