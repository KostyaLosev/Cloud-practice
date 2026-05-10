from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

import pyodbc
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

load_dotenv()


class DatabaseError(RuntimeError):
    pass


def get_available_odbc_drivers() -> list[str]:
    try:
        return [driver.strip() for driver in pyodbc.drivers() if driver.strip()]
    except Exception:
        return []


def resolve_odbc_driver() -> str:
    requested_driver = os.getenv("ODBC_DRIVER", "").strip()
    available_drivers = get_available_odbc_drivers()

    if requested_driver and requested_driver in available_drivers:
        return requested_driver

    for driver in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]:
        if driver in available_drivers:
            return driver

    if requested_driver:
        return requested_driver

    raise DatabaseError("No compatible SQL Server ODBC driver found")


def normalize_server_name(raw_server: str) -> str:
    server = raw_server.strip()
    if server.lower().startswith("tcp:"):
        server = server[4:]
    return server


def get_connection_string() -> str:
    conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING", "").strip()
    if conn_str:
        return conn_str

    db_server = os.getenv("DB_SERVER", "").strip()
    db_database = os.getenv("DB_DATABASE", "").strip()
    db_username = os.getenv("DB_USERNAME", "").strip()
    db_password = os.getenv("DB_PASSWORD", "").strip()
    odbc_driver = resolve_odbc_driver()
    db_port = os.getenv("DB_PORT", "1433").strip()
    encrypt = os.getenv("DB_ENCRYPT", "yes").strip()
    trust_server_certificate = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "no").strip()
    connection_timeout = os.getenv("DB_CONNECTION_TIMEOUT", "30").strip()

    if not all([db_server, db_database, db_username, db_password]):
        raise DatabaseError(
            "AZURE_SQL_CONNECTION_STRING is not set and DB_SERVER/DB_DATABASE/DB_USERNAME/DB_PASSWORD are incomplete"
        )

    server_name = normalize_server_name(db_server)
    if "," not in server_name and db_port:
        server_name = f"{server_name},{db_port}"

    if odbc_driver == "SQL Server":
        return (
            f"Driver={{{odbc_driver}}};"
            f"Server={server_name};"
            f"Database={db_database};"
            f"Uid={db_username};"
            f"Pwd={db_password};"
            f"Network=DBMSSOCN;"
            f"Connection Timeout={connection_timeout};"
        )

    return (
        f"Driver={{{odbc_driver}}};"
        f"Server=tcp:{server_name};"
        f"Database={db_database};"
        f"Uid={db_username};"
        f"Pwd={db_password};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_server_certificate};"
        f"Connection Timeout={connection_timeout};"
    )


@contextmanager
def get_connection() -> pyodbc.Connection:
    try:
        connection = pyodbc.connect(get_connection_string())
    except (pyodbc.Error, DatabaseError) as exc:
        raise DatabaseError("Failed to connect to Azure SQL Database") from exc

    try:
        yield connection
    finally:
        connection.close()


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
    except (pyodbc.Error, DatabaseError) as exc:
        raise DatabaseError("Database query failed") from exc

    result: list[dict[str, Any]] = []
    for row in rows:
        row_dict = {columns[index]: _normalize_value(value) for index, value in enumerate(row)}
        result.append(row_dict)
    return result


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    if not rows:
        return None
    return rows[0]


def execute_non_query(query: str, params: tuple[Any, ...] = ()) -> int:
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params)
            rowcount = cursor.rowcount
            connection.commit()
    except (pyodbc.Error, DatabaseError) as exc:
        raise DatabaseError("Database command failed") from exc

    return rowcount


def healthcheck() -> bool:
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 AS ok")
            row = cursor.fetchone()
        return bool(row and row[0] == 1)
    except DatabaseError:
        return False


def install_database_error_handler(app: FastAPI) -> None:
    @app.exception_handler(DatabaseError)
    async def handle_database_error(_: Request, __: DatabaseError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "DB unavailable"})
