import React from "react";
import { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./Home.css";

const Home: React.FC = () => {
  // Fake data so far for bus routes and stops
  const busRoutes = {
    Gold: ["Stop A", "Stop B", "Stop C"],
    Red: ["Stop D", "Stop E", "Stop F"],
    Blue: ["Stop G", "Stop H", "Stop I"],
    Green: ["Stop J", "Stop K", "Stop L"],
  };

  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [selectedStop, setSelectedStop] = useState<string | null>(null);

  return (
    <div className="page">
      {/* Top Left Text */}
      <div className="top-left-text">GT Stinger Delay</div>

      {/* Title Section */}
      <div className="title-container">
        <div className="title-text">
          Georgia Tech Stinger Shuttle Delay Visualizer
        </div>
      </div>

      {/* Description */}
      <p
        style={{
          fontSize: "18px",
          color: "lightgray",
          marginBottom: "30px",
          marginTop: "30px",
        }}
      >
        A Big Data Big Impact project by the Georgia Tech Data Science Club.
      </p>

      {/* Dropdown for Routes */}
      <div className="dropdown-container">
        <label htmlFor="route-select" className="dropdown-label">
          Choose your bus line
        </label>
        <select
          id="route-select"
          onChange={(e) => {
            setSelectedRoute(e.target.value);
            setSelectedStop(null);
          }}
          value={selectedRoute || ""}
          style={{ marginTop: "10px", fontSize: "16px", width: "100%" }}
        >
          <option value="" disabled>
            Select a route
          </option>
          {Object.keys(busRoutes).map((route) => (
            <option key={route} value={route}>
              {route}
            </option>
          ))}
        </select>
      </div>

      {/* Dropdown for Stops */}
      {selectedRoute && (
        <div className="dropdown-container">
          <label htmlFor="stop-select" className="dropdown-label">
            Current stop
          </label>
          <select
            id="stop-select"
            onChange={(e) => setSelectedStop(e.target.value)}
            value={selectedStop || ""}
            style={{ marginTop: "10px", fontSize: "16px", width: "100%" }}
          >
            <option value="" disabled>
              Select a stop
            </option>
            {busRoutes[selectedRoute as keyof typeof busRoutes].map((stop) => (
              <option key={stop} value={stop}>
                {stop}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Map Placeholder */}
      {selectedRoute && selectedStop && (
        <div style={{ marginTop: "30px" }}>
          <p>
            Displaying map for <strong>{selectedRoute}</strong> at{" "}
            <strong>{selectedStop}</strong>.
          </p>
          <div className="map-placeholder">Static Map Image</div>
        </div>
      )}
    </div>
  );
};

export default Home;
