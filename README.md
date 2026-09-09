# Linked Project Management

### Intelligent Data Capture & Schedule-Linking Layer for Infrastructure Project Management

**SIH 2026 — Problem Statement 26122**
**Organization:** Oil India Limited

Linked Project Management is a planning-to-execution bridge for infrastructure project management. It is designed to connect structured project schedules with actual execution information collected from site reports and other field-level sources.

The system aims to reduce the gap between what is **planned** in Primavera P6/MS Project and what is actually **executed** at the project site.

---

## 🎯 Problem Statement

Infrastructure project schedules typically cascade from high-level milestones (L1/L2) down to detailed executable activities (L5/L6). These activities span multiple disciplines such as:

* Civil
* Piping
* Static Equipment
* Rotating Equipment
* Electrical
* Instrumentation
* HSE

Although the baseline schedule may be well structured, actual execution information is often scattered across:

* Daily Progress Reports (DPRs)
* Site diaries
* Excel sheets
* PDF reports
* Emails
* Chat messages
* Verbal updates
* Site photographs

This makes it difficult for project teams to continuously connect actual field progress with the original project schedule.

---

## 💡 Proposed Solution

Linked Project Management provides an intelligent workflow that connects planning data with execution data.

```text
Project Schedule
       ↓
Schedule Import
       ↓
Structured Activities
       ↓
Progress Report / DPR
       ↓
Information Extraction
       ↓
AI Activity Matching
       ↓
Human Verification
       ↓
Actual Progress Update
       ↓
Planned vs Actual Analysis
       ↓
Delay & Risk Intelligence
```

The system is designed to keep a **human verification step** between AI-generated activity matches and actual schedule updates.

---

# 🚀 Core Features

## 1. Project Management

Users can create and manage infrastructure projects with information such as:

* Project name
* Location
* Project type
* Start date
* Finish date
* Overall progress
* Project status

Project information is stored in Firestore through the FastAPI backend.

---

## 2. Schedule Import

The current system supports importing baseline project schedules.

Supported file formats:

* CSV
* XLSX
* XLS

The schedule processing layer:

* Accepts uploaded schedule files
* Validates required schedule fields
* Extracts activity information
* Extracts WBS information
* Normalizes different schedule formats
* Stores activities in Firestore
* Associates activities with the selected project
* Supports activity retrieval
* Prevents duplicate activity records during re-import using deterministic activity IDs

The normalized activity structure includes information such as:

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
```

---

## 3. Schedule Import Interface

The frontend currently provides a dedicated **Schedule Import** page.

The interface supports:

* Selecting a project
* Selecting a schedule file
* Drag-and-drop file upload
* Importing the schedule
* Displaying import results
* Viewing imported activities

The frontend communicates with the FastAPI backend using REST APIs.

The architecture remains:

```text
Frontend
    ↓
FastAPI REST API
    ↓
Firestore
```

---

## 4. Imported Activity Management

Imported schedule activities are stored in the Firestore `activities` collection.

Activities are associated with their project through `project_id`.

The system uses a deterministic activity identifier based on the project and activity ID:

```text
project_id + activity_id
```

This allows the same schedule to be imported again without unnecessarily creating duplicate activity records.

---

## 5. Progress Report Processing

The system is planned to process execution reports such as:

* DPRs
* Site progress reports
* Excel reports
* PDF documents

Relevant execution information will be extracted for further processing.

This functionality is part of a future development phase.

---

## 6. AI Activity Matching

The planned AI layer will use semantic similarity to match execution descriptions with scheduled activities.

Example:

```text
Schedule Activity:

"Installation of 24-inch pipeline section"

Site Report:

"24 inch pipeline installation completed in Section B"

                    ↓

            AI Activity Matching

                    ↓

Matched Activity

Confidence: 94%
```

The planned matching system will use techniques such as:

* Text embeddings
* Semantic similarity
* Cosine similarity
* Confidence scoring

The AI matching layer is not yet fully integrated into the current prototype.

---

## 7. Progress Tracking

The final system will compare:

* Planned progress
* Actual progress
* Activity status
* Delayed activities
* At-risk activities

The current prototype already stores planned activity progress and project-level progress. Actual execution progress and delay intelligence will be developed in later phases.

---

## 8. Execution Intelligence

The final system will provide project teams with a clearer view of what is happening at the execution level and how it differs from the baseline plan.

The intended workflow is:

```text
Planning
   ↓
Execution Data
   ↓
Activity Matching
   ↓
Verification
   ↓
Progress Update
   ↓
