"""
build_team_timeline.py

Step 1 of feature engineering: reshape the raw `matches` table into a
per-team, oldest-first timeline from each team's OWN perspective.

This does NOT compute any rolling features yet. It only reorganizes the data
so that each team's full match history (home games AND away games) sits in one
chronological timeline. The rolling-window features get built on top of this
in the next step.

Reads:  matches table in the `premier_league` Postgres db
Writes: team_timeline.csv  (one row per team-per-match, oldest first)
"""

import psycopg2
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Pull the raw matches table
# ---------------------------------------------------------------------------
conn = psycopg2.connect(dbname="premier_league", user="matty")

matches = pd.read_sql(
    """
    SELECT match_id, date, season, home_team, away_team,
           home_goals, away_goals, home_xg, away_xg, result
    FROM matches
    ORDER BY date
    """,
    conn,
)
conn.close()

print(f"Loaded {len(matches)} matches from the database.")

# ---------------------------------------------------------------------------
# 2. Build the HOME perspective rows
#    For each match, record it from the home team's point of view.
# ---------------------------------------------------------------------------
home = pd.DataFrame({
    "match_id":       matches["match_id"],
    "date":           matches["date"],
    "season":         matches["season"],
    "team":           matches["home_team"],
    "opponent":       matches["away_team"],
    "venue":          "home",
    "goals_for":      matches["home_goals"],
    "goals_against":  matches["away_goals"],
    "xg_for":         matches["home_xg"],
    "xg_against":     matches["away_xg"],
})
# Derive outcome directly from goals — unambiguous, no perspective confusion.
home["outcome"] = home.apply(
    lambda r: "W" if r["goals_for"] > r["goals_against"]
    else ("L" if r["goals_for"] < r["goals_against"] else "D"),
    axis=1,
)

# ---------------------------------------------------------------------------
# 3. Build the AWAY perspective rows
#    Same matches, but flipped to the away team's point of view.
#    Goals/xG swap sides, and the outcome inverts (home win => away loss).
# ---------------------------------------------------------------------------
away = pd.DataFrame({
    "match_id":       matches["match_id"],
    "date":           matches["date"],
    "season":         matches["season"],
    "team":           matches["away_team"],
    "opponent":       matches["home_team"],
    "venue":          "away",
    "goals_for":      matches["away_goals"],
    "goals_against":  matches["home_goals"],
    "xg_for":         matches["away_xg"],
    "xg_against":     matches["home_xg"],
})
# Derive outcome directly from goals — unambiguous, no perspective confusion.
away["outcome"] = away.apply(
    lambda r: "W" if r["goals_for"] > r["goals_against"]
    else ("L" if r["goals_for"] < r["goals_against"] else "D"),
    axis=1,
)

# ---------------------------------------------------------------------------
# 4. Stack them into one timeline and sort oldest-first per team
# ---------------------------------------------------------------------------
timeline = pd.concat([home, away], ignore_index=True)

# Sort by team, then date ascending (oldest on top) — required for the
# rolling-window math in the next step.
timeline = timeline.sort_values(["team", "date"]).reset_index(drop=True)

# ---------------------------------------------------------------------------
# 5. Save and report
# ---------------------------------------------------------------------------
timeline.to_csv("team_timeline.csv", index=False)

print(f"Built timeline with {len(timeline)} team-match rows "
      f"({len(timeline)//len(matches)}x the match count, as expected — "
      f"each match appears once per team).")
print(f"Teams in timeline: {timeline['team'].nunique()}")
print("\nSaved to team_timeline.csv")

# Quick eyeball: show one team's most recent few games so you can sanity-check
sample_team = "Arsenal"
print(f"\nLast 8 rows for {sample_team} (newest at the bottom):")
cols = ["date", "venue", "opponent", "goals_for", "goals_against",
        "xg_for", "xg_against", "outcome"]
print(timeline[timeline["team"] == sample_team][cols].tail(8).to_string(index=False))