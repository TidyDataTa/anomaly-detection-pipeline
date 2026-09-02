-- new_users: daily volume, split by user segment.
SELECT
    DATE_TRUNC('day', users.created_at) AS date_trunc,

    -- Gender:
    COUNT(DISTINCT users.id) FILTER (WHERE users.gender = 'female') AS female_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.gender = 'male') AS male_new_users,

    -- Registration platform:
    COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'android') AS android_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'ios') AS ios_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'web') AS web_new_users,

    -- Plan tier:
    COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'basic') AS basic_tier_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'premium') AS premium_tier_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'unspecified') AS unspecified_tier_new_users,

    -- Market:
    COUNT(DISTINCT users.id) FILTER (WHERE users.is_domestic = 1) AS domestic_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.is_domestic = 0) AS international_new_users,

    -- Age bucket:
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '<18') AS age_under_18_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '18-24') AS age_18_24_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '25-34') AS age_25_34_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '35-44') AS age_35_44_new_users,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '45+') AS age_45_plus_new_users,
    COUNT(DISTINCT users.id) AS total_new_users
FROM users
WHERE users.created_at > NOW() - INTERVAL '2 years'
  AND users.created_at < DATE_TRUNC('day', NOW())
GROUP BY 1
ORDER BY 1 DESC
