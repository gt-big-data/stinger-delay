// import React from "react";
// import { DelayPrediction } from "@/types/delay";

// interface ETAInfoProps {
//   predictions: DelayPrediction[];
//   selectedStopId?: string;
// }

// const ETAInfo: React.FC<ETAInfoProps> = ({ predictions, selectedStopId }) => {
//   const filtered = selectedStopId
//     ? predictions.filter((p) => p.stopId === selectedStopId)
//     : predictions;

//   if (!filtered.length) {
//     return <p>No upcoming buses or delay data available.</p>;
//   }

//   return (
//     <div>
//       <h3>ETA & Delay Info</h3>
//       <ul>
//         {filtered.map((p) => (
//           <li key={`${p.routeId}-${p.stopId}`}>
//             Route {p.routeId}: ETA {new Date(p.eta).toLocaleTimeString()} —
//             Delay {p.predictedDelayMinutes} min
//           </li>
//         ))}
//       </ul>
//     </div>
//   );
// };

// export default ETAInfo;

import React from "react";
import { DelayPrediction } from "@/types/delay";
import styles from "./ETAInfo.module.css";

interface Props {
  predictions: DelayPrediction[];
  selectedStopId?: string;
}

const ETAInfo: React.FC<Props> = ({ predictions, selectedStopId }) => {
  const filtered = selectedStopId
    ? predictions.filter((p) => p.stopId === selectedStopId)
    : predictions;

  if (!filtered.length) {
    return <p className={styles.empty}>No upcoming buses.</p>;
  }

  return (
    <div className={styles.etaWrapper}>
      <h3 className={styles.title}>Arrivals</h3>

      {filtered.map((p) => (
        <div key={`${p.routeId}-${p.stopId}`} className={styles.etaRow}>
          <span className={styles.etaTime}>{p.eta}</span>
          <span className={styles.delay}>
            Delay: {p.predictedDelayMinutes} min
          </span>
        </div>
      ))}
    </div>
  );
};

export default ETAInfo;
