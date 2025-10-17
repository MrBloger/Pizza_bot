from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.callback_factory import (
    CartAction, CartActionCall, LanguageActionCall, LanguageAction, StartActionCall, StartAction,
    SaveActionCall, SaveAction,
    HomeActionCall, HomeAction
)
from aiogram_i18n import I18nContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Самая начальная клавиатура с кнопкой "Начать"
# после отправления команды "/start"
def start_kb(i18n: I18nContext, username: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.button(
        text=i18n("start_button", username=username),
        callback_data=StartActionCall(action=StartAction.open_language).pack()
    )
    kb_builder.adjust(1)
    return kb_builder.as_markup()



def get_lang_settings_kb(i18n: I18nContext, locales: list[str], checked: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    # Ты сам вставляешь флаг прямо в текст — словарь flags НЕ нужен
    for locale in ["ru", "en"]:
        icon = "🔘" if locale == checked else "⚪️"
        flag = "🇷🇺" if locale == "ru" else "🇺🇸"
        kb_builder.button(
            text=f"{icon} {flag} {i18n.get(locale)}",
            callback_data=LanguageActionCall(
                action=LanguageAction.select_lang,
                language=locale
            ).pack()
        )
    kb_builder.button(
        text=f"{i18n.get('cancel_button')}",
        callback_data=LanguageActionCall(action=LanguageAction.cancel).pack()
    )
    kb_builder.button(
        text=f"{i18n.get('save_button')}",
        callback_data=SaveActionCall(action=SaveAction.save_lang).pack()
    )

    kb_builder.adjust(1, 1, 2)
    return kb_builder.as_markup()


def home_kb(i18n: I18nContext) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    kb_builder.button(text=i18n.get("menu_button"),
                        callback_data=HomeActionCall(action=HomeAction.menu).pack())
    kb_builder.button(text=i18n.get("cart_button"),
                        callback_data=HomeActionCall(action=HomeAction.cart).pack())
    kb_builder.button(text=i18n.get("orders_button"),
                        callback_data=HomeActionCall(action=HomeAction.orders).pack())
    kb_builder.button(text=i18n.get("settings_button"),
                        callback_data=HomeActionCall(action=HomeAction.settings).pack())
    kb_builder.button(text=i18n.get("support_button"),
                        callback_data=HomeActionCall(action=HomeAction.support).pack())

    # Расположение: 2 кнопки в строке
    kb_builder.adjust(2)


    return kb_builder.as_markup()


def get_menu_item_kb(i18n: I18nContext, item_id: int) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    
    kb_builder.button(
        text=i18n.get("cansel_action"),
        callback_data=CartActionCall(action=CartAction.cansel, item_id=item_id).pack())
    kb_builder.button(
        text=i18n.get("add_to_cart"),
        callback_data=CartActionCall(action=CartAction.add, item_id=item_id).pack())
    kb_builder.button(
        text=i18n.get("go_to_cart"),
        callback_data=CartActionCall(action=CartAction.go_to_cart, item_id=item_id).pack())
    
    kb_builder.adjust(2)
    
    
    return kb_builder.as_markup()


def cart_kb(i18n: I18nContext) -> InlineKeyboardMarkup:
    """Создаёт интерактивную клавиатуру для корзины"""
    kb_builder = InlineKeyboardBuilder()
    
    kb_builder.button(
        text=i18n.get("menu_button"),
        callback_data=HomeActionCall(action=HomeAction.menu).pack()
        )
    
    # Кнопки управления корзиной
    kb_builder.button(
        text=i18n.get("clear_cart"),
        callback_data=CartActionCall(action=CartAction.clear_cart).pack()
    )
    
    kb_builder.button(
        text=i18n.get("order_confirm"),
        callback_data=CartActionCall(action=CartAction.confirm_order).pack()
    )
    
    kb_builder.adjust(2)
    
    return kb_builder.as_markup()


def confirm_kb(i18n: I18nContext) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    
    kb_builder.button(
        text=i18n.get("confirm_order_button"),
        callback_data=CartActionCall(action=CartAction.confirm_order).pack()
    )
    return kb_builder.as_markup()

def prepayment_kb(i18n: I18nContext) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    
    kb_builder.button(
        text=i18n.get("start_payment"),
        callback_data=CartActionCall(action=CartAction.start_payment).pack()
    )
    return kb_builder.as_markup()