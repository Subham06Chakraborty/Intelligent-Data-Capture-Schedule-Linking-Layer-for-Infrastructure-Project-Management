# Linked Project Management — Backend — Phase 3

FastAPI + Firestore backend for SIH 26122. Phase 3 adds baseline schedule import and activity management on top of the Project CRUD functionality from Phase 2.

## 1. Requirements

Use **Python 3.11** for this project.

```powershell
py -3.11 -m venv venv

.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -r requirements.txt
```

## 2. Firebase / Firestore setup

1. Create or open your Firebase project in the Firebase Console.

2. Enable **Cloud Firestore** (production/test mode as appropriate for development).

3. In Google Cloud/Firebase, create a service account with permission to access Firestore.

4. Download its JSON key **outside Git tracking**. Never upload it to GitHub.

5. Copy `.env.example` to `.env` and set:

```text
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/service-account.json

GOOGLE_CLOUD_PROJECT=your-firebase-project-id

ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

ENV=development
```

You can alternatively use Google Application Default Credentials and leave `GOOGLE_APPLICATION_CREDENTIALS` blank.

## 3. Run

From the `backend/` directory:

```powershell
uvicorn app.main:app --reload --port 8000
```

Open:

* `http://localhost:8000/docs`
* `http://localhost:8000/api/health`

## 4. Project CRUD endpoints

* `GET /api/projects` — list projects
* `GET /api/projects/{project_id}` — get one project
* `POST /api/projects` — create project
* `PATCH /api/projects/{project_id}` — update project
* `DELETE /api/projects/{project_id}` — delete project

Example POST body:

```json
{
  "name": "North-East Gas Pipeline Expansion",
  "location": "Assam",
  "project_type": "Pipeline & Compression",
  "start_date": "2026-01-01",
  "finish_date": "2027-12-31",
  "overall_progress": 67.4,
  "status": "active"
}
```

## 5. Firestore structure

```text
projects/{projectId}

  name
  location
  project_type
  start_date
  finish_date
  overall_progress
  status
  created_at
  updated_at
```

Dates are stored as ISO date strings and returned in ISO format by the API. This keeps the prototype simple and portable; we can switch to Firestore Timestamp fields later if needed.

## 6. Tests

```powershell
python -m pytest -q
```

The CRUD service is isolated so API validation can be tested without requiring live Firestore credentials.

## 7. Phase 3 — Schedule Import & Activity Management

The backend now supports importing baseline schedule files and storing normalized activities in Firestore.

### Supported schedule files

* CSV
* XLSX
* XLS

The schedule parser accepts common Primavera/MS Project-style column names and normalizes them into the application's activity model.

### Schedule import endpoints

* `POST /api/projects/{project_id}/schedule/import` — import a schedule file
* `GET /api/projects/{project_id}/schedule/activities` — list imported activities

### Activity processing

During import, the backend:

* Validates required activity information.
* Normalizes activity IDs and names/descriptions.
* Extracts WBS information.
* Processes discipline and contractor information.
* Normalizes planned start and finish dates.
* Normalizes planned progress values.
* Stores activities under the corresponding project.
* Reports imported and skipped records.

Imported activities are stored in the `activities` Firestore collection and are scoped to a project.

Deterministic activity document IDs are used so repeated imports of the same activity update the existing record instead of creating duplicate activity documents.

### Activity data

The normalized activity model includes fields such as:

```text
activity_id
activity_name
activity_desc
wbs_code
wbs_level
discipline
contractor
region
planned_start
planned_end
planned_progress
project_id
```

### Upload limit

The prototype supports a maximum schedule file size of **10 MB** per upload.

## 8. Phase 3 Status

Phase 3 is **complete**.

The backend currently provides:

* FastAPI application
* Firestore integration
* Project CRUD
* Baseline schedule import
* CSV/XLSX/XLS parsing
* Schedule validation and normalization
* Activity storage in Firestore
* Project-scoped activity retrieval
* Duplicate-safe activity re-import
* REST APIs for frontend schedule management
* Automated tests for health, project validation/service behavior, and schedule parsing

Current automated test result:

```text
6 passed, 1 warning
```

The warning is a dependency-related deprecation warning and does not indicate a test failure.

## 9. Next Phase

The next backend work will support **Phase 4 — Progress Report Processing**, including progress-report file handling, extraction of actual progress information, and preparation of data for activity matching.
