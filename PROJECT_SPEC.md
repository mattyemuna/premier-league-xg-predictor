# Premier League Predictor — Project Spec

A web app that predicts Premier League match outcomes using historical data and a machine learning model, with Claude-generated plain-English explanations layered on top. Built to be a polished, deployed, end-to-end software project.

---

## 1. Goal & Scope

**One-line pitch:** "I built a machine learning platform that predicts Premier League matches using historical data, and integrated Claude to explain each prediction in plain English."

**Primary goals (in priority order):**
1. Ship something polished and deployed (live URL, works in a demo every time).
2. Demonstrate the full stack: data → ML → backend → frontend → LLM integration.
3. Have a clear, easy-to-explain interview story.

**In scope (v1):**
- Whole-league coverage (all 20 teams, all matches).
- Match outcome prediction (home win / draw / away win) with probabilities.
- Form dashboards (recent results, goals, xG/xGA, league position, home/away splits).
- Match archive showing past predictions vs actual results (model accuracy tracking).
- Structured Claude explanations ("Why this prediction?" buttons).

**Out of scope (v2, only if time permits):**
- Player-level predictions (goals, assists, minutes).
- Free-form conversational chat with Claude.
- Live in-season auto-updating / scheduled scrapes.

**Anti-goal:** scope creep. Freeze the v1 feature set. Everything else is v2.

---

## 2. Architecture Overview

```
Understat (data source)
   │  scrape.py (done)
   ▼
PostgreSQL  ──►  Feature engineering  ──►  ML model (trained, saved to disk)
   │                                              │
   │                                              ▼
   └──────────────►  FastAPI backend  ◄───────────┘
                          │   │
                          │   └──►  Anthropic API (structured explanations)
                          ▼
                    React frontend (Vercel)
```

- **Backend (FastAPI)** loads the trained model once, exposes prediction + data endpoints, and owns the one place that talks to the Anthropic API.
- **Claude integration is a thin layer**, not load-bearing. The app fully works without it; explanations are the polish on top.

---

## 3. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Data source | Understat | Already scraped: 1,900 matches, 2021–22 to 2025–26 |
| Database | PostgreSQL | `premier_league` db, `matches` table |
| Feature eng. | Python (pandas) | Produces a model-ready table/dataframe |
| ML | scikit-learn / XGBoost | Start simple (logistic regression / random forest), then XGBoost |
| Backend | FastAPI | Serves predictions, data, and Claude explanations |
| LLM | Anthropic API | Structured prompts grounded in your own data |
| Frontend | React + TypeScript + Tailwind | |
| Deploy | Vercel (frontend) + Render/Railway (backend) | Managed Postgres on the same host |

---

## 4. Data Layer — DONE ✅

- `matches` table populated: 1,900 rows, 380 per season × 5 seasons.
- Zero duplicates (enforced by `match_id` dedup; consider a UNIQUE constraint as a safety net).
- `result` is home-relative: `w` = home win, `d` = draw, `l` = away win.
- Known property: strong home advantage in the data (966 / 454 / 480) — this is real signal, keep it.

**Optional hardening:**
```sql
ALTER TABLE matches ADD CONSTRAINT matches_match_id_unique UNIQUE (match_id);
```

---

## 5. Feature Engineering

Goal: turn the raw `matches` table into a model-ready dataset where each row is one match with features known *before kickoff*.

**Critical rule: no data leakage.** Every feature for a match must be computed only from matches that happened *before* it. Never include the current match's goals/xG/result as an input.

**Features to compute (per match, for both home and away team):**
- Recent form: points / wins over last 5 matches.
- Goals scored & conceded (rolling avg, last 5).
- xG and xGA (rolling avg, last 5) — these are often more predictive than goals.
- Home/away split: team's performance specifically at home (for the home side) and away (for the away side).
- League position / points-per-game at time of match (optional, more work).
- Rest / recency (optional): days since last match.

**Target variable:** `result` (3-class: home win / draw / away win).

**Output:** a function or script that produces a clean feature dataframe, plus a saved version (e.g. parquet/CSV) for fast model iteration.

---

## 6. Model

**Start simple, then improve.** Don't begin with XGBoost.

