from aiogram_i18n import I18nMiddleware
from aiogram_i18n.managers import BaseManager
from aiogram_i18n.cores import FluentRuntimeCore
from pathlib import Path
import redis.asyncio as redis

# Подключение к Redis
redis_client = redis.from_url("redis://localhost", decode_responses=True)

# Путь до .ftl переводов
LOCALES_PATH = Path(__file__).parent.parent.parent / "locales"

# Менеджер выбора языка
class RedisManager(BaseManager):
    async def get_locale(self, event, data) -> str:
        user_id = getattr(event.from_user, "id", None)
        if user_id is None:
            return "ru"
        lang = await redis_client.get(f"user_lang:{user_id}")
        return lang if lang else "ru"
    async def set_locale(self, event, locale: str, data) -> None:
        user_id = getattr(event.from_user, "id", None)
        if user_id is not None:
            await redis_client.set(f"user_lang:{user_id}", locale)


# Создаём FluentRuntimeCore
core = FluentRuntimeCore(
    path=LOCALES_PATH,
    default_locale="ru",
)

# Создаём I18nMiddleware с кастомным core и менеджером
i18n = I18nMiddleware(
    core=core,
    manager=RedisManager()
)