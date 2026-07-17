import React from "react";
import ThemeManager from "./ThemeManager";

const Dashboard: React.FC = () => {
  return (
    <section style={{ padding: "1rem", maxWidth: "600px", margin: "0 auto" }}>
      <h1 style={{ textAlign: "center" }}>Swider Dashboard</h1>
      <ThemeManager />
      <p style={{ marginTop: "1rem", lineHeight: 1.5 }}>
        The Swider dashboard provides a lightweight interface to control the day/night
        theme and visualizes subtle firefly particles. Designed for mobile devices with
        a strict <strong>&lt;15 MB RAM</strong> target.
      </p>
    </section>
  );
};

export default Dashboard;