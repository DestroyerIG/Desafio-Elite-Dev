from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


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


async def recreate_schema(database_url: str) -> None:
    """Descarta e recria o schema `public` da base de teste.

    `alembic downgrade base` não serve como reset: o downgrade de `20260816_0002`
    recria a constraint única de `payments.reservation_id`, e os próprios cenários
    integrados registram várias tentativas de pagamento na mesma reserva. Com dados
    residuais da execução anterior o downgrade falha e a suíte só roda em uma base
    recém-criada. Descartar o schema remove tabelas, dados e `alembic_version` de
    uma vez, então a execução é repetível.
    """
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()


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

    asyncio.run(recreate_schema(database_url))

    python = sys.executable
    run([python, "-m", "alembic", "upgrade", "head"], environment)
    run([python, "-m", "app.database.seed"], environment)
    run([python, "-m", "pytest", "-m", "integration", "-q"], environment)


if __name__ == "__main__":
    main()
