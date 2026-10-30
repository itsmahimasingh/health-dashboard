"""Data analysis helpers. No Streamlit code here, so these can be tested on their own."""
import pandas as pd


def detect_spikes(readings, threshold=30, window_minutes=120):
    """Find distinct glucose rises within each day.

    readings: DataFrame with a datetime column "ts" and a number column "value".
    A spike starts at a low point and counts once glucose rises by at least
    `threshold` mg/dL within `window_minutes`. We then follow it to its peak.
    It ends when glucose falls back by half the threshold, so the next rise
    can be counted as a new spike.

    Returns a list of dicts, one per spike.
    """
    if readings is None or readings.empty:
        return []

    df = readings.dropna(subset=["ts", "value"]).sort_values("ts")
    episodes = []

    for day, group in df.groupby(df["ts"].dt.date):
        points = list(zip(group["ts"], group["value"]))
        low_time, low_value = points[0]
        current = None  # the spike we are following, if any

        for t, v in points[1:]:
            if current is None:
                minutes = (t - low_time).total_seconds() / 60
                if minutes > window_minutes or v < low_value:
                    # New starting point: either lower, or the old one is too long ago
                    low_time, low_value = t, v
                elif v - low_value >= threshold:
                    current = {"day": day, "start": low_time, "start_value": low_value,
                               "peak": t, "peak_value": v}
            else:
                if v > current["peak_value"]:
                    current["peak"], current["peak_value"] = t, v
                elif v <= current["peak_value"] - threshold / 2:
                    episodes.append(_finish(current))
                    current = None
                    low_time, low_value = t, v

        if current is not None:
            episodes.append(_finish(current))

    return episodes


def _finish(spike):
    return {
        "day": spike["day"],
        "start_time": spike["start"].strftime("%H:%M"),
        "start_value": round(spike["start_value"]),
        "peak_time": spike["peak"].strftime("%H:%M"),
        "peak_value": round(spike["peak_value"]),
        "rise": round(spike["peak_value"] - spike["start_value"]),
        "minutes": round((spike["peak"] - spike["start"]).total_seconds() / 60),
    }


def linear_trend(daily):
    """Fit a straight line to daily averages.

    daily: DataFrame with columns "day" (datetime) and "value".
    Returns (slope per day, intercept, x values in days since the first day).
    """
    import numpy as np

    x = (daily["day"] - daily["day"].min()).dt.days.to_numpy()
    slope, intercept = np.polyfit(x, daily["value"].to_numpy(), 1)
    return slope, intercept, x
