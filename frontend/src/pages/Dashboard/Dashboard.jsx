import { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";

function Dashboard({ apiBase, refreshTrigger, onNavigateToCreate }) {
  const [savedAgents, setSavedAgents] = useState([]);
  const [runs, setRuns] = useState([]);
  const [blueprint, setBlueprint] = useState(null);
  const [runResult, setRunResult] = useState(null);
  
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [runningAgentId, setRunningAgentId] = useState("");
  
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fetchSavedAgents = async () => {
    setLoadingAgents(true);
    try {
      const response = await fetch(`${apiBase}/agents`);
      if (!response.ok) throw new Error();
      const data = await response.json();
      setSavedAgents(data);
    } catch {
      setSavedAgents([]);
    } finally {
      setLoadingAgents(false);
    }
  };

  const fetchRuns = async () => {
    setLoadingRuns(true);
    try {
      const response = await fetch(`${apiBase}/runs`);
      if (!response.ok) throw new Error();
      const data = await response.json();
      setRuns(data);
    } catch {
      setRuns([]);
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    fetchSavedAgents();
    fetchRuns();
  }, [refreshTrigger]);

  const runSavedAgent = async (agentId) => {
    setRunningAgentId(agentId);
    setError("");
    setMessage("");
    setRunResult(null);

    try {
      const response = await fetch(`${apiBase}/agents/${agentId}/run`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Execution failed.");
      }

      const data = await response.json();
      setRunResult(data);
      setMessage(`Agent execution completed successfully!`);
      fetchRuns(); // Refresh runs list
    } catch {
      setError("Failed to execute agent. Backend connection error.");
    } finally {
      setRunningAgentId("");
    }
  };

  const deleteSavedAgent = async (agentId) => {
    if (!window.confirm("Are you sure you want to delete this agent? All runs associated with it will be deleted.")) return;

    setError("");
    setMessage("");

    try {
      const response = await fetch(`${apiBase}/agents/${agentId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error();

      if (blueprint?.id === agentId) {
        setBlueprint(null);
      }
      setRunResult(null);
      setMessage("Agent deleted successfully.");
      fetchSavedAgents();
      fetchRuns();
    } catch {
      setError("Could not delete agent.");
    }
  };

  const loadSavedAgent = (agent) => {
    setBlueprint(agent);
    setRunResult(null);
    setError("");
    setMessage(`Viewing details of agent: ${agent.name}`);
  };

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

  // React Flow integration for blueprint workflow steps
  const flowData = useMemo(() => {
    if (!blueprint || !blueprint.workflow_steps) return { nodes: [], edges: [] };
    
    const steps = blueprint.workflow_steps;
    
    // Add Start Node
    const nodes = [
      {
        id: "start",
        type: "input",
        data: { label: `🏁 Start\nGoal: ${blueprint.goal.substring(0, 45)}...` },
        position: { x: 150, y: 20 },
        style: {
          background: "linear-gradient(135deg, #2457ff, #1740c9)",
          color: "#fff",
          borderRadius: "12px",
          border: "none",
          padding: "10px",
          fontWeight: "bold",
          fontSize: "12px",
          width: "180px",
          boxShadow: "0 4px 12px rgba(36, 87, 255, 0.25)"
        }
      }
    ];

    // Add Step Nodes
    steps.forEach((step, idx) => {
      nodes.push({
        id: `step-${step.step_number}`,
        data: { 
          label: `⚙️ Step ${step.step_number}: ${step.name}\n[Tool: ${step.tool}]` 
        },
        position: { x: 150, y: 120 + idx * 90 },
        style: {
          background: "rgba(255, 255, 255, 0.95)",
          color: "#172033",
          border: "1.5px solid #2457ff",
          borderRadius: "12px",
          padding: "10px",
          fontSize: "12px",
          width: "180px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.05)"
        }
      });
    });

    // Add End Node
    nodes.push({
      id: "end",
      type: "output",
      data: { label: `✅ Output: ${blueprint.output_type.toUpperCase()}` },
      position: { x: 150, y: 120 + steps.length * 90 },
      style: {
        background: "linear-gradient(135deg, #12b76a, #0e9655)",
        color: "#fff",
        borderRadius: "12px",
        border: "none",
        padding: "10px",
        fontWeight: "bold",
        fontSize: "12px",
        width: "180px",
        boxShadow: "0 4px 12px rgba(18, 183, 106, 0.25)"
      }
    });

    // Add Edges
    const edges = [];
    if (steps.length > 0) {
      edges.push({ id: "e-start-1", source: "start", target: "step-1", animated: true, style: { stroke: "#2457ff" } });
      for (let i = 0; i < steps.length - 1; i++) {
        edges.push({
          id: `e-${steps[i].step_number}-${steps[i+1].step_number}`,
          source: `step-${steps[i].step_number}`,
          target: `step-${steps[i+1].step_number}`,
          animated: true,
          style: { stroke: "#2457ff" }
        });
      }
      edges.push({
        id: `e-${steps.length}-end`,
        source: `step-${steps.length}`,
        target: "end",
        animated: true,
        style: { stroke: "#12b76a" }
      });
    }

    return { nodes, edges };
  }, [blueprint]);

  return (
    <div className="dashboardGrid mainGrid">
      {/* Workspace Area: Left Side */}
      <section className="workspace">
        {error && <div className="alert errorBox fade-in">{error}</div>}
        {message && <div className="alert successBox fade-in">{message}</div>}

        {runResult && (
          <div className="resultCard runCard glassCard fade-in">
            <div className="sectionHeader">
              <div>
                <p className="sectionLabel">Execution Result</p>
                <h2>Agent Output</h2>
              </div>
              <button
                className="ghostButton"
                onClick={() => downloadJson("agent_run_output.json", runResult)}
              >
                Download Run Output
              </button>
            </div>

            <div className="summaryGrid">
              <div>
                <span>Status</span>
                <strong className="statusPassed">{runResult.status.toUpperCase()}</strong>
              </div>
              <div>
                <span>Agent</span>
                <strong>{runResult.agent_name || "Untitled"}</strong>
              </div>
              <div>
                <span>Evaluation Score</span>
                <strong>
                  {runResult.evaluation?.final_score ?? "N/A"}/100
                </strong>
              </div>
            </div>

            <h3>Output Messages</h3>
            <pre className="promptArea">{JSON.stringify(runResult.output, null, 2)}</pre>

            <h3>Tool Executions</h3>
            <div className="toolResultsGrid">
              {(runResult.tool_results || []).map((result, idx) => (
                <div key={idx} className="toolResultCard">
                  <strong>{result.tool}</strong>
                  <span className={`badge ${result.status === "success" ? "success" : "danger"}`}>
                    {result.status}
                  </span>
                  <p>{result.summary}</p>
                </div>
              ))}
            </div>

            <h3>Runtime Logs</h3>
            <ul className="logList">
              {(runResult.logs || []).map((log, index) => (
                <li key={index}>⚙️ {log}</li>
              ))}
            </ul>
          </div>
        )}

        {blueprint ? (
          <div className="resultCard glassCard fade-in">
            <div className="sectionHeader">
              <div>
                <p className="sectionLabel">Agent Details</p>
                <h2>{blueprint.name}</h2>
              </div>
              <div className="buttonRow" style={{ marginTop: 0 }}>
                <button
                  className="ghostButton"
                  onClick={() => downloadJson(`${blueprint.name}.json`, blueprint)}
                >
                  Export Blueprint
                </button>
                <button
                  className="greenButton"
                  onClick={() => runSavedAgent(blueprint.id)}
                  disabled={runningAgentId === blueprint.id}
                >
                  {runningAgentId === blueprint.id ? "Running..." : "Run Agent"}
                </button>
              </div>
            </div>

            <div className="summaryGrid">
              <div>
                <span>Frequency</span>
                <strong>{blueprint.frequency}</strong>
              </div>
              <div>
                <span>Output Type</span>
                <strong>{blueprint.output_type}</strong>
              </div>
              <div>
                <span>Registered ID</span>
                <strong><code>{blueprint.id.substring(0, 8)}...</code></strong>
              </div>
            </div>

            <h3>Visual Workflow Graph</h3>
            <div className="flowchartContainer">
              <ReactFlow nodes={flowData.nodes} edges={flowData.edges} fitView>
                <Background color="#ccc" gap={16} />
                <Controls />
              </ReactFlow>
            </div>

            <h3>System Prompt</h3>
            <pre className="promptArea">{blueprint.system_prompt}</pre>

            <h3>Tools Configured</h3>
            <div className="toolList">
              {(blueprint.tool_configurations || []).map((tool, idx) => (
                <div key={idx} className="toolConfigCard">
                  <strong>{tool.name}</strong>
                  <p>{tool.purpose}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          !runResult && (
            <div className="emptyState glassCard">
              <h2>Select or create an agent</h2>
              <p>Choose an agent from the library on the right to inspect its parameters, execute it, or run diagnostics. Or create a new one.</p>
              <button onClick={onNavigateToCreate} className="primaryButton shineEffect">
                Create New Agent
              </button>
            </div>
          )
        )}
      </section>

      {/* Sidebar: Right Side */}
      <aside className="sidebar glassCard">
        {/* Agent Library */}
        <div className="sideHeader">
          <div>
            <p className="sectionLabel">Registry</p>
            <h2>Agent Library</h2>
          </div>
          <button className="ghostButton" onClick={fetchSavedAgents}>
            Refresh
          </button>
        </div>

        {loadingAgents ? (
          <p className="muted">Loading agents...</p>
        ) : savedAgents.length === 0 ? (
          <p className="muted">No agents registered. Create one to begin!</p>
        ) : (
          <div className="agentList">
            {savedAgents.map((agent) => (
              <div 
                className={`agentCard ${blueprint?.id === agent.id ? "activeCard" : ""}`} 
                key={agent.id}
                onClick={() => loadSavedAgent(agent)}
              >
                <h3>{agent.name}</h3>
                <p className="goalExcerpt">{agent.goal}</p>

                <div className="miniMeta">
                  <span className="metaBadge">{agent.frequency}</span>
                  <span className="metaBadge">{agent.output_type}</span>
                </div>

                <div className="cardButtons" onClick={(e) => e.stopPropagation()}>
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
              </div>
            ))}
          </div>
        )}

        <hr className="divider" />

        {/* Execution History */}
        <div className="sideHeader">
          <div>
            <p className="sectionLabel">Audit Logs</p>
            <h2>Run History</h2>
          </div>
          <button className="ghostButton" onClick={fetchRuns}>
            Refresh
          </button>
        </div>

        {loadingRuns ? (
          <p className="muted">Loading runs...</p>
        ) : runs.length === 0 ? (
          <p className="muted">No agent execution history found.</p>
        ) : (
          <div className="agentList scrollableHistory">
            {runs.slice(0, 10).map((run) => (
              <div className="historyCard" key={run.id}>
                <div className="historyHeader">
                  <h4>{run.agent_name}</h4>
                  <span className="statusPassed">Success</span>
                </div>
                <div className="miniMeta">
                  <span>Score: <strong>{run.evaluation?.final_score ?? "N/A"}/100</strong></span>
                  <span>Verdict: <strong>{run.evaluation?.verdict ?? "N/A"}</strong></span>
                </div>
                <p className="evolutionSuggestion">
                  <strong>Suggestion:</strong> {run.evolution?.action || "None"}
                </p>
              </div>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}

export default Dashboard;
