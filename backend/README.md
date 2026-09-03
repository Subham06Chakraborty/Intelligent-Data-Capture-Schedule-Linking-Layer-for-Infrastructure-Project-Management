# SIH 26122 — FastAPI Backend

Intelligent Data Capture & Schedule-Linking Layer for Infrastructure Project
Management — backend prototype.

This README currently covers **Milestone 1**: project skeleton, health
endpoint, and local dev setup. More sections will be added as later
milestones (Firestore, schedule parsing, DPR parsing, matching, etc.) are
built.

## Requirements

- Python 3.11+
- Windows, macOS, or Linux

## 1. Create and activate a virtual environment

**Windows (PowerShell / cmd):**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Note: `sentence-transformers` and its dependencies (torch etc.) are a
> larger download. Milestone 1 doesn't use them yet, but they're listed
> in `requirements.txt` now so the environment is ready for later
> milestones without reinstalling.

## 3. Set up environment variables

Copy the example file and edit it:

```bash
copy .env.example .env        # Windows
cp .env.example .env          # macOS/Linux
```

For Milestone 1 you don't need real Firestore credentials yet — the
defaults are fine. `.env` is listed in `.gitignore` and must never be
committed to GitHub, since later it will contain paths to real credentials.

## 4. Run the server

From inside the `backend/` folder:

```bash
uvicorn app.main:app --reload --port 8000
```

You should see log output ending with something like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 5. Test it

**In your browser:**

- Root: http://localhost:8000 → shows a small JSON welcome message
- Swagger UI: http://localhost:8000/docs → interactive API docs. Expand
  `GET /api/health` and click "Try it out" → "Execute".
- Health check directly: http://localhost:8000/api/health → should return:

```json
{
  "status": "ok",
  "service": "SIH 26122 FastAPI Backend"
}
```

**With curl:**

```bash
curl http://localhost:8000/api/health
```

## 6. Run tests

```bash
pytest
```

## Project structure (Milestone 1)

```
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, router registration
│   ├── config.py          # Loads settings from .env
│   ├── routes/
│   │   └── health.py      # GET /api/health
│   ├── services/          # (empty for now — business logic goes here later)
│   ├── models/            # (empty for now — Pydantic schemas go here later)
│   └── database/          # (empty for now — Firestore client goes here later)
├── uploads/
│   ├── schedules/         # uploaded schedule files land here (dev only)
│   └── reports/           # uploaded DPR/report files land here (dev only)
├── tests/
│   └── test_health.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Security notes

- Never commit `.env` or any Firebase/Google service-account `.json` key
  file to GitHub. `.gitignore` already excludes these.
- CORS is currently restricted to `http://localhost:5500` and
  `http://127.0.0.1:5500` (the frontend's dev address), configurable via
  `ALLOWED_ORIGINS` in `.env`. Do not change this to `"*"` outside of
  quick local experiments.

## What's next

Milestone 2 will add Firestore integration and Project CRUD endpoints.
