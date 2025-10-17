from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Awaitable, Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.crud.user_crud import get_user_by_user_id


class BanCheckMiddleware(BaseMiddleware):
    """Middleware, блокирующее действия забаненных пользователей."""

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any]
    ) -> Any:
        session: AsyncSession = data.get("session")
        user = data.get("event_from_user")

        # если апдейт не от пользователя — просто пропускаем (например callback от чата)
        if not user or not session:
            return await handler(event, data)

        db_user = await get_user_by_user_id(session=session, user_id=user.id)
        if db_user and db_user.banned:
            # Пытаемся ответить пользователю, если это сообщение
            try:
                if hasattr(event, "message") and event.message:
                    await event.message.answer("🚫 Вы заблокированы и не можете пользоваться ботом.")
                elif hasattr(event, "callback_query") and event.callback_query:
                    await event.callback_query.answer("🚫 Вы заблокированы!", show_alert=True)
            except Exception:
                pass

            return  # Прерываем цепочку (хэндлер не будет вызван)

        # Пользователь не забанен — пропускаем дальше
        return await handler(event, data)