-- init_db.sql - MVP Version (sin pgvector)
-- Script de inicialización para PostgreSQL

-- Extension para UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Schema principal
CREATE SCHEMA IF NOT EXISTS agent_system;

-- Tabla de tareas
CREATE TABLE IF NOT EXISTS agent_system.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(50) UNIQUE NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    title TEXT NOT NULL,
    description TEXT,
    assigned_agent VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Índices para tasks
CREATE INDEX idx_tasks_status ON agent_system.tasks(status);
CREATE INDEX idx_tasks_type ON agent_system.tasks(task_type);
CREATE INDEX idx_tasks_created ON agent_system.tasks(created_at DESC);

-- Tabla de eventos outbox (Transactional Outbox Pattern)
CREATE TABLE IF NOT EXISTS agent_system.outbox_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT
);

-- Índices para outbox
CREATE INDEX idx_outbox_status ON agent_system.outbox_events(status);
CREATE INDEX idx_outbox_created ON agent_system.outbox_events(created_at);

-- Tabla de audit trail (inmutable)
CREATE TABLE IF NOT EXISTS agent_system.audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    snapshot JSONB
);

-- Índices para audit_trail
CREATE INDEX idx_audit_entity ON agent_system.audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_timestamp ON agent_system.audit_trail(timestamp DESC);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION agent_system.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para tasks
CREATE TRIGGER tasks_updated_at
    BEFORE UPDATE ON agent_system.tasks
    FOR EACH ROW
    EXECUTE FUNCTION agent_system.update_updated_at();

-- Usuario de solo lectura para métricas
CREATE USER metrics_reader WITH PASSWORD 'metrics_readonly_pass';
GRANT CONNECT ON DATABASE agent_db TO metrics_reader;
GRANT USAGE ON SCHEMA agent_system TO metrics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA agent_system TO metrics_reader;

-- Log de inicialización
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully at %', NOW();
END $$;
