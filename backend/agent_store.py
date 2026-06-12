from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "agents.json"


def now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_agents() -> List[Dict[str, Any]]:
    ensure_store()

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []


def write_agents(agents: List[Dict[str, Any]]) -> None:
    ensure_store()
    DATA_FILE.write_text(json.dumps(agents, indent=2), encoding="utf-8")


def list_agents() -> List[Dict[str, Any]]:
    agents = load_agents()
    return sorted(agents, key=lambda item: item.get("created_at", ""), reverse=True)


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    for agent in load_agents():
        if agent.get("id") == agent_id:
            return agent
    return None


def create_agent(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    agents = load_agents()

    saved_agent = {
        **agent_data,
        "id": str(uuid4()),
        "name": agent_data.get("name") or agent_data.get("goal") or "Untitled Agent",
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }

    agents.append(saved_agent)
    write_agents(agents)

    return saved_agent


def delete_agent(agent_id: str) -> bool:
    agents = load_agents()
    remaining_agents = [agent for agent in agents if agent.get("id") != agent_id]

    if len(remaining_agents) == len(agents):
        return False

    write_agents(remaining_agents)
    return True
