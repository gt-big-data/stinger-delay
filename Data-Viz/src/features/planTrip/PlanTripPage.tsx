import React from "react";
import { Link } from "react-router-dom";
import styles from "./PlanTripPage.module.css";

const PlanTripPage: React.FC = () => {
  return (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h1>Plan Trip</h1>
      <p>This is a placeholder for the Plan Trip Page.</p>
      <Link to="/" className={styles.linkButton}>
        Return Home
      </Link>
    </div>
  );
};

export default PlanTripPage;
