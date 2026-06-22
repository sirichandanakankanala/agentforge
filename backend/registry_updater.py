from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


DATA_DIR = Path(__file__).resolve().parent / "data"


def now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def update_agent_after_run(
    agent_id: str,
    evaluation: Dict[str, Any],
    evolution: Dict[str, Any],
) -> bool:
    """
    Updates the saved agent profile after a run.

    This stores:
    - latest evaluation score
    - latest verdict
    - latest evolution action
    - improvement suggestions
    - last run timestamp

    It safely checks common registry files used in the prototype.
    """

    possible_files = [
        DATA_DIR / "agents.json",
        DATA_DIR / "generated_agents.json",
    ]

    for file_path in possible_files:
        if not file_path.exists():
            continue

        try:
            agents = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        if not isinstance(agents, list):
            continue

        updated = False

        for agent in agents:
            if agent.get("id") == agent_id:
                agent["latest_evaluation"] = {
                    "final_score": evaluation.get("final_score"),
                    "verdict": evaluation.get("verdict"),
                    "feedback": evaluation.get("feedback"),
                }

                agent["latest_evolution"] = {
                    "action": evolution.get("action"),
                    "suggestions": evolution.get("suggestions", []),
                    "auto_modified": evolution.get("auto_modified", False),
                }

                agent["last_run_at"] = now_utc()
                # Attempt simple automatic modifications when safe
                try:
                    auto_apply = evolution.get("auto_apply", False) or evolution.get("auto_modified", False)
                    # If action suggests improvement and auto_apply requested, make minimal safe changes
                    if evolution.get("action") in ("improve_agent", "IMPROVE", "improve") and not agent["latest_evolution"].get("auto_modified"):
                        suggestions = evolution.get("suggestions", []) or []
                        modified = False

                        # If no tools, add conservative defaults
                        if not agent.get("tools_needed"):
                            agent.setdefault("tools_needed", [])
                            agent.setdefault("tool_configurations", [])
                            # conservative default tools
                            for default_tool in ["web_search", "summarizer"]:
                                if default_tool not in agent["tools_needed"]:
                                    agent["tools_needed"].append(default_tool)
                                    agent["tool_configurations"].append({
                                        "tool": default_tool,
                                        "mode": "mock",
                                        "requires_api_key": False,
                                        "status": "auto_added",
                                    })
                                    modified = True

                        # If prompts should be improved, append a clarifying sentence
                        for s in suggestions:
                            lower = s.lower()
                            if "improve the system prompt" in lower or "make the agent goal more specific" in lower:
                                sp = agent.get("system_prompt", "")
                                addition = "\n\n[Auto-Upgrade] Clarify: make the goal explicit and include success criteria."
                                agent["system_prompt"] = (sp or "") + addition
                                modified = True

                        if modified and auto_apply:
                            agent["latest_evolution"]["auto_modified"] = True
                            evolution["auto_modified"] = True
                        
                except Exception:
                    # Non-fatal - don't block writing the main file
                    pass
                updated = True
                break

        if updated:
            file_path.write_text(json.dumps(agents, indent=2), encoding="utf-8")
            return True

    return False
