"""
add_elo.py

Fetches ClubElo ratings for each match date in model_dataset.csv and merges
home_elo, away_elo, and elo_diff into a new model_dataset_elo.csv.

API: http://api.clubelo.com/YYYY-MM-DD  (returns CSV of all clubs on that date)
Cache: one CSV per calendar date stored in elo_cache/ so re-runs are instant.
"""

import time
import os
import io
import requests
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
CACHE_DIR = "elo_cache"
API_BASE  = "http://api.clubelo.com"
SLEEP_S   = 0.5   # pause between API calls to be polite
TIMEOUT_S = 10
MAX_RETRIES = 3

# ClubElo Club name  →  name used in model_dataset.csv
# Add entries here whenever the "unmapped teams" section prints a team.
CLUBELO_TO_MINE: dict[str, str] = {
    "Man City":           "Manchester City",
    "Man United":         "Manchester United",
    "Newcastle":          "Newcastle United",
    "Forest":             "Nottingham Forest",
    "Wolves":             "Wolverhampton Wanderers",
}

MY_TEAMS = {
    "Fulham", "Arsenal", "Chelsea", "Liverpool", "Manchester City",
    "Manchester United", "Tottenham", "Newcastle United", "Aston Villa",
    "Brighton", "West Ham", "Brentford", "Crystal Palace", "Everton",
    "Wolverhampton Wanderers", "Nottingham Forest", "Bournemouth",
    "Leeds", "Leicester", "Burnley", "Southampton", "Luton",
    "Sheffield United", "Watford", "Norwich", "Sunderland", "Ipswich",
}

os.makedirs(CACHE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
def fetch_elo_for_date(date_str: str) -> pd.DataFrame | None:
    """
    Fetch the ClubElo CSV for date_str (YYYY-MM-DD).
    Returns a DataFrame, or None on permanent failure.
    Reads from disk cache when available.
    """
    cache_path = os.path.join(CACHE_DIR, f"{date_str}.csv")
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    url = f"{API_BASE}/{date_str}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=TIMEOUT_S)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            df.to_csv(cache_path, index=False)
            return df
        except requests.RequestException as exc:
            if attempt < MAX_RETRIES:
                wait = SLEEP_S * (2 ** attempt)
                print(f"  Retry {attempt}/{MAX_RETRIES} for {date_str} ({exc}), waiting {wait:.1f}s")
                time.sleep(wait)
            else:
                print(f"  FAILED after {MAX_RETRIES} attempts for {date_str}: {exc}")
                return None


def elo_lookup(elo_df: pd.DataFrame) -> dict[str, float]:
    """
    Build {my_team_name: elo} from one date's ClubElo data.
    Filters to Country=ENG to avoid cross-country name clashes.
    Applies CLUBELO_TO_MINE translations.
    """
    eng = elo_df[elo_df["Country"] == "ENG"].copy()
    lookup: dict[str, float] = {}
    for _, row in eng.iterrows():
        club_name = row["Club"]
        my_name   = CLUBELO_TO_MINE.get(club_name, club_name)  # translate or keep as-is
        lookup[my_name] = float(row["Elo"])
    return lookup


# ---------------------------------------------------------------------------
# 1. Load dataset
# ---------------------------------------------------------------------------
print("Loading model_dataset.csv …")
dataset = pd.read_csv("model_dataset.csv")
dataset["cal_date"] = pd.to_datetime(dataset["date"]).dt.strftime("%Y-%m-%d")

unique_dates = sorted(dataset["cal_date"].unique())
print(f"  {len(dataset)} matches across {len(unique_dates)} unique calendar dates")

# ---------------------------------------------------------------------------
# 2. Fetch (or load from cache) Elo data for every unique date
# ---------------------------------------------------------------------------
print(f"\nFetching ClubElo data (cached in {CACHE_DIR}/) …")
date_to_lookup: dict[str, dict[str, float]] = {}

cached_count = 0
fetched_count = 0

for i, date_str in enumerate(unique_dates):
    cache_path = os.path.join(CACHE_DIR, f"{date_str}.csv")
    from_cache  = os.path.exists(cache_path)

    elo_df = fetch_elo_for_date(date_str)
    if elo_df is None:
        date_to_lookup[date_str] = {}
        continue

    date_to_lookup[date_str] = elo_lookup(elo_df)

    if from_cache:
        cached_count += 1
    else:
        fetched_count += 1
        time.sleep(SLEEP_S)

    if (i + 1) % 50 == 0 or (i + 1) == len(unique_dates):
        print(f"  {i+1}/{len(unique_dates)} dates processed "
              f"({fetched_count} API calls, {cached_count} from cache)")

# ---------------------------------------------------------------------------
# 3. Merge Elo values onto each match row
# ---------------------------------------------------------------------------
print("\nMerging Elo values onto matches …")

home_elos, away_elos = [], []
for _, row in dataset.iterrows():
    lookup    = date_to_lookup.get(row["cal_date"], {})
    home_elos.append(lookup.get(row["home_team"]))
    away_elos.append(lookup.get(row["away_team"]))

dataset["home_elo"] = home_elos
dataset["away_elo"] = away_elos
dataset["elo_diff"] = dataset["home_elo"] - dataset["away_elo"]
dataset = dataset.drop(columns=["cal_date"])

# ---------------------------------------------------------------------------
# 4. Report coverage
# ---------------------------------------------------------------------------
both_ok   = dataset["home_elo"].notna() & dataset["away_elo"].notna()
home_fail = dataset["home_elo"].isna()
away_fail = dataset["away_elo"].isna()

print(f"\n--- Coverage ---")
print(f"Both Elos found : {both_ok.sum():>4d} / {len(dataset)}")
print(f"Missing home Elo: {home_fail.sum():>4d}")
print(f"Missing away Elo: {away_fail.sum():>4d}")

# Which of MY teams never got an Elo?
unmapped_home = set(dataset.loc[home_fail, "home_team"].unique())
unmapped_away = set(dataset.loc[away_fail, "away_team"].unique())
unmapped = (unmapped_home | unmapped_away) & MY_TEAMS

if unmapped:
    print("\nUnmapped teams — extend CLUBELO_TO_MINE for these:")
    for t in sorted(unmapped):
        print(f"  \"{t}\"")
else:
    print("\nAll tracked teams were matched successfully.")

# ---------------------------------------------------------------------------
# 5. Save
# ---------------------------------------------------------------------------
out_path = "model_dataset_elo.csv"
dataset.to_csv(out_path, index=False)
print(f"\nSaved → {out_path}  ({len(dataset)} rows, {dataset.shape[1]} columns)")
