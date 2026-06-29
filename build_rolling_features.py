"""
build_rolling_features.py

Step 2 of feature engineering: add rolling 5-match form features to each
team's timeline, computed with NO leakage.

The critical move is .shift(1) BEFORE .rolling(). For any given match, the
rolling stats are computed from the team's 5 matches strictly BEFORE it —
never including the match itself. Without the shift, a match's own result
would leak into its own features, and the model would memorize the answer key.

Reads:  team_timeline.csv  (from build_team_timeline.py, oldest-first per team)
Writes: team_features.csv  (same rows, plus rolling feature columns)
"""

import pandas as pd

WINDOW = 5  # number of prior matches to average over

# ---------------------------------------------------------------------------
# 1. Load the timeline (already oldest-first per team)
# ---------------------------------------------------------------------------
timeline = pd.read_csv("team_timeline.csv", parse_dates=["date"])

# Make absolutely sure ordering is correct before any rolling math.
timeline = timeline.sort_values(["team", "date"]).reset_index(drop=True)

# Points earned per match (form): win = 3, draw = 1, loss = 0
timeline["points"] = timeline["outcome"].map({"W": 3, "D": 1, "L": 0})

# ---------------------------------------------------------------------------
# 2. Define which raw columns get rolled, and their feature names
# ---------------------------------------------------------------------------
roll_cols = {
    "points":        "form_last5",            # avg points per game
    "goals_for":     "goals_scored_last5",
    "goals_against": "goals_conceded_last5",
    "xg_for":        "xg_last5",
    "xg_against":    "xga_last5",
}

# ---------------------------------------------------------------------------
# 3. Compute shifted rolling averages PER TEAM
#    groupby('team') keeps each team's window from bleeding into the next team.
#    .shift(1) excludes the current match -> no leakage.
# ---------------------------------------------------------------------------
for raw_col, feat_name in roll_cols.items():
    timeline[feat_name] = (
        timeline
        .groupby("team")[raw_col]
        .transform(lambda s: s.shift(1).rolling(WINDOW).mean())
    )

# ---------------------------------------------------------------------------
# 3b. Venue-specific rolling averages: group by TEAM *and* VENUE so a home
#     match's window contains only prior HOME games, and an away match's
#     window only prior AWAY games. Same .shift(1) leakage guard.
#     These capture how differently teams perform at home vs away.
# ---------------------------------------------------------------------------
for raw_col, feat_name in roll_cols.items():
    timeline[feat_name + "_venue"] = (
        timeline
        .groupby(["team", "venue"])[raw_col]
        .transform(lambda s: s.shift(1).rolling(WINDOW).mean())
    )

# ---------------------------------------------------------------------------
# 4. Report how many rows lack a full 5-match history
# ---------------------------------------------------------------------------
incomplete = timeline["form_last5"].isna().sum()
incomplete_venue = timeline["form_last5_venue"].isna().sum()
print(f"Rows total: {len(timeline)}")
print(f"Rows without a full {WINDOW}-match overall history (NaN): {incomplete}")
print(f"Rows without a full {WINDOW}-match SAME-VENUE history (NaN): {incomplete_venue}")
print(f"(Venue-split has more NaNs — it takes longer to accumulate 5 home/away games.)")

# Note: we are NOT dropping the incomplete rows here. We keep them so the
# timeline stays complete; the next step (assembling the match-level dataset)
# decides how to handle early-season rows.

# ---------------------------------------------------------------------------
# 5. Save
# ---------------------------------------------------------------------------
timeline.to_csv("team_features.csv", index=False)
print("\nSaved to team_features.csv")

# ---------------------------------------------------------------------------
# 6. Eyeball Arsenal: the rolling features on row N should reflect the games
#    ABOVE it, not including row N itself.
# ---------------------------------------------------------------------------
sample_team = "Arsenal"
cols = ["date", "venue", "opponent", "goals_for", "outcome",
        "form_last5", "form_last5_venue", "xg_last5", "xg_last5_venue"]
print(f"\nLast 8 rows for {sample_team} (compare overall vs same-venue form):")
print(timeline[timeline["team"] == sample_team][cols].tail(8).to_string(index=False))