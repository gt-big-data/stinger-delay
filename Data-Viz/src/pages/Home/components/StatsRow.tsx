import React from "react";
import StatCard from "./StatCard";

const quickStatsStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(3, 1fr)",
  gap: "12px",
  marginBottom: "24px",
};

interface Stat {
  label: string;
  value: string | number;
}

interface Props {
  stats: Stat[];
}

const StatsRow: React.FC<Props> = ({ stats }) => {
  return (
    <div style={quickStatsStyle}>
      {stats.map((s, idx) => (
        <StatCard key={idx} label={s.label} value={s.value} />
      ))}
    </div>
  );
};

export default StatsRow;
