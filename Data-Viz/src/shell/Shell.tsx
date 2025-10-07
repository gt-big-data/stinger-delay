import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import styles from "./Shell.module.css";

const Shell: React.FC = () => {
  return (
    <div className={styles.appShell}>
      <nav className={styles.navbar}>
        <NavLink to="/" end>
          Home
        </NavLink>
        <NavLink to="/plan-trip">Plan Trip</NavLink>
        <NavLink to="/bus-routes">Bus Routes</NavLink>
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
};

export default Shell;
