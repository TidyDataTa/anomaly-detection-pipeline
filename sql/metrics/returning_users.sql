-- returning_users: sessions booked by users who had been dormant
-- for more than 45 days, split by user segment.
WITH session_history AS (
    SELECT
        sessions.user_id,
        sessions.id AS session_id,
        MIN(sessions.session_at)              AS session_at,
        MIN(sessions.session_number_for_user) AS session_number_for_user,
        LAG(MIN(sessions.session_at)) OVER (
            PARTITION BY sessions.user_id ORDER BY MIN(sessions.session_at)
        ) AS previous_session_at,
        MIN(users.gender)      AS gender,
        MIN(users.platform)    AS platform,
        MIN(users.plan_tier)   AS plan_tier,
        MIN(users.is_domestic) AS is_domestic,
        MIN(users.age_bucket)  AS age_bucket
    FROM sessions
    LEFT JOIN users ON users.id = sessions.user_id
    WHERE sessions.user_id IS NOT NULL
    GROUP BY 1, 2
), attributed AS (
    SELECT
        CASE
            WHEN session_number_for_user = 1 THEN 'new'
            WHEN session_at > previous_session_at + INTERVAL '45 day' THEN 'returned'
            ELSE 'current'
        END AS attribution,
        *
    FROM session_history
)
SELECT
    DATE_TRUNC('day', attributed.session_at) AS date_trunc,

    -- Gender:
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.gender = 'female') AS female_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.gender = 'male') AS male_returning_users,

    -- Registration platform:
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.platform = 'android') AS android_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.platform = 'ios') AS ios_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.platform = 'web') AS web_returning_users,

    -- Plan tier:
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.plan_tier = 'basic') AS basic_tier_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.plan_tier = 'premium') AS premium_tier_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.plan_tier = 'unspecified') AS unspecified_tier_returning_users,

    -- Market:
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.is_domestic = 1) AS domestic_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.is_domestic = 0) AS international_returning_users,

    -- Age bucket:
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.age_bucket = '<18') AS age_under_18_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.age_bucket = '18-24') AS age_18_24_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.age_bucket = '25-34') AS age_25_34_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.age_bucket = '35-44') AS age_35_44_returning_users,
    COUNT(DISTINCT attributed.session_id) FILTER (WHERE attributed.age_bucket = '45+') AS age_45_plus_returning_users,
    COUNT(DISTINCT attributed.session_id) AS total_returning_users
FROM attributed
WHERE attributed.attribution = 'returned'
  AND attributed.session_at BETWEEN NOW() - INTERVAL '2 year'
                                AND DATE_TRUNC('day', NOW())
GROUP BY 1
ORDER BY 1 DESC
