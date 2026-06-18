from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.pipeline import build_agent
from agents.mock_runner import run_mock_agent

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "generated_agents.json"

app = FastAPI(title="AgentForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_saved_agents() -> List[Dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")
        return []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_agents(agents: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(agents, indent=2), encoding="utf-8")


@app.get("/")
def home():
    return {"status": "ok", "message": "AgentForge backend running"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "backend": "online",
        "pipeline_available": True,
        "mode": "mock",
    }


@app.post("/agents/generate")
def generate_agent(payload: dict):
    user_request = payload.get("user_request", "")

    agent = build_agent()
    result = agent.invoke(
        {
            "user_request": user_request,
            "goal": "",
            "frequency": "",
            "output_type": "",
            "tools_needed": [],
            "tool_configurations": [],
            "system_prompt": "",
            "workflow_steps": [],
            "memory_config": {},
            "validation_result": {},
        }
    )

    result["mode"] = "mock"
    return result


@app.post("/agents/save")
def save_agent(payload: dict):
    agents = load_saved_agents()

    agent_data = payload.get("agent", {})
    saved_agent = {
        "id": str(uuid.uuid4()),
        "name": payload.get("name") or agent_data.get("goal") or "Untitled Agent",
        "original_request": payload.get("original_request", ""),
        "created_at": datetime.utcnow().isoformat(),
        **agent_data,
    }

    agents.append(saved_agent)
    save_agents(agents)

    return saved_agent


@app.get("/agents")
def get_agents():
    return load_saved_agents()


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    agents = load_saved_agents()

    for agent in agents:
        if agent.get("id") == agent_id:
            return agent

    raise HTTPException(status_code=404, detail="Agent not found")


@app.post("/agents/{agent_id}/run")
def run_agent(agent_id: str):
    agents = load_saved_agents()

    for agent in agents:
        if agent.get("id") == agent_id:
            return run_mock_agent(agent)

    raise HTTPException(status_code=404, detail="Agent not found")


@app.post("/agents/run-mock")
def run_agent_mock(payload: dict):
    return run_mock_agent(payload)


@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):
    agents = load_saved_agents()
    remaining = [agent for agent in agents if agent.get("id") != agent_id]

    if len(remaining) == len(agents):
        raise HTTPException(status_code=404, detail="Agent not found")

    save_agents(remaining)

    return {"deleted": True, "id": agent_id}
