import { useState, useEffect } from "react";

function AgentScheduler({ apiBase, agentId, onScheduleUpdated, onClose }) {
  const [frequency, setFrequency] = useState("daily");
  const [isScheduled, setIsScheduled] = useState(false);
  const [nextRun, setNextRun] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  
  // Load current schedule on mount
  useEffect(() => {
    const loadSchedule = async () => {
      try {
        const response = await fetch(`${apiBase}/schedules`);
        if (response.ok) {
          const data = await response.json();
          const schedule = data.schedules.find(s => s.agent_id === agentId);
          if (schedule) {
            setIsScheduled(true);
            setFrequency(schedule.frequency);
            setNextRun(schedule.next_run);
          }
        }
      } catch (err) {
        console.error("Failed to load schedule:", err);
      }
    };
    
    loadSchedule();
  }, [agentId, apiBase]);
  
  const handleSchedule = async () => {
    setLoading(true);
    setError("");
    setMessage("");
    
    try {
      if (isScheduled) {
        // Unschedule
        const response = await fetch(`${apiBase}/agents/${agentId}/schedule`, {
          method: "DELETE",
        });
        
        if (!response.ok) throw new Error("Failed to unschedule");
        
        setIsScheduled(false);
        setNextRun(null);
        setMessage("Agent unscheduled successfully!");
      } else {
        // Schedule
        const response = await fetch(`${apiBase}/agents/${agentId}/schedule`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ frequency }),
        });
        
        if (!response.ok) throw new Error("Failed to schedule");
        
        const data = await response.json();
        setIsScheduled(true);
        setNextRun(data.next_run);
        setMessage(`Agent scheduled for ${frequency} execution!`);
      }
      
      if (onScheduleUpdated) {
        onScheduleUpdated();
      }
    } catch (err) {
      setError("Failed to update schedule: " + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const frequencyDescriptions = {
    hourly: "Run every hour at :00",
    daily: "Run daily at 12:00 UTC",
    weekly: "Run every Sunday at 12:00 UTC",
    monthly: "Run on the 1st of each month at 12:00 UTC",
  };
  
  return (
    <div className="schedulerModal">
      <div className="modalContent glassCard">
        <div className="modalHeader">
          <h3>Schedule Agent</h3>
          {onClose && (
            <button onClick={onClose} className="closeButton">×</button>
          )}
        </div>
        
        <div className="modalBody">
          {!isScheduled ? (
            <div>
              <p className="muted">Choose how often this agent should run:</p>
              
              <div className="frequencyOptions">
                {Object.entries(frequencyDescriptions).map(([freq, desc]) => (
                  <label key={freq} className="optionLabel">
                    <input
                      type="radio"
                      value={freq}
                      checked={frequency === freq}
                      onChange={(e) => setFrequency(e.target.value)}
                    />
                    <span>
                      <strong>{freq.charAt(0).toUpperCase() + freq.slice(1)}</strong>
                      <p className="muted">{desc}</p>
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ) : (
            <div className="currentSchedule">
              <div className="scheduleInfo">
                <p><strong>Status:</strong> Scheduled</p>
                <p><strong>Frequency:</strong> {frequency}</p>
                <p><strong>Next Run:</strong> {nextRun ? new Date(nextRun).toLocaleString() : "Unknown"}</p>
              </div>
              <p className="muted">Click "Unschedule" to stop automatic execution.</p>
            </div>
          )}
          
          {error && <div className="alert errorBox">{error}</div>}
          {message && <div className="alert successBox">{message}</div>}
        </div>
        
        <div className="modalFooter">
          <button 
            onClick={handleSchedule} 
            disabled={loading}
            className={isScheduled ? "dangerButton" : "primaryButton"}
          >
            {loading 
              ? "Processing..." 
              : isScheduled 
                ? "Unschedule" 
                : "Schedule Agent"
            }
          </button>
          {onClose && (
            <button onClick={onClose} className="secondaryButton">
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default AgentScheduler;
