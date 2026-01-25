import React from "react";
import { Route } from "@/types/route";

const headerStyles = {
  display: "flex",
  alignItems: "center",
  gap: "0.75rem",
  paddingBottom: "1rem",
  borderBottom: "1px solid #ddd",
};

const colorDotStyles = {
  width: "18px",
  height: "18px",
  borderRadius: "50%",
};

const titleStyles = {
  fontSize: "1.3rem",
  fontWeight: 600,
  color: "var(--primary-color)",
};

interface Props {
  route: Route;
}

const RouteHeader: React.FC<Props> = ({ route }) => {
  return (
    <div style={headerStyles}>
      <div style={{ ...colorDotStyles, backgroundColor: route.color }} />
      <h2 style={titleStyles}>{route.name}</h2>
    </div>
  );
};

export default RouteHeader;
