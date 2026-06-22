from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4
import os

from evaluator import evaluate_agent_run
from evolution_engine import suggest_agent_improvements
from logger import get_logger
from tools import get_tool_registry

logger = get_logger("agent_runner")


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


async def execute_tool_real(tool_name: str, goal: str) -> Dict[str, Any]:
    """
    Execute a real tool using the tool registry.
    
    Args:
        tool_name: Name of the tool to execute
        goal: Goal/query to pass to the tool
    
    Returns:
        Tool result dictionary
    """
    try:
        registry = get_tool_registry()
        tool = registry.get_tool(tool_name)
        
        if not tool:
            logger.warning(f"Tool not found in registry: {tool_name}")
            return {
                "tool": tool_name,
                "status": "error",
                "error": f"Tool not found: {tool_name}",
                "summary": f"Failed to execute {tool_name}",
            }
        
        # Execute tool with the goal as query
        result = await tool.execute(query=goal)
        
        return {
            "tool": tool_name,
            "status": "success" if result.success else "error",
            "summary": result.output.get("summary", "Tool executed") if result.success else result.error,
            "output": result.output,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
        }
    
    except Exception as e:
        logger.error(f"Error executing real tool {tool_name}: {str(e)}", exc_info=True)
        return {
            "tool": tool_name,
            "status": "error",
            "error": str(e),
            "summary": f"Error executing {tool_name}: {str(e)}",
        }


def run_agent_blueprint(agent: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
    """
    Execute an agent blueprint with improved error handling and real tool support.
    
    Args:
        agent: Agent blueprint dictionary
    
    Returns:
        Execution result with evaluation and evolution
    """
    goal = agent.get("goal", "Untitled goal")
    tools: List[str] = agent.get("tools_needed", [])
    output_type = agent.get("output_type", "structured response")
    mock_mode = os.getenv("AGENTFORGE_MOCK_MODE", "true").lower() == "true"
    
    logger.info(f"Running agent: {agent.get('name')} (goal: {goal[:60]}...)")
    logger.info(f"Mock mode: {mock_mode}, Tools: {tools}")
    
    # Execute tools
    tool_results = []
    execution_logs = [
        f"Loaded agent blueprint: {agent.get('name')}",
        f"Goal: {goal}",
        f"Mode: {'Mock' if mock_mode else 'Real'}",
        f"Tools to execute: {', '.join(tools) if tools else 'None'}",
    ]
    
    if mock_mode:
        # Mock execution (original behavior)
        execution_logs.append("Starting mock tool execution...")
        # stream progress if callback provided
        for i, tool in enumerate(tools):
            tr = fake_tool_output(tool, goal)
            tool_results.append(tr)
            execution_logs.append(f"Mock executed tool: {tool}")
            if progress_callback:
                try:
                    progress_callback({
                        "event": "tool_executed",
                        "tool": tool,
                        "index": i,
                        "total": len(tools),
                        "result": tr,
                    })
                except Exception:
                    pass
        execution_logs.append(f"Mock executed {len(tool_results)} tools")
    else:
        # Real execution using tool registry
        try:
            execution_logs.append("Starting real tool execution...")
            registry = get_tool_registry()

            # Run tools sequentially to allow streaming progress per tool
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def execute_all_tools():
                results = []
                for i, t in enumerate(tools):
                    try:
                        res = await execute_tool_real(t, goal)
                    except Exception as ex:
                        res = ex
                    results.append(res)
                    # Forward progress while running
                    if progress_callback:
                        try:
                            if isinstance(res, Exception):
                                progress_callback({
                                    "event": "tool_error",
                                    "tool": t,
                                    "index": i,
                                    "total": len(tools),
                                    "error": str(res),
                                })
                            else:
                                progress_callback({
                                    "event": "tool_executed",
                                    "tool": t,
                                    "index": i,
                                    "total": len(tools),
                                    "result": res,
                                })
                        except Exception:
                            pass
                return results

            results = loop.run_until_complete(execute_all_tools())

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Tool execution failed: {str(result)}", exc_info=True)
                    tool_results.append({
                        "status": "error",
                        "error": str(result),
                        "summary": f"Tool execution error: {str(result)}",
                    })
                else:
                    tool_results.append(result)

            execution_logs.append(f"Real execution completed {len(tool_results)} tools")

        except Exception as e:
            logger.error(f"Error during real tool execution: {str(e)}", exc_info=True)
            execution_logs.append(f"Error during real execution: {str(e)}")
            # Fallback to mock for this run
            tool_results = [fake_tool_output(tool, goal) for tool in tools]

        finally:
            try:
                loop.close()
            except Exception:
                pass
    
    try:
        evaluation = evaluate_agent_run(agent, tool_results)
        execution_logs.append("Evaluation completed")
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}", exc_info=True)
        evaluation = {
            "final_score": 0,
            "verdict": "ERROR",
            "feedback": f"Evaluation failed: {str(e)}",
            "execution_quality": 0,
            "error": str(e),
        }
        execution_logs.append(f"Evaluation error: {str(e)}")
    
    try:
        evolution = suggest_agent_improvements(agent, evaluation)
        execution_logs.append("Evolution suggestions generated")
    except Exception as e:
        logger.error(f"Evolution error: {str(e)}", exc_info=True)
        evolution = {
            "action": "HOLD",
            "suggestions": ["Run the agent again to gather more data for improvement suggestions"],
            "auto_modified": False,
            "error": str(e),
        }
        execution_logs.append(f"Evolution error: {str(e)}")
    
    result = {
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
            "title": f"Agent run result: {goal}",
            "output_type": output_type,
            "message": f"Agent executed in {'mock' if mock_mode else 'real'} mode, evaluated, and passed to the Evolution Engine.",
            "mode": "mock" if mock_mode else "real",
            "key_points": [
                "Agent blueprint loaded successfully.",
                f"Executed {len(tools)} tool(s)." if tools else "No tools needed.",
                f"Evaluation score: {evaluation.get('final_score', 'N/A')}",
                f"Evolution action: {evolution.get('action', 'HOLD')}",
                "Results available for improvement.",
            ],
            "evaluation_summary": {
                "final_score": evaluation.get("final_score", 0),
                "verdict": evaluation.get("verdict", "UNKNOWN"),
                "feedback": evaluation.get("feedback", ""),
            },
            "evolution_summary": {
                "action": evolution.get("action", "HOLD"),
                "suggestions": evolution.get("suggestions", []),
                "auto_modified": evolution.get("auto_modified", False),
            },
        },
        "logs": execution_logs,
    }
    
    logger.info(f"Agent run completed: {result['run_id']}")
    return result
