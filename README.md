# AgentForge: Dynamic AI Agent Builder Platform

AgentForge is a full-stack AI agent blueprint builder that converts a plain-English user goal into a structured specialist agent configuration.

The system takes a request such as:

```text
Create an agent that sends me daily AI news alerts
```

and generates an agent blueprint containing:

* Goal analysis
* Execution frequency
* Output type
* Required tools
* Tool configurations
* System prompt
* Workflow steps
* Memory configuration
* Validation result
* Mock execution output

This project demonstrates the architecture of an AI system that can generate and manage specialized autonomous agents from natural language goals.

---

## Features

* Generate AI agent blueprints from user goals
* Select tools based on the requested task
* Generate system prompts automatically
* Build workflow steps for the agent
* Configure memory structure
* Validate generated blueprints
* Save generated agents
* View saved agents
* Run saved agents in mock mode
* Delete saved agents
* Download a single agent blueprint as JSON
* Download all saved agents as JSON
* React frontend with FastAPI backend

---

## Tech Stack

### Backend

* Python
* FastAPI
* LangGraph
* Pydantic
* Uvicorn
* JSON-based local storage

### Frontend

* React
* Vite
* JavaScript
* HTML/CSS

---

## Project Structure

```text
AgentForge/
├── backend/
│   ├── agents/
│   │   ├── goal_analysis.py
│   │   ├── tool_selection.py
│   │   ├── prompt_generation.py
│   │   ├── workflow_design.py
│   │   ├── memory_config.py
│   │   ├── validation.py
│   │   ├── pipeline.py
│   │   ├── state.py
│   │   └── mock_runner.py
│   ├── app.py
│   ├── server.py
│   ├── requirements.txt
│   └── data/
│       └── generated_agents.json
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## How It Works

AgentForge uses a multi-step agent-building pipeline.

```text
User Goal
   ↓
Goal Analysis
   ↓
Tool Selection
   ↓
Prompt Generation
   ↓
Workflow Design
   ↓
Memory Configuration
   ↓
Validation
   ↓
Agent Blueprint JSON
```

The generated blueprint can then be saved, viewed, downloaded, or executed in mock mode.

---

## Backend API Routes

```text
GET     /health
POST    /agents/generate
POST    /agents/save
GET     /agents
GET     /agents/{agent_id}
POST    /agents/{agent_id}/run
DELETE  /agents/{agent_id}
```

---

## Running the Project Locally

### 1. Clone the repository

```bash
git clone https://github.com/sirichandanakankanala/agentforge.git
cd agentforge
```

---

### 2. Run the backend

```bash
conda activate agentforge
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

---

### 3. Run the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## Example Agent Request

```text
Create an agent that sends me daily AI news alerts
```

Example generated blueprint includes:

```json
{
  "goal": "Create an agent that sends me daily AI news alerts",
  "frequency": "daily",
  "output_type": "alert",
  "tools_needed": [
    "web_search",
    "news_filter",
    "summarizer",
    "notification_sender"
  ],
  "mode": "mock"
}
```

---

## Mock Mode

The current version runs in mock mode.

This means the project does not require a paid LLM API key for demonstration. Instead, it simulates tool execution and agent runs locally.

Mock mode is useful for:

* Local development
* Demo presentations
* Architecture validation
* Testing frontend-backend integration
* Avoiding unnecessary API cost

---

## Current Status

Completed:

* Full-stack React + FastAPI application
* Agent blueprint generation
* LangGraph-style backend pipeline
* Saved agent library
* JSON export
* Mock agent execution
* Local JSON storage
* Working frontend-backend integration

---

## Future Improvements

* Connect real LLM API execution
* Add real external tools such as web search, email, calendar, and notifications
* Add PostgreSQL with pgvector for semantic memory
* Add authentication and user-specific agent storage
* Add deployment using Azure Container Apps and Azure Static Web Apps
* Add BYOK support so users can use their own API keys
* Add execution logs, cost tracking, and latency metrics

---

## Summary

AgentForge is a dynamic AI agent builder platform that converts natural language goals into structured, executable agent blueprints.

It demonstrates how goal analysis, tool selection, prompt generation, workflow planning, memory configuration, validation, saving, and mock execution can be combined into one full-stack AI agent-building system.
