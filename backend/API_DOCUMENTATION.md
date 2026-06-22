# AgentForge API Documentation

## Overview
AgentForge API provides endpoints for generating, managing, executing, and monitoring AI agent blueprints.

## Base URL
```
http://localhost:8000
```

## Interactive API Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Health & Status Endpoints

### Get Health Status
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "backend": "running",
  "version": "1.4.0",
  "mock_mode": "true",
  "pipeline_available": true,
  "tools_registered": 3,
  "scheduler_running": true,
  "scheduled_agents": 0
}
```

---

## Agent Management Endpoints

### Generate Agent Blueprint
```http
POST /agents/generate
Content-Type: application/json

{
  "user_request": "Create an agent that sends me daily AI news alerts"
}
```

**Response:**
```json
{
  "goal": "Create an agent that sends me daily AI news alerts",
  "frequency": "daily",
  "output_type": "alert",
  "tools_needed": ["web_search", "notification_sender"],
  "tool_configurations": [...],
  "system_prompt": "...",
  "workflow_steps": [...],
  "memory_config": {...},
  "validation_result": {...}
}
```

### Save Agent
```http
POST /agents/save
Content-Type: application/json

{
  "name": "Daily AI News Alert",
  "original_request": "Create an agent that sends me daily AI news alerts",
  "agent": { ...agent_blueprint }
}
```

### List All Agents
```http
GET /agents
```

### Get Single Agent
```http
GET /agents/{agent_id}
```

### Delete Agent
```http
DELETE /agents/{agent_id}
```

### Export All Agents
```http
GET /agents/export
```

Returns JSON file with all agents.

---

## Agent Execution Endpoints

### Run Agent
```http
POST /agents/{agent_id}/run
```

**Response:**
```json
{
  "run_id": "uuid",
  "agent_id": "agent_id",
  "status": "completed",
  "used_tools": ["web_search"],
  "tool_results": [...],
  "evaluation": {
    "final_score": 85,
    "verdict": "GOOD",
    "feedback": "Agent performed well"
  },
  "evolution": {
    "action": "IMPROVE",
    "suggestions": ["Add error handling", "Improve prompt clarity"],
    "auto_modified": false
  },
  "output": {...},
  "logs": [...]
}
```

### Get All Runs
```http
GET /runs
```

### Get Agent Run History
```http
GET /agents/{agent_id}/runs
```

---

## Tool Management Endpoints

### List All Tools
```http
GET /tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for information",
      "category": "search",
      "requires_api_key": false,
      "parameters": [
        {
          "name": "query",
          "type": "string",
          "description": "Search query",
          "required": true
        }
      ]
    }
  ],
  "total": 3,
  "mock_mode": true
}
```

### List Tools by Category
```http
GET /tools/{category}
```

**Categories:**
- `search` - Search and retrieval tools
- `notification` - Notification and alert tools
- `content` - Content processing tools
- `data` - Data processing tools

---

## Scheduling Endpoints

### Schedule Agent
```http
POST /agents/{agent_id}/schedule
Content-Type: application/json

{
  "frequency": "daily"
}
```

**Frequency Options:**
- `hourly` - Every hour at :00 minutes
- `daily` - Daily at 12:00 UTC
- `weekly` - Weekly on Sunday at 12:00 UTC
- `monthly` - Monthly on 1st at 12:00 UTC
- `cron_expression` - Custom cron expression (e.g., "0 9 * * 1-5" for 9 AM weekdays)

**Response:**
```json
{
  "agent_id": "agent_id",
  "status": "scheduled",
  "frequency": "daily",
  "job_id": "agent_agent_id",
  "next_run": "2024-01-15T12:00:00"
}
```

### Unschedule Agent
```http
DELETE /agents/{agent_id}/schedule
```

### List All Schedules
```http
GET /schedules
```

**Response:**
```json
{
  "schedules": [
    {
      "agent_id": "agent_id",
      "frequency": "daily",
      "next_run": "2024-01-15T12:00:00"
    }
  ],
  "total": 1
}
```

---

## Memory Management Endpoints

### Store Memory
```http
POST /agents/{agent_id}/memory
Content-Type: application/json

{
  "key": "last_search_results",
  "value": {"items": [...]},
  "ttl_minutes": 60
}
```

### Retrieve Memory
```http
GET /agents/{agent_id}/memory/{key}
```

**Response:**
```json
{
  "agent_id": "agent_id",
  "key": "last_search_results",
  "value": {...}
}
```

### List Agent Memory
```http
GET /agents/{agent_id}/memory
```

**Response:**
```json
{
  "agent_id": "agent_id",
  "memories": {
    "short_term": {
      "item_count": 2,
      "items": [
        {
          "key": "last_search_results",
          "stored_at": "2024-01-14T10:30:00",
          "ttl_minutes": 60
        }
      ]
    }
  }
}
```

### Clear Agent Memory
```http
DELETE /agents/{agent_id}/memory
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Description of the error",
  "error_code": "ERROR_CODE",
  "extra_info": {...}
}
```

---

## Environment Variables

Configure backend behavior with these variables:

```bash
# Mock mode (true/false) - simulates tool execution
AGENTFORGE_MOCK_MODE=true

# OpenAI API key - enables real LLM integration
OPENAI_API_KEY=your_key_here

# SerpAPI key - enables real web search
SERPAPI_API_KEY=your_key_here

# Database URL - for PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/agentforge

# CORS origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Rate Limiting & Performance

- Tool execution timeout: 30 seconds per tool
- Agent generation timeout: 60 seconds
- Memory items expire after TTL (Time-To-Live)
- Scheduled agents run in background without blocking API

---

## Examples

### Example 1: Create and Run an Agent

```bash
# Generate agent
curl -X POST http://localhost:8000/agents/generate \
  -H "Content-Type: application/json" \
  -d '{"user_request": "Send me daily tech news"}'

# Save agent
curl -X POST http://localhost:8000/agents/save \
  -H "ContentType: application/json" \
  -d '{"name": "Tech News Agent", "agent": {...}}'

# Run agent
curl -X POST http://localhost:8000/agents/{agent_id}/run

# Get run history
curl http://localhost:8000/agents/{agent_id}/runs
```

### Example 2: Schedule Agent

```bash
# Schedule for daily execution
curl -X POST http://localhost:8000/agents/{agent_id}/schedule \
  -H "Content-Type: application/json" \
  -d '{"frequency": "daily"}'

# Check schedules
curl http://localhost:8000/schedules

# Unschedule
curl -X DELETE http://localhost:8000/agents/{agent_id}/schedule
```

### Example 3: Use Agent Memory

```bash
# Store data
curl -X POST http://localhost:8000/agents/{agent_id}/memory \
  -H "Content-Type: application/json" \
  -d '{"key": "user_preferences", "value": {"theme": "dark"}, "ttl_minutes": 1440}'

# Retrieve data
curl http://localhost:8000/agents/{agent_id}/memory/user_preferences

# Clear all memory
curl -X DELETE http://localhost:8000/agents/{agent_id}/memory
```

---

## WebSocket Endpoints (Future)

Real-time agent execution updates will be available via WebSocket at `/ws/agents/{agent_id}/run`

---

## Version
API Version: **1.4.0**
Last Updated: 2024-01-15