Project Intelligence
```

---

# 🏗️ System Architecture

```text
┌───────────────────────────────┐
│   Linked Project Management   │
│          Frontend             │
│     HTML / CSS / JavaScript   │
└───────────────┬───────────────┘
                │
                │ REST API
                ▼
┌───────────────────────────────┐
│          FastAPI              │
│       Python Backend          │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌──────────────────┐
│  Firestore   │  │ AI / Processing  │
│   Database   │  │     Services     │
└──────────────┘  └──────────────────┘
```

### Current Architecture

The currently implemented data flow is:

```text
Frontend
    ↓
FastAPI
    ↓
Firestore
```

For schedule processing:

```text
Schedule File
      ↓
FastAPI
      ↓
Schedule Parser
      ↓
Normalized Activities
      ↓
Activity Service
      ↓
Firestore
      ↓
Frontend
```

The AI and execution-processing components will be connected in later phases.

---

# 🛠️ Technology Stack

| Layer                      | Technology                                          |
| -------------------------- | --------------------------------------------------- |
| Frontend                   | HTML, CSS, Vanilla JavaScript                       |
| Backend                    | Python, FastAPI                                     |
| Database                   | Firebase Firestore                                  |
| Authentication             | Firebase service-account authentication for backend |
| Schedule Processing        | Pandas, OpenPyXL, xlrd                              |
| Document Processing        | PyMuPDF                                             |
| AI / NLP                   | Sentence Transformers, semantic similarity          |
| Machine Learning Utilities | Scikit-learn                                        |
| API Server                 | Uvicorn                                             |
| Frontend Hosting           | Firebase Hosting / planned                          |
| Backend Deployment         | To be finalized                                     |

---

# 📁 Project Structure

```text
Linked Project Management/
│
├── README.md
│
├── backend/
│   ├── README.md
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── database/
│   │   │   └── firestore.py
│   │   │
│   │   ├── models/
│   │   │   ├── project.py
│   │   │   └── schedule.py
│   │   │
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── projects.py
│   │   │   └── schedules.py
│   │   │
│   │   └── services/
│   │       ├── firestore_service.py
│   │       ├── project_service.py
│   │       ├── schedule_parser.py
│   │       └── activity_service.py
│   │
│   ├── sample-data/
│   │   └── sample_schedule.csv
│   │
│   ├── tests/
│   │   ├── test_health.py
│   │   ├── test_projects.py
│   │   └── test_schedule_parser.py
│   │
│   └── uploads/
│       ├── schedules/
│       └── reports/
│
├── frontend/
│   ├── README.md
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
│
└── docs/
    ├── 01_Project_Overview.md
    ├── 02_Problem_Statement_and_Requirements.md
    ├── 03_Solution_and_Architecture.md
    ├── 04_Technology_Stack.md
    ├── 05_Development_Progress.md
    ├── 06_Database_and_Firestore_Schema.md
    ├── 07_API_Documentation.md
    ├── 08_Project_Structure.md
    ├── 09_Features_and_Roadmap.md
    ├── 10_Setup_and_Running_Guide.md
    ├── 11_Security_and_Team_Handoff.md
    └── README.md
```

---

# 🔥 Firebase / Firestore

Linked Project Management uses **Firebase Firestore** as the primary database for structured project and schedule information.

The current architecture follows:

```text
Frontend
   ↓
FastAPI
   ↓
Firestore
```

The frontend does **not** directly access Firestore.

The backend handles database operations and keeps Firebase service-account credentials away from the frontend.

---

# 📊 Firestore Data Model

The current prototype uses the following main collections:

```text
projects/
    {projectId}

activities/
    {activityId}
```

Additional collections are planned for execution processing.

The broader planned structure is:

```text
projects/
    {projectId}

activities/
    {activityId}

progress_reports/
    {reportId}

progress_events/
    {eventId}
