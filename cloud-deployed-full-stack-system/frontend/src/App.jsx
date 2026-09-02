import { useEffect, useState } from "react";


// Use the configured API address or fall back to the local FastAPI server.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";


function App() {
  // Track the connection state between the React frontend and backend API.
  const [connection, setConnection] = useState({
    status: "checking",
    message: "Checking backend connection...",
  });

  useEffect(() => {
    // Abort the request if this component is removed before it completes.
    const controller = new AbortController();

    async function checkBackendHealth() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Backend returned status ${response.status}`);
        }

        const health = await response.json();

        setConnection({
          status: health.status === "healthy" ? "healthy" : "error",
          message: `Connected to ${health.service}`,
        });
      } catch (error) {
        // Ignore cancellation caused by React development checks.
        if (error.name === "AbortError") {
          return;
        }

        setConnection({
          status: "error",
          message: "Unable to connect to the backend API",
        });
      }
    }

    checkBackendHealth();

    // Cancel any unfinished request during component cleanup.
    return () => controller.abort();
  }, []);

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Cloud-Deployed Full-Stack System</p>
        <h1>Cloud Operations Platform</h1>
        <p className="description">
          Monitor services, manage incidents, and track operational health
          through one cloud-ready application.
        </p>

        <div className="status-card" role="status" aria-live="polite">
          <span
            className={`status-indicator status-indicator--${connection.status}`}
            aria-hidden="true"
          />

          <div>
            <p className="status-label">Backend API status</p>
            <p className="status-message">{connection.message}</p>
          </div>
        </div>
      </section>
    </main>
  );
}


export default App;