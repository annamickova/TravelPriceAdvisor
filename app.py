import streamlit as st
import pandas as pd
import joblib
import json
from datetime import date, timedelta
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Travel Price Advisor", layout="wide")

# ---------- STYLE ----------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* GLOBAL */

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: white;
}

/* MAIN APP BACKGROUND */

.stApp {
    background-color: #0f0f0f;
}

/* HERO */

.hero-container{
background-image:url("https://images.unsplash.com/photo-1501785888041-af3ef285b470");
background-size:cover;
background-position:center;
padding:120px 60px;
border-radius:20px;
margin-bottom:40px;
}

.hero-overlay{
background:rgba(0,0,0,0.65);
padding:60px;
border-radius:20px;
}

.hero-title{
font-size:48px;
font-weight:700;
color:white;
}

.hero-sub{
color:#d1d5db;
font-size:18px;
margin-top:10px;
}

/* INPUT PANEL */

.input-card{
background:#1a1a1a;
border-radius:16px;
box-shadow:0 10px 30px rgba(0,0,0,0.5);
margin-bottom:30px;
}

.block-container{
    padding-top:1rem;
}

/* RESULT CARD */

.result-card{
background:#1a1a1a;
padding:30px;
border-radius:18px;
box-shadow:0 20px 40px rgba(0,0,0,0.6);
margin-top:20px;
}

/* ALT CARDS */

.alt-card{
background:#1a1a1a;
padding:16px;
border-radius:12px;
margin-bottom:10px;
box-shadow:0 4px 15px rgba(0,0,0,0.5);
}

/* INPUTS */

div[data-baseweb="select"]{
background:#222 !important;
color:white !important;
}

input{
background:#222 !important;
color:white !important;
}

/* DATE PICKER */

.stDateInput input{
background:#222 !important;
color:white !important;
}

/* BUTTON */

.stButton>button{
background:#2563eb;
color:white;
border:none;
border-radius:10px;
padding:10px 25px;
font-weight:500;
}

.stButton>button:hover{
background:#1d4ed8;
}

/* METRICS */

[data-testid="metric-container"]{
background:#1a1a1a;
border-radius:12px;
padding:10px;
}

/* REMOVE WHITE BLOCKS */

section.main > div{
background-color: transparent;
}

/* CHART BACKGROUND */

.js-plotly-plot{
background-color:transparent !important;
}

</style>
""", unsafe_allow_html=True)

# ---------- DATA ----------

@st.cache_data
def load_dataset():
    try:
        df = pd.read_csv("data/letenky.csv")
        df["departure_date"] = pd.to_datetime(df["departure_date"])
        return df
    except:
        return pd.DataFrame()

df_data = load_dataset()

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
        with open("model/advice.json", "r") as f:
            return json.load(f)
    except:
        return {}

advice = load_advice()

# ---------- CONSTANTS ----------

NUMERIC_COLS = [
    "days_until_departure","day_of_week","month","departure_hour",
    "duration_min","transfers","temp_max","temp_min",
    "precipitation_mm","wind_max_kmh","is_holiday"
]

PLANE_DESTINATIONS = {"STN":"London","BCN":"Barcelona","CIA":"Rome","BVA":"Paris","MAD":"Madrid"}

CZECH_HOLIDAYS = {"01-01","05-01","05-08","07-05","07-06","09-28","10-28","11-17","12-24","12-25","12-26"}

# ---------- UTILS ----------

def is_holiday_flag(d):
    return 1 if d.strftime("%m-%d") in CZECH_HOLIDAYS else 0

def build_input(destination, departure_date, transport_type):

    days_until = max(0,(departure_date-date.today()).days)

    df = pd.DataFrame({
        "days_until_departure":[days_until],
        "day_of_week":[departure_date.weekday()],
        "month":[departure_date.month],
        "departure_hour":[12],
        "duration_min":[150],
        "transfers":[0],
        "temp_max":[15],
        "temp_min":[10],
        "precipitation_mm":[0],
        "wind_max_kmh":[15],
        "is_holiday":[is_holiday_flag(departure_date)],
        "destination":[destination],
        "carrier":["Ryanair"],
        "transport_type":[transport_type],
        "days_category":["medium_term"]
    })

    df = pd.get_dummies(df)

    for col in feature_columns:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_columns]
    df[NUMERIC_COLS] = scaler.transform(df[NUMERIC_COLS])

    return df


def predict(df_input: pd.DataFrame):
    pred = model.predict(df_input)[0]
    proba = model.predict_proba(df_input)[0]

    confidence = max(proba)
    label = le.inverse_transform([int(pred)])[0]

    return label, confidence

def confidence_level(conf):
    if conf > 0.7:
        return "High"
    elif conf > 0.5:
        return "Moderate"
    else:
        return "Low"

def generate_recommendation(label, days_until, best_days):

    reasons = []

    # booking window logic
    if best_days and days_until < best_days:
        recommendation = "BUY NOW"
        reasons.append("Optimal booking window has passed. Prices typically rise closer to departure.")

    elif label == "BUY_NOW":
        recommendation = "BUY NOW"
        reasons.append("Model predicts prices are likely to increase soon.")

    elif label == "WAIT":
        recommendation = "WAIT"
        reasons.append("Model predicts a chance of prices dropping.")

    else:
        recommendation = "BUY SOON"
        reasons.append("Prices appear elevated but may increase further.")

    return recommendation, reasons

# ---------- HERO ----------

st.markdown("""
<div class="hero-container">
<div class="hero-overlay">

