import React from "react";
import styles from "./StopTimeline.module.css";
import { Stop } from "@/types/stop";
import { DelayPrediction } from "@/types/delay";
import { LiveBusLocation } from "@/types/delay";

interface Props {
  stops: Stop[];
  predictions: DelayPrediction[];
  selectedStopId?: string;
  onSelectStop?: (stop: Stop) => void;
  busLocations?: LiveBusLocation[];
}

const StopTimeline: React.FC<Props> = ({
  stops,
  predictions,
  selectedStopId,
  onSelectStop,
  busLocations,
}) => {
  const getPredictionForStop = (stopId: string) =>
    predictions.find((p) => p.stopId === stopId);

  return (
    <div className={styles.timeline}>
      {stops.map((stop, index) => {
        const prediction = getPredictionForStop(stop.id);

        const isSelected = selectedStopId === stop.id;
        const isNext = index === 0; // You can replace this when real "next stop" logic is present.
        const isPassed = false; // Placeholder until real bus tracking logic.

        const stopClass = `${styles.stopItem} 
          ${isPassed ? styles.passed : ""} 
          ${isNext ? styles.next : ""} 
          ${isSelected ? styles.next : ""}`;

        return (
          <div
            key={stop.id}
            className={stopClass}
            onClick={() => onSelectStop?.(stop)}
            style={{ cursor: "pointer" }}
          >
            <div className={styles.stopMarker} />

            <div className={styles.stopNumber}>Stop {index + 1}</div>

            <div className={styles.stopHeader}>
              <div className={styles.stopName}>{stop.name}</div>

              <div className={styles.stopTime}>
                {prediction ? (
                  <>
                    <span className={isPassed ? styles.etaPassed : styles.eta}>
                      {prediction.eta}
                    </span>

                    {prediction.predictedDelayMinutes > 0 && (
                      <span
                        className={
                          prediction.predictedDelayMinutes >= 2
                            ? styles.delayHigh
                            : styles.delay
                        }
                      >
                        +{prediction.predictedDelayMinutes} min
                      </span>
                    )}
                  </>
                ) : (
                  <span className={styles.etaPassed}>No ETA</span>
                )}
              </div>
            </div>
          </div>
        );
      })}

      {/* Example bus position block */}
      {busLocations && busLocations.length > 0 && (
        <div className={styles.busPosition}>
          <div className={styles.busIcon}>🚌</div>
          <div className={styles.busInfo}>
            <div className={styles.busNumber}>Bus #{busLocations[0].busId}</div>
            <div className={styles.busStatus}>Currently Moving</div>
            <div className={styles.betweenStops}>Between stops</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StopTimeline;
