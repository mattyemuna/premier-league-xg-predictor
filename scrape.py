import requests
import psycopg2
import time
from datetime import datetime

conn = psycopg2.connect(dbname="premier_league", user="matty")
cur = conn.cursor()

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

teams = [
    "Fulham", "Arsenal", "Chelsea", "Liverpool", "Manchester City",
    "Manchester United", "Tottenham", "Newcastle United", "Aston Villa",
    "Brighton", "West Ham", "Brentford", "Crystal Palace", "Everton",
    "Wolverhampton Wanderers", "Nottingham Forest", "Bournemouth", "Leeds",
    "Leicester", "Burnley", "Southampton", "Luton", "Sheffield United",
    "Watford", "Norwich", "Sunderland", "Ipswich"
]

seasons = [2021, 2022, 2023, 2024, 2025]

inserted = 0
skipped = 0


def fetch_with_retry(url, headers, max_retries=3):
    """Fetch a URL with timeout and retry. Returns response or None."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response
        except requests.exceptions.RequestException as e:
            wait = 5 * attempt  # back off longer each time
            print(f"  Request failed (attempt {attempt}/{max_retries}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    print(f"  Giving up on {url} after {max_retries} attempts.")
    return None


for team in teams:
    for season in seasons:
        url = f"https://understat.com/getTeamData/{team}/{season}"
        headers["Referer"] = f"https://understat.com/team/{team}/{season}"

        response = fetch_with_retry(url, headers)
        if response is None:
            print(f"Skipping {team} {season} — no response after retries")
            continue

        if response.status_code != 200:
            print(f"Skipping {team} {season} — status {response.status_code}")
            continue

        try:
            data = response.json()
        except Exception:
            print(f"Skipping {team} {season} — no JSON")
            continue

        matches = data.get("dates", [])

        for match in matches:
            try:
                # Derive actual season from match date
                match_date = datetime.strptime(match["datetime"], "%Y-%m-%d %H:%M:%S")
                actual_season = match_date.year if match_date.month >= 8 else match_date.year - 1

                if actual_season != season:
                    skipped += 1
                    continue

                # Check if match already in db
                cur.execute("SELECT 1 FROM matches WHERE match_id = %s", (match["id"],))
                if cur.fetchone():
                    skipped += 1
                    continue

                cur.execute("""
                    INSERT INTO matches (
                        match_id, date, season, home_team, away_team,
                        home_goals, away_goals, home_xg, away_xg,
                        home_forecast_w, home_forecast_d, home_forecast_l,
                        result
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    match["id"],
                    match["datetime"],
                    season,
                    match["h"]["title"],
                    match["a"]["title"],
                    int(match["goals"]["h"]),
                    int(match["goals"]["a"]),
                    float(match["xG"]["h"]),
                    float(match["xG"]["a"]),
                    match["forecast"]["w"],
                    match["forecast"]["d"],
                    match["forecast"]["l"],
                    match["result"]
                ))
                conn.commit()
                inserted += 1
                print(f"Added match {match['id']} — {match['h']['title']} vs {match['a']['title']} ({team} {season})")
            except Exception as e:
                conn.rollback()
                print(f"Error inserting match {match.get('id', '?')}: {e}")
                skipped += 1

        time.sleep(2)  # be polite to Understat to avoid rate limiting

cur.close()
conn.close()
print(f"\nFinished. Inserted: {inserted}, Skipped: {skipped}")