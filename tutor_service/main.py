from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.db import fetch_all, fetch_one, healthcheck, install_database_error_handler

app = FastAPI(title="TutorService", version="1.0.0")
install_database_error_handler(app)


@app.get("/health")
def get_health() -> dict[str, str]:
    if not healthcheck():
        raise HTTPException(status_code=503, detail="DB unavailable")
    return {"status": "ok"}


@app.get("/api/tutors/{tutor_id}")
def get_tutor_by_id(tutor_id: str) -> dict:
    query = """
    SELECT
        t.tutor_id,
        t.full_name,
        t.email,
        t.bio,
        t.rating_avg,
        t.created_at
    FROM tutor_service.tutors AS t
    WHERE t.tutor_id = ?
    """
    row = fetch_one(query, (tutor_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return row


@app.get("/api/tutors/bySubject/{subject}")
def get_tutors_by_subject(subject: str) -> list[dict]:
    query = """
    SELECT
        t.tutor_id,
        t.full_name,
        t.email,
        t.bio,
        t.rating_avg,
        t.created_at,
        s.subject_id,
        s.name AS subject_name,
        ts.hourly_rate
    FROM tutor_service.tutors AS t
    INNER JOIN tutor_service.tutor_subjects AS ts ON ts.tutor_id = t.tutor_id
    INNER JOIN tutor_service.subjects AS s ON s.subject_id = ts.subject_id
    WHERE LOWER(s.name) = LOWER(?)
    ORDER BY t.rating_avg DESC
    """
    return fetch_all(query, (subject,))


@app.get("/api/tutors/{tutor_id}/availability")
def get_tutor_availability(tutor_id: str) -> list[dict]:
    query = """
    SELECT
        ta.availability_id,
        ta.tutor_id,
        ta.available_from,
        ta.available_to,
        ta.is_booked
    FROM tutor_service.tutor_availability AS ta
    WHERE ta.tutor_id = ?
    ORDER BY ta.available_from
    """
    return fetch_all(query, (tutor_id,))


@app.get("/api/tutors/{tutor_id}/subjects")
def get_tutor_subjects(tutor_id: str) -> list[dict]:
    query = """
    SELECT
        s.subject_id,
        s.name,
        s.category,
        ts.hourly_rate
    FROM tutor_service.tutor_subjects AS ts
    INNER JOIN tutor_service.subjects AS s ON s.subject_id = ts.subject_id
    WHERE ts.tutor_id = ?
    ORDER BY s.name
    """
    return fetch_all(query, (tutor_id,))


@app.get("/api/subjects")
def get_subjects() -> list[dict]:
    query = """
    SELECT
        s.subject_id,
        s.name,
        s.category
    FROM tutor_service.subjects AS s
    ORDER BY s.name
    """
    return fetch_all(query)


@app.get("/api/subjects/{subject_id}")
def get_subject_by_id(subject_id: str) -> dict:
    query = """
    SELECT
        s.subject_id,
        s.name,
        s.category
    FROM tutor_service.subjects AS s
    WHERE s.subject_id = ?
    """
    row = fetch_one(query, (subject_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return row
