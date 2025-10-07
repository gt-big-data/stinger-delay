import React from "react";
import { Link } from "react-router-dom";
import styles from "./Home.module.css";

const Home: React.FC = () => {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>
          Georgia Tech Stinger Shuttle Delay Visualizer
        </h1>
        <p className={styles.subtitle}>
          A Georgia Tech's Big Data Big Impact project.
        </p>
      </header>

      <section className={styles.content}>
        <p className={styles.paragraph}>Select a feature to begin:</p>

        <div className={styles.links}>
          <Link to="/plan-trip" className={styles.linkButton}>
            Plan Your Trip
          </Link>

          <Link to="/bus-routes" className={styles.linkButton}>
            View Bus Routes
          </Link>
        </div>
      </section>

      <footer className={styles.footer}>
        &copy; {new Date().getFullYear()} Stinger Delay
      </footer>
    </div>
  );
};

export default Home;
