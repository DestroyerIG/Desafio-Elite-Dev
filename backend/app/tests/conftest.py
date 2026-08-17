import os

import pytest
from sqlalchemy.engine import make_url


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        return

    database_url = os.getenv("DATABASE_URL", "")
    database_name = make_url(database_url).database if database_url else None
    if not database_name or "test" not in database_name.lower():
        raise pytest.UsageError(
            "A suíte integrada só pode executar em um banco cujo nome contenha 'test'. "
            "Configure DATABASE_URL para a base isolada antes de definir "
            "RUN_INTEGRATION_TESTS=1."
        )
