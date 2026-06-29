"""
app.py — FastAPI backend for xG match predictions + AI chat analyst.

Run:  uvicorn app:app --reload --port 8000
"""

import json
import os
import time
import urllib.request
from contextlib import asynccontextmanager
from typing import Optional

import anthropic
import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# football-data.org team name → model team name normalisation
# ---------------------------------------------------------------------------
_TEAM_NAME_MAP = {
    "Brighton & Hove Albion": "Brighton",
    "Tottenham Hotspur":       "Tottenham",
    "West Ham United":         "West Ham",
    "Leicester City":          "Leicester",
    "Ipswich Town":            "Ipswich",
    "Luton Town":              "Luton",
    "Leeds United":            "Leeds",
    "Norwich City":            "Norwich",
    "Sheffield Utd":           "Sheffield United",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers",
    "Nott'm Forest":           "Nottingham Forest",
    "Nottm Forest":            "Nottingham Forest",
}


def _normalise_team(api_name: str) -> str:
    """Map a football-data.org team name to the model's canonical team name."""
    name = api_name.strip()
    for suffix in (" FC", " AFC"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if name.startswith("AFC "):
        name = name[4:]
    return _TEAM_NAME_MAP.get(name, name)


# ---------------------------------------------------------------------------
# Upcoming-fixtures in-memory cache (refresh at most once per hour)
# ---------------------------------------------------------------------------
_upcoming_cache: dict = {"payload": None, "ts": 0.0}
_CACHE_TTL = 3600  # seconds


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GENERAL_FEATURES = [
    "form_last5",
    "goals_scored_last5",
    "goals_conceded_last5",
    "xg_last5",
    "xga_last5",
]
VENUE_FEATURES = [
    "form_last5_venue",
    "goals_scored_last5_venue",
    "goals_conceded_last5_venue",
    "xg_last5_venue",
    "xga_last5_venue",
]

SYSTEM_PROMPT = """You are an elite Premier League football analyst AI with access to an xG \
(expected goals) prediction model trained on 5 seasons of Premier League data (2021-2026). \
The model incorporates rolling team form, venue-specific statistics, and Elo ratings.

Your role: help fans understand match dynamics, analyse matchups, and explain what the \
numbers mean in the context of real football. Be engaging, precise, and insightful. Keep \
replies concise — 2-4 paragraphs max.

Key principles to always uphold:
- xG measures the statistical quality of scoring opportunities based on historical shot \
  location and type data — not guaranteed outcomes
- Football is inherently high-variance: a lower-xG team wins roughly 30% of matches
- The model cannot account for injuries, suspensions, recent transfers, or mid-season \
  tactical shifts — always flag this caveat when relevant
- Contextualise numbers with footballing insight: pressing shape, defensive structure, \
  set-piece threat, key player dynamics, home crowd effect

When discussing a specific matchup, call the predict_match tool to retrieve xG values, \
then explain them with depth and nuance.

Valid team names (use exactly as shown):
Arsenal, Aston Villa, Bournemouth, Brentford, Brighton, Burnley, Chelsea, Crystal Palace,
Everton, Fulham, Ipswich, Leeds, Leicester, Liverpool, Luton, Manchester City,
Manchester United, Newcastle United, Norwich, Nottingham Forest, Sheffield United,
Southampton, Sunderland, Tottenham, Watford, West Ham, Wolverhampton Wanderers

If a team is not in this list, tell the user politely and suggest the closest valid name."""

TOOLS = [
    {
        "name": "predict_match",
        "description": (
            "Predict the expected goals (xG) for a Premier League match between two teams. "
            "Call this whenever the user asks about a specific matchup, head-to-head, "
            "or who would win. home_team plays at their home ground."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "home_team": {
                    "type": "string",
                    "description": "Home team name, exactly as in the valid teams list.",
                },
                "away_team": {
                    "type": "string",
                    "description": "Away team name, exactly as in the valid teams list.",
                },
            },
            "required": ["home_team", "away_team"],
        },
    }
]

