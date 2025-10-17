from aiogram import Router, F
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
from aiogram_i18n import I18nContext
from aiogram.fsm.context import FSMContext
from app.bot.enums.roles import UserRole
from app.bot.filters.filters import UserRoleFilter
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.states.states import AddMenuItem
from app.infrastructure.database.crud.user_crud import (
    get_user_by_user_id, get_user_by_username,
)
from app.infrastructure.database.models import MenuItem, Activity
from app.infrastructure.database.crud.admin_crud import (
    add_user_activity, change_user_banned_status_by_id,
    change_user_banned_status_by_username, get_top_users_statistics,
    get_user_banned_status_by_id, get_user_banned_status_by_username
)

from datetime import datetime, timedelta

admin_router = Router()

admin_router.message.filter(UserRoleFilter(UserRole.ADMIN))

# Этот хэндлер будет срабатывать на команду "/help"
# для пользователя с ролью `UserRole.ADMIN`
@admin_router.message(Command(commands=["help"]))
async def process_admin_help_command(message: Message, i18n: I18nContext):
    await message.answer(i18n.get("help_admin"))


# Этот хэндлер будет срабатывать на команду "/cansel" в любых состояниях,
# кроме состояния по умолчанию, и отключает машину состояний
@admin_router.message(Command(commands=["cansel"]), ~StateFilter(default_state))
async def process_cansel_command(message: Message, i18n: I18nContext, state: FSMContext):
    await message.answer(i18n.get("cansel_item"))
    await state.clear()

# Этот хэндлер будет срабатывать на команду "add_menu_item"
# и переводить бота в состояние оиждания ввода названия товара
@admin_router.message(Command("add_menu_item"))
async def start_add_menu_item(message: Message, state: FSMContext):
    await state.set_state(AddMenuItem.name)
    await message.answer("Введите название пиццы:")


# Этот хэндлер пеереводит в состояние ввода "Название" товара
@admin_router.message(StateFilter(AddMenuItem.name), F.text)
async def set_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddMenuItem.description)
    await message.answer("Введите описание пиццы:")


# Этот хэндлер пеереводит в состояние ввода "Описание" товара
@admin_router.message(StateFilter(AddMenuItem.description), F.text)
async def set_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddMenuItem.price)
    await message.answer("Введите цену пиццы (например, 12.50):")


# Цена
@admin_router.message(StateFilter(AddMenuItem.price), F.text)
async def set_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer("Некорректный формат. Введите число.")
    
    await state.update_data(price=price)
    await state.set_state(AddMenuItem.category)
    await message.answer("Введите категорию пиццы (например, 'Классика' или 'Острая'):")


# Категория
@admin_router.message(StateFilter(AddMenuItem.category), F.text)
async def set_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddMenuItem.photo)
    await message.answer("Пришлите фото пиццы (через галерею Telegram):")


# Фото
@admin_router.message(StateFilter(AddMenuItem.photo), F.photo)
async def set_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()

    try:
        text = (
            f"❓ Подтвердите добавление товара:\n\n"
            f"🍕 Название: {data['name']}\n"
            f"📝 Описание: {data['description']}\n"
            f"💰 Цена: {data['price']}\n"
            f"📦 Категория: {data['category']}\n\n"
            f"Введите '✅' для подтверждения или '❌' для отмены:"
        )

        await message.answer_photo(
            photo=data["photo"],
            caption=text
        )

        await state.set_state(AddMenuItem.confirm)

    except KeyError as e:
        await message.answer(
            f"❌ Ошибка: отсутствует ключ '{e.args[0]}' в данных состояния.\n"
            f"Попробуйте начать заново."
        )
        await state.clear()


# Подтверждение (ручной ввод)
@admin_router.message(StateFilter(AddMenuItem.confirm), F.text.in_(["✅", "❌"]))
async def confirm_item(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌":
        await state.clear()
        return await message.answer("Добавление отменено.")
    
    data = await state.get_data()

    item = MenuItem(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        category=data["category"],
        photo_id=data["photo"],
    )
    session.add(item)
    await session.commit()
    await state.clear()
    await message.answer("Пицца успешно добавлена в меню! 🍕")


# Этот хэндлер будет отвечать на команду "/statistics"
@admin_router.message(Command("statistics"))
async def show_statistics(message: Message, session: AsyncSession):
    """Показывает статистику активности пользователей за 7, 30 дней и всё время."""
    now = datetime.utcnow()

    periods = {
        "7 дней": now - timedelta(days=7),
        "30 дней": now - timedelta(days=30),
        "всё время": None,
    }

    text = "📊 Статистика активности пользователей:\n\n"

    for label, since in periods.items():
        users = await get_top_users_statistics(session, limit=5, since=since)

        text += f"🔥 Топ за {label}:\n"
        if not users:
            text += "Нет данных 😢\n\n"
            continue

        for i, (user_id, username, total_actions, last_seen) in enumerate(users, start=1):
            last_seen_str = last_seen.strftime("%Y-%m-%d %H:%M:%S") if last_seen else "—"
            text += (
                f"{i}. @{username or 'Unknown'} — {total_actions} действий "
                f"(последняя активность: {last_seen_str})\n"
            )

        text += "\n"

    await message.answer(text)

# Этот хэндлер срабатывает на команду "/ban"
# для блокировки пользователя
@admin_router.message(Command("ban"))
async def process_ban_command(
    message: Message,
    command: CommandObject,
    i18n: I18nContext,
    session: AsyncSession,
):
    args = command.args
    if not args:
        await message.answer(i18n.get("empty_ban_answer"))
        return

    arg_user = args.split()[0].strip()

    # Получаем статус
    if arg_user.isdigit():
        banned_status = await get_user_banned_status_by_id(session, int(arg_user))
    elif arg_user.startswith("@"):
        banned_status = await get_user_banned_status_by_username(session, arg_user[1:])
    else:
        await message.answer(i18n.get("incorrect_ban_arg"))
        return

    if banned_status is None:
        await message.answer(i18n.get("no_user"))
    elif banned_status:
        await message.answer(i18n.get("already_banned"))
    else:
        if arg_user.isdigit():
            await change_user_banned_status_by_id(session, int(arg_user), True)
        else:
            await change_user_banned_status_by_username(session, arg_user[1:], True)
        await message.answer(i18n.get("successfully_banned"))


# Этот хэндлер срабатывает на команду "/unban"
# для разблокировки пользователя
@admin_router.message(Command("unban"))
async def process_unban_command(
    message: Message,
    command: CommandObject,
    i18n: I18nContext,
    session: AsyncSession,
):
    args = command.args
    if not args:
        await message.answer(i18n.get("empty_unban_answer"))
        return

    arg_user = args.split()[0].strip()

    if arg_user.isdigit():
        banned_status = await get_user_banned_status_by_id(session, int(arg_user))
    elif arg_user.startswith("@"):
        banned_status = await get_user_banned_status_by_username(session, arg_user[1:])
    else:
        await message.answer(i18n.get("incorrect_unban_arg"))
        return

    if banned_status is None:
        await message.answer(i18n.get("no_user"))
    elif not banned_status:
        await message.answer(i18n.get("already_unbanned"))
    else:
        if arg_user.isdigit():
            await change_user_banned_status_by_id(session, int(arg_user), False)
        else:
            await change_user_banned_status_by_username(session, arg_user[1:], False)
        await message.answer(i18n.get("successfully_unbanned"))