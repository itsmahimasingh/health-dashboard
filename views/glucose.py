from datetime import date, time, timedelta

import pandas as pd
import streamlit as st

import analysis
import database as db
import ui

st.title(":material/show_chart: Glucose Trend")
st.caption("Log your readings and see the pattern. This shows trends only. It is not a medical prediction.")

# ---------- add a reading ----------
with st.form("glucose_form", clear_on_submit=False):
    c1, c2, c3, c4 = st.columns(4)
    day = c1.date_input("Date", date.today(), max_value=date.today())
    measured_at = c2.time_input("Time", time(8, 0), step=timedelta(minutes=15))
    context = c3.selectbox("When was it measured?", db.GLUCOSE_CONTEXTS,
                           help="Fasting: morning, before eating. Before meal: just before lunch or dinner. "
                                "After meal: about 2 hours after you start eating.")
    value = c4.number_input("Glucose (mg/dL)", 30, 600, 100,
                            help="The number on your glucose meter. Normal fasting is 70 to 99.")
    if st.form_submit_button("Save reading", icon=":material/save:", type="primary"):
        db.add_glucose(day, context, value, measured_at)
        st.success(f"Saved {value} mg/dL ({context.lower()}) for {day:%d %b}, {measured_at:%H:%M}.")

g = db.get_glucose(30)
if g.empty:
    st.info("No readings yet. Add your first one above. Tip: a reading before and about 2 hours after "
            "a meal lets the app spot glucose spikes.", icon=":material/info:")
    st.stop()

# ---------- headline numbers ----------
latest = g.iloc[-1]
week = g[g["day"] >= pd.Timestamp(date.today() - timedelta(days=6))]
m1, m2, m3 = st.columns(3)
m1.metric(f"Latest ({latest['context'].lower()})", f"{latest['value']:.0f} mg/dL")
m2.metric("Average (last 7 days)", f"{week['value'].mean():.0f} mg/dL" if not week.empty else "–")
m3.metric("Readings (last 30 days)", len(g))

# ---------- readings by type ----------
st.subheader("Readings by type")
ui.glucose_by_type(g)

# ---------- trend ----------
st.subheader("Trend and 7-day outlook")
daily = g.groupby("day", as_index=False)["value"].mean()
if len(daily) < 5:
    st.info("Log readings on at least 5 different days to see a trend line.")
else:
    slope, intercept, x = analysis.linear_trend(daily)
    future_x = list(range(0, int(x.max()) + 8))
    forecast = pd.DataFrame({
        "day": daily["day"].min() + pd.to_timedelta(future_x, unit="D"),
        "value": [slope * i + intercept for i in future_x],
    })
    ui.glucose_trend(daily, forecast)
    if abs(slope) < 0.3:
        st.write("Your average glucose looks **roughly steady**.")
    elif slope > 0:
        st.write(f"Your average glucose is **trending up** by about {slope:.1f} mg/dL per day.")
    else:
        st.write(f"Your average glucose is **trending down** by about {abs(slope):.1f} mg/dL per day.")
    st.caption(f"If this straight-line trend continued, the average a week after your last reading "
               f"would be around {slope * (x.max() + 7) + intercept:.0f} mg/dL. It is a simple estimate only.")

# ---------- spikes ----------
st.subheader("Glucose spikes")
st.caption("A spike is a quick rise between two readings on the same day. "
           "You need readings with times, for example before and after a meal.")

s1, s2 = st.columns(2)
threshold = s1.slider("Minimum rise to count as a spike (mg/dL)", 20, 60, 30, step=5)
window_minutes = s2.selectbox("Within", [60, 90, 120], index=2,
                              format_func=lambda m: f"{m} minutes")

timed = db.get_glucose_timed(30)
episodes = analysis.detect_spikes(timed, threshold, window_minutes)

untimed = len(g) - len(timed)
if untimed:
    st.caption(f"{ui.plural(untimed, 'older reading')} without a time "
               f"{'is' if untimed == 1 else 'are'} skipped here.")

if timed.empty:
    st.info("No readings with a time yet. Save a reading above to start finding spikes.")
elif not episodes:
    st.success("No spikes matching this rule in the last 30 days.", icon=":material/check_circle:")
else:
    days_with_spikes = len({e["day"] for e in episodes})
    k1, k2, k3 = st.columns(3)
    k1.metric("Spikes found", len(episodes))
    k2.metric("Days with a spike", days_with_spikes)
    k3.metric("Average rise", f"{sum(e['rise'] for e in episodes) / len(episodes):.0f} mg/dL")

    table = pd.DataFrame([{
        "Date": e["day"].strftime("%d %b"),
        "Rise began": e["start_time"],
        "Starting (mg/dL)": e["start_value"],
        "Peak time": e["peak_time"],
        "Peak (mg/dL)": e["peak_value"],
        "Rise (mg/dL)": e["rise"],
        "Minutes to peak": e["minutes"],
    } for e in reversed(episodes)])  # newest first
    st.dataframe(table, width="stretch", hide_index=True)

st.caption("This is a pattern-finding estimate, not a medical definition. "
           "Few readings can miss spikes.")

# ---------- what affects glucose ----------
st.subheader("What seems to affect your glucose?")
shown = False
totals = db.daily_totals(30)
if not totals.empty:
    m = daily.merge(totals, on="day")
    if len(m) >= 6:
        cut = m["carbs"].median()
        hi, lo = m[m["carbs"] > cut]["value"], m[m["carbs"] <= cut]["value"]
        if len(hi) and len(lo):
            a, b = st.columns(2)
            a.metric("Avg glucose on higher-carb days", f"{hi.mean():.0f} mg/dL")
            b.metric("Avg glucose on lower-carb days", f"{lo.mean():.0f} mg/dL")
            shown = True
act = db.get_activity(30)
if not act.empty:
    m = daily.merge(act[["day", "sleep_hours"]], on="day")
    short, ok = m[m["sleep_hours"] < 7]["value"], m[m["sleep_hours"] >= 7]["value"]
    if len(short) >= 2 and len(ok) >= 2:
        a, b = st.columns(2)
        a.metric("Avg glucose after under 7 h sleep", f"{short.mean():.0f} mg/dL")
        b.metric("Avg glucose after 7 h or more sleep", f"{ok.mean():.0f} mg/dL")
        shown = True
if shown:
    st.caption("These are patterns in your own data, not proof of cause.")
else:
    st.info("Log meals and sleep for a few days to see how they relate to your glucose.")

st.caption("Talk to your doctor if your readings are often outside the range they gave you, and seek "
           "medical help promptly if you feel unwell with very high or very low readings.")
