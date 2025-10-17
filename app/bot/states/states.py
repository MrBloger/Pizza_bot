from aiogram.fsm.state import State, StatesGroup

class LangSG(StatesGroup):
    lang = State()

class AddMenuItem(StatesGroup):
    name = State()
    description = State()
    category = State()
    price = State()
    photo = State()
    confirm = State()