"""
Scraper Ryanair flights
Run:
    pip install requests pandas, playwright, asyncio
"""
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta
import random
import os

OUTPUT_FILE = "data/letenky.csv"

ROUTES = [("PRG", "STN"),
          ("PRG", "BCN"),
          ("PRG", "CIA"),
          ("PRG", "BVA"),
          ("PRG", "MAD"),
          ("PRG", "PMI"),
          ("PRG", "AGP"),
          ("PRG", "DUB"),
          ("PRG", "SVQ"),
          ("PRG", "NAP"),
          ("PRG", "BRI"),
          ("PRG", "TSF")
          ]
DAYS_AHEAD = [3, 4, 6, 7, 8, 9]


async def scrape_route(origin, dest, date_str):
    """Session initialization to load data about flights."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        flights_found = []
        collected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # calculating days before departure
        target_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        today_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_until = (target_date_obj - today_obj).days

        # sniffer network communication
        async def handle_response(response):
            # tries to get request with "availability" to get parameters
            if "availability" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    for trip in data.get("trips", []):
                        for d in trip.get("dates", []):
                            if d.get("dateOut", "").startswith(date_str):
                                for f in d.get("flights", []):
                                    fare = f.get("regularFare")
                                    if fare:
                                        time_utc = f.get("timeUTC", ["", ""])
                                        dep_time = time_utc[0][:16] if len(time_utc) > 0 else ""
                                        arr_time = time_utc[1][:16] if len(time_utc) > 1 else ""
                                        price = fare["fares"][0]["amount"]

                                        flights_found.append({
                                            "collected_at": collected_time,
                                            "origin": origin,
                                            "destination": dest,
                                            "departure_date": date_str,
                                            "departure_time": dep_time,
                                            "arrival_time": arr_time,
                                            "price": price,
                                            "carrier": "Ryanair",
                                            "days_until_departure": days_until
                                        })
                except Exception as e:
                    pass

        page.on("response", handle_response)

        # getting cookies from page
        try:
            print("Loading for session initialization...")
            # start session
            await page.goto("https://www.ryanair.com/gb/en", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
        except Exception:
            pass

        # searching flight
        search_url = f"https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut={date_str}&dateIn=&isReturn=false&originIata={origin}&destinationIata={dest}"

        try:
            print(f"Searching flight: {origin} -> {dest} ({date_str})")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

            # waiting loop
            for _ in range(15):
                if flights_found:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error while searching: {e}")

        await browser.close()
        return flights_found


async def main():
    os.makedirs("data", exist_ok=True)

    columns_order = [
        "collected_at", "origin", "destination", "departure_date",
        "departure_time", "arrival_time", "price", "carrier", "days_until_departure"
    ]

    for origin, dest in ROUTES:
        for days in DAYS_AHEAD:
            target_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

            data = await scrape_route(origin, dest, target_date)

            if data:
                df = pd.DataFrame(data)[columns_order]
                header_needed = not os.path.exists(OUTPUT_FILE)
                # saving to csv, a-append
                df.to_csv(OUTPUT_FILE, mode='a', index=False, header=header_needed, encoding='utf-8')
                print(f"Saved {len(data)} rows to CSV")
            else:
                print(f"No data for: {target_date}")

            # random pause between requests to not get blocked
            await asyncio.sleep(random.uniform(3, 7))


if __name__ == "__main__":
    asyncio.run(main())