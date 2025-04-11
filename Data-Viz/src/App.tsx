import React from "react";
import "./App.css";
import Home from "./pages/Home";
import { Route, Routes } from "react-router-dom";

const App = () => {
  return (
    <div className="App">
      <Routes>
        {/* Default route */}
        <Route path="/" element={<Home />} />
        {/* Existing route */}
        <Route path="/home" element={<Home />} />
      </Routes>
    </div>
  );
};

export default App;
