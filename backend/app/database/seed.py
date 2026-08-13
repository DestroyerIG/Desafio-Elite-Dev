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


SEED_USERS = (
    SeedUser("Organizador Elite", "organizer@elite.local", UserRole.ORGANIZER),
    SeedUser("Cliente Um", "customer1@elite.local", UserRole.CUSTOMER),
    SeedUser("Cliente Dois", "customer2@elite.local", UserRole.CUSTOMER),
    SeedUser("Portaria Elite", "gate@elite.local", UserRole.GATE),
)


async def seed_users() -> int:
    settings = get_settings()
    created = 0

    async with async_session_factory() as session:
        existing_emails = set((await session.scalars(select(User.email))).all())
        for seed_user in SEED_USERS:
            if seed_user.email in existing_emails:
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

    return created


async def main() -> None:
    try:
        created = await seed_users()
        print(f"Seed concluído: {created} usuário(s) criado(s).")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

