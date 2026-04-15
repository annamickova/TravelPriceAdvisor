"""
Scraper trains and buses - RegioJet public API
Same API that uses Regiojet.cz

Run:
    pip install requests pandas schedule
    python scraper_regiojet.py

Does not require API key
"""

import requests
import pandas as pd
import schedule
import time
import os
from datetime import datetime, timedelta
import random

OUTPUT_FILE = "data/regiojet.csv"

# RegioJet API base URL (public, used by their own website)
API_BASE = "https://brn-ybus-pubapi.sa.cz/restapi"

# routes: [from_city, to_city, from_location_id, to_location_id]
# location IDs from RegioJet's own location list
ROUTES = [
    # correct IDs verified via /restapi/consts/locations
    ("Prague", "London",     10202003, 10202049),
    ("Prague", "Paris",      10202003, 10202096),
    ("Prague", "Amsterdam",  10202003, 10202030),
    ("Prague", "Brussels",   10202003, 10202044),
    ("Prague", "Vienna",     10202003, 10202052),
    ("Prague", "Budapest",   10202003, 10202091),
    ("Prague", "Bratislava", 10202003, 10202001),
    ("Prague", "Munich",     10202003, 10202006),
]

# how many days ahead to check prices
DAYS_AHEAD = list(range(1, 91, 3))

INTERVAL_HOURS = 24

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json",
    "X-Lang":     "en",
    "X-Currency": "CZK",
}


def fetch_location_id(city_name: str) -> int | None:
    """
    Look up RegioJet location ID for a city name.
    Used to verify/update location IDs if they change.
    """
    url = f"{API_BASE}/locations"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()

        for country in data.get("countries", []):
            for city in country.get("cities", []):
                if city_name.lower() in city.get("name", "").lower():
                    return city.get("id")
    except Exception as e:
        print(f"  Location lookup error: {e}")

    return None


def fetch_connections(origin_name, dest_name, origin_id, dest_id, date):
    """
    Fetch available connections between two cities on a given date.
    Returns list of records with prices.
    """
    date_str = date.strftime("%Y-%m-%d")
    today = datetime.now()

    url = f"{API_BASE}/routes/search/simple"

    params = {
        "fromLocationId": origin_id,
        "toLocationId": dest_id,
        "fromLocationType": "CITY",
        "toLocationType": "CITY",
        "departureDate": date_str,
        "numberOfPassengers": 1,
        "tariffs": "REGULAR",
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)

        if r.status_code == 404:
            return []
        # protection from blocking - rate limiting
        if r.status_code in [403, 429]:
            print(f"Blocked – waiting...")
            # when blocked we wait 10 seconds
            time.sleep(10)
            return []

        r.raise_for_status()
        data = r.json()

    except Exception as e:
        print(f"  Error {origin_name}->{dest_name} {date_str}: {e}")
        return []

    records = []

    for route in data.get("routes", []):

        try:
            # price info
            price_from = route.get("priceFrom")
            if not price_from or price_from <= 0:
                continue

            # departure and arrival times
            departure = route.get("departureTime", "")
            arrival = route.get("arrivalTime", "")

            # transport type (BUS or TRAIN)
            vehicle_types = route.get("vehicleTypes", ["BUS"])
            transport_type = vehicle_types[0] if vehicle_types else "BUS"

            # travel duration in minutes
            duration_min = route.get("travelTime", 0)

            # number of transfers
            transfers = route.get("transfersCount", 0)

            # carrier
            carrier = route.get("notice", "RegioJet")

            record = {
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "origin": origin_name,
                "destination": dest_name,
                "departure_date": date_str,
                "departure_time": departure[:16] if departure else "",
                "arrival_time": arrival[:16] if arrival else "",
                "price": price_from,
                "transport_type": transport_type,
                "duration_min": duration_min,
                "transfers": transfers,
                "carrier": carrier,
                "days_until_departure": (date - today).days,
            }
            records.append(record)

        except Exception:
            continue

    return records


def run_collection():

    print(f"Routes: {len(ROUTES)} | Dates: {len(DAYS_AHEAD)}")

    today = datetime.now()
    all_records = []

    for origin_name, dest_name, origin_id, dest_id in ROUTES:

        print(f"\nRoute: {origin_name} -> {dest_name}")

        for d in DAYS_AHEAD:

            date = today + timedelta(days=d)
            records = fetch_connections(
                origin_name, dest_name,
                origin_id, dest_id,
                date
            )

            if records:
                cheapest = min(r["price"] for r in records)
                print(
                    f"    {date.strftime('%Y-%m-%d')} "
                    f"(in {d}d): {len(records)} connections, "
                    f"from {cheapest:.0f} CZK"
                )

            all_records.extend(records)
            time.sleep(random.uniform(0.5, 1.5))

    if not all_records:
        print("No data collected")
        return

    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(all_records)

    if os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved: {len(df)} records")


if __name__ == "__main__":

    print("RegioJet scraper (bus + train)")
    print(f"Output: {OUTPUT_FILE}\n")

    run_collection()

    schedule.every(INTERVAL_HOURS).hours.do(run_collection)

    while True:
        schedule.run_pending()
        time.sleep(60)