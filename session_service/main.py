from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status

from shared.db import fetch_all, fetch_one, healthcheck, install_database_error_handler
from shared.service_bus import (
    ServiceBusConfigurationError,
    ServiceBusOperationError,
    get_send_connection_string,
    publish_json_message,
)

app = FastAPI(title="SessionService", version="1.0.0")
install_database_error_handler(app)


@app.get("/health")
def get_health() -> dict[str, str]:
    if not healthcheck():
        raise HTTPException(status_code=503, detail="DB unavailable")
    return {"status": "ok"}


@app.get("/api/sessions/{session_id}")
def get_session_by_id(session_id: str) -> dict:
    row = _get_session_row(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


def _get_session_row(session_id: str) -> dict | None:
    query = """
    SELECT
        s.session_id,
        s.student_id,
        s.tutor_id,
        s.subject_id,
        s.scheduled_start,
        s.scheduled_end,
        s.status,
        s.notes,
        s.created_at
    FROM session_service.sessions AS s
    WHERE s.session_id = ?
    """
    return fetch_one(query, (session_id,))


@app.get("/api/sessions/byStatus/{status}")
def get_sessions_by_status(status: str) -> list[dict]:
    query = """
    SELECT
        s.session_id,
        s.student_id,
        s.tutor_id,
        s.subject_id,
        s.scheduled_start,
        s.scheduled_end,
        s.status,
        s.notes,
        s.created_at
    FROM session_service.sessions AS s
    WHERE s.status = ?
    ORDER BY s.scheduled_start
    """
    return fetch_all(query, (status,))


@app.get("/api/sessions/byTutor/{tutor_id}")
def get_sessions_by_tutor(tutor_id: str) -> list[dict]:
    query = """
    SELECT
        s.session_id,
        s.student_id,
        s.tutor_id,
        s.subject_id,
        s.scheduled_start,
        s.scheduled_end,
        s.status,
        s.notes,
        s.created_at
    FROM session_service.sessions AS s
    WHERE s.tutor_id = ?
    ORDER BY s.scheduled_start
    """
    return fetch_all(query, (tutor_id,))


@app.get("/api/sessions/byStudent/{student_id}")
def get_sessions_by_student(student_id: str) -> list[dict]:
    query = """
    SELECT
        s.session_id,
        s.student_id,
        s.tutor_id,
        s.subject_id,
        s.scheduled_start,
        s.scheduled_end,
        s.status,
        s.notes,
        s.created_at
    FROM session_service.sessions AS s
    WHERE s.student_id = ?
    ORDER BY s.scheduled_start
    """
    return fetch_all(query, (student_id,))


@app.post("/api/sessions/{session_id}/feedback-request", status_code=status.HTTP_202_ACCEPTED)
def publish_feedback_request(session_id: str) -> dict[str, str]:
    session = _get_session_row(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Only completed sessions can be sent to the feedback queue",
        )

    event_id = str(uuid4())
    payload = {
        "event_id": event_id,
        "event_type": "feedback.requested",
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "session_id": session["session_id"],
        "student_id": session["student_id"],
        "tutor_id": session["tutor_id"],
        "subject_id": session["subject_id"],
        "scheduled_end": session["scheduled_end"],
        "status": session["status"],
        "notes": session["notes"],
    }

    try:
        publish_json_message(
            connection_string=get_send_connection_string(),
            payload=payload,
            message_id=event_id,
            subject="feedback.requested",
        )
    except (ServiceBusConfigurationError, ServiceBusOperationError) as exc:
        raise HTTPException(status_code=503, detail="Service Bus unavailable") from exc

    return {
        "status": "queued",
        "event_id": event_id,
        "session_id": session_id,
    }


@app.get("/api/students")
def get_students() -> list[dict]:
    query = """
    SELECT
        s.student_id,
        s.full_name,
        s.email,
        s.created_at
    FROM session_service.students AS s
    ORDER BY s.full_name
    """
    return fetch_all(query)


@app.get("/api/students/{student_id}")
def get_student_by_id(student_id: str) -> dict:
    query = """
    SELECT
        s.student_id,
        s.full_name,
        s.email,
        s.created_at
    FROM session_service.students AS s
    WHERE s.student_id = ?
    """
    row = fetch_one(query, (student_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return row
