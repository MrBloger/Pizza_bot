import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode

from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores.fluent_runtime_core import FluentRuntimeCore

from aiogram.client.default import DefaultBotProperties

from app.bot.middleware import (DbSessionMiddleware, LangSettingsMiddleware,
                                ConfigMiddleware, ActivityCounterMiddleware,
                                BanCheckMiddleware)

from .handlers.user import user_router
from .handlers.admin import admin_router
from .handlers.others import router

from app.infrastructure.database.engine import create_engine, get_session_maker, init_models

from config.config import load_config


# Инициализируем логгер
logger = logging.getLogger(__name__)


async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='{filename}:{lineno} #{levelname:8} '
                '[{asctime}] - {name} - {message}',
        style='{'
    )
    
    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    config = load_config()
    
    storage = config.redis.get_redis_storage()
    
    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=storage)
    
    
    i18n_middleware = I18nMiddleware(
        core=FluentRuntimeCore(path="locales/{locale}"),
        default_locale="ru"
    )
    
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(router)
    
    i18n_middleware.setup(dispatcher=dp)
    
    me = await bot.get_me()
    print('Started')
    print(me.username)
    
    await init_models()
    
    async_engine = create_engine()
    session_maker = get_session_maker(async_engine)
    
    dp.update.middleware(DbSessionMiddleware(session_pool=session_maker))
    dp.update.middleware(LangSettingsMiddleware())
    dp.update.middleware(ConfigMiddleware(config))
    dp.update.middleware(ActivityCounterMiddleware())
    dp.update.middleware(BanCheckMiddleware())

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")