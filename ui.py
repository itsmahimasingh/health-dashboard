"""Shared look: colours, cards, badges and charts, so every page matches."""
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

TEAL = "#3E9DA9"
TEAL_DARK = "#2F8793"
ORANGE = "#F4A340"
GREEN, YELLOW, RED = "#2E9E6B", "#D99A00", "#D9534F"

# One colour per risk level, used on every page
RISK_COLORS = {"Low": GREEN, "Moderate": YELLOW, "High": RED}

GLUCOSE_COLORS = {
    "Fasting": TEAL,
    "Before meal": "#7FC4CC",
    "After meal": ORANGE,
    "Random": "#9A8FD1",
}

CHART_HEIGHT = 280


# ---------- text ----------
def plural(n, word):
    """plural(1, "cup") -> "1 cup", plural(3, "cup") -> "3 cups"."""
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


# ---------- cards and badges ----------
def badge_html(text, color):
    return (
        "<span style='display:inline-block;margin-top:4px;padding:3px 12px;border-radius:99px;"
        f"background:{color}22;color:{color};font-weight:600;font-size:0.85rem'>{text}</span>"
    )


def card(label, value, badge, color, bar=None, note=None):
    """One white card: label, big value, coloured badge, an optional progress bar (0-100)
    and an optional short note explaining what the number means."""
    bar_html = ""
    if bar is not None:
        width = max(0, min(bar, 100))
        bar_html = (
            "<div style='height:8px;background:#E3F1F2;border-radius:99px;margin-top:12px'>"
            f"<div style='height:8px;width:{width}%;background:{color};border-radius:99px'></div></div>"
        )
    note_html = ""
    if note:
        note_html = (f"<div style='font-size:0.8rem;color:#6B8A91;margin-top:10px;line-height:1.35'>"
                     f"{note}</div>")
    return (
        "<div class='hd-card' style='background:white;border-radius:18px;padding:18px 22px;height:100%;"
        "margin-bottom:0.5rem;"
        "box-shadow:0 6px 20px rgba(62,157,169,0.15)'>"
        f"<div style='font-size:0.9rem;color:#5B7C84'>{label}</div>"
        f"<div class='hd-card-value' style='font-size:2rem;font-weight:600;color:#2C4A52;line-height:1.3'>"
        f"{value}</div>"
        f"{badge_html(badge, color)}{bar_html}{note_html}</div>"
    )


def show_card(label, value, badge, color, bar=None, where=st, note=None):
    where.markdown(card(label, value, badge, color, bar, note), unsafe_allow_html=True)


# ---------- charts ----------
def _past_days(df, col="day"):
    """Copy of df with col as a plain date, dropping anything after today."""
    out = df.copy()
    out[col] = pd.to_datetime(out[col]).dt.normalize()
    return out[out[col] <= pd.Timestamp(date.today())]


def _day_axis():
    # :O = one slot per day, so bars are proper bars and there are no hour ticks
    return alt.X(
        "yearmonthdate(day):O",
        title=None,
        axis=alt.Axis(format="%d %b", labelAngle=0, labelOverlap="parity"),
    )


def daily_bars(df, column, y_title, color=TEAL, goal=None):
    """Bar chart with one bar per day. goal draws a dashed target line."""
    data = _past_days(df)
    if data.empty:
        st.info("No data for this period yet.")
        return
    bars = (
        alt.Chart(data)
        .mark_bar(color=color, cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=_day_axis(),
            y=alt.Y(f"{column}:Q", title=y_title),
            tooltip=[alt.Tooltip("day:T", title="Date", format="%d %b %Y"),
                     alt.Tooltip(f"{column}:Q", title=y_title, format=",.1f")],
        )
    )
    chart = bars
    if goal is not None:
        rule = (
            alt.Chart(pd.DataFrame({"goal": [goal]}))
            .mark_rule(color=TEAL_DARK, strokeDash=[6, 4], size=1.5)
            .encode(y=alt.Y("goal:Q", title=y_title))
        )
        chart = bars + rule
    st.altair_chart(chart.properties(height=CHART_HEIGHT), width="stretch")
    if goal is not None:
        st.caption(f"Dashed line: goal of {goal:g}.")


def daily_line(df, column, y_title, color=TEAL_DARK):
    """Line chart with one point per day."""
    data = _past_days(df)
    if data.empty:
        st.info("No data for this period yet.")
        return
    chart = (
        alt.Chart(data)
        .mark_line(color=color, point=alt.OverlayMarkDef(color=color, size=40), strokeWidth=2.5)
        .encode(
            x=_day_axis(),
            y=alt.Y(f"{column}:Q", title=y_title),
            tooltip=[alt.Tooltip("day:T", title="Date", format="%d %b %Y"),
                     alt.Tooltip(f"{column}:Q", title=y_title, format=",.0f")],
        )
        .properties(height=CHART_HEIGHT)
    )
    st.altair_chart(chart, width="stretch")


def glucose_domain(values, pad=15):
    """y-axis range for glucose: start near 60, not 0, so changes are visible."""
    low = min(60, float(values.min()) - pad)
    high = max(180, float(values.max()) + pad)
    return [low, high]


