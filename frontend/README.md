# Linked Project Management Frontend — Milestone 2

Vanilla HTML/CSS/JS frontend for SIH 26122. Milestone 2 connects the Projects page to the FastAPI Project CRUD API.

## Run

From this folder:

```powershell
python -m http.server 5500
```

Open `http://localhost:5500/`.

Backend should run at `http://localhost:8000`.

## Projects page

The Projects page now:
- loads projects with `GET /api/projects`
- creates projects with `POST /api/projects`
- edits name/progress with `PATCH /api/projects/{id}`
- deletes projects with `DELETE /api/projects/{id}`

The browser never talks directly to Firestore. It talks to FastAPI, and FastAPI talks to Firestore.
