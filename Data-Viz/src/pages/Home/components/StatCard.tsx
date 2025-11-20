import React from "react";

const statCardStyle: React.CSSProperties = {
  background: "white",
  padding: "16px",
  borderRadius: "12px",
  textAlign: "center",
  boxShadow: "0 2px 6px rgba(0, 0, 0, 0.06)",
};

const statValueStyle: React.CSSProperties = {
  fontSize: "24px",
  fontWeight: 700,
  color: "#003057",
  marginBottom: "4px",
};

const statLabelStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#666",
};

interface Props {
  label: string;
  value: string | number;
}

const StatCard: React.FC<Props> = ({ label, value }) => {
  return (
    <div style={statCardStyle}>
      <div style={statValueStyle}>{value}</div>
      <div style={statLabelStyle}>{label}</div>
    </div>
  );
};

export default StatCard;