1. **Baseline:** always predict "home win." Record its accuracy (~51%). Every model must beat this.
2. **Logistic regression:** simple, fast, interpretable. First real model.
3. **Random forest / XGBoost:** once the pipeline works end-to-end.

**Validation — do this right, it's an interview talking point:**
- Split **by time**, not randomly. Train on earlier seasons, test on the most recent. Random splits leak future info into the past.
- Watch class imbalance (966/454/480). Accuracy alone is misleading — a lazy model just predicts home wins.
- Report **per-class precision/recall** and a **confusion matrix**, not just accuracy.
- Draws are the hardest class to predict — expect weak recall there. That's normal and worth being able to explain.

**Output:** model probabilities for [home win, draw, away win], plus optionally a predicted score (e.g. from team xG averages). Save the trained model to disk (`joblib`) so the backend loads it instead of retraining.

---

## 7. Backend (FastAPI)

Load the model once at startup. Suggested endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /matches/upcoming` | Upcoming fixtures with predicted probabilities |
| `GET /matches/{id}` | Single match details + prediction |
| `GET /teams/{name}/form` | Form dashboard data (last 5, xG, splits, position) |
| `GET /archive` | Past predictions vs actual results (accuracy tracking) |
| `GET /explain/{match_id}` | **Claude explanation** for a match's prediction |

**Pattern for `/explain/{match_id}`:**
1. Pull the two teams' form, xG/xGA, home/away splits, league positions, and the model's probability output from the DB/model.
2. Format into a fixed prompt template: *"Here is the data for this match: [...]. The model predicts [...]. Explain in 3–4 sentences why the model favors X."*
3. Call the Anthropic API.
4. Return the text to the frontend.

Every other Claude feature (team form summary, "biggest upset this week") is a copy of this pattern with a different prompt + data fields. Keep the API key server-side only — never in the frontend.

---

## 8. Frontend (React)

**Pages:**
- **Upcoming match** — probabilities, predicted score, "Why this prediction?" button (calls `/explain`).
- **Form dashboard** — per-team last-5, goals, xG/xGA, position, home vs away, with simple charts.
- **Match archive** — past prediction vs actual result, running accuracy stat.

Charts make it look professional (recharts works well). Keep the design clean and consistent; a polished simple UI beats a cluttered ambitious one in a demo.

---

## 9. Claude Integration (Polish Layer)

**Approach: structured, not conversational.** Pre-built buttons/summaries that call Claude under the hood with grounded data.

**Why structured:** you control the input completely, it can't go off the rails in a demo, and the resume story is identical ("retrieval-augmented generation over my own match data and model outputs"). Conversational chat shares the same grounding backend and is a clean v2 addition.

**Build it last.** The app should work fully before this is added, so it can never block your deploy.

---

## 10. Deployment

- Frontend → Vercel.
- Backend → Render or Railway (free tier is fine for a demo).
- Database → managed Postgres on the same host as the backend.
- Set the Anthropic API key as a backend environment variable.
- Goal: a single live URL you can put on your resume and open in an interview.

---

## 11. Build Order (Checklist)

- [x] Scrape whole-league data into Postgres
- [ ] (Optional) Add UNIQUE constraint on `match_id`
- [ ] Feature engineering script (no leakage) → model-ready dataset
- [ ] Baseline accuracy (predict home win)
- [ ] Logistic regression model + time-based validation
- [ ] Upgrade to random forest / XGBoost
- [ ] Save trained model to disk
- [ ] FastAPI backend: prediction + data endpoints
- [ ] React frontend: upcoming match + form dashboard + archive
- [ ] Deploy backend + frontend + DB
- [ ] Add structured Claude `/explain` endpoint + "Why?" button
- [ ] (v2) Player predictions, conversational chat

---

## 12. Interview Talking Points (things this project lets you say)

- End-to-end ownership: scraping, cleaning, modeling, API, frontend, deployment.
- Proper ML hygiene: avoided data leakage, used time-based splits, judged the model on per-class metrics under class imbalance rather than raw accuracy.
- Practical LLM integration: grounded Claude in your own data/model outputs (RAG-style) rather than using it as a generic chatbot — understood that the value is in the data pipeline and grounding.
- Product thinking: scoped a v1, shipped it, and deferred nice-to-haves.
