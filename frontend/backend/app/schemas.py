from pydantic import BaseModel
from typing import List


class AgentRequest(BaseModel):
    goal: str
    frequency: str = "on-demand"
    output_type: str = "structured response"


class WorkflowStep(BaseModel):
    step_number: int
    name: str
    description: str
    tool: str


class AgentBlueprint(BaseModel):
    goal: str
    frequency: str
    output_type: str
    tools_needed: List[str]
    system_prompt: str
    workflow_steps: List[WorkflowStep]
