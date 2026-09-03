# Linked Project Management


### Intelligent Data Capture & Schedule-Linking Layer for Infrastructure Project Management

**SIH 2026 — Problem Statement 26122**
**Oil India Limited**

ProjectBridge is a planning-to-execution bridge for infrastructure project management. It is designed to connect structured project schedules with actual execution information collected from site reports and other field-level sources.

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

ProjectBridge provides an intelligent workflow that connects planning data with execution data.

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

## 🚀 Core Features

### 1. Project Management

Create and manage infrastructure projects with information such as:

* Project name
* Location
* Project type
* Start date
* Finish date
* Overall progress
* Project status

### 2. Schedule Import

Planned for upcoming milestones:

* Import project schedule data
* Extract WBS and activity information
* Store activities in Firestore
* Maintain activity-level schedule information

### 3. Progress Report Processing

The system will process execution reports such as:

* DPRs
* Site progress reports
* Excel reports
* PDF documents

Relevant execution information will be extracted for further processing.

### 4. AI Activity Matching

The system will use semantic similarity to match execution descriptions with scheduled activities.

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

### 5. Progress Tracking

The system will compare:

* Planned progress
* Actual progress
* Activity status
* Delayed activities
* At-risk activities

### 6. Execution Intelligence

The final system will provide project teams with a clearer view of what is happening at the execution level and how it differs from the baseline plan.

---

## 🏗️ System Architecture

```text
┌───────────────────────────────┐
│       ProjectBridge UI        │
│      HTML / CSS / JavaScript  │
└───────────────┬───────────────┘
                │
                │ REST API
                ▼
┌───────────────────────────────┐
│          FastAPI              │
│        Python Backend         │
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

### Data Flow

```text
Planning Data
     ↓
Schedule Parser
     ↓
Activities
     ↓
Firestore
     ↑
Progress Reports
     ↓
Report Parser
     ↓
Event Extraction
     ↓
AI Activity Matcher
     ↓
Human Verification
     ↓
Progress Engine
```

---

## 🛠️ Technology Stack

| Layer                      | Technology                                 |
| -------------------------- | ------------------------------------------ |
| Frontend                   | HTML, CSS, Vanilla JavaScript              |
| Backend                    | Python, FastAPI                            |
| Database                   | Firebase Firestore                         |
| Authentication             | Firebase / planned integration             |
| Document Processing        | PyMuPDF, Pandas, OpenPyXL                  |
| AI / NLP                   | Sentence Transformers, semantic similarity |
| Machine Learning Utilities | Scikit-learn                               |
| Hosting                    | Firebase Hosting / planned                 |
| Backend Deployment         | To be finalized                            |

---

## 📁 Project Structure

```text
ProjectBridge/
│
├── README.md
│
├── backend/
│   ├── README.md
│   ├── .env.example
│   ├── .gitignore
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database/
│   │   ├── models/
│   │   ├── routes/
│   │   └── services/
│   ├── tests/
│   └── uploads/
│
└── frontend/
    ├── README.md
    ├── index.html
    ├── css/
    │   └── styles.css
    └── js/
        └── app.js
```

---

# 🔥 Firebase / Firestore

ProjectBridge uses Firestore as the primary database for project and execution-related structured data.

The architecture follows:

```text
Frontend
   ↓
FastAPI
   ↓
Firestore
```

The frontend does **not** directly access Firestore for the current architecture.

Sensitive Firebase service-account credentials must remain on the backend and must never be committed to GitHub.

---

## 🔐 Security

Never commit the following to GitHub:

```text
.env
serviceAccountKey.json
Firebase service-account credentials
Private API keys
Other secret credentials
```

The repository contains `.env.example` as a safe configuration template.

Each developer should configure their own local `.env`.

---

# 📊 Firestore Data Model

The planned Firestore structure includes:

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

```text
project_id
activity_code
wbs_code
activity_name
discipline
planned_start
planned_finish
actual_start
actual_finish
planned_progress
actual_progress
status
```

### Progress Events

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

### Milestone 1 — Foundation ✅

* FastAPI backend
* Frontend foundation
* Health check
* Project structure
* Development environment

### Milestone 2 — Firestore + Project CRUD ✅

* Firestore connection
* Project model
* Project CRUD API
* Projects frontend integration

### Milestone 3 — Schedule Import

* Schedule file upload
* Schedule parsing
* WBS extraction
* Activity extraction
* Activity storage

### Milestone 4 — Progress Report Processing

* DPR/report upload
* PDF/Excel processing
* Execution information extraction
* Progress event generation

### Milestone 5 — AI Activity Matching

* Semantic embeddings
* Activity similarity matching
* Confidence scoring
* Human verification workflow

### Milestone 6 — Progress & Delay Intelligence

* Planned vs actual comparison
* Delay identification
* At-risk activities
* Progress dashboard
* Execution analytics

---

# 👥 Team Development

The repository is divided into independent frontend and backend components.

### Frontend Developer

Works primarily inside:

```text
frontend/
```

### Backend Developer

Works primarily inside:

```text
backend/
```

### AI / Data Processing

AI and document-processing services will be integrated into:

```text
backend/app/services/
```

---

# 🧪 Current Status

**Current milestone: Milestone 2 — Firestore + Project CRUD**

Currently implemented:

* ProjectBridge frontend
* FastAPI backend
* Firestore connection
* Project model
* Project CRUD API
* Frontend-to-FastAPI project integration
* Create, update, view, and delete project functionality

The schedule-processing and AI activity-matching components are planned for subsequent milestones.

---

## 🎯 Long-Term Goal

ProjectBridge aims to provide a practical bridge between **project planning and field execution**.

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

The final objective is to provide project teams with faster, more reliable visibility into actual project progress and emerging execution delays.
