from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from evaluator import evaluate_agent_run
from evolution_engine import suggest_agent_improvements


def now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def fake_tool_output(tool_name: str, goal: str) -> Dict[str, Any]:
    lower_tool = tool_name.lower()

    if "web" in lower_tool or "news" in lower_tool or "search" in lower_tool:
        return {
            "tool": tool_name,
            "status": "success",
            "summary": f"Mock web/news search completed for: {goal}",
            "items_found": 5,
        }

    if "notification" in lower_tool or "alert" in lower_tool:
        return {
            "tool": tool_name,
            "status": "success",
            "summary": "Mock notification prepared successfully.",
        }

    if "email" in lower_tool:
        return {
            "tool": tool_name,
            "status": "success",
            "summary": "Mock email draft prepared successfully.",
        }

    if "summarizer" in lower_tool or "summary" in lower_tool:
        return {
            "tool": tool_name,
            "status": "success",
            "summary": "Mock summary generated successfully.",
        }

    return {
        "tool": tool_name,
        "status": "success",
        "summary": f"Mock execution completed for {tool_name}.",
    }


def run_agent_blueprint(agent: Dict[str, Any]) -> Dict[str, Any]:
    goal = agent.get("goal", "Untitled goal")
    tools: List[str] = agent.get("tools_needed", [])
    output_type = agent.get("output_type", "structured response")

    tool_results = [fake_tool_output(tool, goal) for tool in tools]

    evaluation = evaluate_agent_run(agent, tool_results)
    evolution = suggest_agent_improvements(agent, evaluation)

    return {
        "run_id": str(uuid4()),
        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),
        "status": "completed",
        "started_at": now_utc(),
        "completed_at": now_utc(),
        "used_tools": tools,
        "tool_results": tool_results,
        "evaluation": evaluation,
        "evolution": evolution,
        "output": {
            "title": f"Mock run result for: {goal}",
            "output_type": output_type,
            "message": "The saved agent blueprint was loaded, executed in mock mode, evaluated, and passed to the Evolution Engine.",
            "key_points": [
                "Saved agent was found.",
                "Workflow was simulated.",
                "Tool calls were mocked.",
                "Evaluation Agent scored the run.",
                "Evolution Engine generated improvement suggestions.",
                "Final result was generated.",
            ],
            "evaluation_summary": {
                "final_score": evaluation["final_score"],
                "verdict": evaluation["verdict"],
                "feedback": evaluation["feedback"],
            },
            "evolution_summary": {
                "action": evolution["action"],
                "suggestions": evolution["suggestions"],
                "auto_modified": evolution["auto_modified"],
            },
            "next_upgrade": "Store Evolution Engine suggestions in the Agent Registry for future agent improvement.",
        },
        "logs": [
            "Loaded saved agent blueprint.",
            "Read selected tools.",
            "Executed mock tools.",
            "Generated final output.",
            "Evaluation Agent scored the result.",
            "Evolution Engine suggested improvements.",
        ],
    }
