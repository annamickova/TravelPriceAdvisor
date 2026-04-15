"""
Scraper weather from Open-Meteo
Source: open-meteo.com API (public, no key)

Run:
    pip install requests pandas
    python scraper_weather.py
"""
import requests
import pandas as pd
import schedule
import time
import os
from datetime import datetime, timedelta

OUTPUT_FILE = "data/pocasi.csv"

# Destination cities with their coordinates
# Matches the destinations in ryanair_scraper.py
DESTINATIONS = {
    "STN": {"city": "London", "lat": 51.5074, "lon": -0.1278},
    "BCN": {"city": "Barcelona", "lat": 41.3874, "lon":  2.1686},
    "CIA": {"city": "Rome", "lat": 41.9028, "lon": 12.4964},
    "BVA": {"city": "Paris", "lat": 48.8566, "lon":  2.3522},
    "EIN": {"city": "Eindhoven", "lat": 51.4416, "lon":  5.4697},
    "MAD": {"city": "Madrid", "lat": 40.4168, "lon": -3.7038},
    "PMI": {"city": "Mallorca", "lat": 39.6953, "lon":  3.0176},
    "AGP": {"city": "Malaga", "lat": 36.7213, "lon": -4.4214},
    "DUB": {"city": "Dublin", "lat": 53.3498, "lon": -6.2603},
    "ATH": {"city": "Athens", "lat": 37.9838, "lon": 23.7275},
    "LIS": {"city": "Lisbon", "lat": 38.7169, "lon": -9.1395},
    "OPO": {"city": "Porto", "lat": 41.1579, "lon": -8.6291},
    "VLC": {"city": "Valencia", "lat": 39.4699, "lon": -0.3763},
    "SVQ": {"city": "Seville", "lat": 37.3886, "lon": -5.9823},
    "ACE": {"city": "Lanzarote", "lat": 28.9635, "lon": -13.5477},
    "FCO": {"city": "Rome FCO", "lat": 41.8003, "lon": 12.2389},
    "MXP": {"city": "Milan", "lat": 45.4654, "lon":  9.1859},
    "NAP": {"city": "Naples", "lat": 40.8518, "lon": 14.2681},
    "BRI": {"city": "Bari", "lat": 41.1171, "lon": 16.8719},
    "TSF": {"city": "Venice", "lat": 45.4408, "lon": 12.3155},
}

# how many days ahead to fetch forecast for
DAYS_AHEAD = list(range(1, 121, 2))


def fetch_weather(iata_code, city_info, date):
    """
    Fetches weather forecast for a destination city on a given date.
    Uses Open-Meteo API — free, no API key required.
    """
    date_str = date.strftime("%Y-%m-%d")

    # Build URL manually to avoid requests encoding commas in daily parameter
    # Also removed forecast_days — cannot be used together with start_date/end_date
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={city_info['lat']}&longitude={city_info['lon']}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
        f"&timezone=Europe%2FPrague"
        f"&start_date={date_str}&end_date={date_str}"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  Weather error {iata_code} {date_str}: {e}")
        return None

    daily = data.get("daily", {})
    dates = daily.get("time", [])

    if not dates or dates[0] != date_str:
        return None

    record = {
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "destination": iata_code,
        "city": city_info["city"],
        "date": date_str,
        "temp_max": daily.get("temperature_2m_max",  [None])[0],
        "temp_min": daily.get("temperature_2m_min",  [None])[0],
        "precipitation_mm": daily.get("precipitation_sum",   [None])[0],
        "wind_max_kmh": daily.get("windspeed_10m_max",   [None])[0],
    }
    return record


def run_collection():
    print(f"Destinations: {len(DESTINATIONS)} | Dates: {len(DAYS_AHEAD)}")

    today = datetime.now()
    all_records = []

    for iata_code, city_info in DESTINATIONS.items():

        print(f"\n  {iata_code} — {city_info['city']}")

        for d in DAYS_AHEAD:

            date = today + timedelta(days=d)

            # Open-Meteo only forecasts 16 days ahead
            if d > 16:
                break

            record = fetch_weather(iata_code, city_info, date)

            if record:
                print(
                    f"    {date.strftime('%Y-%m-%d')}: "
                    f"{record['temp_min']}°C – {record['temp_max']}°C, "
                    f"rain {record['precipitation_mm']}mm"
                )
                all_records.append(record)

            time.sleep(0.2)

    if not all_records:
        print("No weather data collected")
        return

    os.makedirs("data", exist_ok=True)

    df = pd.DataFrame(all_records)

    if os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved: {len(df)} weather records")


if __name__ == "__main__":
    print("Weather scraper start (Open-Meteo)")
    print("No API key required\n")

    run_collection()

    # Refresh weather forecast once per day
    schedule.every(24).hours.do(run_collection)

    while True:
        schedule.run_pending()
        time.sleep(60)