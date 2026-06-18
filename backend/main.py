from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from registry_updater import update_agent_after_run
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_runner import run_agent_blueprint
from agent_store import create_agent, delete_agent, get_agent, list_agents
from run_store import create_run, list_runs, list_runs_for_agent

load_dotenv()
os.environ.setdefault("AGENTFORGE_MOCK_MODE", "true")


PIPELINE_IMPORT_ERROR: Optional[str] = None

try:
    from agents.pipeline import build_agent
except Exception as error:
    build_agent = None
    PIPELINE_IMPORT_ERROR = repr(error)


app = FastAPI(
    title="AgentForge API",
    description="Generate, save, run, and export AI agent blueprints.",
    version="1.3.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    user_request: str


class SaveAgentRequest(BaseModel):
    name: Optional[str] = None
    original_request: Optional[str] = None
    agent: Dict[str, Any]


def detect_frequency(text: str) -> str:
    lower_text = text.lower()

    if "daily" in lower_text or "every day" in lower_text:
        return "daily"
    if "weekly" in lower_text or "every week" in lower_text:
        return "weekly"
    if "monthly" in lower_text:
        return "monthly"
    if "hourly" in lower_text:
        return "hourly"

    return "on-demand"


def detect_output_type(text: str) -> str:
    lower_text = text.lower()

    if "alert" in lower_text or "notify" in lower_text or "notification" in lower_text:
        return "alert"
    if "email" in lower_text:
        return "email"
    if "report" in lower_text:
        return "report"
    if "summary" in lower_text:
        return "summary"

    return "structured response"


def select_mock_tools(text: str) -> List[str]:
    lower_text = text.lower()
    tools: List[str] = []

    if any(word in lower_text for word in ["news", "latest", "web", "search", "research"]):
        tools.append("web_search")

    if "ai" in lower_text and "news" in lower_text:
        tools.append("ai_news_monitor")

    if any(word in lower_text for word in ["alert", "notify", "notification", "daily"]):
        tools.append("notification_sender")

    if any(word in lower_text for word in ["summary", "summarize", "report"]):
        tools.append("summarizer")

    if "email" in lower_text:
        tools.append("email_sender")

    if not tools:
        tools = ["internal_reasoning"]

    return tools


def fallback_generate_agent(user_request: str) -> Dict[str, Any]:
    frequency = detect_frequency(user_request)
    output_type = detect_output_type(user_request)
    tools_needed = select_mock_tools(user_request)

    workflow_steps = [
        {
            "step_number": 1,
            "name": "Understand User Goal",
            "description": f"Analyze the user request: {user_request}",
            "tool": "internal_reasoning",
        },
        {
            "step_number": 2,
            "name": "Select Tools",
            "description": "Choose the tools required for the agent.",
            "tool": "internal_reasoning",
        },
        {
            "step_number": 3,
            "name": "Execute Agent Task",
            "description": "Run the selected tools in the correct order.",
            "tool": tools_needed[0],
        },
        {
            "step_number": 4,
            "name": "Generate Final Output",
            "description": f"Return the final result as {output_type}.",
            "tool": "internal_reasoning",
        },
    ]

    system_prompt = f"""You are a specialized AI agent created by AgentForge.

Your goal:
{user_request}

Execution frequency:
{frequency}

Expected output type:
{output_type}

Available tools:
{chr(10).join("- " + tool for tool in tools_needed)}

Operating instructions:
1. Understand the user's request clearly.
2. Use the available tools only when relevant.
3. Produce a useful and practical final output.
4. If information is missing, state assumptions clearly.
5. Keep the response professional and concise.

This agent is currently running in mock mode.
"""

    return {
        "goal": user_request,
        "frequency": frequency,
        "output_type": output_type,
        "tools_needed": tools_needed,
        "tool_configurations": [
            {
                "tool": tool,
                "mode": "mock",
                "requires_api_key": False,
                "status": "configured",
            }
            for tool in tools_needed
        ],
        "system_prompt": system_prompt,
        "workflow_steps": workflow_steps,
        "memory_config": {
            "enabled": True,
            "type": "local_json",
            "description": "Agent memory is currently simulated using local JSON storage.",
        },
        "validation_result": {
            "is_valid": True,
            "score": 90,
            "mode": "fallback_mock",
            "notes": [
                "Generated using fallback mock generator.",
                "This keeps the app working even if LangGraph pipeline import fails.",
            ],
            "pipeline_import_error": PIPELINE_IMPORT_ERROR,
        },
        "mode": "mock",
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "AgentForge API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "backend": "running",
        "mock_mode": os.getenv("AGENTFORGE_MOCK_MODE", "true"),
        "pipeline_available": build_agent is not None,
        "pipeline_import_error": PIPELINE_IMPORT_ERROR,
    }


@app.post("/agents/generate")
def generate_agent(request: AgentRequest) -> Dict[str, Any]:
    if build_agent is None:
        return fallback_generate_agent(request.user_request)

    try:
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

        return {
            "goal": result.get("goal", request.user_request),
            "frequency": result.get("frequency", detect_frequency(request.user_request)),
            "output_type": result.get("output_type", detect_output_type(request.user_request)),
            "tools_needed": result.get("tools_needed", select_mock_tools(request.user_request)),
            "tool_configurations": result.get("tool_configurations", []),
            "system_prompt": result.get("system_prompt", ""),
            "workflow_steps": result.get("workflow_steps", []),
            "memory_config": result.get("memory_config", {}),
            "validation_result": result.get("validation_result", {}),
            "mode": os.getenv("AGENTFORGE_MOCK_MODE", "true"),
        }

    except Exception as error:
        fallback = fallback_generate_agent(request.user_request)
        fallback["validation_result"]["pipeline_runtime_error"] = repr(error)
        return fallback


@app.post("/agents/save")
def save_agent(request: SaveAgentRequest) -> Dict[str, Any]:
    saved_agent = create_agent(
        {
            "name": request.name or request.agent.get("goal") or "Untitled Agent",
            "original_request": request.original_request,
            **request.agent,
        }
    )

    return saved_agent


@app.get("/agents")
def get_agents() -> List[Dict[str, Any]]:
    return list_agents()


@app.get("/agents/export")
def export_agents() -> Response:
    agents = list_agents()
    content = json.dumps(agents, indent=2)

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="agentforge_saved_agents.json"'
        },
    )


@app.get("/agents/{agent_id}")
def get_single_agent(agent_id: str) -> Dict[str, Any]:
    agent = get_agent(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return agent


@app.post("/agents/{agent_id}/run")
def run_agent(agent_id: str) -> Dict[str, Any]:
    agent = get_agent(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    run_result = run_agent_blueprint(agent)

    update_agent_after_run(
        agent_id=agent_id,
        evaluation=run_result.get("evaluation", {}),
        evolution=run_result.get("evolution", {}),
    )

    saved_run = create_run(agent_id, run_result)

    return saved_run


@app.get("/runs")
def get_all_runs() -> List[Dict[str, Any]]:
    return list_runs()


@app.get("/agents/{agent_id}/runs")
def get_agent_runs(agent_id: str) -> List[Dict[str, Any]]:
    agent = get_agent(agent_id)

    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return list_runs_for_agent(agent_id)

@app.delete("/agents/{agent_id}")
def remove_agent(agent_id: str) -> Dict[str, Any]:
    deleted = delete_agent(agent_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return {
        "deleted": True,
        "id": agent_id,
    }
