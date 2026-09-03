# Linked Project Management Backend

Python/FastAPI backend for **ProjectBridge — SIH 2026 Problem Statement 26122**.

The backend provides REST APIs for project management and acts as the secure communication layer between the frontend and Firebase Firestore.

---

## 🏗️ Architecture

```text
Frontend
   │
   │ HTTP REST API
   ▼
FastAPI Backend
   │
   ├── Project Services
   ├── Schedule Processing
   ├── Report Processing
   ├── AI Matching
   └── Progress Engine
   │
   ▼
Firebase Firestore
```

The frontend never directly connects to Firestore.

---

# 🛠️ Technology

* Python 3.11
* FastAPI
* Uvicorn
* Firebase Firestore
* Google Cloud Firestore SDK
* Pydantic
* Pandas
* OpenPyXL
* PyMuPDF
* Sentence Transformers
* Scikit-learn
* NumPy
* Pytest

---

# 📁 Backend Structure

```text
backend/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── database/
│   │   └── firestore.py
│   │
│   ├── models/
│   │   └── project.py
│   │
│   ├── routes/
│   │   ├── health.py
│   │   └── projects.py
│   │
│   └── services/
│       └── project_service.py
│
├── tests/
│   ├── test_health.py
│   └── test_projects.py
│
└── uploads/
    ├── schedules/
    └── reports/
```

---

# ⚙️ Setup

## 1. Create the virtual environment

Python 3.11 is recommended.

```powershell
py -3.11 -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

# 🔥 Firebase / Firestore Configuration

The backend requires access to the Firebase project.

Create a Firebase service-account key and store it **locally**.

Do not commit the JSON credential file to GitHub.

---

## 3. Create `.env`

Copy:

```text
.env.example
```

to:

```text
.env
```

Example:

```env
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/serviceAccountKey.json
GOOGLE_CLOUD_PROJECT=linked-project-management
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
ENV=development
```

### Important

`.env` is local configuration.

It should **never** be committed to GitHub.

The service-account JSON file must also remain outside version control.

---

# ▶️ Run the Backend

From the `backend` directory:

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/api/health
```

---

# 📡 API Endpoints

## Health

```http
GET /api/health
```

Used to verify that the backend is running.

---

## Projects

### List projects

```http
GET /api/projects
```

### Get a project

```http
GET /api/projects/{project_id}
```

### Create a project

```http
POST /api/projects
```

### Update a project

```http
PATCH /api/projects/{project_id}
```

### Delete a project

```http
DELETE /api/projects/{project_id}
```

---

# 📦 Project Model

A project currently contains:

```text
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

Supported project statuses:

```text
planned
active
on_hold
completed
```

Progress must be between:

```text
0 – 100
```

---

# 🔥 Firestore Collection

Projects are stored in:

```text
projects
```

Example document:

```json
{
  "name": "Pipeline Expansion Project",
  "location": "Assam",
  "project_type": "Pipeline",
  "start_date": "2026-01-01",
  "finish_date": "2027-12-31",
  "overall_progress": 35,
  "status": "active"
}
```

---

# 🧪 Testing

Run all backend tests:

```powershell
python -m pytest -q
```

Compile-check the application:

```powershell
python -m compileall -q app tests
```

---

# 🌐 CORS

The development frontend runs on:

```text
http://localhost:5500
http://127.0.0.1:5500
```

These origins are configured through:

```env
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

If the frontend port changes, update the environment configuration.

---

# 🔐 Security

Never commit:

```text
.env
*.json service-account files
API keys
Private credentials
```

The repository should contain:

```text
.env.example
```

instead of the actual `.env`.

---

# 🛣️ Backend Roadmap

### Completed

* FastAPI foundation
* Health endpoint
* Firestore integration
* Project model
* Project CRUD

### Next

* Schedule parser
* Schedule activity model
* Schedule upload API
* DPR/report parser
* Progress event extraction
* Semantic activity matching
* Confidence scoring
* Human verification
* Progress calculation
* Delay analysis

---

## 📌 Current Status

**Milestone 2 — Firestore + Project CRUD**

The backend is currently focused on establishing the database foundation and project management APIs.

Future milestones will add schedule and execution intelligence capabilities.
