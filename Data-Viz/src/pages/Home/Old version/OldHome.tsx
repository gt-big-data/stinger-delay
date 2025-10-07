import React from "react";
import { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./Home.css";

const Home: React.FC = () => {
  // Need more routes and stops from database
  const busRoutes = {
    Gold: [
      "Marta Midtown Station",
      "Tech Square WB",
      "5th Street Bridge WB",
      "Russ Chandler Stadium",
      "Klaus Building WB",
      "Nanotechnology",
      "Kendeda Building",
      "Couch Park",
      "CRC & Stamps Health",
      "Ferst Drive & Campus Center",
      "Transit Hub",
      "Campus Center",
      "Exhibition Hall",
      "Ferst Dr & Hemphill Ave",
      "Cherry Emerson",
      "5th Street Bridge EB",
      "Tech Square EB",
      "College of Business",
      "Academic of Medicine",
    ],
    Red: [
      "North Avenue Apts",
      "Tech Tower",
      "Transit Hub & Weber Building",
      "Campus Center",
      "Exhibition Hall",
      "Fitten Hall",
      "West Village",
      "8th St & Hemphill Ave",
      "Ferst Dr & Hemphill Ave",
      "Cherry Emerson",
      "Klaus Building EB",
    ],
    Blue: [
      "Paper Tricentennial",
      "West Village",
      "8th St & Hemphill Ave",
      "Couch Park",
      "CRC & Stamps Health",
      "Ferst Drive & Campus Center",
      "Transit Hub & Tech Parkway",
      "Ferst Dr & Cherry St",
      "North Avenue Apts",
      "Brown Residence Hall",
    ],
    Green: [
      "575 14th Street",
      "14th St & State St",
      "GTRI Conference Center",
      "10th and Fowler",
      "Graduate Living Center",
      "Baker Building",
      "Kendeda Building",
      "Couch Park",
      "CRC & Stamps Health",
      "Ferst Drive & Campus Center",
      "Transit Hub",
      "Campus Center",
      "Exhibition Hall",
    ],
    Clough: [
      "Clough Commons",
      "5th Street Bridge EB",
      "Tech Square EB",
      "Spring St @ 4th St",
      "West Peachtree @ 4th St",
      "Tech Square WB",
      "Techwood & 5th SW Corner",
    ],
  };

  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [selectedStop, setSelectedStop] = useState<string | null>(null);
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [delayTime, setDelayTime] = useState<number | null>(null);

  const handleImageError = () => {
    setImageSrc("/assets/images/default.png");
  };

  const handleRouteChange = (route: string) => {
    setSelectedRoute(route);
    setSelectedStop(null);
    setImageSrc(`/assets/images/${route.replace(/\s+/g, "")}.png`);
  };

  // Randomize delay time whenever the selected stop changes
  useEffect(() => {
    if (selectedStop) {
      const randomDelay = Math.floor(Math.random() * 15) + 1; // 1-15 mins
      setDelayTime(randomDelay);
    } else {
      setDelayTime(null); // Reset delay time if no stop is selected
    }
  }, [selectedStop]);

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
        A Georgia Tech's Big Data Big Impact project
      </p>

      {/* Dropdown for Routes */}
      <div className="dropdown-wrapper">
        <label htmlFor="route-select" className="dropdown-label">
          Choose your bus line
        </label>
        <select
          className="dropdown-container"
          id="route-select"
          onChange={(e) => handleRouteChange(e.target.value)}
          value={selectedRoute || ""}
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
        <div className="dropdown-wrapper">
          <label htmlFor="stop-select" className="dropdown-label">
            Current stop
          </label>
          <select
            className="dropdown-container"
            id="stop-select"
            onChange={(e) => setSelectedStop(e.target.value)}
            value={selectedStop || ""}
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

      {/* Delay Time & Map Placeholder */}
      <div style={{ marginTop: "30px" }}>
        {selectedRoute && selectedStop && (
          <div>
            <p className="delay-text">Delay Time: {delayTime} minutes</p>
            <p>
              Displaying map for <strong>{selectedRoute}</strong> route at{" "}
              <strong>{selectedStop}</strong>
            </p>
          </div>
        )}
        <div className="map-placeholder">
          <img
            src={imageSrc || "/assets/images/default.png"}
            alt={`${selectedRoute || "Default"} route`}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
            onError={handleImageError}
          />
        </div>
      </div>
    </div>
  );
};

export default Home;
