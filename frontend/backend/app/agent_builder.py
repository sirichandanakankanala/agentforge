from app.schemas import AgentRequest, AgentBlueprint, WorkflowStep


def infer_tools(goal: str):
    goal_lower = goal.lower()

    tools = []

    if "news" in goal_lower or "search" in goal_lower or "research" in goal_lower:
        tools.append("web_search")

    if "email" in goal_lower:
        tools.append("email_sender")

    if "linkedin" in goal_lower:
        tools.append("linkedin_monitor")

    if "report" in goal_lower or "summary" in goal_lower:
        tools.append("summarizer")

    if "alert" in goal_lower or "notify" in goal_lower:
        tools.append("notification_sender")

    if not tools:
        tools.append("general_reasoning")

    return tools


def build_agent_blueprint(request: AgentRequest):
    tools = infer_tools(request.goal)

    system_prompt = f"""
You are a specialized AI agent created by AgentForge.

Your goal:
{request.goal}

Execution frequency:
{request.frequency}

Expected output type:
{request.output_type}

Available tools:
{chr(10).join("- " + tool for tool in tools)}

Operating instructions:
1. Understand the user's request clearly before acting.
2. Use the available tools only when relevant.
3. Produce a clear and practical final output.
4. If information is missing, state assumptions clearly.
5. Keep the response professional and concise.
""".strip()

    workflow_steps = [
        WorkflowStep(
            step_number=1,
            name="Understand User Objective",
            description=f"Analyze the goal: {request.goal}",
            tool="internal_reasoning"
        ),
        WorkflowStep(
            step_number=2,
            name="Select Required Tools",
            description="Choose tools needed to complete the task.",
            tool="tool_selector"
        ),
        WorkflowStep(
            step_number=3,
            name="Execute Task",
            description="Use selected tools to complete the goal.",
            tool=tools[0]
        ),
        WorkflowStep(
            step_number=4,
            name="Generate Final Output",
            description=f"Return the result as a {request.output_type}.",
            tool="response_generator"
        )
    ]

    return AgentBlueprint(
        goal=request.goal,
        frequency=request.frequency,
        output_type=request.output_type,
        tools_needed=tools,
        system_prompt=system_prompt,
        workflow_steps=workflow_steps
    )
