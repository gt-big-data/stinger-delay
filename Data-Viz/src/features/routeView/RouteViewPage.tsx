import React from "react";
import styles from "./RouteViewPage.module.css";
import { Link } from "react-router-dom";

const RouteViewPage: React.FC = () => {
  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h1>Route View Page</h1>
      <p>This is a placeholder for the Route View Page.</p>
      <Link to="/" className={styles.linkButton}>
        Return Home
      </Link>
    </div>
  );
};

export default RouteViewPage;
