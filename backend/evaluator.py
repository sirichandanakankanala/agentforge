from __future__ import annotations

from typing import Any, Dict, List


def evaluate_agent_run(agent: Dict[str, Any], tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluation Agent for AgentForge.

    This evaluates a saved agent run using simple deterministic scoring.
    Later, this can be upgraded to LLM-based evaluation.
    """

    goal = agent.get("goal", "")
    tools_needed = agent.get("tools_needed", [])
    workflow_steps = agent.get("workflow_steps", [])

    successful_tools = [
        result for result in tool_results
        if result.get("status") == "success"
    ]

    relevance_score = 9 if goal else 5
    completeness_score = 9 if workflow_steps else 6
    tool_usage_score = 9 if len(successful_tools) == len(tools_needed) else 6
    execution_score = 9 if successful_tools else 5

    final_score = round(
        (relevance_score + completeness_score + tool_usage_score + execution_score) / 4,
        2
    )

    if final_score >= 8:
        verdict = "good"
        feedback = "The agent blueprint is relevant, executable, and suitable for the user objective."
    elif final_score >= 6:
        verdict = "needs_improvement"
        feedback = "The agent works, but some tools or workflow details can be improved."
    else:
        verdict = "weak"
        feedback = "The agent needs better goal understanding, workflow planning, or tool execution."

    return {
        "agent": "Evaluation Agent",
        "final_score": final_score,
        "verdict": verdict,
        "scores": {
            "relevance": relevance_score,
            "completeness": completeness_score,
            "tool_usage": tool_usage_score,
            "execution": execution_score,
        },
        "feedback": feedback,
        "next_improvement": "Use this evaluation result later inside the Evolution Engine.",
    }
