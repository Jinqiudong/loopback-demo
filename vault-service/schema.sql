-- LoopBack Knowledge Vault — database schema
-- Run this once in Supabase SQL Editor (Project → SQL Editor → New query)
-- Order matters: vault_entries must exist before task_cards (foreign key).

-- Step 1: enable pgvector (required for vector(1536) columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: long-lived knowledge entries
CREATE TABLE IF NOT EXISTS vault_entries (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    question_canonical  TEXT        NOT NULL,
    embedding           vector(1536),            -- text-embedding-3-small output
    current_answer      TEXT,
    owner_id            TEXT,                    -- Slack user ID of resolver
    status              TEXT        NOT NULL DEFAULT 'unconfirmed'
                            CHECK (status IN ('verified', 'unconfirmed', 'outdated')),
    confidence_score    FLOAT       NOT NULL DEFAULT 0.0,
    usage_count         INT         NOT NULL DEFAULT 0,
    source_thread       TEXT,                    -- Slack thread URL where answer originated
    last_confirmed_at   TIMESTAMPTZ,
    -- Array of {answer, valid_from, valid_until, changed_by, reason} — never deleted
    version_history     JSONB       NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 3: short-lived task cards (one per Slack question)
CREATE TABLE IF NOT EXISTS task_cards (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id      TEXT        NOT NULL,      -- Slack user ID
    channel_id        TEXT        NOT NULL,
    thread_ts         TEXT        NOT NULL,
    question_raw      TEXT        NOT NULL,
    question_intent   TEXT,
    status            TEXT        NOT NULL DEFAULT 'draft'
                          CHECK (status IN (
                              'draft', 'ai_searching', 'human_working',
                              'pending_confirm', 'verified', 'unconfirmed', 'escalate'
                          )),
    resolver_id       TEXT,
    vault_entry_id    UUID        REFERENCES vault_entries(id),
    search_log        JSONB,
    confidence_signal TEXT        CHECK (confidence_signal IN ('signal_1', 'signal_2', 'signal_3')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 4: index for fast cosine similarity search
-- Note: ivfflat needs data to build well; fine to create now, improves with rows.
CREATE INDEX IF NOT EXISTS vault_entries_embedding_idx
    ON vault_entries USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Step 5: RPC function called by search_vault via supabase.rpc("match_vault_entries", ...)
-- Returns top-N entries ranked by cosine similarity to the query embedding.
CREATE OR REPLACE FUNCTION match_vault_entries(
    query_embedding float[],
    match_count     int DEFAULT 1
)
RETURNS TABLE (
    id                  uuid,
    question_canonical  text,
    current_answer      text,
    owner_id            text,
    status              text,
    confidence_score    float,
    usage_count         int,
    last_confirmed_at   timestamptz,
    source_thread       text,
    similarity          float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        question_canonical,
        current_answer,
        owner_id,
        status,
        confidence_score,
        usage_count,
        last_confirmed_at,
        source_thread,
        -- cast float[] → vector, then invert cosine distance to get similarity
        1 - (embedding <=> query_embedding::vector) AS similarity
    FROM vault_entries
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> query_embedding::vector
    LIMIT match_count;
$$;
