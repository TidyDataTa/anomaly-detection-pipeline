-- s2_retention_14d: share of a weekly cohort reaching a 2nd session
-- within 14 days of their first one. Weekly grain.
WITH cohort AS (
    SELECT
        users.id,
        users.first_session_at,
        MAX(sessions.session_number_for_user) FILTER (
            WHERE sessions.session_at < users.first_session_at + INTERVAL '14 days'
        ) AS sessions_in_window,
        MIN(users.gender)      AS gender,
        MIN(users.platform)    AS platform,
        MIN(users.plan_tier)   AS plan_tier,
        MIN(users.is_domestic) AS is_domestic,
        MIN(users.age_bucket)  AS age_bucket
    FROM sessions
    LEFT JOIN users ON users.id = sessions.user_id
    WHERE users.first_session_at BETWEEN NOW() - INTERVAL '2 year'
                                     AND DATE_TRUNC('week', NOW()) - INTERVAL '14 day'
    GROUP BY 1, 2
)
SELECT
    DATE_TRUNC('week', cohort.first_session_at) AS date_trunc,

    -- Gender:
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.gender = 'female')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.gender = 'female'), 0) AS female_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.gender = 'male')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.gender = 'male'), 0) AS male_s2_retention_14d,

    -- Registration platform:
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.platform = 'android')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.platform = 'android'), 0) AS android_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.platform = 'ios')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.platform = 'ios'), 0) AS ios_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.platform = 'web')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.platform = 'web'), 0) AS web_s2_retention_14d,

    -- Plan tier:
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.plan_tier = 'basic')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.plan_tier = 'basic'), 0) AS basic_tier_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.plan_tier = 'premium')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.plan_tier = 'premium'), 0) AS premium_tier_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.plan_tier = 'unspecified')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.plan_tier = 'unspecified'), 0) AS unspecified_tier_s2_retention_14d,

    -- Market:
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.is_domestic = 1)::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.is_domestic = 1), 0) AS domestic_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.is_domestic = 0)::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.is_domestic = 0), 0) AS international_s2_retention_14d,

    -- Age bucket:
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.age_bucket = '<18')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.age_bucket = '<18'), 0) AS age_under_18_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.age_bucket = '18-24')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.age_bucket = '18-24'), 0) AS age_18_24_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.age_bucket = '25-34')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.age_bucket = '25-34'), 0) AS age_25_34_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.age_bucket = '35-44')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.age_bucket = '35-44'), 0) AS age_35_44_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2 AND cohort.age_bucket = '45+')::float
        / NULLIF(COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.age_bucket = '45+'), 0) AS age_45_plus_s2_retention_14d,
    COUNT(DISTINCT cohort.id) FILTER (WHERE cohort.sessions_in_window >= 2)::float
        / NULLIF(COUNT(DISTINCT cohort.id), 0) AS total_s2_retention_14d
FROM cohort
GROUP BY 1
ORDER BY 1 DESC
