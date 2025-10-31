import React from "react";
import { Stop } from "@/types/stop";

interface StopListProps {
  stops: Stop[];
  onSelectStop: (stop: Stop) => void;
  selectedStopId?: string;
}

const StopList: React.FC<StopListProps> = ({
  stops,
  onSelectStop,
  selectedStopId,
}) => {
  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {stops.map((stop) => (
        <li
          key={stop.id}
          onClick={() => onSelectStop(stop)}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "#f5f5f5";
            e.currentTarget.style.transition = "background-color 0.15s ease";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor =
              stop.id === selectedStopId ? "#eee" : "transparent";
          }}
          style={{
            padding: "1rem",
            cursor: "pointer",
            backgroundColor:
              stop.id === selectedStopId ? "#eee" : "transparent",
          }}
        >
          {stop.name}
        </li>
      ))}
    </ul>
  );
};

export default StopList;
