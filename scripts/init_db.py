from __future__ import annotations

import re
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from shared.db import get_connection


def split_batches(sql_text: str) -> list[str]:
    batches = re.split(r"(?im)^\s*GO\s*$", sql_text)
    return [batch.strip() for batch in batches if batch.strip()]


def run_sql_file(path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    batches = split_batches(sql_text)

    with get_connection() as connection:
        cursor = connection.cursor()
        for batch in batches:
            cursor.execute(batch)
        connection.commit()


def main() -> None:
    sql_dir = BASE_DIR / "sql"
    scripts = sorted(sql_dir.glob("*.sql"))

    if not scripts:
        raise FileNotFoundError(f"No SQL scripts found in {sql_dir}")

    for script in scripts:
        print(f"Running {script.name} ...")
        run_sql_file(script)

    print("Database initialization completed.")


if __name__ == "__main__":
    main()
