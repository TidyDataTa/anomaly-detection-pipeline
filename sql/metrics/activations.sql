-- activations: daily volume, split by user segment.
SELECT
    DATE_TRUNC('day', users.activated_at) AS date_trunc,

    -- Gender:
    COUNT(DISTINCT users.id) FILTER (WHERE users.gender = 'female') AS female_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.gender = 'male') AS male_activations,

    -- Registration platform:
    COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'android') AS android_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'ios') AS ios_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'web') AS web_activations,

    -- Plan tier:
    COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'basic') AS basic_tier_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'premium') AS premium_tier_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'unspecified') AS unspecified_tier_activations,

    -- Market:
    COUNT(DISTINCT users.id) FILTER (WHERE users.is_domestic = 1) AS domestic_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.is_domestic = 0) AS international_activations,

    -- Age bucket:
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '<18') AS age_under_18_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '18-24') AS age_18_24_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '25-34') AS age_25_34_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '35-44') AS age_35_44_activations,
    COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '45+') AS age_45_plus_activations,
    COUNT(DISTINCT users.id) AS total_activations
FROM users
WHERE users.activated_at > NOW() - INTERVAL '2 years'
  AND users.activated_at < DATE_TRUNC('day', NOW())
GROUP BY 1
ORDER BY 1 DESC
