import { useEffect, useState } from "react";

function RunHistory({ apiBase }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchRuns = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${apiBase}/runs`);

      if (!response.ok) {
        throw new Error("Could not fetch run history.");
      }

      const data = await response.json();
      setRuns(data);
    } catch {
      setError("Run history is not available yet. Check backend /runs endpoint.");
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  return (
    <div className="agentCard">
      <div className="sideHeader">
        <div>
          <p className="sectionLabel">History</p>
          <h2>Agent Runs</h2>
        </div>

        <button className="ghostButton" onClick={fetchRuns}>
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && <p className="muted">{error}</p>}

      {runs.length === 0 && !error ? (
        <p className="muted">No agent runs saved yet.</p>
      ) : (
        <div className="agentList">
          {runs.slice(0, 5).map((run) => (
            <div className="agentCard" key={run.id || run.run_id}>
              <h3>{run.agent_name || "Untitled Agent"}</h3>

              <p>Status: {run.status}</p>

              <div className="miniMeta">
                <span>
                  Score:{" "}
                  {run.evaluation?.final_score ??
                    run.output?.evaluation_summary?.final_score ??
                    "N/A"}
                </span>

                <span>
                  Verdict:{" "}
                  {run.evaluation?.verdict ??
                    run.output?.evaluation_summary?.verdict ??
                    "N/A"}
                </span>
              </div>

              <p>
                Evolution:{" "}
                {run.evolution?.action ??
                  run.output?.evolution_summary?.action ??
                  "N/A"}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RunHistory;
