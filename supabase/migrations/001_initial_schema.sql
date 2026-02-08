-- YSS Brand Content Copywriter - Initial Database Schema
-- Run this migration in Supabase SQL Editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: platforms
-- ============================================================
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

INSERT INTO platforms (name, display_name) VALUES
    ('instagram', 'Instagram'),
    ('tiktok', 'TikTok'),
    ('youtube', 'YouTube');

-- ============================================================
-- TABLE: content_types
-- ============================================================
CREATE TABLE content_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT
);

INSERT INTO content_types (name, display_name, description) VALUES
    ('caption', 'Caption', 'Single post caption for Instagram/TikTok/YouTube'),
    ('carousel', 'Carousel Post', 'Multi-slide carousel copy (title + body per slide)'),
    ('edm', 'EDM Copy', 'Email/direct message marketing copy'),
    ('reel_script', 'Reel Script', 'Short-form video script with hooks and CTAs');

-- ============================================================
-- TABLE: scraped_content
-- Raw scraped viral content from social platforms
-- ============================================================
CREATE TABLE scraped_content (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    source_url TEXT,
    source_handle TEXT,
    content_text TEXT,
    content_type TEXT,
    media_urls TEXT[],

    -- Engagement metrics
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    saves_count INTEGER DEFAULT 0,

    -- Metadata
    hashtags TEXT[],
    mentions TEXT[],
    posted_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),

    -- Scraping metadata
    scrape_job_id TEXT,
    raw_data JSONB,

    -- Embedding for RAG (Voyage AI voyage-3.5 = 1024 dims)
    embedding VECTOR(1024),

    -- Computed virality score
    virality_score FLOAT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scraped_content_platform ON scraped_content(platform_id);
CREATE INDEX idx_scraped_content_virality ON scraped_content(virality_score DESC);
CREATE INDEX idx_scraped_content_posted ON scraped_content(posted_at DESC);
CREATE INDEX idx_scraped_content_embedding ON scraped_content
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ============================================================
-- TABLE: brand_voice_profiles
-- ============================================================
CREATE TABLE brand_voice_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    brand_name TEXT NOT NULL,
    brand_handle TEXT,

    -- Voice characteristics
    tone_attributes JSONB,
    vocabulary_patterns JSONB,
    sentence_structure JSONB,
    emoji_usage JSONB,
    hashtag_strategy JSONB,
    cta_patterns JSONB,

    -- Full analysis
    analysis_text TEXT,
    analysis_embedding VECTOR(1024),

    -- Source data
    source_posts_count INTEGER,
    source_urls TEXT[],

    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLE: chat_sessions
-- ============================================================
CREATE TABLE chat_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT,
    content_type_id INTEGER REFERENCES content_types(id),
    platform_id INTEGER REFERENCES platforms(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLE: chat_messages
-- ============================================================
CREATE TABLE chat_messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model_used TEXT,
    tokens_used INTEGER,
    rag_context_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);

-- ============================================================
-- TABLE: generated_content
-- ============================================================
CREATE TABLE generated_content (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content_type_id INTEGER REFERENCES content_types(id),
    platform_id INTEGER REFERENCES platforms(id),
    chat_session_id UUID REFERENCES chat_sessions(id),

    title TEXT,
    body TEXT NOT NULL,
    slides JSONB,
    hashtags TEXT[],
    cta TEXT,
    hook TEXT,

    -- Generation metadata
    prompt_used TEXT,
    system_prompt_version TEXT,
    model_used TEXT,
    rag_sources UUID[],

    -- User feedback
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback TEXT,
    is_favorite BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLE: scrape_jobs
-- ============================================================
CREATE TABLE scrape_jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id),
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),

    search_terms TEXT[],
    target_handles TEXT[],
    max_results INTEGER DEFAULT 100,

    results_count INTEGER DEFAULT 0,
    apify_run_id TEXT,
    error_message TEXT,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABLE: reports
-- ============================================================
CREATE TABLE reports (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    report_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    full_content TEXT,
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FUNCTION: match_content (vector similarity search)
-- ============================================================
CREATE OR REPLACE FUNCTION match_content(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    filter_platform_id INT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content_text TEXT,
    source_url TEXT,
    source_handle TEXT,
    platform_id INT,
    virality_score FLOAT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        sc.id,
        sc.content_text,
        sc.source_url,
        sc.source_handle,
        sc.platform_id,
        sc.virality_score,
        1 - (sc.embedding <=> query_embedding) AS similarity
    FROM scraped_content sc
    WHERE
        sc.embedding IS NOT NULL
        AND 1 - (sc.embedding <=> query_embedding) > match_threshold
        AND (filter_platform_id IS NULL OR sc.platform_id = filter_platform_id)
    ORDER BY sc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- TRIGGER: auto-update updated_at timestamps
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_scraped_content_updated_at
    BEFORE UPDATE ON scraped_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_brand_voice_updated_at
    BEFORE UPDATE ON brand_voice_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_generated_content_updated_at
    BEFORE UPDATE ON generated_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
