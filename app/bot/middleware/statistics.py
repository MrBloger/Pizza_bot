import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update, User
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.crud.admin_crud import add_user_activity

logger = logging.getLogger(__name__)


class ActivityCounterMiddleware(BaseMiddleware):
    """Middleware для подсчёта активности пользователей."""

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        user: User = data.get("event_from_user")

        # если апдейт без пользователя (например, channel_post)
        if user is None:
            return await handler(event, data)

        result = await handler(event, data)

        # достаём SQLAlchemy-сессию
        session: AsyncSession = data.get("session")
        if session is None:
            logger.error("No SQLAlchemy session found in middleware data.")
            raise RuntimeError("Missing AsyncSession for activity logging.")

        # записываем активность
        try:
            await add_user_activity(session, user_id=user.id)
        except Exception as e:
            logger.error(f"Failed to log user activity: {e}")
            await session.rollback()
        else:
            await session.commit()

        return result
