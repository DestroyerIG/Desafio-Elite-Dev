import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import async_session_factory, engine
from app.models.enums import UserRole
from app.models.user import User


@dataclass(frozen=True)
class SeedUser:
    name: str
    email: str
    role: UserRole
    legacy_email: str | None = None


SEED_USERS = (
    SeedUser(
        "Organizador Elite",
        "organizer@example.com",
        UserRole.ORGANIZER,
        "organizer@elite.local",
    ),
    SeedUser(
        "Cliente Um",
        "customer1@example.com",
        UserRole.CUSTOMER,
        "customer1@elite.local",
    ),
    SeedUser(
        "Cliente Dois",
        "customer2@example.com",
        UserRole.CUSTOMER,
        "customer2@elite.local",
    ),
    SeedUser(
        "Portaria Elite",
        "gate@example.com",
        UserRole.GATE,
        "gate@elite.local",
    ),
)


async def seed_users() -> tuple[int, int]:
    settings = get_settings()
    created = 0
    updated = 0

    async with async_session_factory() as session:
        existing_users = {
            user.email: user for user in (await session.scalars(select(User))).all()
        }
        for seed_user in SEED_USERS:
            if seed_user.email in existing_users:
                continue

            legacy_user = existing_users.get(seed_user.legacy_email or "")
            if legacy_user is not None:
                legacy_user.email = seed_user.email
                updated += 1
                continue

            session.add(
                User(
                    name=seed_user.name,
                    email=seed_user.email,
                    password_hash=hash_password(settings.seed_password),
                    role=seed_user.role,
                )
            )
            created += 1
        await session.commit()

    return created, updated


async def main() -> None:
    try:
        created, updated = await seed_users()
        print(
            "Seed concluído: "
            f"{created} usuário(s) criado(s), {updated} atualizado(s)."
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
