-- Database schema for production chat application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,  -- For multi-user support
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index on user_id for fast user queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for fast message queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- API keys table (for API access)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    rate_limit INTEGER DEFAULT 100,  -- Requests per hour
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- Usage tracking table (for cost and metrics)
CREATE TABLE IF NOT EXISTS usage_tracking (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost DECIMAL(10, 6),  -- Cost in USD
    latency_ms INTEGER,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for usage queries
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_conversation_id ON usage_tracking(conversation_id);

-- Partitioning for usage tracking (by month)
-- This helps with performance for large datasets
CREATE TABLE IF NOT EXISTS usage_tracking_2024_01 PARTITION OF usage_tracking
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS usage_tracking_2024_02 PARTITION OF usage_tracking
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Add more partitions as needed...

-- Feedback table (for model improvement)
CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id BIGINT REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_conversation_id ON feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_message_id ON feedback(message_id);

-- Rate limiting table (Redis fallback)
CREATE TABLE IF NOT EXISTS rate_limits (
    key VARCHAR(255) PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_expires_at ON rate_limits(expires_at);

-- Function to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for conversations
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete conversations older than 90 days with no activity
    DELETE FROM conversations
    WHERE updated_at < NOW() - INTERVAL '90 days';

    -- Delete expired rate limits
    DELETE FROM rate_limits
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- View for conversation analytics
CREATE OR REPLACE VIEW conversation_analytics AS
SELECT
    c.id as conversation_id,
    c.user_id,
    c.created_at,
    COUNT(m.id) as message_count,
    SUM(CASE WHEN m.role = 'user' THEN 1 ELSE 0 END) as user_messages,
    SUM(CASE WHEN m.role = 'assistant' THEN 1 ELSE 0 END) as assistant_messages,
    SUM(m.tokens_used) as total_tokens,
    MAX(m.created_at) as last_message_at
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.user_id, c.created_at;

-- View for usage analytics
CREATE OR REPLACE VIEW daily_usage_stats AS
SELECT
    DATE(created_at) as date,
    user_id,
    model,
    COUNT(*) as request_count,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(input_tokens + output_tokens) as total_tokens,
    SUM(cost) as total_cost,
    AVG(latency_ms) as avg_latency_ms,
    SUM(CASE WHEN cached THEN 1 ELSE 0 END) as cached_requests
FROM usage_tracking
GROUP BY DATE(created_at), user_id, model;

-- Materialized view for faster dashboard queries
CREATE MATERIALIZED VIEW IF NOT EXISTS user_monthly_usage AS
SELECT
    user_id,
    DATE_TRUNC('month', created_at) as month,
    model,
    COUNT(*) as request_count,
    SUM(input_tokens + output_tokens) as total_tokens,
    SUM(cost) as total_cost,
    AVG(latency_ms) as avg_latency_ms
FROM usage_tracking
GROUP BY user_id, DATE_TRUNC('month', created_at), model;

-- Index on materialized view
CREATE INDEX IF NOT EXISTS idx_user_monthly_usage_user_month
    ON user_monthly_usage(user_id, month);

-- Refresh materialized view (run periodically)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY user_monthly_usage;
