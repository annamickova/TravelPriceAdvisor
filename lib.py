import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Optional, Tuple


def get_market_position_plot(df_filtered: pd.DataFrame, transport_type: str) -> Optional[go.Figure]:
    """
    Generates a horizontal bar chart comparing Min, Avg, and Max prices.
    Professional styling with Plotly Dark template.
    """
    if df_filtered.empty:
        return None

    try:
        stats = {
            'Min Price': float(df_filtered["price"].min()),
            'Avg Price': float(df_filtered["price"].mean()),
            'Max Price': float(df_filtered["price"].max())
        }

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=list(stats.keys()),
            x=list(stats.values()),
            orientation='h',
            marker=dict(
                color=['#22c55e', '#2563eb', '#ef4444'],
                line=dict(color='rgba(255, 255, 255, 0.1)', width=1)
            ),
            text=[f"{v:,.0f} CZK" for v in stats.values()],
            textposition='auto',
        ))

        fig.update_layout(
            title=dict(text=f"Market Benchmarks: {transport_type}", font=dict(size=18)),
            template="plotly_dark",
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor='#333'),
            yaxis=dict(autorange="reversed")
        )
        return fig
    except Exception:
        return None


def get_price_trend_plot(df_filtered: pd.DataFrame, days_to_go: int) -> Optional[go.Figure]:
    """
    Computes rolling averages and generates a time-series scatter plot
    for price trends leading up to departure.
    """
    if len(df_filtered) < 3:
        return None

    # Aggregate data by days remaining
    trend = df_filtered.groupby("days_until_departure")["price"].mean().reset_index()
    trend = trend.sort_values("days_until_departure", ascending=False)

    fig = go.Figure()

    # Main Trend Line
    fig.add_scatter(
        x=trend["days_until_departure"],
        y=trend["price"],
        mode='lines+markers',
        line=dict(color='#2563eb', width=3, shape='spline'),  # Spline makes it curvy/pro
        marker=dict(size=6, color='#60a5fa'),
        name="Market Average"
    )

    # User Selection Indicator
    fig.add_vline(
        x=days_to_go,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text="Your Booking Window",
        annotation_position="top left"
    )

    fig.update_layout(
        xaxis_title="Days Remaining Before Trip",
        yaxis_title="Price (CZK)",
        xaxis_autorange="reversed",
        template="plotly_dark",
        height=400,
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def process_raw_data(planes_path: str, ground_path: str) -> pd.DataFrame:
    """
    Pipeline to ingest, clean, and unify multi-source transport data.
    Handles city-to-IATA mapping and data type normalization.
    """
    city_map = {
        "London": "STN", "Barcelona": "BCN", "Rome": "CIA",
        "Paris": "BVA", "Madrid": "MAD", "Amsterdam": "EIN",
        "Vienna": "VIE", "Budapest": "BUD", "Bratislava": "BTS", "Munich": "MXP"
    }

    try:
        df_p = pd.read_csv(planes_path)
        df_p["transport_type"] = "PLANE"

        df_g = pd.read_csv(ground_path)
        df_g["destination"] = df_g["destination"].replace(city_map)

        if "transport_type" not in df_g.columns:
            df_g["transport_type"] = "BUS"

        combined = pd.concat([df_p, df_g], ignore_index=True)

        # Vectorized cleaning
        combined["destination"] = combined["destination"].str.strip().str.upper()
        combined["transport_type"] = combined["transport_type"].str.strip().str.upper()
        combined["departure_date"] = pd.to_datetime(combined["departure_date"])

        return combined
    except Exception as e:
        print(f"Data Pipeline Error: {e}")
        return pd.DataFrame()


def get_route_advice(advice_data: dict, dest_code: str) -> dict:
    """
    Safely retrieves advice metrics for a specific destination.
    Returns default values if the destination is not found.
    """
    return advice_data.get(dest_code.upper(), {
        "best_days_before": "21-30",
        "avg_price_czk": "N/A",
        "holiday_premium_pct": "0"
    })