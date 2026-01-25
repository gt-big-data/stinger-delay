import React from "react";
import styles from "./RouteStatsBanner.module.css";
import { Route } from "@/types/route";

interface Props {
  route: Route;
}

const RouteStatsBanner: React.FC<Props> = ({ route }) => {
  const totalStops = route.stops?.length || 0;
  const busCount = route.busLocations?.length || 0;

  // Compute average delay (if any predictions exist)
  const avgDelay = route.delayPredictions?.length
    ? Math.round(
        route.delayPredictions.reduce(
          (sum, p) => sum + (p.predictedDelayMinutes || 0),
          0
        ) / route.delayPredictions.length
      )
    : 0;

  return (
    <div className={styles.infoBannerRoute}>
      <div className={styles.bannerItem}>
        <div className={styles.bannerLabel}>Total Stops</div>
        <div className={styles.bannerValue}>{totalStops}</div>
      </div>

      <div className={styles.bannerItem}>
        <div className={styles.bannerLabel}>Buses</div>
        <div className={styles.bannerValue}>{busCount}</div>
      </div>

      <div className={styles.bannerItem}>
        <div className={styles.bannerLabel}>Avg. Delay</div>
        <div
          className={styles.bannerValue}
          style={{ color: avgDelay > 0 ? "#ffc107" : "#28a745" }}
        >
          {avgDelay > 0 ? `+${avgDelay} min` : "On Time"}
        </div>
      </div>
    </div>
  );
};

export default RouteStatsBanner;
