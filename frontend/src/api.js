const API_BASE_URL = "http://127.0.0.1:8000";

export async function generateAgentBlueprint(agentRequest) {
  const response = await fetch(`${API_BASE_URL}/agents/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(agentRequest),
  });

  if (!response.ok) {
    throw new Error("Failed to generate agent blueprint");
  }

  return response.json();
}
