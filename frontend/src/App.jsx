import { useEffect, useMemo, useState } from "react";
import "./App.css";
import RunHistory from "./RunHistory";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [userRequest, setUserRequest] = useState(
    "Create an agent that sends me daily AI news alerts"
  );
  const [backendStatus, setBackendStatus] = useState("checking");
  const [backendDetails, setBackendDetails] = useState(null);
  const [blueprint, setBlueprint] = useState(null);
  const [savedAgents, setSavedAgents] = useState([]);
  const [runResult, setRunResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [runningAgentId, setRunningAgentId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const selectedAgentId = blueprint?.id || "";

  const statusLabel = useMemo(() => {
    if (backendStatus === "online") return "Backend online";
    if (backendStatus === "offline") return "Backend offline";
    return "Checking backend";
  }, [backendStatus]);

  const downloadJson = (filename, data) => {
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const checkBackend = async () => {
    setBackendStatus("checking");

    try {
      const response = await fetch(`${API_BASE}/health`);

      if (!response.ok) {
        throw new Error("Health check failed.");
      }

      const data = await response.json();
      setBackendDetails(data);
      setBackendStatus("online");
      setError("");
    } catch {
      setBackendDetails(null);
      setBackendStatus("offline");
      setError(
        `Backend is not connected. Start backend with: python -m uvicorn main:app --reload`
      );
    }
  };

  const fetchSavedAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/agents`);

      if (!response.ok) {
        throw new Error("Could not fetch saved agents.");
      }

      const data = await response.json();
      setSavedAgents(data);
    } catch {
      setSavedAgents([]);
    }
  };

  useEffect(() => {
    checkBackend();
    fetchSavedAgents();
  }, []);

  const generateAgent = async () => {
    if (!userRequest.trim()) {
      setError("Enter an agent idea first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setBlueprint(null);
    setRunResult(null);

    try {
      const response = await fetch(`${API_BASE}/agents/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_request: userRequest,
        }),
      });

      if (!response.ok) {
        throw new Error("Generate failed.");
      }

      const data = await response.json();
      setBlueprint(data);
      setMessage("Agent blueprint generated.");
      await checkBackend();
    } catch {
      setError(
        "Could not connect to backend. Make sure backend is running on http://127.0.0.1:8000"
      );
      setBackendStatus("offline");
    } finally {
      setLoading(false);
    }
  };

  const saveAgent = async () => {
    if (!blueprint) {
      setError("Generate an agent before saving.");
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/agents/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: blueprint.goal || "Untitled Agent",
          original_request: userRequest,
          agent: blueprint,
        }),
      });

      if (!response.ok) {
        throw new Error("Save failed.");
      }

      const saved = await response.json();
      setBlueprint(saved);
      setMessage(`Saved agent: ${saved.name}`);
      await fetchSavedAgents();
    } catch {
      setError("Could not save agent. Check if backend is running.");
    } finally {
      setSaving(false);
    }
  };

  const runSavedAgent = async (agentId) => {
    if (!agentId) {
      setError("Save or select an agent first.");
      return;
    }

    setRunningAgentId(agentId);
    setError("");
    setMessage("");
    setRunResult(null);

    try {
      const response = await fetch(`${API_BASE}/agents/${agentId}/run`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Run failed.");
      }

      const data = await response.json();
      setRunResult(data);
      setMessage(`Run completed: ${data.agent_name || "Agent"}`);
    } catch {
      setError("Could not run agent. Check backend connection.");
    } finally {
      setRunningAgentId("");
    }
  };

  const loadSavedAgent = (agent) => {
    setBlueprint(agent);
    setUserRequest(agent.original_request || agent.goal || "");
    setRunResult(null);
    setError("");
    setMessage(`Loaded saved agent: ${agent.name}`);
  };

  const deleteSavedAgent = async (agentId) => {
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/agents/${agentId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Delete failed.");
      }

      if (blueprint?.id === agentId) {
        setBlueprint(null);
      }

      setRunResult(null);
      setMessage("Agent deleted.");
      await fetchSavedAgents();
    } catch {
      setError("Could not delete agent.");
    }
  };

  const downloadAllSavedAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/agents`);

      if (!response.ok) {
        throw new Error("Export failed.");
      }

      const data = await response.json();
      downloadJson("agentforge_saved_agents.json", data);
    } catch {
      setError("Could not download saved agents JSON.");
    }
  };

  return (
    <div className="appShell">
      <header className="topBar">
        <div>
          <p className="brandTag">AgentForge</p>
          <h1>AI Agent Blueprint Builder</h1>
          <p className="subtitle">
            Generate, save, run, and export specialist AI agent blueprints.
          </p>
        </div>

        <div className={`statusPill ${backendStatus}`}>
          <span />
          {statusLabel}
        </div>
      </header>

      <section className="controlCard">
        <div className="inputHeader">
          <div>
            <h2>Create a new agent</h2>
            <p>Describe what the agent should do.</p>
          </div>

          <button className="ghostButton" onClick={checkBackend}>
            Check Backend
          </button>
        </div>

        <textarea
          value={userRequest}
          onChange={(event) => setUserRequest(event.target.value)}
          placeholder="Example: Create an agent that sends me daily AI news alerts"
        />

        <div className="buttonRow">
          <button onClick={generateAgent} disabled={loading}>
            {loading ? "Generating..." : "Generate Agent"}
          </button>

          <button className="darkButton" onClick={saveAgent} disabled={!blueprint || saving}>
            {saving ? "Saving..." : "Save Agent"}
          </button>

          <button
            className="greenButton"
            onClick={() => runSavedAgent(selectedAgentId)}
            disabled={!selectedAgentId || runningAgentId === selectedAgentId}
          >
            {runningAgentId === selectedAgentId ? "Running..." : "Run Agent"}
          </button>

          <button
            className="ghostButton"
            onClick={() => downloadJson("agent_blueprint.json", blueprint)}
            disabled={!blueprint}
          >
            Download Blueprint JSON
          </button>

          <button className="ghostButton" onClick={downloadAllSavedAgents}>
            Download All Saved JSON
          </button>
        </div>

        {error && <div className="alert errorBox">{error}</div>}
        {message && <div className="alert successBox">{message}</div>}

        {backendDetails && (
          <div className="backendInfo">
            <strong>Backend:</strong> {backendDetails.backend} ·{" "}
            <strong>Pipeline:</strong>{" "}
            {backendDetails.pipeline_available ? "available" : "fallback mock mode"}
          </div>
        )}
      </section>

      <main className="mainGrid">
        <section className="workspace">
          {runResult && (
            <div className="resultCard runCard">
              <div className="sectionHeader">
                <div>
                  <p className="sectionLabel">Execution</p>
                  <h2>Agent Run Output</h2>
                </div>

                <button
                  className="ghostButton"
                  onClick={() => downloadJson("agent_run_output.json", runResult)}
                >
                  Download Run JSON
                </button>
              </div>

              <div className="summaryGrid">
                <div>
                  <span>Status</span>
                  <strong>{runResult.status}</strong>
                </div>
                <div>
                  <span>Agent</span>
                  <strong>{runResult.agent_name || "Untitled"}</strong>
                </div>
                <div>
                  <span>Tools Used</span>
                  <strong>{runResult.used_tools?.length || 0}</strong>
                </div>
              </div>

              <pre>{JSON.stringify(runResult.output, null, 2)}</pre>

              <h3>Tool Results</h3>
              <pre>{JSON.stringify(runResult.tool_results, null, 2)}</pre>

              <h3>Logs</h3>
              <ul className="logList">
                {(runResult.logs || []).map((log, index) => (
                  <li key={index}>{log}</li>
                ))}
              </ul>
            </div>
          )}

          {blueprint ? (
            <div className="resultCard">
              <div className="sectionHeader">
                <div>
                  <p className="sectionLabel">Blueprint</p>
                  <h2>{blueprint.name || blueprint.goal}</h2>
                </div>

                <button
                  className="ghostButton"
                  onClick={() => downloadJson("agent_blueprint.json", blueprint)}
                >
                  Download JSON
                </button>
              </div>

              <div className="summaryGrid">
                <div>
                  <span>Frequency</span>
                  <strong>{blueprint.frequency}</strong>
                </div>
                <div>
                  <span>Output</span>
                  <strong>{blueprint.output_type}</strong>
                </div>
                <div>
                  <span>Mode</span>
                  <strong>{blueprint.mode}</strong>
                </div>
              </div>

              {blueprint.id && (
                <div className="idBox">
                  <strong>Saved ID:</strong> {blueprint.id}
                </div>
              )}

              <h3>Tools Needed</h3>
              <div className="toolList">
                {(blueprint.tools_needed || []).map((tool) => (
                  <span key={tool}>{tool}</span>
                ))}
              </div>

              <h3>System Prompt</h3>
              <pre>{blueprint.system_prompt}</pre>

              <h3>Workflow Steps</h3>
              <pre>{JSON.stringify(blueprint.workflow_steps || [], null, 2)}</pre>

              <h3>Memory Config</h3>
              <pre>{JSON.stringify(blueprint.memory_config || {}, null, 2)}</pre>

              <h3>Validation</h3>
              <pre>{JSON.stringify(blueprint.validation_result || {}, null, 2)}</pre>
            </div>
          ) : (
            <div className="emptyState">
              <h2>No blueprint yet</h2>
              <p>Generate an agent to see its full blueprint here.</p>
            </div>
          )}
        </section>

        <aside className="sidebar">
          <div className="sideHeader">
            <div>
              <p className="sectionLabel">Library</p>
              <h2>Saved Agents</h2>
            </div>

            <button className="ghostButton" onClick={fetchSavedAgents}>
              Refresh
            </button>
          </div>

          {savedAgents.length === 0 ? (
            <p className="muted">No saved agents yet.</p>
          ) : (
            <div className="agentList">
              {savedAgents.map((agent) => (
                <div className="agentCard" key={agent.id}>
                  <h3>{agent.name}</h3>
                  <p>{agent.goal}</p>

                  <div className="miniMeta">
                    <span>{agent.frequency}</span>
                    <span>{agent.output_type}</span>
                  </div>

                  <div className="cardButtons">
                    <button className="smallButton" onClick={() => loadSavedAgent(agent)}>
                      View
                    </button>

                    <button
                      className="smallButton greenMini"
                      onClick={() => runSavedAgent(agent.id)}
                      disabled={runningAgentId === agent.id}
                    >
                      {runningAgentId === agent.id ? "Running..." : "Run"}
                    </button>

                    <button
                      className="smallButton dangerMini"
                      onClick={() => deleteSavedAgent(agent.id)}
                    >
                      Delete
                    </button>
                  </div>

                  <button
                    className="downloadMini"
                    onClick={() => downloadJson(`${agent.name || "agent"}.json`, agent)}
                  >
                    Download this JSON
                  </button>
                </div>
              ))}
            </div>
          )}
        <RunHistory apiBase={API_BASE} />
        </aside>
      </main>
    </div>
  );
}

export default App;
