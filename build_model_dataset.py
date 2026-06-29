"""
build_model_dataset.py

Step 3 (final) of feature engineering: assemble the model-ready table.

For each MATCH, pull the home team's pre-match form features and the away
team's pre-match form features, place them side by side on one row, attach a
head-to-head feature, and keep `result` as the target.

Matches where EITHER team lacks a complete 5-match history are dropped, since
they have NaN features. This costs a small number of early-season matches.

Reads:
  - team_features.csv  (per-team timeline with rolling features)
  - matches  (raw table, for match list + head-to-head + target)
Writes:
  - model_dataset.csv  (one row per usable match, ready for training)
"""

import psycopg2
import pandas as pd

FEATURE_COLS = [
    "form_last5",
    "goals_scored_last5",
    "goals_conceded_last5",
    "xg_last5",
    "xga_last5",
    "form_last5_venue",
    "goals_scored_last5_venue",
    "goals_conceded_last5_venue",
    "xg_last5_venue",
    "xga_last5_venue",
]

# ---------------------------------------------------------------------------
# 1. Load per-team features and the raw matches table
# ---------------------------------------------------------------------------
feats = pd.read_csv("team_features.csv", parse_dates=["date"])

conn = psycopg2.connect(dbname="premier_league", user="matty")
matches = pd.read_sql(
    """
    SELECT match_id, date, season, home_team, away_team,
           home_goals, away_goals, result
    FROM matches
    ORDER BY date
    """,
    conn,
)
conn.close()
matches["date"] = pd.to_datetime(matches["date"])

# match_id is stored as text in the DB but int in the CSV — make both int so
# the (match_id, team) lookup matches.
matches["match_id"] = matches["match_id"].astype(int)
feats["match_id"] = feats["match_id"].astype(int)

print(f"Raw matches: {len(matches)}")

# ---------------------------------------------------------------------------
# 2. Build a lookup: (match_id, team) -> that team's pre-match features
#    Each match_id appears twice in feats (once per team), so this is unique.
# ---------------------------------------------------------------------------
feat_lookup = feats.set_index(["match_id", "team"])[FEATURE_COLS]

# ---------------------------------------------------------------------------
# 3. Attach home-team and away-team features to each match
# ---------------------------------------------------------------------------
def get_feats(match_id, team):
    try:
        return feat_lookup.loc[(match_id, team)]
    except KeyError:
        return pd.Series([float("nan")] * len(FEATURE_COLS), index=FEATURE_COLS)

home_feats = matches.apply(
    lambda m: get_feats(m["match_id"], m["home_team"]), axis=1
).add_prefix("home_")

away_feats = matches.apply(
    lambda m: get_feats(m["match_id"], m["away_team"]), axis=1
).add_prefix("away_")

dataset = pd.concat([matches, home_feats, away_feats], axis=1)

# ---------------------------------------------------------------------------
# 4. Head-to-head: goal difference (home perspective) of these two teams'
#    most recent PRIOR meeting. Strictly before the current match's date.
# ---------------------------------------------------------------------------
def h2h_last_gd(row):
    prior = matches[
        (matches["date"] < row["date"]) &
        (
            ((matches["home_team"] == row["home_team"]) & (matches["away_team"] == row["away_team"])) |
            ((matches["home_team"] == row["away_team"]) & (matches["away_team"] == row["home_team"]))
        )
    ]
    if prior.empty:
        return float("nan")
    last = prior.sort_values("date").iloc[-1]
    # goal difference from the CURRENT home team's perspective
    if last["home_team"] == row["home_team"]:
        return last["home_goals"] - last["away_goals"]
    else:
        return last["away_goals"] - last["home_goals"]

dataset["h2h_last_gd"] = dataset.apply(h2h_last_gd, axis=1)

# ---------------------------------------------------------------------------
# 5. Drop matches with incomplete features (either team lacked 5-match history)
#    NOTE: h2h is allowed to be NaN (first-ever meeting), so we only require the
#    rolling form features to be present. We'll fill h2h NaN with 0 (neutral).
# ---------------------------------------------------------------------------
required = [f"home_{c}" for c in FEATURE_COLS] + [f"away_{c}" for c in FEATURE_COLS]

before = len(dataset)
dataset = dataset.dropna(subset=required).reset_index(drop=True)
after = len(dataset)

# Fill first-meeting head-to-head with 0 (no prior result = neutral)
dataset["h2h_last_gd"] = dataset["h2h_last_gd"].fillna(0)

print(f"Dropped {before - after} matches with incomplete form history.")
print(f"Usable training matches: {after}")

# ---------------------------------------------------------------------------
# 6. Final column selection and save
# ---------------------------------------------------------------------------
keep = (
    ["match_id", "date", "season", "home_team", "away_team"]
    + [f"home_{c}" for c in FEATURE_COLS]
    + [f"away_{c}" for c in FEATURE_COLS]
    + ["h2h_last_gd", "result"]
)
dataset = dataset[keep]

dataset.to_csv("model_dataset.csv", index=False)
print("\nSaved to model_dataset.csv")

# ---------------------------------------------------------------------------
# 7. Eyeball: show a few rows and the target distribution
# ---------------------------------------------------------------------------
print("\nFirst 3 rows:")
print(dataset.head(3).to_string(index=False))

print("\nTarget (result) distribution:")
print(dataset["result"].value_counts())