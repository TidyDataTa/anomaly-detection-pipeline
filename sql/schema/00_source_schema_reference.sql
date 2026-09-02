-- ---------------------------------------------------------------------------
-- Reference schema (illustrative)
--
-- The production queries of this pipeline run against a proprietary warehouse
-- schema that is not part of this repository. The queries shipped here are
-- rewritten against the neutral, generic schema documented below, so that the
-- analytical logic stays readable and reproducible while no internal data
-- model, table name or business definition is disclosed.
--
-- Point the pipeline at your own warehouse by editing `sql/metrics/*.sql`:
-- every query only has to return a `date_trunc` column, one column per
-- segment named `<segment>_<metric>`, and a `total_<metric>` column.
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    id              bigint PRIMARY KEY,
    created_at      timestamp   NOT NULL,   -- registration (lead created)
    activated_at    timestamp,              -- completed onboarding / signed up
    state           text,                   -- 'lead' | 'activated' | ...
    platform        text,                   -- 'ios' | 'android' | 'web'
    gender          text,                   -- 'female' | 'male'
    plan_tier       text,                   -- 'basic' | 'premium' | 'unspecified'
    is_domestic     smallint,               -- 1 = home market, 0 = international
    age_bucket      text,                   -- '<18' | '18-24' | '25-34' | '35-44' | '45+'
    first_session_at timestamp              -- first delivered session
);

CREATE TABLE sessions (
    id                      bigint PRIMARY KEY,
    user_id                 bigint REFERENCES users (id),
    session_at              timestamp NOT NULL,
    session_number_for_user integer   NOT NULL  -- 1 = first session of this user
);

CREATE TABLE guest_sessions (
    id         bigint PRIMARY KEY,
    user_id    bigint REFERENCES users (id),
    created_at timestamp NOT NULL
);
