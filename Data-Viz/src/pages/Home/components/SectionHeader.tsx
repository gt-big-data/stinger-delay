import React from "react";

const sectionHeaderStyle: React.CSSProperties = {
  fontSize: "18px",
  fontWeight: 600,
  color: "#003057",
  marginBottom: "16px",
  paddingLeft: "4px",
};

interface Props {
  title: string;
}

const SectionHeader: React.FC<Props> = ({ title }) => {
  return <div style={sectionHeaderStyle}>{title}</div>;
};

export default SectionHeader;
