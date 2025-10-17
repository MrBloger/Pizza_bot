from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            try:
                async with session.begin():  # Автоматически начнёт и завершит транзакцию
                    data["session"] = session
                    return await handler(event, data)
            except Exception:
                await session.rollback()
                raise


class ConfigMiddleware(BaseMiddleware):
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["admin_ids"] = self.config.bot.admin_ids
        return await handler(event, data)