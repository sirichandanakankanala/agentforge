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
                updated = True
                break

        if updated:
            file_path.write_text(json.dumps(agents, indent=2), encoding="utf-8")
            return True

    return False
