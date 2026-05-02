from __future__ import annotations

import json
import os
from typing import Any

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from dotenv import load_dotenv

load_dotenv()


class ServiceBusConfigurationError(RuntimeError):
    pass


class ServiceBusOperationError(RuntimeError):
    pass


def _parse_connection_string(connection_string: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for chunk in connection_string.split(";"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        parsed[key.strip().lower()] = value.strip()
    return parsed


def get_queue_name_from_connection_string(connection_string: str) -> str:
    queue_name = _parse_connection_string(connection_string).get("entitypath", "").strip()
    if not queue_name:
        raise ServiceBusConfigurationError("Service Bus connection string does not contain EntityPath")
    return queue_name


def get_send_connection_string() -> str:
    connection_string = os.getenv("SERVICE_BUS_SEND_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise ServiceBusConfigurationError("SERVICE_BUS_SEND_CONNECTION_STRING is not set")
    return connection_string


def get_listen_connection_string() -> str:
    connection_string = os.getenv("SERVICE_BUS_LISTEN_CONNECTION_STRING", "").strip()
    if not connection_string:
        raise ServiceBusConfigurationError("SERVICE_BUS_LISTEN_CONNECTION_STRING is not set")
    return connection_string


def get_poll_interval_seconds() -> int:
    raw_value = os.getenv("SERVICE_BUS_POLL_INTERVAL_SECONDS", "15").strip()
    try:
        poll_interval = int(raw_value)
    except ValueError as exc:
        raise ServiceBusConfigurationError("SERVICE_BUS_POLL_INTERVAL_SECONDS must be an integer") from exc

    if poll_interval <= 0:
        raise ServiceBusConfigurationError("SERVICE_BUS_POLL_INTERVAL_SECONDS must be greater than zero")
    return poll_interval


def publish_json_message(
    *,
    connection_string: str,
    payload: dict[str, Any],
    message_id: str,
    subject: str,
) -> None:
    queue_name = get_queue_name_from_connection_string(connection_string)
    message_body = json.dumps(payload)
    message = ServiceBusMessage(
        message_body,
        content_type="application/json",
        message_id=message_id,
        subject=subject,
    )

    try:
        with ServiceBusClient.from_connection_string(connection_string) as client:
            with client.get_queue_sender(queue_name=queue_name) as sender:
                sender.send_messages(message)
    except Exception as exc:
        raise ServiceBusOperationError("Failed to send message to Azure Service Bus queue") from exc
