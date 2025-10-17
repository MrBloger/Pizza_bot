from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Update
from aiogram_i18n.context import I18nContext
from app.bot.keyboards.callback_factory import LanguageAction, LanguageActionCall


class LangSettingsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        callback: CallbackQuery | None = event.callback_query
        if not callback or not callback.data:
            return await handler(event, data)

        try:
            call_data = LanguageActionCall.unpack(callback.data)
        except Exception:
            # Не удалось распарсить — значит, это не LanguageActionCall
            return await handler(event, data)

        # Проверяем, что это именно выбор языка
        if call_data.action == LanguageAction.select_lang:
            lang_code = call_data.language
            i18n: I18nContext = data.get("i18n")
            if i18n:
                await i18n.set_locale(lang_code)

        return await handler(event, data)