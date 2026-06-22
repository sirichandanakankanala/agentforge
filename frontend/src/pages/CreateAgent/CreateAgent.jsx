import { useState } from "react";

function CreateAgent({ apiBase, onAgentSaved, onNavigateToDashboard }) {
  const [userRequest, setUserRequest] = useState(
    "Create an agent that sends me daily AI news alerts"
  );
  const [frequency, setFrequency] = useState("daily");
  const [outputType, setOutputType] = useState("alert");
  const [openaiKey, setOpenaiKey] = useState("");
  
  const [blueprint, setBlueprint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const generateAgent = async () => {
    if (!userRequest.trim()) {
      setError("Please describe what the agent should do.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setBlueprint(null);

    try {
      const response = await fetch(`${apiBase}/agents/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_request: userRequest,
          frequency: frequency,
          output_type: outputType,
        }),
      });

      if (!response.ok) {
        throw new Error("Generation failed.");
      }

      const data = await response.json();
      setBlueprint(data);
      setMessage("Agent blueprint generated successfully!");
    } catch (err) {
      setError("Could not connect to the backend. Please ensure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  const saveAgent = async () => {
    if (!blueprint) return;

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${apiBase}/agents/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: blueprint.name || blueprint.goal || "Untitled Agent",
          original_request: userRequest,
          agent: blueprint,
        }),
      });

      if (!response.ok) {
        throw new Error("Save failed.");
      }

      const saved = await response.json();
      setMessage(`Agent "${saved.name}" saved successfully!`);
      setBlueprint(null);
      if (onAgentSaved) onAgentSaved();
      // Redirect to dashboard library automatically after saving
      setTimeout(() => {
        onNavigateToDashboard();
      }, 1000);
    } catch (err) {
      setError("Could not save the agent blueprint.");
    } finally {
      setSaving(false);
    }
  };

  const downloadBlueprint = () => {
    if (!blueprint) return;
    const json = JSON.stringify(blueprint, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${blueprint.name || "agent_blueprint"}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="createAgentContainer">
      <section className="controlCard glassCard">
        <div className="inputHeader">
          <div>
            <h2>Describe your agent goal</h2>
            <p className="muted">Specify what task you want your custom AI agent to accomplish.</p>
          </div>
        </div>

        <textarea
          value={userRequest}
          onChange={(e) => setUserRequest(e.target.value)}
          placeholder="Example: Create an agent that monitors LinkedIn for Data Engineer jobs and sends me daily summaries"
          className="glassInput"
        />

        <div className="paramsGrid">
          <div className="paramField">
            <label>Execution Frequency</label>
            <select value={frequency} onChange={(e) => setFrequency(e.target.value)} className="glassSelect">
              <option value="on-demand">On-Demand</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div className="paramField">
            <label>Output Format</label>
            <select value={outputType} onChange={(e) => setOutputType(e.target.value)} className="glassSelect">
              <option value="structured response">Structured Response</option>
              <option value="email summary">Email Summary</option>
              <option value="report">PDF/Markdown Report</option>
              <option value="alert">Real-Time Alert</option>
              <option value="dashboard">Dashboard Widget</option>
            </select>
          </div>

          <div className="paramField fullWidth">
            <label>BYOK: OpenAI API Key (Optional)</label>
            <input
              type="password"
              placeholder="sk-..."
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              className="glassInput textInput"
            />
            <span className="inputNote">Provided key is only used to execute this request and is not stored.</span>
          </div>
        </div>

        <div className="buttonRow">
          <button onClick={generateAgent} disabled={loading} className="primaryButton shineEffect">
            {loading ? "Generating Agent Blueprint..." : "Generate Agent"}
          </button>
        </div>

        {error && <div className="alert errorBox fade-in">{error}</div>}
        {message && <div className="alert successBox fade-in">{message}</div>}
      </section>

      {blueprint && (
        <section className="blueprintPreviewSection fade-in">
          <div className="resultCard glassCard">
            <div className="sectionHeader">
              <div>
                <p className="sectionLabel">Agent Preview</p>
                <h2>{blueprint.name || blueprint.goal}</h2>
              </div>
              <div className="previewActions">
                <button onClick={downloadBlueprint} className="ghostButton">
                  Download JSON
                </button>
              </div>
            </div>

            <div className="summaryGrid">
              <div>
                <span>Frequency</span>
                <strong>{blueprint.frequency || frequency}</strong>
              </div>
              <div>
                <span>Output</span>
                <strong>{blueprint.output_type || outputType}</strong>
              </div>
              <div>
                <span>Status</span>
                <strong className="statusPassed">Validated & Ready</strong>
              </div>
            </div>

            <div className="previewDetails">
              <h3>Selected Tools</h3>
              <div className="toolList">
                {(blueprint.tools_needed || []).map((tool) => (
                  <span key={tool} className="toolBadge">{tool}</span>
                ))}
              </div>

              <h3>System Prompt</h3>
              <pre className="promptArea">{blueprint.system_prompt}</pre>

              <h3>Proposed Steps</h3>
              <div className="stepPreviewList">
                {(blueprint.workflow_steps || []).map((step) => (
                  <div key={step.step_number} className="stepPreviewCard">
                    <span className="stepNumberBadge">{step.step_number}</span>
                    <div className="stepPreviewInfo">
                      <h4>{step.name}</h4>
                      <p>{step.description}</p>
                      <span className="stepToolLabel">Tool: <code>{step.tool}</code></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="buttonRow borderTop">
              <button onClick={saveAgent} disabled={saving} className="greenButton shineEffect">
                {saving ? "Saving Agent..." : "Save Agent & Register"}
              </button>
              <button onClick={() => setBlueprint(null)} className="ghostButton dangerButton">
                Discard Blueprint
              </button>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

export default CreateAgent;
