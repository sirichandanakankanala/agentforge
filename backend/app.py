from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agents.pipeline import build_agent
from agent_runner import run_agent_blueprint
from agent_store import create_agent, delete_agent, get_agent, list_agents


load_dotenv()
os.environ.setdefault("AGENTFORGE_MOCK_MODE", "true")


app = FastAPI(
    title="AgentForge Mock API",
    description="Browser API for generating, saving, and running AgentForge agent blueprints.",
    version="1.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    user_request: str


class AgentResponse(BaseModel):
    goal: str
    frequency: str
    output_type: str
    tools_needed: List[str]
    tool_configurations: List[Dict[str, Any]]
    system_prompt: str
    workflow_steps: List[Dict[str, Any]]
    memory_config: Dict[str, Any]
    validation_result: Dict[str, Any]
    mode: str


class SaveAgentRequest(BaseModel):
    name: Optional[str] = None
    original_request: Optional[str] = None
    agent: AgentResponse


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@app.get("/")
def home() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "AgentForge Mock API",
        "mode": os.getenv("AGENTFORGE_MOCK_MODE", "true"),
        "docs": "/docs",
        "ui": "/ui",
    }


@app.post("/agents/generate", response_model=AgentResponse)
def generate_agent(request: AgentRequest) -> AgentResponse:
    agent = build_agent()

    result = agent.invoke(
        {
            "user_request": request.user_request,
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

    return AgentResponse(
        goal=result.get("goal", ""),
        frequency=result.get("frequency", ""),
        output_type=result.get("output_type", ""),
        tools_needed=result.get("tools_needed", []),
        tool_configurations=result.get("tool_configurations", []),
        system_prompt=result.get("system_prompt", ""),
        workflow_steps=result.get("workflow_steps", []),
        memory_config=result.get("memory_config", {}),
        validation_result=result.get("validation_result", {}),
        mode=os.getenv("AGENTFORGE_MOCK_MODE", "true"),
    )


@app.post("/agents/save")
def save_agent(request: SaveAgentRequest) -> Dict[str, Any]:
    agent_data = model_to_dict(request.agent)

    saved_agent = create_agent(
        {
            "name": request.name or agent_data.get("goal") or "Untitled Agent",
            "original_request": request.original_request,
            **agent_data,
        }
    )

    return saved_agent


@app.get("/agents")
def get_saved_agents() -> List[Dict[str, Any]]:
    return list_agents()


@app.get("/agents/{agent_id}")
def get_saved_agent(agent_id: str) -> Dict[str, Any]:
    agent = get_agent(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return agent


@app.post("/agents/{agent_id}/run")
def run_saved_agent(agent_id: str) -> Dict[str, Any]:
    agent = get_agent(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return run_agent_blueprint(agent)


@app.delete("/agents/{agent_id}")
def remove_saved_agent(agent_id: str) -> Dict[str, Any]:
    deleted = delete_agent(agent_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return {
        "deleted": True,
        "id": agent_id,
    }


@app.get("/ui", response_class=HTMLResponse)
def ui() -> str:
    return """
    <html>
      <head>
        <title>AgentForge Mock UI</title>
      </head>
      <body>
        <h1>AgentForge Mock UI</h1>
        <p>Use the React frontend for the full generate + save + run experience.</p>
        <p>API docs are available at <a href="/docs">/docs</a>.</p>
      </body>
    </html>
    """


@app.post("/agents/{agent_id}/run")
def run_saved_agent(agent_id: str) -> dict[str, Any]:
    agents = load_saved_agents()

    saved_agent = next(
        (agent for agent in agents if agent.get("id") == agent_id),
        None,
    )

    if saved_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    from agents.mock_runner import run_mock_agent

    return run_mock_agent(saved_agent)
