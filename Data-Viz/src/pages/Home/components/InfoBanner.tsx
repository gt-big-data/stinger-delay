import React from "react";

const infoBannerStyle: React.CSSProperties = {
  background: "linear-gradient(135deg, #B3A369 0%, #8a7d4f 100%)",
  color: "#fff",
  padding: "20px",
  borderRadius: "12px",
  textAlign: "center",
  marginBottom: "24px",
};

const infoBannerTitleStyle: React.CSSProperties = {
  fontSize: "16px",
  fontWeight: 600,
  marginBottom: "6px",
};

const infoBannerTextStyle: React.CSSProperties = {
  fontSize: "13px",
  lineHeight: "1.4",
};

interface Props {
  title: string;
  text: string;
}

const InfoBanner: React.FC<Props> = ({ title, text }) => {
  return (
    <div style={infoBannerStyle}>
      <div style={infoBannerTitleStyle}>{title}</div>
      <div style={infoBannerTextStyle}>{text}</div>
    </div>
  );
};

export default InfoBanner;
