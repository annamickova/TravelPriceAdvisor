"""
Scraper czech holidays
Source: Nager.Date API (public, no key) + MŠMT

Run:
    pip install requests pandas
    python scraper_holidays.py

Run only once
"""

import requests
import pandas as pd
import os
from datetime import date, timedelta

OUTPUT_FILE = "data/svatky.csv"


def fetch_public_holidays(year: int) -> list:
    """Fetch Czech public holidays from Nager.Date API."""
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/CZ"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  Error fetching holidays for {year}: {e}")
        return []

    # is_holiday: 1 is holiday day
    records = []
    for item in data:
        records.append({
            "date":        item["date"],
            "name_en":     item["localName"],
            "name_cz":     item["name"],
            "type":        "public_holiday",
            "is_holiday":  1,
        })

    return records


# defined school breaks for year 2025/2026
SCHOOL_BREAKS = [
    {"name_cz": "Podzimní prázdniny", "start": "2025-10-29", "end": "2025-10-31"},
    {"name_cz": "Vánoční prázdniny",  "start": "2025-12-22", "end": "2026-01-04"},
    {"name_cz": "Pololetní prázdniny","start": "2026-01-30", "end": "2026-01-30"},
    {"name_cz": "Jarní prázdniny",    "start": "2026-02-16", "end": "2026-02-22"},
    {"name_cz": "Velikonoční prázdniny", "start": "2026-04-02", "end": "2026-04-05"},
    {"name_cz": "Letní prázdniny",    "start": "2026-06-27", "end": "2026-09-01"},
]


def generate_school_break_records() -> list:
    """Generate one record per day of each school break."""
    records = []

    for break_info in SCHOOL_BREAKS:
        start = date.fromisoformat(break_info["start"])
        end = date.fromisoformat(break_info["end"])

        current = start
        while current <= end:
            records.append({
                "date":        current.isoformat(),
                "name_en":     break_info["name_cz"],
                "name_cz":     break_info["name_cz"],
                "type":        "school_break",
                "is_holiday":  1,
            })
            current += timedelta(days=1)

    return records


def run_collection():
    all_records = []

    # public holidays for 2025 and 2026
    for year in [2025, 2026]:
        print(f"\n  Fetching public holidays {year}...")
        records = fetch_public_holidays(year)
        print(f"  Found {len(records)} holidays")
        all_records.extend(records)

    # school breaks
    print(f"\n  Generating school break days...")
    records = generate_school_break_records()
    print(f"  Generated {len(records)} school break days")
    all_records.extend(records)

    if not all_records:
        print("No data collected")
        return

    os.makedirs("data", exist_ok=True)

    df = pd.DataFrame(all_records)

    # sort by date
    df = df.sort_values("date").reset_index(drop=True)

    # remove duplicates (holiday + school break on same day)
    df = df.drop_duplicates(subset=["date", "type"])

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved: {len(df)} records to {OUTPUT_FILE}")
    print("\nSample:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    print("Holiday & school break scraper")
    run_collection()