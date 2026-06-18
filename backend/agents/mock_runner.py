from __future__ import annotations

from datetime import datetime
from typing import Any


def _extract_blueprint(saved_agent: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Handles both possible saved JSON shapes:

    Shape 1:
    {
      "id": "...",
      "agent": {
        "name": "...",
        "original_request": "...",
        "agent": { actual_blueprint_here }
      }
    }

    Shape 2:
    {
      "id": "...",
      "agent": { actual_blueprint_here }
    }
    """
    wrapper = saved_agent.get("agent", {})

    if isinstance(wrapper, dict) and isinstance(wrapper.get("agent"), dict):
        blueprint = wrapper["agent"]
        name = wrapper.get("name") or blueprint.get("goal") or "Untitled Agent"
        return name, blueprint

    if isinstance(wrapper, dict):
        name = wrapper.get("name") or wrapper.get("goal") or "Untitled Agent"
        return name, wrapper

    return "Untitled Agent", {}


def _simulate_tool(tool_name: str, goal: str) -> dict[str, Any]:
    tool = tool_name.lower()

    if "web" in tool or "search" in tool:
        return {
            "tool": tool_name,
            "status": "success",
            "result": f"Mock web search completed for goal: {goal}",
        }

    if "news" in tool:
        return {
            "tool": tool_name,
            "status": "success",
            "result": [
                "Mock AI news item 1: New model release announced.",
                "Mock AI news item 2: AI regulation update published.",
                "Mock AI news item 3: Startup launches agent automation platform.",
            ],
        }

    if "summar" in tool:
        return {
            "tool": tool_name,
            "status": "success",
            "result": "Mock summary created from collected information.",
        }

    if "notification" in tool or "alert" in tool:
        return {
            "tool": tool_name,
            "status": "success",
            "result": "Mock notification prepared. No real notification was sent.",
        }

    if "linkedin" in tool:
        return {
            "tool": tool_name,
            "status": "success",
            "result": "Mock LinkedIn updates collected.",
        }

    return {
        "tool": tool_name,
        "status": "success",
        "result": f"Mock execution completed for tool: {tool_name}",
    }


def run_mock_agent(saved_agent: dict[str, Any]) -> dict[str, Any]:
    agent_name, blueprint = _extract_blueprint(saved_agent)

    goal = blueprint.get("goal", agent_name)
    tools_needed = blueprint.get("tools_needed", [])
    workflow_steps = blueprint.get("workflow_steps", [])

    logs: list[str] = []
    tool_results: list[dict[str, Any]] = []

    logs.append(f"Loaded saved agent: {agent_name}")
    logs.append(f"Goal: {goal}")

    if workflow_steps:
        logs.append(f"Found {len(workflow_steps)} workflow steps.")
        for index, step in enumerate(workflow_steps, start=1):
            step_name = step.get("name") or step.get("step") or f"Step {index}"
            logs.append(f"Step {index}: {step_name}")
    else:
        logs.append("No workflow steps found. Running directly from tools list.")

    for tool in tools_needed:
        logs.append(f"Running tool: {tool}")
        tool_results.append(_simulate_tool(tool, goal))

    final_output = {
        "title": f"Mock output from {agent_name}",
        "goal": goal,
        "summary": "This is a simulated run. The agent JSON was loaded and executed in mock mode.",
        "next_real_step": "Replace mock tool simulation with real tool APIs.",
    }

    return {
        "agent_id": saved_agent.get("id"),
        "agent_name": agent_name,
        "status": "completed",
        "mode": "mock",
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": datetime.utcnow().isoformat(),
        "used_tools": tools_needed,
        "output": final_output,
        "tool_results": tool_results,
        "logs": logs,
        "source_json": saved_agent,
    }
