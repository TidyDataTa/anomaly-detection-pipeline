-- lifetime_30d: average number of sessions a weekly cohort completes
-- within 30 days of its first session. Weekly grain.
WITH cohort AS (
    SELECT
        users.id,
        users.first_session_at,
        MAX(sessions.session_number_for_user) FILTER (
            WHERE sessions.session_at < users.first_session_at + INTERVAL '30 days'
        ) AS sessions_in_window,
        MIN(users.gender)      AS gender,
        MIN(users.platform)    AS platform,
        MIN(users.plan_tier)   AS plan_tier,
        MIN(users.is_domestic) AS is_domestic,
        MIN(users.age_bucket)  AS age_bucket
    FROM users
    LEFT JOIN sessions ON users.id = sessions.user_id
    WHERE users.first_session_at BETWEEN NOW() - INTERVAL '2 year'
                                     AND DATE_TRUNC('week', NOW()) - INTERVAL '30 day'
    GROUP BY 1, 2
)
SELECT
    DATE_TRUNC('week', cohort.first_session_at) AS date_trunc,

    -- Gender:
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.gender = 'female') AS female_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.gender = 'male') AS male_lifetime_30d,

    -- Registration platform:
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.platform = 'android') AS android_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.platform = 'ios') AS ios_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.platform = 'web') AS web_lifetime_30d,

    -- Plan tier:
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.plan_tier = 'basic') AS basic_tier_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.plan_tier = 'premium') AS premium_tier_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.plan_tier = 'unspecified') AS unspecified_tier_lifetime_30d,

    -- Market:
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.is_domestic = 1) AS domestic_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.is_domestic = 0) AS international_lifetime_30d,

    -- Age bucket:
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.age_bucket = '<18') AS age_under_18_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.age_bucket = '18-24') AS age_18_24_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.age_bucket = '25-34') AS age_25_34_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.age_bucket = '35-44') AS age_35_44_lifetime_30d,
    AVG(cohort.sessions_in_window) FILTER (WHERE cohort.age_bucket = '45+') AS age_45_plus_lifetime_30d,
    AVG(cohort.sessions_in_window) AS total_lifetime_30d
FROM cohort
GROUP BY 1
ORDER BY 1 DESC