# ---------------------------------------------------------------------------
# Startup: load models and reference data once
# ---------------------------------------------------------------------------
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["home_model"]   = joblib.load("models/home_xg_model.pkl")
    _state["away_model"]   = joblib.load("models/away_xg_model.pkl")
    _state["scaler"]       = joblib.load("models/scaler.pkl")
    _state["feature_cols"] = joblib.load("models/feature_cols.pkl")

    tf = pd.read_csv("team_features.csv")
    tf["date"] = pd.to_datetime(tf["date"])
    _state["team_features"] = tf

    elo = pd.read_csv("model_dataset_elo.csv")
    elo["date"] = pd.to_datetime(elo["date"])
    _state["elo_data"] = elo

    print(f"Loaded models ({len(_state['feature_cols'])} features)")
    print(f"Teams: {sorted(tf['team'].unique())}")
    yield
    _state.clear()


app = FastAPI(title="xG Predictor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------
def get_team_latest_features(team: str, venue: str, tf: pd.DataFrame) -> dict:
    team_rows = tf[tf["team"] == team].sort_values("date")
    if team_rows.empty:
        raise ValueError(f"Team '{team}' not found in team_features.")

    general_row = team_rows.iloc[-1]
    venue_rows = team_rows[team_rows["venue"] == venue]
    if venue_rows.empty:
        raise ValueError(f"No {venue} appearances found for '{team}'.")
    venue_row = venue_rows.iloc[-1]

    feats: dict = {}
    for col in GENERAL_FEATURES:
        feats[col] = general_row[col]
    for col in VENUE_FEATURES:
        feats[col] = venue_row[col]
    return feats


def get_team_latest_elo(team: str, elo: pd.DataFrame) -> float:
    home_rows = elo[elo["home_team"] == team].sort_values("date")
    away_rows = elo[elo["away_team"] == team].sort_values("date")
    candidates: list[tuple] = []
    if not home_rows.empty:
        r = home_rows.iloc[-1]
        candidates.append((r["date"], float(r["home_elo"])))
    if not away_rows.empty:
        r = away_rows.iloc[-1]
        candidates.append((r["date"], float(r["away_elo"])))
    if not candidates:
        raise ValueError(f"No Elo found for '{team}'.")
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def get_h2h_gd(home_team: str, away_team: str) -> float:
    """
    Return the most recent head-to-head goal difference from the perspective of
    home_team, derived from model_dataset_elo.csv.

    The CSV stores h2h_last_gd as the GD from the PREVIOUS encounter, so the
    most recent row for this pair gives us the real most-recent GD without
    needing a separate database.
    """
    elo = _state["elo_data"]
    mask = (
        ((elo["home_team"] == home_team) & (elo["away_team"] == away_team)) |
        ((elo["home_team"] == away_team) & (elo["away_team"] == home_team))
    )
    h2h = elo[mask].sort_values("date")
    if h2h.empty:
        return 0.0

    last = h2h.iloc[-1]
    gd = float(last["h2h_last_gd"])
    # h2h_last_gd is always stored from the perspective of the home team in that row;
    # negate if the roles are swapped relative to the current prediction.
    if last["home_team"] != home_team:
        gd = -gd
    return gd


def _run_prediction(home: str, away: str) -> dict:
    """Core prediction logic shared by /predict and the chat tool."""
    tf           = _state["team_features"]
    elo          = _state["elo_data"]
    feature_cols = _state["feature_cols"]
    scaler       = _state["scaler"]
    home_model   = _state["home_model"]
    away_model   = _state["away_model"]

    all_teams = set(tf["team"].unique())
    if home not in all_teams:
        raise ValueError(f"Home team '{home}' not recognised. Valid: {sorted(all_teams)}")
    if away not in all_teams:
        raise ValueError(f"Away team '{away}' not recognised. Valid: {sorted(all_teams)}")
    if home == away:
        raise ValueError("Home and away teams must differ.")

    home_feats = get_team_latest_features(home, "home", tf)
    away_feats = get_team_latest_features(away, "away", tf)
    home_elo   = get_team_latest_elo(home, elo)
    away_elo   = get_team_latest_elo(away, elo)
    h2h_gd     = get_h2h_gd(home, away)

    row: dict = {}
    for col in GENERAL_FEATURES:
        row[f"home_{col}"] = home_feats[col]
        row[f"away_{col}"] = away_feats[col]
    for col in VENUE_FEATURES:
        row[f"home_{col}"] = home_feats[col]
        row[f"away_{col}"] = away_feats[col]
    row["h2h_last_gd"] = h2h_gd
    row["home_elo"]    = home_elo
    row["away_elo"]    = away_elo
    row["elo_diff"]    = home_elo - away_elo

    X = pd.DataFrame([row])[feature_cols]
    X_scaled     = scaler.transform(X)
    pred_home_xg = float(np.clip(home_model.predict(X_scaled)[0], 0, None))
    pred_away_xg = float(np.clip(away_model.predict(X_scaled)[0], 0, None))

    return {
        "home_team": home,
        "away_team": away,
        "home_xg":   round(pred_home_xg, 2),
        "away_xg":   round(pred_away_xg, 2),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/upcoming-fixtures")
def get_upcoming_fixtures():
    """
    Return upcoming PL fixtures from football-data.org, grouped by matchday.
    Cached server-side for one hour to respect the free-tier rate limit.
    Response: { "matchdays": { "1": [{home_team, away_team, date}, ...], ... } }
    """
    api_key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="FOOTBALL_DATA_API_KEY not configured")

    now = time.time()
    if _upcoming_cache["payload"] is not None and now - _upcoming_cache["ts"] < _CACHE_TTL:
        return _upcoming_cache["payload"]

    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    req = urllib.request.Request(url, headers={"X-Auth-Token": api_key})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read())
    except Exception as exc:
        if _upcoming_cache["payload"] is not None:
            return _upcoming_cache["payload"]
        raise HTTPException(status_code=502, detail=f"football-data.org error: {exc}") from exc

    known_teams = set(_state["team_features"]["team"].unique())
    matchdays: dict = {}
    unmapped: set = set()

    for match in raw.get("matches", []):
        md   = str(match["matchday"])
        home = _normalise_team(match["homeTeam"]["name"])
        away = _normalise_team(match["awayTeam"]["name"])

        for team in (home, away):
            if team not in known_teams:
                unmapped.add(team)

        matchdays.setdefault(md, []).append(
            {"home_team": home, "away_team": away, "date": match["utcDate"][:10]}
        )

    if unmapped:
        print(f"[upcoming-fixtures] Teams not in model (newly promoted?): {sorted(unmapped)}")

    payload = {"matchdays": matchdays}
    _upcoming_cache["payload"] = payload
    _upcoming_cache["ts"] = now
    return payload


