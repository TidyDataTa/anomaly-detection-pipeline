-- Result tables written by the pipeline. Both are read by the BI layer.

-- One row per metric per run: the observed value and the band it was
-- expected to fall into.
CREATE TABLE IF NOT EXISTS analytics.total_anomaly (
    calendar_date date,
    metric_name   text,
    metric_value  float,
    is_lower      int,     -- 1 = below the expected band
    is_upper      int,     -- 1 = above the expected band
    is_anomaly    int,     -- max(is_lower, is_upper)
    lower_bound   float,
    upper_bound   float,
    load_date     date
);

-- Segment breakdown, written only for metrics that were flagged: how each
-- segment moved against its own 30-day baseline.
CREATE TABLE IF NOT EXISTS analytics.segment_anomaly (
    calendar_date   date,
    metric_name     text,
    segment         text,
    segment_value   float,
    mean_last_month float,
    diff_percentage float,
    load_date       date
);
