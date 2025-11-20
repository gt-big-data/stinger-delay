import React from "react";
import { Route } from "@/types/route";
import RouteCard from "./RouteCard";

const routesGridStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "16px",
  width: "100%",
};

interface Props {
  routes: Route[];
}

const RoutesGrid: React.FC<Props> = ({ routes }) => {
  return (
    <div style={routesGridStyle}>
      {routes.map((route) => (
        <RouteCard key={route.id} route={route} />
      ))}
    </div>
  );
};

export default RoutesGrid;
