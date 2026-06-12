import { useState } from "react";
import "./App.css";
import { generateAgentBlueprint } from "./api";

function App() {
  const [goal, setGoal] = useState("");
  const [frequency, setFrequency] = useState("on-demand");
  const [outputType, setOutputType] = useState("structured response");
  const [blueprint, setBlueprint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate(event) {
    event.preventDefault();

    if (!goal.trim()) {
      setError("Please enter an agent goal.");
      return;
    }

    setLoading(true);
    setError("");
    setBlueprint(null);

    try {
      const result = await generateAgentBlueprint({
        goal,
        frequency,
        output_type: outputType,
      });

      setBlueprint(result);
    } catch (err) {
      setError("Could not connect to backend. Make sure FastAPI is running on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <section className="hero">
        <p className="eyebrow">AgentForge</p>
        <h1>Generate specialized AI agent blueprints</h1>
        <p className="subtitle">
          Enter a goal and AgentForge will create the agent tools, system prompt,
          and workflow steps using the FastAPI backend.
        </p>
      </section>

      <section className="panel">
        <form onSubmit={handleGenerate} className="form">
          <label>
            Agent Goal
            <textarea
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              placeholder="Create an agent that sends me daily AI news alerts"
              rows="4"
            />
          </label>

          <div className="grid">
            <label>
              Frequency
              <select
                value={frequency}
                onChange={(event) => setFrequency(event.target.value)}
              >
                <option value="on-demand">On-demand</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="real-time">Real-time</option>
              </select>
            </label>

            <label>
              Output Type
              <select
                value={outputType}
                onChange={(event) => setOutputType(event.target.value)}
              >
                <option value="structured response">Structured response</option>
                <option value="alert">Alert</option>
                <option value="report">Report</option>
                <option value="summary">Summary</option>
              </select>
            </label>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Generating..." : "Generate Agent"}
          </button>

          {error && <p className="error">{error}</p>}
        </form>
      </section>

      {blueprint && (
        <section className="result">
          <h2>Generated Agent Blueprint</h2>

          <div className="card">
            <h3>Goal</h3>
            <p>{blueprint.goal}</p>
          </div>

          <div className="card-row">
            <div className="card">
              <h3>Frequency</h3>
              <p>{blueprint.frequency}</p>
            </div>

            <div className="card">
              <h3>Output Type</h3>
              <p>{blueprint.output_type}</p>
            </div>
          </div>

          <div className="card">
            <h3>Tools Needed</h3>
            <div className="tools">
              {blueprint.tools_needed.map((tool) => (
                <span key={tool}>{tool}</span>
              ))}
            </div>
          </div>

          <div className="card">
            <h3>System Prompt</h3>
            <pre>{blueprint.system_prompt}</pre>
          </div>

          <div className="card">
            <h3>Workflow Steps</h3>
            <div className="steps">
              {blueprint.workflow_steps.map((step) => (
                <div className="step" key={step.step_number}>
                  <strong>
                    {step.step_number}. {step.name}
                  </strong>
                  <p>{step.description}</p>
                  <small>Tool: {step.tool}</small>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
