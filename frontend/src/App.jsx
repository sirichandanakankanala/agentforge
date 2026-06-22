import { useEffect, useMemo, useState } from "react";
import "./App.css";
import CreateAgent from "./pages/CreateAgent/CreateAgent";
import Dashboard from "./pages/Dashboard/Dashboard";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [activeTab, setActiveTab] = useState("create"); // "create" or "dashboard"
  const [backendStatus, setBackendStatus] = useState("checking");
  const [backendDetails, setBackendDetails] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [error, setError] = useState("");

  const statusLabel = useMemo(() => {
    if (backendStatus === "online") return "Backend online";
    if (backendStatus === "offline") return "Backend offline";
    return "Checking backend";
  }, [backendStatus]);

  const STREAMLIT_URL = import.meta.env.VITE_STREAMLIT_URL || "http://127.0.0.1:8501";

  const checkBackend = async () => {
    setBackendStatus("checking");
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (!response.ok) {
        throw new Error();
      }
      const data = await response.json();
      setBackendDetails(data);
      setBackendStatus("online");
      setError("");
    } catch {
      setBackendDetails(null);
      setBackendStatus("offline");
      setError(
        "Backend not connected. Start the backend with: python -m uvicorn app:app --reload"
      );
    }
  };

  useEffect(() => {
    checkBackend();
  }, []);

  const handleAgentSaved = () => {
    // Increment triggers to refresh Dashboard data
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="appShell">
      <header className="topBar">
        <div>
          <p className="brandTag">AgentForge</p>
          <h1>AI Agent Builder Platform</h1>
          <p className="subtitle">
            Generate, validate, configure, and execute custom autonomous AI agents from natural language.
          </p>
        </div>

        <div className="headerActions">
          <div className={`statusPill ${backendStatus}`}>
            <span />
            {statusLabel}
          </div>
          <button className="ghostButton checkBackendBtn" onClick={checkBackend}>
            🔄 Check
          </button>
          <button
            className="ghostButton openStreamlitBtn"
            onClick={() => window.open(STREAMLIT_URL, "_blank")}
            title="Open Streamlit Console"
          >
            🧭 Streamlit Console
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="navTabs glassCard">
        <button
          className={`tabButton ${activeTab === "create" ? "activeTab" : ""}`}
          onClick={() => setActiveTab("create")}
        >
          ➕ Create New Agent
        </button>
        <button
          className={`tabButton ${activeTab === "dashboard" ? "activeTab" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          📊 Agent Dashboard & Library
        </button>
      </nav>

      {error && <div className="alert errorBox globalError fade-in">{error}</div>}

      <main className="tabContent">
        {activeTab === "create" ? (
          <CreateAgent
            apiBase={API_BASE}
            onAgentSaved={handleAgentSaved}
            onNavigateToDashboard={() => setActiveTab("dashboard")}
          />
        ) : (
          <Dashboard
            apiBase={API_BASE}
            refreshTrigger={refreshTrigger}
            onNavigateToCreate={() => setActiveTab("create")}
          />
        )}
      </main>

      {backendDetails && (
        <footer className="footerDetails fade-in">
          <strong>Service Status:</strong> Active · 
          <strong> Engine Mode:</strong> {backendDetails.mock_mode === "true" || backendDetails.mode === "mock" ? "Mock Mode" : "Real LLM Mode"} · 
          <strong> Pipeline Status:</strong> {backendDetails.pipeline_available ? "Active" : "Mock Fallback"}
        </footer>
      )}
    </div>
  );
}

export default App;
