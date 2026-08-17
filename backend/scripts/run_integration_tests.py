from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://elite_test:elite_test@localhost:5433/elite_test"
)


def run(command: list[str], environment: dict[str, str]) -> None:
    subprocess.run(
        command,
        cwd=BACKEND_DIRECTORY,
        env=environment,
        check=True,
    )


def main() -> None:
    database_url = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    database_name = make_url(database_url).database or ""
    if "test" not in database_name.lower():
        raise SystemExit(
            "TEST_DATABASE_URL deve apontar para um banco isolado cujo nome contenha 'test'."
        )

    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    environment["RUN_INTEGRATION_TESTS"] = "1"

    python = sys.executable
    run([python, "-m", "alembic", "downgrade", "base"], environment)
    run([python, "-m", "alembic", "upgrade", "head"], environment)
    run([python, "-m", "app.database.seed"], environment)
    run([python, "-m", "pytest", "-m", "integration", "-q"], environment)


if __name__ == "__main__":
    main()
