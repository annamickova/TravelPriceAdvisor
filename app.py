import streamlit as st
import pandas as pd
import joblib
import json
from datetime import date, timedelta
import plotly.graph_objects as go
import numpy as np
from lib import process_raw_data, get_market_position_plot, get_price_trend_plot, get_route_advice

st.set_page_config(page_title="Travel Price Advisor", layout="wide")

# style
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: white; }
.stApp { background-color: #0f0f0f; }
.hero-container{
    background-image:url("https://images.unsplash.com/photo-1501785888041-af3ef285b470");
    background-size:cover; background-position:center; padding:100px 60px; border-radius:20px; margin-bottom:40px;
}
.hero-overlay{ background:rgba(0,0,0,0.7); padding:40px; border-radius:20px; }
.hero-title{ font-size:48px; font-weight:700; color:white; }
.hero-sub{ color:#d1d5db; font-size:18px; margin-top:10px; }
.input-card{ background:#1a1a1a; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.5); margin-bottom:30px; padding: 25px; }
.result-card{ background:#1a1a1a; padding:30px; border-radius:18px; box-shadow:0 20px 40px rgba(0,0,0,0.6); margin-top:20px; border-left: 8px solid #2563eb; }
.alt-card{ background:#1a1a1a; padding:16px; border-radius:12px; margin-bottom:10px; border: 1px solid #333; }
.stButton>button{ background:#2563eb; color:white; border:none; border-radius:10px; padding:12px; font-weight:600; width: 100%; cursor: pointer; }
.stButton>button:hover{ background:#1d4ed8; }
</style>
""", unsafe_allow_html=True)


# data loading
@st.cache_data
def load_all_data():
    return process_raw_data("data/letenky.csv", "data/regiojet.csv")


df_data = load_all_data()


@st.cache_resource
def load_model():
    model = joblib.load("model/flight_price_model.pkl")
    scaler = joblib.load("model/scaler.pkl")
    feature_columns = joblib.load("model/feature_columns.pkl")
    le = joblib.load("model/label_encoder.pkl")
    return model, scaler, feature_columns, le


model, scaler, feature_columns, le = load_model()


@st.cache_data
def load_advice():
    try:
        with open("model/advice.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


advice = load_advice()

# destination mapping
# destinations available ONLY by plane
PLANE_ONLY = {
    "STN": "London", "BCN": "Barcelona", "CIA": "Rome",
    "BVA": "Paris / Brussels", "MAD": "Madrid", "EIN": "Amsterdam"
}

# destinations available by BUS, TRAIN, and potentially PLANE
GROUND_DESTINATIONS = {
    "VIE": "Vienna", "BUD": "Budapest", "BTS": "Bratislava", "MXP": "Munich"
}


def build_input(destination, departure_date, transport_type):
    days_until = max(0, (departure_date - date.today()).days)
    df = pd.DataFrame({
        "days_until_departure": [days_until],
        "day_of_week": [departure_date.weekday()],
        "month": [departure_date.month],
        "departure_hour": [12], "duration_min": [150 if transport_type == "PLANE" else 480],
        "transfers": [0], "temp_max": [15], "temp_min": [10], "precipitation_mm": [0], "wind_max_kmh": [15],
        "is_holiday": [1 if departure_date.strftime("%m-%d") in ["12-24", "01-01"] else 0],
        "destination": [destination], "carrier": ["Ryanair" if transport_type == "PLANE" else "RegioJet"],
        "transport_type": [transport_type], "days_category": ["medium_term"]
    })
    df = pd.get_dummies(df)
    for col in feature_columns:
        if col not in df.columns: df[col] = 0
    df = df[feature_columns]
    df[["days_until_departure", "day_of_week", "month", "departure_hour", "duration_min", "transfers", "temp_max",
        "temp_min", "precipitation_mm", "wind_max_kmh", "is_holiday"]] = scaler.transform(df[["days_until_departure",
                                                                                              "day_of_week", "month",
                                                                                              "departure_hour",
                                                                                              "duration_min",
                                                                                              "transfers", "temp_max",
                                                                                              "temp_min",
                                                                                              "precipitation_mm",
                                                                                              "wind_max_kmh",
                                                                                              "is_holiday"]])
    return df


# ui
st.markdown(
    '<div class="hero-container"><div class="hero-overlay"><div class="hero-title">✈ Travel Price Advisor</div><div class="hero-sub">Flight & transport price prediction system</div></div></div>',
    unsafe_allow_html=True)

st.markdown('<div class="input-card">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    t_type = st.selectbox("Transport Mode", ["PLANE", "BUS", "TRAIN"])

with c2:
    # logic: If BUS or TRAIN is selected, show only ground destinations.
    # if PLANE is selected, show everything
    if t_type in ["BUS", "TRAIN"]:
        available_options = GROUND_DESTINATIONS
    else:
        # for planes, combine both lists
        available_options = {**PLANE_ONLY, **GROUND_DESTINATIONS}

    dest_name = st.selectbox("Destination", list(available_options.values()))
    dest_code = [k for k, v in available_options.items() if v == dest_name][0]

with c3: dep_date = st.date_input("Date", value=date.today() + timedelta(days=21))
with c4:
    st.write("")
    run = st.button("Analyze Price")
st.markdown('</div>', unsafe_allow_html=True)

if run:
    # prediction
    df_inp = build_input(dest_code, dep_date, t_type)
    prediction = model.predict(df_inp)[0]
    label = le.inverse_transform([int(prediction)])[0]
    days_to_go = (dep_date - date.today()).days

    dest_advice = get_route_advice(advice, dest_code)

    # result
    color = "#22c55e" if label == "BUY_NOW" else "#eab308" if label == "WAIT" else "#ef4444"
    st.markdown(f'''
            <div class="result-card" style="border-left-color: {color};">
                <h1 style="color: {color}; margin:0;">{label.replace("_", " ")}</h1>
                <p>Route: <b>Prague → {dest_name}</b> | Method: <b>{t_type}</b></p>
            </div>
        ''', unsafe_allow_html=True)

    st.write("---")

    # filtration
    df_data["destination"] = df_data["destination"].str.strip().str.upper()
    df_data["transport_type"] = df_data["transport_type"].str.strip().str.upper()

    df_filtered = df_data[
        (df_data["destination"] == dest_code.upper()) &
        (df_data["transport_type"] == t_type.upper())
    ]

    col_left, col_right = st.columns(2)

    with col_left:
        st.write("###  Route Benchmarks")
        st.metric("Optimal Booking", f"{dest_advice.get('best_days_before', '?')} days before")
        st.metric("Historical Average", f"{dest_advice.get('avg_price_czk', '?')} CZK")
        st.metric("Holiday Surcharge", f"{dest_advice.get('holiday_premium_pct', '?')}%")

    with col_right:
        st.write("###  Market Positioning")
        if not df_filtered.empty:
            min_p = float(df_filtered["price"].min())
            max_p = float(df_filtered["price"].max())
            avg_p = float(df_filtered["price"].mean())

            fig_bench = go.Figure()
            fig_bench.add_trace(go.Bar(
                y=['Min Price', 'Avg Price', 'Max Price'],
                x=[min_p, avg_p, max_p],
                orientation='h',
                marker=dict(color=['#22c55e', '#2563eb', '#ef4444'], opacity=0.7)
            ))
            fig_bench.update_layout(
                title=f"Price Range (CZK)",
                template="plotly_dark", height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_bench, use_container_width=True)
        else:
            st.warning(f"No historical data for {dest_code} as {t_type}.")

    st.write("---")

    # graph
    st.write("###  Historical Price Trend")
    if len(df_filtered) > 3:
        trend = df_filtered.groupby("days_until_departure")["price"].mean().reset_index()
        fig_trend = go.Figure()
        fig_trend.add_scatter(
            x=trend["days_until_departure"],
            y=trend["price"],
            line=dict(color='#2563eb', width=3),
            name="Average Price"
        )
        fig_trend.add_vline(x=days_to_go, line_dash="dash", line_color="#ff4b4b", annotation_text="Your Selection")
        fig_trend.update_layout(
            xaxis_title="Days until Departure",
            yaxis_title="Price (CZK)",
            xaxis_autorange="reversed",
            template="plotly_dark",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Insufficient data points to show trend line for this selection.")

    st.write("---")

    st.write("###  Historical Price Trend")
    if len(df_filtered) > 3:
        trend = df_filtered.groupby("days_until_departure")["price"].mean().reset_index()
        fig_trend = go.Figure()
        fig_trend.add_scatter(x=trend["days_until_departure"], y=trend["price"],
                              line=dict(color='#2563eb', width=3), name="Average Price")

