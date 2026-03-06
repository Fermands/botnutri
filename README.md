# BotNutri MVP (Telegram AI Nutrition Tracker for Uzbekistan)

## 1) System Architecture

- **Telegram Bot (aiogram)**: onboarding, meal logging (text/voice/photo), summaries, invites, leaderboards.
- **FastAPI API**: meal/summary/dashboard endpoints for web and integrations.
- **AI Layer (OpenAI)**:
  - LLM prompt parser for natural-language meal descriptions.
  - Whisper transcription for voice notes.
  - Vision analysis for food photos.
- **SQLite + SQLAlchemy**: users, meals, scores, friends, invites.
- **Web Dashboard (HTML + JS + Chart.js)**: progress UI and charts.

Flow: User -> Telegram bot -> AI parsing -> DB -> score engine -> bot/dashboard.

## 2) Folder Structure

```text
app/
  api/main.py
  bot/bot.py
  core/config.py
  db/session.py
  models/models.py
  schemas/schemas.py
  services/
    ai.py
    nutrition.py
    app_logic.py
  templates/dashboard.html
  dashboard/static/dashboard.js
run_api.py
run_bot.py
Dockerfile
docker-compose.yml
```

## 3) Telegram Bot

- `/start`: onboarding + optional referral via `?start=USER_ID`
- `/add`: prompt user to send text/voice/photo
- `/summary`: today's macro progress and remaining calories
- `/profile`: stored anthropometrics and targets
- `/delete_last`: remove most recent meal
- `/invite`: referral link
- `/leaderboard`: friend + global rankings
- `/dashboard`: deep link to web dashboard

## 4) FastAPI Backend

- `GET /health`
- `POST /api/users/{telegram_id}/meals`
- `GET /api/users/{telegram_id}/summary`
- `GET /api/users/{telegram_id}/dashboard-data`
- `GET /dashboard?user_id=...`

## 5) Database Models

Implemented tables:
- `users`
- `meals`
- `friends`
- `scores`
- `invites`

## 6) AI Nutrition Parser Prompt

Prompt is in `app/services/ai.py` and enforces strict JSON:
`food_name, portion, calories, protein, carbs, fats`.
It explicitly supports Uzbek foods: plov, lagman, samsa, shashlik, manty, non.

## 7) Food Photo Logic

1. Download Telegram photo.
2. Send to OpenAI vision model.
3. Get structured macro estimate.
4. Save to meals and recalculate score.

## 8) Voice Transcription Logic

1. Download voice message.
2. Whisper API transcribes speech.
3. Transcription is parsed with LLM nutrition parser.
4. Save meal + recompute score.

## 9) Web Dashboard

- Today's calories and daily score.
- Weekly calorie line chart.
- Macro distribution doughnut chart.
- Friend leaderboard.
- Chart.js + vanilla JS.

## 10) Example API Calls

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/users/12345/summary
curl -X POST http://localhost:8000/api/users/12345/meals \
  -H "Content-Type: application/json" \
  -d '{"food_description":"plov","calories":500,"protein":20,"carbs":60,"fats":20}'
```

## 11) Deployment (Docker + VPS)

### Docker local
```bash
cp .env.example .env
# fill real BOT_TOKEN and OPENAI_API_KEY
docker compose up --build
```

### VPS (Ubuntu)
1. Install Docker + Compose plugin.
2. Clone repo and set `.env`.
3. Run `docker compose up -d --build`.
4. Put Nginx in front for HTTPS and set `BASE_URL=https://yourdomain.com`.
5. Use `systemd` or compose restart policy.

## 12) Scaling Suggestions

- Move SQLite -> PostgreSQL.
- Switch polling bot to webhook mode.
- Queue AI jobs (Redis + Celery/RQ).
- Cache summaries/leaderboards.
- Add auth tokens for dashboard URLs.
- Add i18n (Uzbek Latin/Cyrillic + Russian).
- Add payment/subscription gates.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run_api.py
python run_bot.py
```
