-- Content feedback table for RAG improvement loop
-- Stores user ratings on generated content so future generations improve

CREATE TABLE content_feedback (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content_type TEXT NOT NULL,
    platform TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    rating TEXT NOT NULL CHECK (rating IN ('positive', 'negative')),
    feedback_note TEXT,
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_feedback_rating ON content_feedback(rating);
CREATE INDEX idx_content_feedback_type ON content_feedback(content_type, platform);
CREATE INDEX idx_content_feedback_created ON content_feedback(created_at DESC);
CREATE INDEX idx_content_feedback_embedding ON content_feedback
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- RPC for feedback similarity search
CREATE OR REPLACE FUNCTION match_feedback(
    query_embedding VECTOR(1024),
    match_threshold FLOAT DEFAULT 0.3,
    match_count INT DEFAULT 5,
    filter_rating TEXT DEFAULT NULL,
    filter_content_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content_type TEXT,
    platform TEXT,
    user_message TEXT,
    assistant_message TEXT,
    rating TEXT,
    feedback_note TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        cf.id,
        cf.content_type,
        cf.platform,
        cf.user_message,
        cf.assistant_message,
        cf.rating,
        cf.feedback_note,
        1 - (cf.embedding <=> query_embedding) AS similarity
    FROM content_feedback cf
    WHERE
        cf.embedding IS NOT NULL
        AND 1 - (cf.embedding <=> query_embedding) > match_threshold
        AND (filter_rating IS NULL OR cf.rating = filter_rating)
        AND (filter_content_type IS NULL OR cf.content_type = filter_content_type)
    ORDER BY cf.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
