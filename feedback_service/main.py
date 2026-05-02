from __future__ import annotations

import json
import logging
import threading
from typing import Any

from azure.servicebus import ServiceBusClient
from fastapi import FastAPI, HTTPException

from shared.db import execute_non_query, fetch_all, fetch_one, healthcheck, install_database_error_handler
from shared.service_bus import (
    ServiceBusConfigurationError,
    get_listen_connection_string,
    get_poll_interval_seconds,
    get_queue_name_from_connection_string,
)

app = FastAPI(title="FeedbackService", version="1.0.0")
install_database_error_handler(app)
logger = logging.getLogger(__name__)


class FeedbackQueueConsumer:
    def __init__(self) -> None:
        self.connection_string = get_listen_connection_string()
        self.queue_name = get_queue_name_from_connection_string(self.connection_string)
        self.poll_interval_seconds = get_poll_interval_seconds()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="feedback-queue-consumer", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=self.poll_interval_seconds + 5)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._poll_once()
            except Exception:
                logger.exception("Unexpected error while polling Azure Service Bus")

            self._stop_event.wait(self.poll_interval_seconds)

    def _poll_once(self) -> None:
        with ServiceBusClient.from_connection_string(self.connection_string) as client:
            with client.get_queue_receiver(queue_name=self.queue_name, max_wait_time=5) as receiver:
                messages = receiver.receive_messages(max_message_count=10, max_wait_time=5)

                for message in messages:
                    payload: dict[str, Any] | None = None
                    try:
                        payload = json.loads(_decode_message_body(message))
                        _process_feedback_event(payload)
                        receiver.complete_message(message)
                    except Exception as exc:
                        logger.exception("Failed to process feedback message")
                        if payload is not None:
                            try:
                                _mark_event_sent_to_dlq(
                                    event_id=str(payload.get("event_id", "")),
                                    session_id=str(payload.get("session_id", "")),
                                    error_message=str(exc),
                                )
                            except Exception:
                                logger.exception("Failed to persist sent_to_dlq status")
                        receiver.dead_letter_message(
                            message,
                            reason="Feedback processing failed",
                            error_description=str(exc),
                        )


consumer: FeedbackQueueConsumer | None = None


@app.get("/health")
def get_health() -> dict[str, str]:
    if not healthcheck():
        raise HTTPException(status_code=503, detail="DB unavailable")
    return {"status": "ok"}


@app.on_event("startup")
def start_background_consumer() -> None:
    global consumer

    try:
        consumer = FeedbackQueueConsumer()
    except ServiceBusConfigurationError as exc:
        logger.warning("Feedback queue consumer is disabled: %s", exc)
        consumer = None
        return

    consumer.start()
    logger.info("Feedback queue consumer started for queue %s", consumer.queue_name)


@app.on_event("shutdown")
def stop_background_consumer() -> None:
    if consumer is not None:
        consumer.stop()
        logger.info("Feedback queue consumer stopped")


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


def _decode_message_body(message: Any) -> str:
    return b"".join(bytes(chunk) for chunk in message.body).decode("utf-8")


def _process_feedback_event(payload: dict[str, Any]) -> None:
    event_id = str(payload["event_id"])
    session_id = str(payload["session_id"])

    execute_non_query(
        """
        IF NOT EXISTS (
            SELECT 1
            FROM feedback_service.feedback_event_log
            WHERE event_id = ?
        )
        BEGIN
            INSERT INTO feedback_service.feedback_event_log (
                event_id,
                session_id,
                processing_status,
                error_message
            )
            VALUES (?, ?, 'received', NULL)
        END
        """,
        (event_id, event_id, session_id),
    )

    execute_non_query(
        """
        IF NOT EXISTS (
            SELECT 1
            FROM feedback_service.processed_session_feedback
            WHERE session_id = ?
        )
        BEGIN
            INSERT INTO feedback_service.processed_session_feedback (
                session_id,
                source_event_id
            )
            VALUES (?, ?)
        END
        """,
        (session_id, session_id, event_id),
    )

    execute_non_query(
        """
        UPDATE feedback_service.feedback_event_log
        SET processing_status = 'processed',
            error_message = NULL
        WHERE event_id = ?
        """,
        (event_id,),
    )


def _mark_event_sent_to_dlq(event_id: str, session_id: str, error_message: str) -> None:
    if not event_id or not session_id:
        return

    execute_non_query(
        """
        IF EXISTS (
            SELECT 1
            FROM feedback_service.feedback_event_log
            WHERE event_id = ?
        )
        BEGIN
            UPDATE feedback_service.feedback_event_log
            SET processing_status = 'sent_to_dlq',
                error_message = ?
            WHERE event_id = ?
        END
        ELSE
        BEGIN
            INSERT INTO feedback_service.feedback_event_log (
                event_id,
                session_id,
                processing_status,
                error_message
            )
            VALUES (?, ?, 'sent_to_dlq', ?)
        END
        """,
        (event_id, error_message, event_id, event_id, session_id, error_message),
    )
