import React from "react";
import styles from "./Home.module.css";
import { mockRoutes } from "../../lib/mocks/mockTripData";
import InfoBanner from "./components/InfoBanner";
import StatsRow from "./components/StatsRow";
import SectionHeader from "./components/SectionHeader";
import RoutesGrid from "./components/RoutesGrid";

const Home: React.FC = () => {
  return (
    <div className={styles.screen}>
      <header className={styles.mainHeader}>
        <div className={styles.appLogo}>🐝</div>
        <div className={styles.appTitle}>
          Georgia Tech Stinger Shuttle Delay
        </div>
        <div className={styles.appSubtitle}>
          A Georgia Tech's Big Data Big Impact project
        </div>
      </header>
      <div className={styles.container}>
        <InfoBanner
          title="Real-Time Transit Updates"
          text="Track your bus with live locations, accurate ETAs, and predicted delays powered by machine learning"
        />

        <StatsRow
          stats={[
            { label: "Active Routes", value: mockRoutes.length },
            { label: "Buses Running", value: "12" },
            { label: "Avg. Delay", value: "~3 min" },
          ]}
        />

        <SectionHeader title="Select a Route" />

        <RoutesGrid routes={mockRoutes} />
      </div>

      <footer className={styles.footer}>
        &copy; {new Date().getFullYear()} Stinger Delay
      </footer>
    </div>
  );
};

export default Home;
