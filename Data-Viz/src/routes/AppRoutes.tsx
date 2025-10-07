import React from "react";
import { Routes, Route } from "react-router-dom";
import Shell from "../shell/Shell";
import Home from "../pages/Home/Home";
import PlanTripPage from "../features/planTrip/PlanTripPage";
import RouteViewPage from "../features/routeView/RouteViewPage";

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Shell />}>
        <Route index element={<Home />} />
        <Route path="plan-trip" element={<PlanTripPage />} />
        <Route path="bus-routes" element={<RouteViewPage />} />
      </Route>
    </Routes>
  );
};
