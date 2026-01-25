import React from "react";
import { Stop } from "@/types/stop";
import styles from "./StopList.module.css";

interface Props {
  stops: Stop[];
  selectedStopId?: string;
  onSelectStop: (stop: Stop) => void;
}

const StopList: React.FC<Props> = ({ stops, selectedStopId, onSelectStop }) => {
  return (
    <div className={styles.timelineContainer}>
      {stops.map((stop, index) => (
        <div
          key={stop.id}
          className={`${styles.stopItem} ${
            selectedStopId === stop.id ? styles.active : ""
          }`}
          onClick={() => onSelectStop(stop)}
        >
          <div className={styles.dot} />
          <div className={styles.stopContent}>
            <div className={styles.stopName}>{stop.name}</div>

            {index < stops.length - 1 && <div className={styles.line} />}
          </div>
        </div>
      ))}
    </div>
  );
};

export default StopList;
