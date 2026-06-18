from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.pipeline import build_agent
from agents.mock_runner import run_mock_agent

app = FastAPI(title="AgentForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"status": "ok", "message": "AgentForge backend running"}


@app.get("/health")
def health():
    return {"status": "ok", "backend": "online"}


@app.post("/agents/generate")
def generate_agent(payload: dict):
    user_request = payload.get("user_request", "")

    agent = build_agent()
    result = agent.invoke(
        {
            "user_request": user_request,
            "goal": "",
            "frequency": "",
            "output_type": "",
            "tools_needed": [],
            "tool_configurations": [],
            "system_prompt": "",
            "workflow_steps": [],
            "memory_config": {},
            "validation_result": {},
        }
    )

    return result


@app.post("/agents/run-mock")
def run_agent_mock(payload: dict):
    return run_mock_agent(payload)
