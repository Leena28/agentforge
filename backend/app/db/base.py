import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass