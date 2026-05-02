# Azure Practice 3: Local Apps Connected to Azure SQL and Service Bus Queue

This repository contains a Python implementation of the **Online Science Tutoring System** for the assignment **"Local apps with API to connect to DB"**, extended with Azure Service Bus communication between two local apps.

The project consists of three local FastAPI services:

- `session_service`
- `tutor_service`
- `feedback_service`

Each service runs locally, reads data from a real **Azure SQL Database**, and two of the apps now communicate through an **Azure Service Bus queue**.

## Project Scope

The system is split into three business domains:

- `SessionService` manages students and tutoring sessions
- `TutorService` manages tutors, subjects, and availability
- `FeedbackService` manages feedback, processed feedback records, and feedback event logs

## Service Bus Flow

- `SessionService` publishes a `feedback.requested` message when a completed tutoring session is explicitly triggered through an API call
- `FeedbackService` runs a background polling worker that reads queue messages at a configurable interval
- After reading a message, `FeedbackService` writes a record to `feedback_event_log` and marks the session in `processed_session_feedback`

The database is organized with a separate schema for each service:

- `session_service`
- `tutor_service`
- `feedback_service`

## Tech Stack

- Python 3
- FastAPI
- Uvicorn
- pyodbc
- Azure SQL Database

## Project Structure

```text
.
|-- feedback_service/
|   `-- main.py
|-- scripts/
|   `-- init_db.py
|-- session_service/
|   `-- main.py
|-- shared/
|   `-- db.py
|-- sql/
|   |-- 01_create_schemas.sql
|   |-- 02_create_tables.sql
|   `-- 03_seed_data.sql
|-- tutor_service/
|   `-- main.py
|-- .env.example
|-- requirements.txt
`-- README.md
```

## Database Design

### `session_service`

- `students`
- `sessions`

### `tutor_service`

- `tutors`
- `subjects`
- `tutor_subjects`
- `tutor_availability`

### `feedback_service`

- `feedback`
- `feedback_event_log`
- `processed_session_feedback`

The SQL scripts create schemas, tables, foreign keys, indexes, and stub data.

## Environment Configuration

Create a local `.env` file based on `.env.example`.

Primary configuration format used in this project:

```env
DB_SERVER=your-server.database.windows.net
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password

SERVICE_BUS_SEND_CONNECTION_STRING=Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=send;SharedAccessKey=your-send-key;EntityPath=your-queue-name
SERVICE_BUS_LISTEN_CONNECTION_STRING=Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=listen;SharedAccessKey=your-listen-key;EntityPath=your-queue-name
SERVICE_BUS_POLL_INTERVAL_SECONDS=15

ODBC_DRIVER=ODBC Driver 18 for SQL Server
DB_PORT=1433
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERTIFICATE=no
DB_CONNECTION_TIMEOUT=30
```

Notes:

- The app supports both `DB_*` variables and a full `AZURE_SQL_CONNECTION_STRING`
- The database layer automatically tries to use an available SQL Server ODBC driver
- On the current machine, the project successfully worked with the installed SQL Server ODBC driver
- The Service Bus sender and listener use separate connection strings, as required by the assignment

## Installation

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Initialize Azure SQL Database

Run the database initialization script:

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
```

This script executes:

1. `sql/01_create_schemas.sql`
2. `sql/02_create_tables.sql`
3. `sql/03_seed_data.sql`

## Run the Services

Start each service in a separate terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn session_service.main:app --reload --port 8001
.\.venv\Scripts\python.exe -m uvicorn tutor_service.main:app --reload --port 8002
.\.venv\Scripts\python.exe -m uvicorn feedback_service.main:app --reload --port 8003
```

When `feedback_service` starts, it automatically launches a background queue consumer. The polling interval is controlled by `SERVICE_BUS_POLL_INTERVAL_SECONDS`.

## API Overview

### SessionService

Base URL: `http://127.0.0.1:8001`

- `GET /health`
- `GET /api/sessions/{session_id}`
- `GET /api/sessions/byStatus/{status}`
- `GET /api/sessions/byTutor/{tutor_id}`
- `GET /api/sessions/byStudent/{student_id}`
- `POST /api/sessions/{session_id}/feedback-request`
- `GET /api/students`
- `GET /api/students/{student_id}`

### TutorService

Base URL: `http://127.0.0.1:8002`

- `GET /health`
- `GET /api/tutors/{tutor_id}`
- `GET /api/tutors/bySubject/{subject}`
- `GET /api/tutors/{tutor_id}/availability`
- `GET /api/tutors/{tutor_id}/subjects`
- `GET /api/subjects`
- `GET /api/subjects/{subject_id}`

### FeedbackService

Base URL: `http://127.0.0.1:8003`

- `GET /health`
- `GET /api/feedback/{feedback_id}`
- `GET /api/feedback/bySession/{session_id}`
- `GET /api/feedback/byTutor/{tutor_id}`
- `GET /api/feedback/events`
- `GET /api/feedback/events/{event_id}`
- `GET /api/feedback/processed`
- `GET /api/feedback/processed/{session_id}`

## Swagger UI

Each service exposes interactive API documentation:

- `http://127.0.0.1:8001/docs`
- `http://127.0.0.1:8002/docs`
- `http://127.0.0.1:8003/docs`

## Seed Data

The database is populated with stub data for:

- students
- tutors
- subjects
- tutor-subject assignments
- tutor availability
- sessions
- feedback
- feedback event logs
- processed feedback records

This allows the APIs to return real data immediately after database initialization.

## Current Status

The project currently supports the assignment requirement for:

- local applications
- connection to a real Azure SQL Database
- communication between two local apps through an Azure Service Bus queue
- trigger-based queue publishing from `SessionService`
- background queue polling in `FeedbackService`
- separate schemas per service
- tables and relationships based on the domain model
- stub data
- read APIs for the corresponding service data
- queue-driven feedback processing records

## Demo Scenario

Use the seeded completed session:

- `55555555-5555-5555-5555-555555555555`

Trigger message publishing:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8001/api/sessions/55555555-5555-5555-5555-555555555555/feedback-request
```

Then verify processing:

```powershell
Invoke-RestMethod http://127.0.0.1:8003/api/feedback/events
Invoke-RestMethod http://127.0.0.1:8003/api/feedback/processed
```

## Notes

- `GET /favicon.ico` returning `404` in the browser is expected and not an application error
- `GET /` returning `404` is also expected because the services expose API routes, not a homepage
- Health checks are available through `/health`
