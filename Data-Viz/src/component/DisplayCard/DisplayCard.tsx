import React from "react";

interface DisplayCardProps {
  title: string;
  description: string;
  imageUrl?: string;
}

const DisplayCard: React.FC<DisplayCardProps> = ({
  title,
  description,
  imageUrl,
}) => {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: "8px",
        padding: "16px",
        maxWidth: "320px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        background: "#fff",
      }}
    >
      {imageUrl && (
        <img
          src={imageUrl}
          alt={title}
          style={{ width: "100%", borderRadius: "6px", marginBottom: "12px" }}
        />
      )}
      <h2 style={{ margin: "0 0 8px 0", fontSize: "1.25rem" }}>{title}</h2>
      <p style={{ margin: 0, color: "#555" }}>{description}</p>
    </div>
  );
};

export default DisplayCard;
