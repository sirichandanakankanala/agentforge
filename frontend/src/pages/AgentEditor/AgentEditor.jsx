import { useState, useEffect } from "react";

function AgentEditor({ apiBase, agentId, onAgentUpdated, onNavigateToDashboard, onClose }) {
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  
  // Edit form state
  const [editedName, setEditedName] = useState("");
  const [editedGoal, setEditedGoal] = useState("");
  const [editedFrequency, setEditedFrequency] = useState("");
  const [editedOutputType, setEditedOutputType] = useState("");
  const [editedSystemPrompt, setEditedSystemPrompt] = useState("");
  
  // Fetch agent details
  useEffect(() => {
    const fetchAgent = async () => {
      try {
        const response = await fetch(`${apiBase}/agents/${agentId}`);
        if (!response.ok) throw new Error("Failed to fetch agent");
        
        const data = await response.json();
        setAgent(data);
        setEditedName(data.name || "");
        setEditedGoal(data.goal || "");
        setEditedFrequency(data.frequency || "");
        setEditedOutputType(data.output_type || "");
        setEditedSystemPrompt(data.system_prompt || "");
      } catch (err) {
        setError("Could not load agent for editing");
      } finally {
        setLoading(false);
      }
    };
    
    if (agentId) fetchAgent();
  }, [agentId, apiBase]);
  
  const saveChanges = async () => {
    if (!editedName.trim() || !editedGoal.trim()) {
      setError("Name and goal are required");
      return;
    }
    
    setSaving(true);
    setError("");
    setMessage("");
    
    try {
      const updatedAgent = {
        ...agent,
        name: editedName,
        goal: editedGoal,
        frequency: editedFrequency,
        output_type: editedOutputType,
        system_prompt: editedSystemPrompt,
      };
      
      const response = await fetch(`${apiBase}/agents/${agentId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updatedAgent),
      });
      
      if (!response.ok) {
        // For now, POST as save since PUT might not be implemented
        const saveResponse = await fetch(`${apiBase}/agents/save`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: editedName,
            agent: updatedAgent,
          }),
        });
        
        if (!saveResponse.ok) throw new Error("Failed to save changes");
      }
      
      setMessage("Agent updated successfully!");
      setAgent(updatedAgent);
      
      if (onAgentUpdated) {
        onAgentUpdated();
      }
      
      setTimeout(() => {
        onNavigateToDashboard();
      }, 1500);
    } catch (err) {
      setError("Failed to save changes: " + err.message);
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <div className="editorContainer">
        <div className="loadingSpinner">Loading agent for editing...</div>
      </div>
    );
  }
  
  if (!agent) {
    return (
      <div className="editorContainer">
        <div className="alert errorBox">Agent not found</div>
      </div>
    );
  }
  
  return (
    <div className="editorContainer">
      <section className="controlCard glassCard">
        <div className="inputHeader">
          <div>
            <h2>Edit Agent</h2>
            <p className="muted">Modify your agent's configuration and behavior</p>
          </div>
        </div>
        
        {/* Basic Info */}
        <div className="formSection">
          <h3>Basic Information</h3>
          
          <div className="formField">
            <label>Agent Name *</label>
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              placeholder="Agent name"
              className="glassInput"
            />
          </div>
          
          <div className="formField">
            <label>Goal/Description *</label>
            <textarea
              value={editedGoal}
              onChange={(e) => setEditedGoal(e.target.value)}
              placeholder="What should this agent do?"
              className="glassInput"
              rows="4"
            />
          </div>
        </div>
        
        {/* Configuration */}
        <div className="formSection">
          <h3>Configuration</h3>
          
          <div className="paramsGrid">
            <div className="paramField">
              <label>Execution Frequency</label>
              <select 
                value={editedFrequency} 
                onChange={(e) => setEditedFrequency(e.target.value)} 
                className="glassSelect"
              >
                <option value="">Select frequency...</option>
                <option value="on-demand">On-Demand</option>
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            
            <div className="paramField">
              <label>Output Format</label>
              <select 
                value={editedOutputType} 
                onChange={(e) => setEditedOutputType(e.target.value)} 
                className="glassSelect"
              >
                <option value="">Select format...</option>
                <option value="structured response">Structured Response</option>
                <option value="email summary">Email Summary</option>
                <option value="report">PDF/Markdown Report</option>
                <option value="alert">Real-Time Alert</option>
                <option value="dashboard">Dashboard Widget</option>
              </select>
            </div>
          </div>
        </div>
        
        {/* System Prompt */}
        <div className="formSection">
          <h3>System Prompt</h3>
          <p className="muted">Advanced: Customize the agent's behavior instructions</p>
          
          <div className="formField">
            <textarea
              value={editedSystemPrompt}
              onChange={(e) => setEditedSystemPrompt(e.target.value)}
              placeholder="You are a specialized AI agent..."
              className="glassInput"
              rows="6"
            />
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="buttonRow">
          <button 
            onClick={saveChanges} 
            disabled={saving} 
            className="primaryButton shineEffect"
          >
            {saving ? "Saving Changes..." : "Save Changes"}
          </button>
          <button 
            onClick={onClose || onNavigateToDashboard} 
            className="secondaryButton"
          >
            Cancel
          </button>
        </div>
        
        {error && <div className="alert errorBox fade-in">{error}</div>}
        {message && <div className="alert successBox fade-in">{message}</div>}
      </section>
      
      {/* Agent Details Preview */}
      <section className="previewSection">
        <div className="resultCard glassCard">
          <h3>Agent Details</h3>
          
          <div className="detailsGrid">
            <div>
              <span>Agent ID</span>
              <code>{agent.id}</code>
            </div>
            <div>
              <span>Created</span>
              <code>{new Date(agent.created_at).toLocaleDateString()}</code>
            </div>
            <div>
              <span>Tools</span>
              <code>{(agent.tools_needed || []).join(", ") || "None"}</code>
            </div>
            <div>
              <span>Mode</span>
              <code>{agent.mode || "mock"}</code>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default AgentEditor;
