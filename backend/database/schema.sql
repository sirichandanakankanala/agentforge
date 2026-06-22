-- AgentForge Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    goal TEXT NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    output_type VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    memory_config TEXT NOT NULL, -- JSON string
    validation_result TEXT, -- JSON string
    tools_needed TEXT, -- JSON string
    tool_configurations TEXT, -- JSON string
    mode VARCHAR(50),
    original_request TEXT,
    created_at VARCHAR(100) NOT NULL,
    updated_at VARCHAR(100) NOT NULL
);

-- Workflows table (agent steps)
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- SQLite fallback autoincrement
    agent_id VARCHAR(255) REFERENCES agents(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    tool VARCHAR(100) NOT NULL
);

-- Execution logs table
CREATE TABLE IF NOT EXISTS execution_logs (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) REFERENCES agents(id) ON DELETE CASCADE,
    run_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at VARCHAR(100) NOT NULL,
    completed_at VARCHAR(100) NOT NULL,
    used_tools TEXT NOT NULL, -- JSON string
    tool_results TEXT NOT NULL, -- JSON string
    evaluation TEXT NOT NULL, -- JSON string
    evolution TEXT NOT NULL, -- JSON string
    output TEXT NOT NULL, -- JSON string
    logs TEXT NOT NULL, -- JSON string
    created_at VARCHAR(100) NOT NULL
);

-- Memory table
CREATE TABLE IF NOT EXISTS memory (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) REFERENCES agents(id) ON DELETE CASCADE,
    memory_key VARCHAR(255) NOT NULL,
    memory_value TEXT NOT NULL,
    embedding TEXT, -- Stores array of floats as string for SQLite compatibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
