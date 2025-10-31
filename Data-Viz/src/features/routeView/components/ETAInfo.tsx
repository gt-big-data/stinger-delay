import React from "react";
import { DelayPrediction } from "@/types/delay";

interface ETAInfoProps {
  predictions: DelayPrediction[];
  selectedStopId?: string;
}

const ETAInfo: React.FC<ETAInfoProps> = ({ predictions, selectedStopId }) => {
  const filtered = selectedStopId
    ? predictions.filter((p) => p.stopId === selectedStopId)
    : predictions;

  if (!filtered.length) {
    return <p>No upcoming buses or delay data available.</p>;
  }

  return (
    <div>
      <h3>ETA & Delay Info</h3>
      <ul>
        {filtered.map((p) => (
          <li key={`${p.routeId}-${p.stopId}`}>
            Route {p.routeId}: ETA {new Date(p.eta).toLocaleTimeString()} —
            Delay {p.predictedDelayMinutes} min
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ETAInfo;
