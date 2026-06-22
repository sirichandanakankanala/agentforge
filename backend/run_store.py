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


def parse_run_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert database row fields to run dictionary format."""
    return {
        "id": row["id"],
        "agent_id": row["agent_id"],
        "agent_name": row.get("agent_name") or "Untitled Agent",
        "run_id": row["run_id"],
        "status": row["status"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "used_tools": deserialize(row["used_tools"]) or [],
        "tool_results": deserialize(row["tool_results"]) or [],
        "evaluation": deserialize(row["evaluation"]) or {},
        "evolution": deserialize(row["evolution"]) or {},
        "output": deserialize(row["output"]) or {},
        "logs": deserialize(row["logs"]) or [],
        "created_at": row["created_at"],
    }


def create_run(agent_id: str, run_result: Dict[str, Any]) -> Dict[str, Any]:
    run_db_id = str(uuid4())
    created = now_utc()

    run_id = run_result.get("run_id") or str(uuid4())
    status = run_result.get("status", "completed")
    started_at = run_result.get("started_at") or created
    completed_at = run_result.get("completed_at") or created
    
    used_tools = serialize(run_result.get("used_tools", []))
    tool_results = serialize(run_result.get("tool_results", []))
    evaluation = serialize(run_result.get("evaluation", {}))
    evolution = serialize(run_result.get("evolution", {}))
    output = serialize(run_result.get("output", {}))
    logs = serialize(run_result.get("logs", []))

    # Insert execution log
    execute_query(
        """
        INSERT INTO execution_logs (
            id, agent_id, run_id, status, started_at, completed_at, 
            used_tools, tool_results, evaluation, evolution, output, logs, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            run_db_id, agent_id, run_id, status, started_at, completed_at,
            used_tools, tool_results, evaluation, evolution, output, logs, created
        )
    )

    # Return the created run (joining with agents table to get agent_name)
    rows = execute_read(
        """
        SELECT e.*, a.name AS agent_name 
        FROM execution_logs e 
        LEFT JOIN agents a ON e.agent_id = a.id 
        WHERE e.id = %s
        """,
        (run_db_id,)
    )
    return parse_run_row(rows[0])


def list_runs() -> List[Dict[str, Any]]:
    rows = execute_read(
        """
        SELECT e.*, a.name AS agent_name 
        FROM execution_logs e 
        LEFT JOIN agents a ON e.agent_id = a.id
        """
    )
    runs = [parse_run_row(row) for row in rows]
    return sorted(runs, key=lambda item: item.get("created_at", ""), reverse=True)


def list_runs_for_agent(agent_id: str) -> List[Dict[str, Any]]:
    rows = execute_read(
        """
        SELECT e.*, a.name AS agent_name 
        FROM execution_logs e 
        LEFT JOIN agents a ON e.agent_id = a.id 
        WHERE e.agent_id = %s
        """,
        (agent_id,)
    )
    runs = [parse_run_row(row) for row in rows]
    return sorted(runs, key=lambda item: item.get("created_at", ""), reverse=True)
