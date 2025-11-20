import React from "react";
import { Route } from "@/types/route";
import { Link } from "react-router-dom";
import styles from "./RouteCard.module.css";

interface Props {
  route: Route;
}

const RouteCard: React.FC<Props> = ({ route }) => {
  const routeColorClass = route.name.toLowerCase().includes("gold")
    ? styles.gold
    : route.name.toLowerCase().includes("red")
    ? styles.red
    : route.name.toLowerCase().includes("green")
    ? styles.green
    : route.name.toLowerCase().includes("blue")
    ? styles.blue
    : route.name.toLowerCase().includes("purple")
    ? styles.purple
    : styles.defaultRoute;

  return (
    <Link
      to={`/bus-routes?routeId=${route.id}`}
      className={`${styles.routeCard} ${routeColorClass}`}
    >
      <div className={styles.routeInfo}>
        <div className={styles.routeHeader}>
          <div className={styles.routeName}>{route.name}</div>
          <div
            className={`${styles.routeBadge} ${
              route.active ? styles.active : styles.inactive
            }`}
          >
            {route.active ? "Active" : "Inactive"}
          </div>
        </div>

        <div className={styles.routeDetails}>
          <div className={styles.detailItem}>
            📍 <span>{route.stops.length} Stops</span>
          </div>
          <div className={styles.detailItem}>
            🚌 <span>{route.busLocations?.length ?? 0} Buses</span>
          </div>
          <div className={styles.detailItem}>
            {(() => {
              // Derive aggregate delay from predictions (max predicted delay)
              const predictions = route.delayPredictions ?? [];
              const delay = predictions.length
                ? Math.max(
                    ...predictions.map((p) => p.predictedDelayMinutes || 0)
                  )
                : 0;
              const isInactive = route.active === false;
              if (isInactive) {
                return (
                  <span
                    className={`${styles.delayIndicator} ${styles.unknown}`.trim()}
                  >
                    Unknown
                  </span>
                );
              }
              const label = delay > 0 ? `+${delay} min` : "On time";
              const severityClass =
                delay >= 5 ? styles.high : delay > 0 ? styles.medium : "";
              return (
                <span
                  className={`${styles.delayIndicator} ${severityClass}`.trim()}
                >
                  {label}
                </span>
              );
            })()}
          </div>
        </div>
      </div>

      <div className={styles.routeArrow}>→</div>
    </Link>
  );
};

export default RouteCard;
