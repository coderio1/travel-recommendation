-- =============================================================================
-- Travel Recommendation System - Database Schema
-- =============================================================================
-- Target DBMS : PostgreSQL 13+
-- Description : Schema for storing users, destinations, activities, and
--               personalized travel recommendation requests / results.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: users
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users
(
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT,
    password_hash TEXT NOT NULL DEFAULT ''
);


-- -----------------------------------------------------------------------------
-- Table: destinations
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS destinations
(
    id      BIGSERIAL PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE,
    country TEXT,
    area    TEXT
);


-- -----------------------------------------------------------------------------
-- Table: activity_types
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_types
(
    id   BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);


-- -----------------------------------------------------------------------------
-- Table: destination_activities
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS destination_activities
(
    id               BIGSERIAL PRIMARY KEY,
    destination_id   BIGINT NOT NULL
        REFERENCES destinations (id) ON DELETE CASCADE,
    activity_type_id BIGINT NOT NULL
        REFERENCES activity_types (id),
    start_month      INT    NOT NULL CHECK (start_month  BETWEEN 1 AND 12),
    end_month        INT    NOT NULL CHECK (end_month    BETWEEN 1 AND 12),
    price_level      INT             CHECK (price_level  BETWEEN 1 AND 3),
    quiet_level      INT             CHECK (quiet_level  BETWEEN 1 AND 3),
    luxury_level     INT             CHECK (luxury_level BETWEEN 1 AND 3),

    UNIQUE (destination_id, activity_type_id)
);


-- -----------------------------------------------------------------------------
-- Table: recommendation_requests
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendation_requests
(
    id                    BIGSERIAL PRIMARY KEY,
    user_id               BIGINT NOT NULL
        REFERENCES users (id) ON DELETE CASCADE,
    wanted_destination_id BIGINT
        REFERENCES destinations (id),
    wanted_country        TEXT,
    wanted_area           TEXT,
    activity_type_id      BIGINT
        REFERENCES activity_types (id),
    vacation_start_month  INT         CHECK (vacation_start_month BETWEEN 1 AND 12),
    vacation_end_month    INT         CHECK (vacation_end_month   BETWEEN 1 AND 12),
    preference            TEXT        CHECK (preference IN ('cheap', 'quiet', 'luxury')),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- -----------------------------------------------------------------------------
-- Table: recommendation_results
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendation_results
(
    id                        BIGSERIAL PRIMARY KEY,
    recommendation_request_id BIGINT NOT NULL
        REFERENCES recommendation_requests (id) ON DELETE CASCADE,
    destination_activity_id   BIGINT NOT NULL
        REFERENCES destination_activities (id) ON DELETE CASCADE,
    recommended_start_month   INT           CHECK (recommended_start_month BETWEEN 1 AND 12),
    recommended_end_month     INT           CHECK (recommended_end_month   BETWEEN 1 AND 12),
    match_score               NUMERIC(5, 2),
    rank_position             INT,
    reason                    TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (recommendation_request_id, destination_activity_id)
);


-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dest_activities_destination ON destination_activities (destination_id);
CREATE INDEX IF NOT EXISTS idx_dest_activities_activity    ON destination_activities (activity_type_id);

CREATE INDEX IF NOT EXISTS idx_rec_requests_user           ON recommendation_requests (user_id);
CREATE INDEX IF NOT EXISTS idx_rec_requests_activity       ON recommendation_requests (activity_type_id);
CREATE INDEX IF NOT EXISTS idx_rec_requests_destination    ON recommendation_requests (wanted_destination_id);

CREATE INDEX IF NOT EXISTS idx_rec_results_request         ON recommendation_results (recommendation_request_id);
CREATE INDEX IF NOT EXISTS idx_rec_results_dest_activity   ON recommendation_results (destination_activity_id);
