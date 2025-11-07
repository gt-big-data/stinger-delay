import React, { useState, useEffect } from "react";
import styles from "./RouteViewPage.module.css";
import { Route } from "@/types/route";
import { Stop } from "@/types/stop";
import { DelayPrediction, LiveBusLocation } from "@/types/delay";
import { fetchRouteGeometry, fetchTimeMatrix } from "@/lib/api/ors";
import { mockRoutes } from "../../lib/mocks/mockTripData";
import StopList from "./components/StopList";
import RouteMap from "./components/RouteMap";
import ETAInfo from "./components/ETAInfo";
import menu_open from "../../assets/menu_open.png";
import menu_closed from "../../assets/menu_closed.png";

const RouteViewPage: React.FC = () => {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
  const [selectedStop, setSelectedStop] = useState<Stop | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    setRoutes(mockRoutes);
  }, []);

  const handleRouteSelect = (routeId: string) => {
    const route = routes.find((r) => r.id === routeId) || null;
    setSelectedRoute(route);
    setSelectedStop(null);
  };

  const handleStopSelect = (stop: Stop) => {
    setSelectedStop(stop);
  };

  return (
    <div className={styles.container}>
      {/* <h1 className={styles.header}>Route View</h1> */}
      <div className={styles.mapFullWrapper}>
        <button
          className={styles.collapseToggleAlways}
          onClick={() => setSidebarCollapsed((c) => !c)}
        >
          {sidebarCollapsed ? (
            <img src={menu_open} alt="Expand Sidebar" />
          ) : (
            <img src={menu_closed} alt="Collapse Sidebar" />
          )}
        </button>

        <div
          className={`${styles.sidebarOverlay} ${
            sidebarCollapsed ? styles.hidden : ""
          }`}
        >
          <select
            className={styles.selectRoute}
            value={selectedRoute?.id || ""}
            onChange={(e) => handleRouteSelect(e.target.value)}
          >
            <option value="">Select a route</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>

          {selectedRoute && (
            <StopList
              stops={selectedRoute.stops}
              onSelectStop={handleStopSelect}
              selectedStopId={selectedStop?.id}
            />
          )}

          {selectedRoute && (
            <div className={styles.infoPanel}>
              <ETAInfo
                predictions={selectedRoute.delayPredictions || []}
                selectedStopId={selectedStop?.id}
              />
            </div>
          )}
        </div>

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
