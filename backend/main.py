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
from logger import get_logger
from error_handler import handle_errors, monitor_performance
from scheduler import get_agent_scheduler
from memory import get_memory_manager
from tools import get_tool_registry, MockWebSearchTool, MockNotificationSenderTool, MockSummarizerTool
from ws_manager import get_ws_manager
from fastapi import WebSocket, WebSocketDisconnect

load_dotenv()
os.environ.setdefault("AGENTFORGE_MOCK_MODE", "true")

# Initialize logging
logger = get_logger("main")


PIPELINE_IMPORT_ERROR: Optional[str] = None

try:
    from agents.pipeline import build_agent
except Exception as error:
    build_agent = None
    PIPELINE_IMPORT_ERROR = repr(error)


app = FastAPI(
    title="AgentForge API",
    description="Generate, save, run, and export AI agent blueprints.",
    version="1.4.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize systems
@app.on_event("startup")
async def startup_event():
    """Initialize backend systems on startup."""
    logger.info("Starting AgentForge backend...")
    
    # Initialize tool registry
    registry = get_tool_registry()
    registry.register(MockWebSearchTool())
    registry.register(MockNotificationSenderTool())
    registry.register(MockSummarizerTool())
    logger.info(f"Registered {len(registry.list_tools())} mock tools")
    
    # Start scheduler
    scheduler = get_agent_scheduler()
    scheduler.start()
    logger.info("Agent scheduler started")
    
    # Initialize memory manager
    memory_manager = get_memory_manager()
    logger.info("Memory manager initialized")
    
    logger.info("✅ Backend startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down AgentForge backend...")
    scheduler = get_agent_scheduler()
    scheduler.stop()
    logger.info("✅ Backend shutdown complete")


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
@monitor_performance(threshold_ms=100)
def health() -> Dict[str, Any]:
    registry = get_tool_registry()
    scheduler = get_agent_scheduler()
    
    return {
        "status": "healthy",
        "backend": "running",
        "version": "1.4.0",
        "mock_mode": os.getenv("AGENTFORGE_MOCK_MODE", "true"),
        "pipeline_available": build_agent is not None,
        "pipeline_import_error": PIPELINE_IMPORT_ERROR,
        "tools_registered": len(registry.list_tools()),
        "scheduler_running": scheduler.scheduler.running,
        "scheduled_agents": len(scheduler.list_schedules()),
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


@app.websocket("/ws/agents/{agent_id}/run")
async def websocket_run_agent(websocket: WebSocket, agent_id: str):
    """Run an agent and stream progress over WebSocket."""
    ws = get_ws_manager()
    await ws.connect(agent_id, websocket)

    try:
        agent = get_agent(agent_id)
        if not agent:
            await websocket.send_json({"error": "Agent not found"})
            return

        # define progress callback
        def progress_cb(evt: dict):
            # send as JSON; ensure non-async callback wraps sending
            try:
                # best-effort: use create_task to avoid blocking
                import asyncio as _asyncio

                # include the agent_id key so the WebSocketManager can route messages
                _asyncio.create_task(ws.send_json(agent_id, {"type": "progress", "data": evt}))
            except Exception:
                pass

        # run agent synchronously but stream via callback
        result = run_agent_blueprint(agent, progress_callback=progress_cb)

        # send final result (route to this agent's connections)
        await ws.send_json(agent_id, {"type": "complete", "data": result})

    except WebSocketDisconnect:
        ws.disconnect(agent_id, websocket)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        ws.disconnect(agent_id, websocket)

@app.delete("/agents/{agent_id}")
def remove_agent(agent_id: str) -> Dict[str, Any]:
    deleted = delete_agent(agent_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found.")

    return {
        "deleted": True,
        "id": agent_id,
    }


# ============================================================================
# NEW ROUTES: Tools, Memory, and Scheduling
# ============================================================================

@app.get("/tools")
@monitor_performance(threshold_ms=100)
def list_tools() -> Dict[str, Any]:
    """List all available tools."""
    registry = get_tool_registry()
    tools = registry.list_tools()
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "requires_api_key": tool.requires_api_key,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                        "enum": p.enum,
                    }
                    for p in tool.parameters
                ],
            }
            for tool in tools
        ],
        "total": len(tools),
        "mock_mode": registry.mock_mode,
    }


