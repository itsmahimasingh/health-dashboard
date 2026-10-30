"""Tests for glucose spike detection and the trend line in analysis.py."""
import pandas as pd
import pytest

import analysis


def readings(*pairs, day="2026-10-01"):
    """readings(("07:00", 95), ("08:00", 140)) -> DataFrame with ts and value."""
    return pd.DataFrame({
        "ts": pd.to_datetime([f"{day} {t}" for t, _ in pairs]),
        "value": [v for _, v in pairs],
    })


def test_no_readings_means_no_spikes():
    assert analysis.detect_spikes(pd.DataFrame({"ts": [], "value": []})) == []
    assert analysis.detect_spikes(None) == []


def test_single_reading_means_no_spikes():
    assert analysis.detect_spikes(readings(("08:00", 150))) == []


def test_simple_spike_is_found():
    spikes = analysis.detect_spikes(readings(("13:00", 100), ("14:30", 145)), threshold=30)
    assert len(spikes) == 1
    s = spikes[0]
    assert (s["start_time"], s["start_value"]) == ("13:00", 100)
    assert (s["peak_time"], s["peak_value"]) == ("14:30", 145)
    assert s["rise"] == 45
    assert s["minutes"] == 90


def test_small_rise_is_not_a_spike():
    assert analysis.detect_spikes(readings(("13:00", 100), ("14:00", 120)), threshold=30) == []


def test_rise_that_takes_too_long_is_not_a_spike():
    # +50 mg/dL, but over 3 hours with a 120-minute window
    data = readings(("07:00", 100), ("10:00", 150))
    assert analysis.detect_spikes(data, threshold=30, window_minutes=120) == []


def test_spike_follows_rise_to_its_true_peak():
    data = readings(("07:00", 95), ("08:00", 140), ("09:00", 160))
    spikes = analysis.detect_spikes(data, threshold=30)
    assert len(spikes) == 1
    assert spikes[0]["peak_value"] == 160
    assert spikes[0]["peak_time"] == "09:00"


def test_two_separate_spikes_in_one_day():
    data = readings(("07:00", 95), ("09:00", 160), ("11:00", 110),
                    ("12:30", 105), ("13:30", 150), ("18:00", 100))
    spikes = analysis.detect_spikes(data, threshold=30)
    assert [(s["start_time"], s["peak_time"]) for s in spikes] == [("07:00", "09:00"), ("12:30", "13:30")]


def test_spikes_do_not_cross_midnight():
    late = readings(("23:00", 100), day="2026-10-01")
    early = readings(("00:30", 150), day="2026-10-02")
    assert analysis.detect_spikes(pd.concat([late, early])) == []


def test_readings_out_of_order_are_sorted():
    data = readings(("14:30", 145), ("13:00", 100))
    assert len(analysis.detect_spikes(data, threshold=30)) == 1


def test_linear_trend_finds_slope():
    daily = pd.DataFrame({
        "day": pd.date_range("2026-10-01", periods=10),
        "value": [100 + 2 * i for i in range(10)],  # rises 2 mg/dL per day
    })
    slope, intercept, x = analysis.linear_trend(daily)
    assert slope == pytest.approx(2.0)
    assert intercept == pytest.approx(100.0)
    assert list(x) == list(range(10))
