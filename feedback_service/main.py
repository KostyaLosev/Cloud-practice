from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.db import fetch_all, fetch_one, healthcheck, install_database_error_handler

app = FastAPI(title="FeedbackService", version="1.0.0")
install_database_error_handler(app)


@app.get("/health")
def get_health() -> dict[str, str]:
    if not healthcheck():
        raise HTTPException(status_code=503, detail="DB unavailable")
    return {"status": "ok"}


@app.get("/api/feedback/events")
def get_feedback_events() -> list[dict]:
    query = """
    SELECT
        el.event_id,
        el.session_id,
        el.received_at,
        el.processing_status,
        el.error_message
    FROM feedback_service.feedback_event_log AS el
    ORDER BY el.received_at DESC
    """
    return fetch_all(query)


@app.get("/api/feedback/events/{event_id}")
def get_feedback_event_by_id(event_id: str) -> dict:
    query = """
    SELECT
        el.event_id,
        el.session_id,
        el.received_at,
        el.processing_status,
        el.error_message
    FROM feedback_service.feedback_event_log AS el
    WHERE el.event_id = ?
    """
    row = fetch_one(query, (event_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Feedback event not found")
    return row


@app.get("/api/feedback/processed")
def get_processed_feedback_sessions() -> list[dict]:
    query = """
    SELECT
        psf.session_id,
        psf.processed_at,
        psf.source_event_id
    FROM feedback_service.processed_session_feedback AS psf
    ORDER BY psf.processed_at DESC
    """
    return fetch_all(query)


@app.get("/api/feedback/processed/{session_id}")
def get_processed_feedback_session_by_id(session_id: str) -> dict:
    query = """
    SELECT
        psf.session_id,
        psf.processed_at,
        psf.source_event_id
    FROM feedback_service.processed_session_feedback AS psf
    WHERE psf.session_id = ?
    """
    row = fetch_one(query, (session_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Processed feedback session not found")
    return row


@app.get("/api/feedback/{feedback_id}")
def get_feedback_by_id(feedback_id: str) -> dict:
    query = """
    SELECT
        f.feedback_id,
        f.session_id,
        f.student_id,
        f.tutor_id,
        f.rating,
        f.comment,
        f.created_at
    FROM feedback_service.feedback AS f
    WHERE f.feedback_id = ?
    """
    row = fetch_one(query, (feedback_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return row


@app.get("/api/feedback/bySession/{session_id}")
def get_feedback_by_session(session_id: str) -> list[dict]:
    query = """
    SELECT
        f.feedback_id,
        f.session_id,
        f.student_id,
        f.tutor_id,
        f.rating,
        f.comment,
        f.created_at
    FROM feedback_service.feedback AS f
    WHERE f.session_id = ?
    ORDER BY f.created_at DESC
    """
    return fetch_all(query, (session_id,))


@app.get("/api/feedback/byTutor/{tutor_id}")
def get_feedback_by_tutor(tutor_id: str) -> list[dict]:
    query = """
    SELECT
        f.feedback_id,
        f.session_id,
        f.student_id,
        f.tutor_id,
        f.rating,
        f.comment,
        f.created_at
    FROM feedback_service.feedback AS f
    WHERE f.tutor_id = ?
    ORDER BY f.created_at DESC
    """
    return fetch_all(query, (tutor_id,))
