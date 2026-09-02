"""Daily anomaly detection over product metrics.

The package is deliberately small and boring: load a metric time series,
fit a forecast, compare yesterday against its prediction interval, and if it
falls outside, explain which user segment moved.
"""

__version__ = "2.0.0"

__all__ = ["__version__"]
