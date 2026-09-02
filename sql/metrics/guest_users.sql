-- guest_users: daily volume, split by user segment.
SELECT
    DATE_TRUNC('day', guest_sessions.created_at) AS date_trunc,

    -- Gender:
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.gender = 'female') AS female_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.gender = 'male') AS male_guest_users,

    -- Registration platform:
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.platform = 'android') AS android_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.platform = 'ios') AS ios_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.platform = 'web') AS web_guest_users,

    -- Plan tier:
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.plan_tier = 'basic') AS basic_tier_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.plan_tier = 'premium') AS premium_tier_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.plan_tier = 'unspecified') AS unspecified_tier_guest_users,

    -- Market:
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.is_domestic = 1) AS domestic_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.is_domestic = 0) AS international_guest_users,

    -- Age bucket:
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.age_bucket = '<18') AS age_under_18_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.age_bucket = '18-24') AS age_18_24_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.age_bucket = '25-34') AS age_25_34_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.age_bucket = '35-44') AS age_35_44_guest_users,
    COUNT(DISTINCT guest_sessions.id) FILTER (WHERE users.age_bucket = '45+') AS age_45_plus_guest_users,
    COUNT(DISTINCT guest_sessions.id) AS total_guest_users
FROM guest_sessions
LEFT JOIN users ON users.id = guest_sessions.user_id
WHERE guest_sessions.created_at > NOW() - INTERVAL '2 years'
  AND guest_sessions.created_at < DATE_TRUNC('day', NOW())
GROUP BY 1
ORDER BY 1 DESC