def glucose_by_type(g):
    """Daily average per reading type, with a shaded normal fasting band (70-99 mg/dL)."""
    data = _past_days(g)
    data = data.groupby(["day", "context"], as_index=False)["value"].mean()
    contexts = [c for c in GLUCOSE_COLORS if c in set(data["context"])]

    domain = glucose_domain(data["value"])
    band = (
        alt.Chart(pd.DataFrame({"low": [70], "high": [99]}))
        .mark_rect(color=GREEN, opacity=0.10)
        # same y-scale as the lines, otherwise the band pulls the axis down to 0
        .encode(y=alt.Y("low:Q", title="Glucose (mg/dL)", scale=alt.Scale(domain=domain)), y2="high:Q")
    )
    lines = (
        alt.Chart(data)
        .mark_line(point=alt.OverlayMarkDef(size=35), strokeWidth=2.5)
        .encode(
            x=_day_axis(),
            y=alt.Y("value:Q", title="Glucose (mg/dL)",
                    scale=alt.Scale(domain=domain)),
            color=alt.Color(
                "context:N", title=None,
                scale=alt.Scale(domain=contexts, range=[GLUCOSE_COLORS[c] for c in contexts]),
                legend=alt.Legend(orient="bottom"),
            ),
            tooltip=[alt.Tooltip("day:T", title="Date", format="%d %b %Y"),
                     alt.Tooltip("context:N", title="Type"),
                     alt.Tooltip("value:Q", title="mg/dL", format=".0f")],
        )
    )
    st.altair_chart((band + lines).properties(height=320), width="stretch")
    st.caption("Shaded band: normal fasting range (70 to 99 mg/dL).")


def contribution_chart(contrib):
    """contrib: DataFrame with columns "input" and "effect" (positive = raises risk)."""
    data = contrib.assign(direction=["Raises risk" if v > 0 else "Lowers risk" for v in contrib["effect"]])
    limit = max(1.0, float(data["effect"].abs().max()) * 1.15)
    bars = (
        alt.Chart(data)
        .mark_bar(cornerRadius=4, height=26)
        .encode(
            y=alt.Y("input:N", title=None, sort=alt.SortField("effect", order="descending"),
                    axis=alt.Axis(labelLimit=220)),
            x=alt.X("effect:Q", title="← lowers risk      raises risk →",
                    scale=alt.Scale(domain=[-limit, limit])),
            color=alt.Color("direction:N", title=None,
                            scale=alt.Scale(domain=["Raises risk", "Lowers risk"], range=[RED, TEAL]),
                            legend=alt.Legend(orient="bottom")),
            tooltip=[alt.Tooltip("input:N", title="Input"),
                     alt.Tooltip("direction:N", title="Effect"),
                     alt.Tooltip("effect:Q", title="Strength", format="+.2f")],
        )
    )
    zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#5B7C84").encode(x="x:Q")
    st.altair_chart((bars + zero).properties(height=60 * len(data) + 40), width="stretch")


def glucose_trend(history, forecast):
    """history: day + value (daily averages). forecast: day + value (straight-line trend,
    including 7 days past the last reading). The future part of the trend is dashed."""
    last_day = history["day"].max()
    past = forecast[forecast["day"] <= last_day]
    future = forecast[forecast["day"] >= last_day]  # shares the last day, so the lines join

    x = alt.X("day:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0))
    y_scale = alt.Scale(domain=glucose_domain(pd.concat([history["value"], forecast["value"]])))

    actual = (
        alt.Chart(history.assign(series="Daily average"))
        .mark_line(point=alt.OverlayMarkDef(size=35), strokeWidth=2.5)
        .encode(x=x, y=alt.Y("value:Q", title="Glucose (mg/dL)", scale=y_scale),
                color=alt.Color("series:N", title=None,
                                scale=alt.Scale(domain=["Daily average", "Trend line"],
                                                range=[TEAL, ORANGE]),
                                legend=alt.Legend(orient="bottom")),
                tooltip=[alt.Tooltip("day:T", title="Date", format="%d %b %Y"),
                         alt.Tooltip("value:Q", title="Average mg/dL", format=".0f")])
    )
    trend_past = (
        alt.Chart(past.assign(series="Trend line"))
        .mark_line(strokeWidth=2)
        .encode(x=x, y=alt.Y("value:Q", title="Glucose (mg/dL)", scale=y_scale), color="series:N")
    )
    trend_future = (
        alt.Chart(future.assign(series="Trend line"))
        .mark_line(strokeWidth=2, strokeDash=[6, 4])
        .encode(x=x, y=alt.Y("value:Q", title="Glucose (mg/dL)", scale=y_scale), color="series:N",
                tooltip=[alt.Tooltip("day:T", title="Date", format="%d %b %Y"),
                         alt.Tooltip("value:Q", title="Trend mg/dL", format=".0f")])
    )
    st.altair_chart((actual + trend_past + trend_future).properties(height=320), width="stretch")
    st.caption("Dashed part: where the straight-line trend would go over the next 7 days.")
