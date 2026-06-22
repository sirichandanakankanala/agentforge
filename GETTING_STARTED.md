# AgentForge - Getting Started Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- Git

### Backend Setup

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start the backend:**
```bash
python -m uvicorn main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Start development server:**
```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  CreateAgent     │  │  Dashboard       │                │
│  │  Agent Editor    │  │  Run History     │                │
│  │  Scheduler UI    │  │  Agent Library   │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                           ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Routes (Generation, Management, Execution)       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  LangGraph Pipeline (Goal → Tool → Workflow → Valid)  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tool Registry (Web Search, Notifications, etc.)      │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Agent Scheduler (APScheduler - Background Jobs)      │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Memory Manager (Short-term & Long-term)              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Execution Engine (Mock & Real Tool Support)          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│            Database & External Services                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SQLite/     │  │  OpenAI API  │  │  SerpAPI     │      │
│  │  PostgreSQL  │  │  (Real LLMs) │  │  (Web Search)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Backend (.env)

```bash
# Mock mode (set false to enable real LLM/tool execution)
AGENTFORGE_MOCK_MODE=true

# OpenAI settings (for real agent generation)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Web search (SerpAPI)
SERPAPI_API_KEY=your_serpapi_key

# Database
DATABASE_URL=sqlite:///agentforge.db
# For PostgreSQL: postgresql://user:pass@localhost/agentforge

# CORS settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

### Frontend (.env)

```bash
VITE_API_BASE=http://localhost:8000
```

---

## 📚 Key Features

### 1. Agent Generation
Generate AI agent blueprints from natural language descriptions:
- Goal analysis
- Tool selection
- Prompt generation
- Workflow design
- Memory configuration
- Validation

### 2. Agent Management
- **List agents** in your library
- **View agent details** with full configuration
- **Edit agents** (name, goal, frequency, output type)
- **Delete agents** and associated runs
- **Export agents** as JSON

### 3. Agent Execution
- **Run agents** manually or scheduled
- **Mock mode** for testing without API keys
- **Real execution** with configured tools
- **Evaluation** of run quality
- **Evolution suggestions** for improvements

### 4. Scheduling
Schedule agents to run automatically:
- Hourly, daily, weekly, monthly
- Custom cron expressions
- View next scheduled run times
- Manage all schedules

### 5. Tool Registry
Built-in tools with extensible architecture:
- **Web Search** (Mock & Real via SerpAPI)
- **Notification Sender** (Mock email/Slack)
- **Text Summarizer** (Mock)
- Easily add more tools!

### 6. Memory System
Store and retrieve execution context:
- Short-term memory (session-based)
- Long-term memory (persistent)
- TTL support (expiration)
- Search capabilities

### 7. Observability
- Comprehensive logging to files and console
- Performance monitoring
- Execution logs with detailed trace
- Error tracking and reporting

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest --cov=. tests/
```

### Test Categories
- **Unit tests** - individual components
- **Integration tests** - components working together
- **Async tests** - async/await code
- **Tool tests** - tool execution and registry

---

## 🛠️ Development Commands

### Backend

```bash
# Development server with auto-reload
python -m uvicorn main:app --reload

# Run with specific port
python -m uvicorn main:app --port 8001

# Run with workers (production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# Check logs
tail -f logs/agentforge_*.log

# Run linter
pylint backend/

# Format code
black backend/
```

### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint

# Format code
npm run format
```

---

## 📖 API Examples

### Generate Agent Blueprint
```bash
curl -X POST http://localhost:8000/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Send me daily AI news"
  }'
```

### Save Agent
```bash
curl -X POST http://localhost:8000/agents/save \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI News Agent",
    "agent": { ...blueprint }
  }'
```

### List Agents
```bash
curl http://localhost:8000/agents
```

### Run Agent
```bash
curl -X POST http://localhost:8000/agents/{agent_id}/run
```

### Schedule Agent
```bash
curl -X POST http://localhost:8000/agents/{agent_id}/schedule \
  -H "Content-Type: application/json" \
  -d '{"frequency": "daily"}'
```

### View Schedules
```bash
curl http://localhost:8000/schedules
```

### Store Agent Memory
```bash
curl -X POST http://localhost:8000/agents/{agent_id}/memory \
  -H "Content-Type: application/json" \
  -d '{
    "key": "last_results",
    "value": { "data": "..." },
    "ttl_minutes": 60
  }'
```

### List Tools
```bash
curl http://localhost:8000/tools
```

---

## 🚀 Deployment

### Docker Deployment

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      AGENTFORGE_MOCK_MODE: "false"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      SERPAPI_API_KEY: "${SERPAPI_API_KEY}"
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      VITE_API_BASE: "http://localhost:8000"
    depends_on:
      - backend
```

### Heroku Deployment

```bash
# Create Heroku app
heroku create agentforge-app

# Set environment variables
heroku config:set OPENAI_API_KEY="..."
heroku config:set AGENTFORGE_MOCK_MODE=false

# Deploy
git push heroku main
```

---

## 🔐 Security Considerations

1. **API Keys**
   - Never commit .env files
   - Use environment variables for secrets
   - Implement API key rotation
   - Rate limit API endpoints

2. **Database**
   - Use strong passwords
   - Enable SSL for production DB
   - Regular backups
   - Parameterized queries (built-in)

3. **Frontend**
   - CORS restrictions
   - Input validation
   - Output sanitization
   - HTTPS only in production

---

## 📊 Monitoring

### Logs
Backend logs are stored in `logs/` directory with daily rotation.

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
Hook into `/health` endpoint to see:
- Tools registered
- Scheduler status
- Scheduled agents count
- Pipeline availability

---

## 📝 Troubleshooting

### Backend won't start
```bash
# Check port availability
lsof -i :8000

# Check dependencies
pip list | grep -E "fastapi|uvicorn"

# Check Python version
python --version
```

### Frontend can't connect to backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings in .env
# Check API base URL in frontend
```

### Tools not executing
```bash
# Check mock mode
curl http://localhost:8000/health | grep mock_mode

# Check tool registry
curl http://localhost:8000/tools

# Check logs
tail -f logs/agentforge_*.log
```

### Database errors
```bash
# Reset SQLite
rm agentforge.db
# Restart backend to recreate schema

# For PostgreSQL, check connection
psql $DATABASE_URL -c "SELECT 1"
```

---

## 📚 Next Steps

1. **Configure API Keys**
   - Set `OPENAI_API_KEY` for real agent generation
   - Set `SERPAPI_API_KEY` for real web search
   - Set `AGENTFORGE_MOCK_MODE=false`

2. **Implement Additional Tools**
   - Create tool classes in `backend/tools/implementations.py`
   - Register tools in `main.py` startup

3. **Add Unit Tests**
   - Add tests in `backend/tests/`
   - Run `pytest` before commits

4. **Deploy to Production**
   - Use Docker for consistent environment
   - Set up PostgreSQL for scalability
   - Configure CDN for frontend
   - Set up monitoring and alerting

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/amazing`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing`
4. Open pull request

---

## 📄 License

[Add your license here]

---

## 📞 Support

For issues and questions:
- Check [API Documentation](./backend/API_DOCUMENTATION.md)
- Review [logs](./backend/logs/)
- Open GitHub issues

---

**Happy Agent Building! 🤖**
