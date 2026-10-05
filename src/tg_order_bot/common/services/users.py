"""User-related service functions.

Provides get-or-create semantics for Telegram users interacting with
the bot, so other domains can rely on ``users.id`` being available.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tg_order_bot.database.models.user import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str,
) -> User:
    """Return the User row for ``telegram_id``, creating it if missing.

    On every call, the stored ``username`` and ``full_name`` are
    refreshed from the values passed in (Telegram users can change
    either at any time).

    The session is flushed after insertion so ``user.id`` is populated
    even before the surrounding transaction is committed.
    """
    stmt = select(User).where(User.telegram_id == telegram_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
        )
        session.add(user)
        await session.flush()
        return user

    # Refresh mutable fields in case they changed in Telegram.
    if user.username != username:
        user.username = username
    if user.full_name != full_name:
        user.full_name = full_name

    return user


__all__ = ["get_or_create_user"]
