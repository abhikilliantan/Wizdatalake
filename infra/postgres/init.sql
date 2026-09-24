-- Create metadata catalog / application state schema
-- Runs automatically on first PostgreSQL container boot.

CREATE TABLE IF NOT EXISTS ingestion_events (
    id              BIGSERIAL PRIMARY KEY,
    object_key      TEXT        NOT NULL,
    source          TEXT        NOT NULL,
    event_type      TEXT        NOT NULL,
    object_id       TEXT,
    content_type    TEXT,
    byte_size       BIGINT,
    tags            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    status          TEXT        NOT NULL DEFAULT 'stored',
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_events_source
    ON ingestion_events (source);

CREATE INDEX IF NOT EXISTS idx_ingestion_events_created_at
    ON ingestion_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_events_object_key
    ON ingestion_events (object_key);

CREATE TABLE IF NOT EXISTS stream_checkpoints (
    consumer_group  TEXT        NOT NULL,
    topic           TEXT        NOT NULL,
    partition_id    INT         NOT NULL,
    offset_value    BIGINT      NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (consumer_group, topic, partition_id)
);