@app.get("/fixtures")
def get_fixtures(season: int = Query(None, description="Season year, e.g. 2024")):
    elo = _state["elo_data"]
    available = [int(s) for s in sorted(elo["season"].unique())]

    if season is None:
        season = max(available)

    if season not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Season {season} not found. Available: {available}",
        )

    df = (
        elo[elo["season"] == season][["date", "home_team", "away_team"]]
        .drop_duplicates()
        .sort_values("date")
        .reset_index(drop=True)
    )

    df["matchweek"] = (df.index // 10) + 1

    matchweeks: dict = {}
    for mw, group in df.groupby("matchweek"):
        matchweeks[int(mw)] = [
            {
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "date": str(row["date"])[:10],
            }
            for _, row in group.iterrows()
        ]

    return {"season": season, "available_seasons": available, "matchweeks": matchweeks}


@app.get("/teams")
def list_teams():
    teams = sorted(_state["team_features"]["team"].unique().tolist())
    return {"teams": teams}


@app.get("/predict")
def predict(
    home: str = Query(..., description="Home team name, e.g. Arsenal"),
    away: str = Query(..., description="Away team name, e.g. Chelsea"),
):
    try:
        return _run_prediction(home, away)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------
class ChatHistoryMessage(BaseModel):
    role: str     # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryMessage] = []


@app.post("/chat")
async def chat(req: ChatRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key)

    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    prediction_data: Optional[dict] = None

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if block.name == "predict_match":
                    try:
                        result = _run_prediction(
                            block.input["home_team"],
                            block.input["away_team"],
                        )
                        prediction_data = result
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                    except ValueError as exc:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(exc),
                            "is_error": True,
                        })

            messages.append({"role": "user", "content": tool_results})

        else:
            text_reply = " ".join(
                block.text
                for block in response.content
                if hasattr(block, "text")
            )
            return {"reply": text_reply, "prediction": prediction_data}
