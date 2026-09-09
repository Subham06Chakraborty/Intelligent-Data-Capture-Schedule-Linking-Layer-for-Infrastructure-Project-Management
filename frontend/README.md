# Linked Project Management — Frontend — Phase 3

Vanilla HTML/CSS/JS frontend for SIH 26122. Phase 3 connects the frontend to the FastAPI backend for project management and baseline schedule/activity management.

## Run

From this folder:

```powershell
python -m http.server 5500
```

Open `http://localhost:5500/`.

Backend should run at `http://localhost:8000`.

## Projects page

The Projects page is connected to the FastAPI Project CRUD API.

Current behavior:

* Loads projects with `GET /api/projects`
* Creates projects with `POST /api/projects`
* Edits project name/progress with `PATCH /api/projects/{id}`
* Deletes projects with `DELETE /api/projects/{id}`

The browser never talks directly to Firestore. It communicates with FastAPI, and FastAPI communicates with Firestore.

## Phase 3 — Schedule Import

The Schedule Import page is connected to the FastAPI backend.

Current behavior:

* Select an existing project.
* Choose or drag-and-drop a CSV/XLSX/XLS schedule.
* Import the schedule through the REST API.
* Validate and normalize schedule activities.
* See import counts and parser notes.
* View imported activities for the selected project.
* Display imported activity details such as Activity ID, activity name, WBS, discipline, contractor, dates, and planned progress.

The frontend never connects directly to Firestore; it communicates with FastAPI.

## Phase 3 Status

**Completed**

The frontend currently supports:

* Project CRUD
* Project selection for schedule import
* Schedule file upload
* CSV/XLSX/XLS support
* Schedule import
* Import summary
* Imported activity viewing
* Real project and schedule data from the backend
* Dashboard data based on backend data instead of hard-coded demo data

## Next Phase

The next frontend work will support **Phase 4 — Progress Report Processing**, including the UI required for uploading and processing progress reports.
