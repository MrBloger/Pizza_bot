from aiogram.filters.callback_data import CallbackData
from enum import Enum


class StartAction(str, Enum):
    open_language = "open_language"

class StartActionCall(CallbackData, prefix="start"):
    action: str

class SaveAction(str, Enum):
    save_lang = "save_lang"

class SaveActionCall(CallbackData, prefix="save"):
    action: str

class LanguageAction(str, Enum):
    select_lang = "select_lang"
    save_lang = "save_lang"
    cancel = "cancel"

class LanguageActionCall(CallbackData, prefix="language"):
    action: LanguageAction
    language: str = ""


class HomeAction(str, Enum):
    menu = "menu"
    cart = "cart"
    orders = "orders"
    settings = "settings"
    support = "support"

class HomeActionCall(CallbackData, prefix="home"):
    action: HomeAction


class CartAction(str, Enum):
    add = "add"
    cansel = "cansel"
    go_to_cart = "go_to_cart"
    clear = "clear"
    confirm_order = "confirm"
    remove_item = "remove_item"
    update_quantity = "update_quantity"
    clear_cart = "clear_cart"
    decrease = "decrease"
    increase = "increase"
    start_payment = "start_payment"

class CartActionCall(CallbackData, prefix="cart"):
    action: CartAction
    item_id: int | None = None
    quantity: int | None = None