<div class="hero-title">✈ Travel Price Advisor</div>
<div class="hero-sub">AI-powered transport price forecasting from Prague</div>

</div>
</div>
""", unsafe_allow_html=True)

# ---------- SEARCH PANEL ----------
st.markdown('<div class="input-card">', unsafe_allow_html=True)

col1,col2,col3,col4 = st.columns([1,1,1,1])

with col1:
    transport_type = st.selectbox("Transport",["PLANE"])

with col2:
    dest_display = st.selectbox("Destination",list(PLANE_DESTINATIONS.values()))
    destination = [k for k,v in PLANE_DESTINATIONS.items() if v==dest_display][0]

with col3:
    departure_date = st.date_input(
        "Date",
        value=date.today()+timedelta(days=30)
    )

with col4:
    run = st.button("Predict")

st.markdown('</div>', unsafe_allow_html=True)
# ---------- PREDICTION ----------

if run:

    with st.spinner("Analyzing travel market signals..."):

        df_inp = build_input(destination, departure_date, transport_type)

        label, conf = predict(df_inp)

    days_until = (departure_date - date.today()).days

    dest_advice = advice.get(destination, {})
    best_days = dest_advice.get("best_days_before")

    recommendation, reasons = generate_recommendation(label, days_until, best_days)

    conf_text = confidence_level(conf)

    st.markdown(f"""
    <div class="result-card">

    <h2>✈ Recommendation: {recommendation}</h2>

    <p>
    Departure in <b>{days_until}</b> days  
    Model confidence: <b>{conf_text}</b>
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.subheader("Why this recommendation?")

    for r in reasons:
        st.markdown(f"""
        <div class="alt-card">
        • {r}
        </div>
        """, unsafe_allow_html=True)
    # ---------- METRICS ----------

    dest_advice = advice.get(destination,{})

    col1,col2,col3 = st.columns(3)

    with col1:
        st.metric("Typical best booking time", f"{dest_advice.get('best_days_before', '?')} days before departure")
        with col2:
            st.metric("Average price", f"{dest_advice.get('avg_price_czk','?')} CZK")

    with col3:
        st.metric("Holiday premium", f"{dest_advice.get('holiday_premium_pct','?')} %")

    # ---------- HISTORICAL TREND ----------

    if not df_data.empty:

        df_dest = df_data[df_data["destination"]==destination]

        if len(df_dest)>5:

            trend = df_dest.groupby("days_until_departure")["price"].mean().reset_index()

            fig_trend = go.Figure()

            fig_trend.add_scatter(
                x=trend["days_until_departure"],
                y=trend["price"],
                mode="lines",
                line=dict(width=4)
            )

            fig_trend.add_vline(x=days_until)

            fig_trend.update_layout(
                title="Historical Market Price",
                xaxis_autorange="reversed"
            )

            st.plotly_chart(fig_trend, use_container_width=True)

    # alternative days

    st.subheader("Potentially better travel dates")

    for i in range(-3,4):

        alt_date = departure_date + timedelta(days=i)

        if alt_date < date.today():
            continue

        df_alt = build_input(destination,alt_date,transport_type)
        lbl, conf = predict(df_alt)

        st.markdown(f"""
        <div class="alt-card">

        <b>{alt_date.strftime('%d %b')}</b>  
        {lbl} • {conf}% confidence

        </div>
        """, unsafe_allow_html=True)