```

### Projects

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

### Activities

Current schedule activities contain normalized information such as:

```text
project_id
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
```

Future activity fields may include:

```text
actual_start
actual_finish
actual_progress
status
```

### Future Progress Events

The planned progress-event structure includes:

```text
report_id
activity_id
extracted_activity
event_type
progress
event_date
confidence
ai_reasoning
verification_status
```

---

# 🛣️ Development Roadmap

## Phase 1 — Foundation ✅

Completed:

* FastAPI backend
* Frontend foundation
* Health check
* Project structure
* Development environment
* Basic testing setup

---

## Phase 2 — Firestore + Project Management ✅

Completed:

* Firestore connection
* Project model
* Project CRUD API
* Projects frontend integration
* Create project
* View project
* Update project
* Delete project
* Real project data connection

---

## Phase 3 — Baseline Schedule & Activity Management ✅

Completed:

* Schedule file upload
* CSV schedule parsing
* XLSX schedule parsing
* XLS schedule parsing
* Schedule validation
* WBS information extraction
* Activity extraction
* Activity normalization
* Activity storage
* Project-activity association
* Deterministic activity IDs
* Duplicate-safe schedule re-import
* Schedule Import frontend
* Drag-and-drop upload
* Imported Activities view
* Real schedule data displayed through the application

### Phase 3 Testing

Backend automated tests currently pass:

```text
6 passed
1 warning
```

The tests cover:

* Health endpoint
* Root endpoint
* Project validation
* Project listing/service
* Schedule CSV normalization
* Missing required schedule column validation

The live frontend workflow is also being tested using a synthetic Oil & Gas EPC schedule.

---

## Phase 4 — Progress Report Processing

Planned:

* DPR/report upload
* PDF processing
* Excel report processing
* Execution information extraction
* Progress event generation
* Actual progress extraction

---

## Phase 5 — AI Activity Matching

Planned:

* Semantic embeddings
* Activity similarity matching
* Confidence scoring
* Candidate activity ranking
* Human verification workflow
* Matching audit trail

---

## Phase 6 — Progress & Delay Intelligence

Planned:

* Planned vs actual comparison
* Delay identification
* At-risk activities
* Progress dashboard
* Execution analytics
* Project performance indicators

---

# 👥 Team Development

The repository is divided into independent frontend, backend, and data/AI components.

### Frontend Development

Primary directory:

```text
frontend/
```

Responsible for:

* User interface
* Dashboard
* Project management interface
* Schedule Import interface
* Activity display
* Future progress-tracking interfaces

### Backend Development

Primary directory:

```text
backend/
```

Responsible for:

* REST APIs
* Firestore operations
* Project management
* Schedule processing
* Activity management
* Future report processing
* Future AI integration

### AI / Data Processing

Primary integration location:

```text
backend/app/services/
```

Additional Databricks-related work is being developed separately and will be integrated into the main system later.

---

# 🧪 Current Status

## Current Phase: Phase 3 — Baseline Schedule & Activity Management ✅

Currently implemented:

* Linked Project Management frontend
* FastAPI backend
* Firestore connection
* Project management
* Project CRUD API
* Frontend-to-FastAPI integration
* Schedule file upload
* CSV/XLSX/XLS schedule processing
* Schedule validation
* Activity extraction
* Activity normalization
* Activity storage
* Activity retrieval
* Schedule Import interface
* Imported Activities interface
* Real project and schedule data
* Automated backend tests

### Current Test Project

For application testing, the current synthetic project is:

```text
ABCD Gas Compression & Utility Expansion Project
```

Example project type:

```text
Oil & Gas EPC
```

The schedule data used for testing is synthetic and is intended only to simulate a realistic infrastructure project schedule.

---

# 🔄 Current End-to-End Workflow

The currently working schedule workflow is:

```text
Create Project
      ↓
Select Project
      ↓
Upload Schedule
      ↓
Schedule Parser
      ↓
Validate & Normalize
      ↓
Extract Activities
      ↓
Store in Firestore
      ↓
Retrieve Activities
      ↓
Display in Frontend
      ↓
Dashboard
```

The future execution workflow will extend this:

```text
Baseline Schedule
       ↓
Progress Report / DPR
       ↓
Information Extraction
       ↓
AI Activity Matching
       ↓
Human Verification
       ↓
Actual Progress Update
       ↓
Planned vs Actual
       ↓
Delay & Risk Intelligence
```

---

# 🔐 Security

Never commit the following to GitHub:

```text
.env
Firebase service-account JSON
serviceAccountKey.json
Private API keys
Passwords
Other secret credentials
```

The repository contains `.env.example` as a safe configuration template.

Each developer should configure their own local `.env`.

Firebase service-account credentials must remain on the backend and must never be exposed through the frontend.

---

# 🎯 Long-Term Goal

Linked Project Management aims to provide a practical bridge between **project planning and field execution**.

Instead of requiring project teams to manually reconcile schedule data with daily execution reports, the system will progressively automate:

```text
Plan
  ↓
Capture
  ↓
Understand
  ↓
Match
  ↓
Verify
  ↓
Update
  ↓
Analyze
```

The final objective is to provide project teams with faster and more reliable visibility into actual project progress, schedule deviations, and emerging execution delays.
