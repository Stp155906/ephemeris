#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates the NEXT year's ephemeris JSON (00:00 UT snapshot) and saves as:
  ephemeris/YYYY_ephemeris_with_signs.json
Skips creation if the file already exists.
"""
import os, re, json, time, calendar, datetime
import requests
from bs4 import BeautifulSoup

OUT_DIR = "ephemeris"

PLANET_ABBRS = ["SU", "MO", "ME", "VE", "MA", "JU", "SA", "UR", "NE", "PL"]
PLANET_MAP = {
    "SU": "Sun","MO": "Moon","ME": "Mercury","VE": "Venus","MA": "Mars",
    "JU": "Jupiter","SA": "Saturn","UR": "Uranus","NE": "Neptune","PL": "Pluto"
}
ZODIAC_MAP = {
    "ARI": "Aries","TAU": "Taurus","GEM": "Gemini","CAN": "Cancer",
    "LEO": "Leo","VIR": "Virgo","LIB": "Libra","SCO": "Scorpio",
    "SAG": "Sagittarius","CAP": "Capricorn","AQU": "Aquarius","PIS": "Pisces"
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

def extract_day_num(tr):
    tds = tr.find_all("td")
    if not tds:
        return None
    m = re.search(r"\b([0-3]?\d)\b", tds[0].get_text(" ", strip=True))  # e.g., "Sat 2"
    return int(m.group(1)) if m else None

def fetch_month(month, year):
    month_name = calendar.month_name[month]
    url = f"https://horoscopes.astro-seek.com/astrology-ephemeris-{month_name.lower()}-{year}"

    # light retry
    for attempt in range(3):
        try:
            res = requests.get(url, headers=HEADERS, timeout=25); res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table")
            if not table:
                print(f"  ⚠️ Table not found for {month_name} {year}")
                return None
            break
        except Exception as e:
            if attempt == 2:
                print(f"  ❌ Failed {month_name} {year}: {e}")
                return None
            time.sleep(1.5*(attempt+1))

    month_data = {}
    for tr in table.find_all("tr"):
        planet_tds = tr.find_all("td", class_="udaj_planeta")
        if len(planet_tds) < 10:
            continue
        day_num = extract_day_num(tr)
        if day_num is None:
            continue

        daily = {}
        for abbr, td in zip(PLANET_ABBRS, planet_tds[:len(PLANET_ABBRS)]):
            img = td.find("img")
            sign_abbr = img["alt"].strip() if img and img.has_attr("alt") else None
            sign = ZODIAC_MAP.get(sign_abbr, "Unknown")
            spans = td.find_all("span")
            degree = " ".join(s.get_text(strip=True) for s in spans)
            daily[PLANET_MAP[abbr]] = f"{sign} {degree}".strip()

        month_data[str(day_num)] = daily

    if not month_data:
        print(f"  ⚠️ No rows parsed for {month_name} {year}")
        return None

    sorted_items = sorted(((int(k), v) for k, v in month_data.items()), key=lambda kv: kv[0])
    return month_name, {str(k): v for k, v in sorted_items}

def build_year(year):
    year_data = {}
    print(f"📅 Building year: {year}")
    for m in range(1, 13):
        print(f"  🔄 {calendar.month_name[m]} {year} ...")
        r = fetch_month(m, year)
        if not r:
            continue
        mn, md = r
        year_data[mn] = md
        time.sleep(1.0)  # be polite
    return year_data

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    today = datetime.date.today()
    target_year = today.year + 1
    print(f"Target year: {target_year}")

    out_path = os.path.join(OUT_DIR, f"{target_year}_ephemeris_with_signs.json")
    if os.path.exists(out_path):
        print(f"✅ {out_path} already exists. Nothing to do.")
        return

    data = build_year(target_year)
    if not data:
        raise SystemExit("No data generated; aborting.")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved: {out_path}")

if __name__ == "__main__":
    main()
