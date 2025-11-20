import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import styles from "./RouteViewPage.module.css";

import { Route } from "@/types/route";
import { Stop } from "@/types/stop";
import { mockRoutes } from "../../lib/mocks/mockTripData";

import RouteHeader from "./components/RouteHeader";
import RouteStatsBanner from "./components/RouteStatsBanner";
import StopTimeline from "./components/StopTimeline";
import RouteMap from "./components/RouteMap";

const RouteViewPage: React.FC = () => {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const [searchParams] = useSearchParams();
  const routeId = searchParams.get("routeId");

  useEffect(() => {
    setRoutes(mockRoutes);
  }, []);

  useEffect(() => {
    if (!routes.length) return;

    if (routeId) {
      const found = routes.find((r) => r.id === routeId);
      setSelectedRoute(found || routes[0]);
    } else {
      setSelectedRoute(routes[0]);
    }
  }, [routes, routeId]);

  return (
    <div className={styles.container}>
      <div className={styles.mapFullWrapper}>
        {/* Sidebar toggle button */}
        <button
          className={styles.collapseToggleAlways}
          onClick={() => setSidebarCollapsed((c) => !c)}
        >
          {sidebarCollapsed ? (
            <span aria-label="Expand sidebar">🡢</span>
          ) : (
            <span aria-label="Collapse sidebar">🡠</span>
          )}
        </button>

        {/* Sidebar */}
        <div
          className={`${styles.sidebarOverlay} ${
            sidebarCollapsed ? styles.hidden : ""
          }`}
        >
          {selectedRoute && <RouteHeader route={selectedRoute} />}

          {selectedRoute && <RouteStatsBanner route={selectedRoute} />}

          {selectedRoute && (
            <StopTimeline
              stops={selectedRoute.stops}
              predictions={selectedRoute.delayPredictions || []}
              busLocations={selectedRoute.busLocations}
            />
          )}
        </div>

        {/* Map container */}
        <div className={styles.mapContainer}>
          <RouteMap
            stops={selectedRoute?.stops || []}
            routes={routes}
            busLocations={selectedRoute?.busLocations}
            pathCoordinates={selectedRoute?.pathGeoJson}
          />
        </div>
      </div>
    </div>
  );
};

export default RouteViewPage;
