"""
train_xg.py

Predict home_xg and away_xg with two separate LinearRegressions trained on
pre-match features, then evaluate how much better they are than a dumb
mean-prediction baseline.

Reads:
  - model_dataset.csv  (pre-match features, no leakage)
  - matches table in Postgres  (actual home_xg / away_xg targets)
"""

import numpy as np
import pandas as pd
import psycopg2
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score

# ---------------------------------------------------------------------------
# 1. Load the feature dataset and join on the actual xG target from Postgres
# ---------------------------------------------------------------------------
dataset = pd.read_csv("model_dataset_elo.csv")
dataset = dataset.dropna(subset=["home_elo", "away_elo", "elo_diff"]).reset_index(drop=True)


conn = psycopg2.connect(dbname="premier_league", user="matty")
xg = pd.read_sql("SELECT match_id, home_xg, away_xg FROM matches", conn)
conn.close()

xg["match_id"] = xg["match_id"].astype(int)
dataset["match_id"] = dataset["match_id"].astype(int)

dataset = dataset.merge(xg, on="match_id", how="left")

before = len(dataset)
dataset = dataset.dropna(subset=["home_xg", "away_xg"]).reset_index(drop=True)
print(f"Joined actual xG for {len(dataset)}/{before} matches.")

# ---------------------------------------------------------------------------
# 2. Time-based train/test split — train on the past, test on the most recent
#    season so the model never sees the future.
# ---------------------------------------------------------------------------
drop_cols = ["match_id", "date", "season", "home_team", "away_team",
             "result", "home_xg", "away_xg"]
feature_cols = [c for c in dataset.columns if c not in drop_cols]

train = dataset[dataset["season"] <= 2024]
test  = dataset[dataset["season"] == 2025].copy()

X_train, X_test = train[feature_cols], test[feature_cols]
y_train_home, y_test_home = train["home_xg"], test["home_xg"]
y_train_away, y_test_away = train["away_xg"], test["away_xg"]

print(f"Train size: {len(X_train)}  Test size: {len(X_test)}")

# ---------------------------------------------------------------------------
# 3. Naive baseline: always predict the training-set mean
#    This is the "dumb guess" our model must beat.
# ---------------------------------------------------------------------------
mean_home_xg = y_train_home.mean()
mean_away_xg = y_train_away.mean()

naive_home_mae = mean_absolute_error(y_test_home, np.full(len(y_test_home), mean_home_xg))
naive_away_mae = mean_absolute_error(y_test_away, np.full(len(y_test_away), mean_away_xg))

print(f"\nTraining-set means — home xG: {mean_home_xg:.3f}  away xG: {mean_away_xg:.3f}")

# ---------------------------------------------------------------------------
# 4. Train two linear regressions: one for home_xg, one for away_xg
# ---------------------------------------------------------------------------
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

home_model = LinearRegression()
home_model.fit(X_train_scaled, y_train_home)
pred_home = home_model.predict(X_test_scaled)

away_model = LinearRegression()
away_model.fit(X_train_scaled, y_train_away)
pred_away = away_model.predict(X_test_scaled)

home_mae = mean_absolute_error(y_test_home, pred_home)
away_mae = mean_absolute_error(y_test_away, pred_away)
home_r2  = r2_score(y_test_home, pred_home)
away_r2  = r2_score(y_test_away, pred_away)

# ---------------------------------------------------------------------------
# 5. Results
# ---------------------------------------------------------------------------
print("\n--- xG model vs naive baseline ---")
print(f"{'':25s}  {'HOME xG':>10s}  {'AWAY xG':>10s}")
print(f"{'Naive mean MAE':25s}  {naive_home_mae:10.3f}  {naive_away_mae:10.3f}")
print(f"{'Model MAE':25s}  {home_mae:10.3f}  {away_mae:10.3f}")
print(f"{'MAE improvement':25s}  {naive_home_mae - home_mae:+10.3f}  {naive_away_mae - away_mae:+10.3f}")
print(f"{'R²':25s}  {home_r2:10.3f}  {away_r2:10.3f}")

home_beats = home_mae < naive_home_mae
away_beats = away_mae < naive_away_mae
print(f"\nBeats naive baseline?  home: {'YES' if home_beats else 'NO'}  away: {'YES' if away_beats else 'NO'}")

# ---------------------------------------------------------------------------
# 6. Example predictions — a handful of matches so results are eyeball-able
# ---------------------------------------------------------------------------
print("\n--- Example predictions (first 8 test matches) ---")
print(f"{'Match':35s}  {'Pred H':>6s}  {'Act H':>6s}  {'Pred A':>6s}  {'Act A':>6s}")
for i, (_, row) in enumerate(test.head(8).iterrows()):
    matchup = f"{row['home_team']} vs {row['away_team']}"
    print(
        f"{matchup:35s}  "
        f"{pred_home[i]:6.2f}  {row['home_xg']:6.2f}  "
        f"{pred_away[i]:6.2f}  {row['away_xg']:6.2f}"
    )

# ---------------------------------------------------------------------------
# 7. Refit on full dataset and save for backend use
# ---------------------------------------------------------------------------
import os
import joblib

os.makedirs("models", exist_ok=True)

X_all = dataset[feature_cols]
y_all_home = dataset["home_xg"]
y_all_away = dataset["away_xg"]

full_scaler = StandardScaler()
X_all_scaled = full_scaler.fit_transform(X_all)

full_home_model = LinearRegression()
full_home_model.fit(X_all_scaled, y_all_home)

full_away_model = LinearRegression()
full_away_model.fit(X_all_scaled, y_all_away)

joblib.dump(full_home_model, "models/home_xg_model.pkl")
joblib.dump(full_away_model, "models/away_xg_model.pkl")
joblib.dump(full_scaler,     "models/scaler.pkl")
joblib.dump(feature_cols,    "models/feature_cols.pkl")

print("\n--- Saved to models/ ---")
print(f"  home_xg_model.pkl  ({len(feature_cols)} features, {len(dataset)} training rows)")
print(f"  away_xg_model.pkl")
print(f"  scaler.pkl")
print(f"  feature_cols.pkl   {feature_cols}")
