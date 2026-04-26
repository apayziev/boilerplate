import random

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User

fake = Faker()

# Username uniqueness across many fake users
_seq = 0


def _next_username() -> str:
    global _seq
    _seq += 1
    return f"u{_seq:08d}"


def fake_uz_phone() -> str:
    """Generate an `+998` E.164 phone with 9 random digits — unique enough for test fixtures."""
    return "+998" + "".join(str(random.randint(0, 9)) for _ in range(9))


async def create_user(
    db: AsyncSession,
    is_superuser: bool = False,
    password: str | None = None,
    phone: str | None = None,
) -> User:
    user = User(
        name=fake.name()[:30],
        username=_next_username(),
        phone=phone or fake_uz_phone(),
        hashed_password=get_password_hash(password or fake.password()),
        profile_image_url=fake.image_url(),
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
