"""Declarative base and shared metadata for SQLAlchemy models.

All ORM models inherit from ``Base``. Alembic (see ``alembic/env.py``)
imports ``Base.metadata`` to autogenerate migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all ORM models.

    Uses SQLAlchemy 2.0 style (``DeclarativeBase``) with type-annotated
    columns. Subclasses declare columns as class-level annotations.
    """
