from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from database.db import execute_query, execute_read


def now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def serialize(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return json.dumps(val)


def deserialize(val: Optional[str]) -> Any:
    if not val:
        return None
    try:
        return json.loads(val)
    except Exception:
        return val


def parse_agent_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert database row fields to agent dictionary format."""
    agent_id = row["id"]
    
    # Query workflow steps for this agent
    steps_rows = execute_read(
        "SELECT step_number, name, description, tool FROM workflows WHERE agent_id = %s ORDER BY step_number",
        (agent_id,)
    )
    
    workflow_steps = []
    for step in steps_rows:
        workflow_steps.append({
            "step_number": step["step_number"],
            "name": step["name"],
            "description": step["description"],
            "tool": step["tool"]
        })

    return {
        "id": agent_id,
        "name": row["name"],
        "goal": row["goal"],
        "frequency": row["frequency"],
        "output_type": row["output_type"],
        "system_prompt": row["system_prompt"],
        "memory_config": deserialize(row["memory_config"]),
        "validation_result": deserialize(row["validation_result"]),
        "tools_needed": deserialize(row["tools_needed"]) or [],
        "tool_configurations": deserialize(row["tool_configurations"]) or [],
        "mode": row["mode"],
        "original_request": row["original_request"],
        "workflow_steps": workflow_steps,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_agents() -> List[Dict[str, Any]]:
    rows = execute_read("SELECT * FROM agents")
    agents = [parse_agent_row(row) for row in rows]
    return sorted(agents, key=lambda item: item.get("created_at", ""), reverse=True)


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    rows = execute_read("SELECT * FROM agents WHERE id = %s", (agent_id,))
    if not rows:
        return None
    return parse_agent_row(rows[0])


def create_agent(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = agent_data.get("id") or str(uuid4())
    created = agent_data.get("created_at") or now_utc()
    updated = now_utc()
    
    name = agent_data.get("name") or agent_data.get("goal") or "Untitled Agent"
    goal = agent_data.get("goal", "")
    frequency = agent_data.get("frequency", "on-demand")
    output_type = agent_data.get("output_type", "structured response")
    system_prompt = agent_data.get("system_prompt", "")
    
    memory_config = serialize(agent_data.get("memory_config", {}))
    validation_result = serialize(agent_data.get("validation_result", {}))
    tools_needed = serialize(agent_data.get("tools_needed", []))
    tool_configurations = serialize(agent_data.get("tool_configurations", []))
    
    mode = agent_data.get("mode", "mock")
    original_request = agent_data.get("original_request", "")

    # Insert agent details
    execute_query(
        """
        INSERT INTO agents (
            id, name, goal, frequency, output_type, system_prompt, 
            memory_config, validation_result, tools_needed, 
            tool_configurations, mode, original_request, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            agent_id, name, goal, frequency, output_type, system_prompt,
            memory_config, validation_result, tools_needed,
            tool_configurations, mode, original_request, created, updated
        )
    )

    # Insert workflow steps
    workflow_steps = agent_data.get("workflow_steps", [])
    for step in workflow_steps:
        execute_query(
            """
            INSERT INTO workflows (agent_id, step_number, name, description, tool)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                agent_id,
                step.get("step_number"),
                step.get("name", ""),
                step.get("description", ""),
                step.get("tool", "")
            )
        )

    return get_agent(agent_id)


def delete_agent(agent_id: str) -> bool:
    rows = execute_read("SELECT id FROM agents WHERE id = %s", (agent_id,))
    if not rows:
        return False
        
    execute_query("DELETE FROM agents WHERE id = %s", (agent_id,))
    return True
