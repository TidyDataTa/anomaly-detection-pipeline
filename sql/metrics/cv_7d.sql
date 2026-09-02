-- cv_7d: share of registrations that activate within 7 days, by segment.
SELECT
    DATE_TRUNC('day', users.created_at) AS date_trunc,

    -- Gender:
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.gender = 'female'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.gender = 'female'), 0) AS female_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.gender = 'male'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.gender = 'male'), 0) AS male_cv_7d,

    -- Registration platform:
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.platform = 'android'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'android'), 0) AS android_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.platform = 'ios'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'ios'), 0) AS ios_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.platform = 'web'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.platform = 'web'), 0) AS web_cv_7d,

    -- Plan tier:
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.plan_tier = 'basic'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'basic'), 0) AS basic_tier_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.plan_tier = 'premium'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'premium'), 0) AS premium_tier_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.plan_tier = 'unspecified'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.plan_tier = 'unspecified'), 0) AS unspecified_tier_cv_7d,

    -- Market:
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.is_domestic = 1
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.is_domestic = 1), 0) AS domestic_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.is_domestic = 0
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.is_domestic = 0), 0) AS international_cv_7d,

    -- Age bucket:
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.age_bucket = '<18'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '<18'), 0) AS age_under_18_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.age_bucket = '18-24'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '18-24'), 0) AS age_18_24_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.age_bucket = '25-34'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '25-34'), 0) AS age_25_34_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.age_bucket = '35-44'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '35-44'), 0) AS age_35_44_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
                 AND users.age_bucket = '45+'
    )::numeric
        / NULLIF(COUNT(DISTINCT users.id) FILTER (WHERE users.age_bucket = '45+'), 0) AS age_45_plus_cv_7d,
    COUNT(DISTINCT users.id) FILTER (
        WHERE users.state = 'activated'
                 AND (users.activated_at::date - users.created_at::date <= 7
                      OR users.activated_at IS NULL)
    )::numeric / NULLIF(COUNT(DISTINCT users.id), 0) AS total_cv_7d
FROM users
WHERE users.created_at > NOW() - INTERVAL '2 years'
  AND users.created_at < DATE_TRUNC('day', NOW()) - INTERVAL '7 day'
GROUP BY 1
ORDER BY 1 DESC