@app.get("/tools/{category}")
@monitor_performance(threshold_ms=100)
def list_tools_by_category(category: str) -> Dict[str, Any]:
    """List tools in a specific category."""
    registry = get_tool_registry()
    tools = registry.list_tools_by_category(category)
    
    if not tools:
        raise HTTPException(status_code=404, detail=f"No tools found in category: {category}")
    
    return {
        "category": category,
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "requires_api_key": tool.requires_api_key,
            }
            for tool in tools
        ],
        "total": len(tools),
    }


class ScheduleAgentRequest(BaseModel):
    frequency: str  # "daily", "weekly", "hourly", or cron expression


@app.post("/agents/{agent_id}/schedule")
@monitor_performance(threshold_ms=500)
def schedule_agent(agent_id: str, request: ScheduleAgentRequest) -> Dict[str, Any]:
    """Schedule an agent to run at specified frequency."""
    agent = get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    scheduler = get_agent_scheduler()
    
    try:
        # Define callback to run the agent
        def agent_callback():
            logger.info(f"Executing scheduled agent: {agent_id}")
            run_agent(agent_id)
        
        job_id = scheduler.schedule_agent(agent_id, request.frequency, agent_callback)
        
        if not job_id:
            raise HTTPException(status_code=400, detail="Failed to schedule agent")
        
        schedule = scheduler.get_schedule(agent_id)
        return {
            "agent_id": agent_id,
            "status": "scheduled",
            "frequency": request.frequency,
            "job_id": job_id,
            "next_run": str(schedule["next_run"]) if schedule else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid frequency: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to schedule agent {agent_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule agent")


@app.delete("/agents/{agent_id}/schedule")
def unschedule_agent(agent_id: str) -> Dict[str, Any]:
    """Remove scheduled execution for an agent."""
    scheduler = get_agent_scheduler()
    
    if scheduler.remove_schedule(agent_id):
        return {
            "agent_id": agent_id,
            "status": "unscheduled",
        }
    else:
        raise HTTPException(status_code=404, detail="Agent not scheduled")


@app.get("/schedules")
@monitor_performance(threshold_ms=100)
def list_schedules() -> Dict[str, Any]:
    """List all scheduled agents."""
    scheduler = get_agent_scheduler()
    schedules = scheduler.list_schedules()
    
    return {
        "schedules": [
            {
                "agent_id": agent_id,
                "frequency": info["frequency"],
                "next_run": str(info["next_run"]) if info["next_run"] else None,
            }
            for agent_id, info in schedules.items()
        ],
        "total": len(schedules),
    }


class StoreMemoryRequest(BaseModel):
    key: str
    value: Any
    ttl_minutes: Optional[int] = None


@app.post("/agents/{agent_id}/memory")
def store_agent_memory(agent_id: str, request: StoreMemoryRequest) -> Dict[str, Any]:
    """Store data in agent memory."""
    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(agent_id, "short_term")
    
    if memory.store(request.key, request.value, request.ttl_minutes):
        return {
            "agent_id": agent_id,
            "key": request.key,
            "status": "stored",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to store memory")


@app.get("/agents/{agent_id}/memory/{key}")
def retrieve_agent_memory(agent_id: str, key: str) -> Dict[str, Any]:
    """Retrieve data from agent memory."""
    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(agent_id, "short_term")
    
    value = memory.retrieve(key)
    if value is not None:
        return {
            "agent_id": agent_id,
            "key": key,
            "value": value,
        }
    else:
        raise HTTPException(status_code=404, detail=f"Memory key not found: {key}")


@app.get("/agents/{agent_id}/memory")
def list_agent_memory(agent_id: str) -> Dict[str, Any]:
    """List all memory for an agent."""
    memory_manager = get_memory_manager()
    stats = memory_manager.get_stats(agent_id)
    
    return stats


@app.delete("/agents/{agent_id}/memory")
def clear_agent_memory(agent_id: str) -> Dict[str, Any]:
    """Clear all memory for an agent."""
    memory_manager = get_memory_manager()
    memory_manager.clear_agent_memory(agent_id)
    
    return {
        "agent_id": agent_id,
        "status": "cleared",
    }
