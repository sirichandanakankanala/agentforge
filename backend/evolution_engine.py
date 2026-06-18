from __future__ import annotations

from typing import Any, Dict, List


def suggest_agent_improvements(agent: Dict[str, Any], evaluation: Dict[str, Any]) -> Dict[str, Any]:
    score = evaluation.get("final_score", 0)
    verdict = evaluation.get("verdict", "unknown")

    tools_needed = agent.get("tools_needed", [])
    workflow_steps = agent.get("workflow_steps", []) or agent.get("workflow", [])

    suggestions: List[str] = []

    if not tools_needed:
        suggestions.append("Add relevant tools based on the user goal.")

    if not workflow_steps:
        suggestions.append("Add clearer workflow steps for the agent.")

    if score < 8:
        suggestions.append("Improve the system prompt to make the agent goal more specific.")
        suggestions.append("Check whether the selected tools actually match the user objective.")
        suggestions.append("Add missing execution steps before running the agent again.")

    if score >= 8:
        action = "keep_agent"
        suggestions.append("Agent is performing well. Keep this version in the registry.")
    elif score >= 6:
        action = "improve_agent"
        suggestions.append("Agent is usable, but should be improved before reuse.")
    else:
        action = "redesign_agent"
        suggestions.append("Agent should be redesigned because the evaluation score is weak.")

    return {
        "agent": "Evolution Engine",
        "action": action,
        "based_on_verdict": verdict,
        "based_on_score": score,
        "suggestions": suggestions,
        "auto_modified": False,
        "note": "This prototype only suggests improvements. It does not automatically rewrite saved agents yet.",
    }
