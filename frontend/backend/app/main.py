from fastapi import FastAPI
from app.schemas import AgentRequest
from app.agent_builder import build_agent_blueprint

app = FastAPI(
    title="AgentForge API",
    description="Backend API for generating specialized AI agent blueprints.",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "AgentForge API"
    }


@app.post("/agents/generate")
def generate_agent(request: AgentRequest):
    return build_agent_blueprint(request)
