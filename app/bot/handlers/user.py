from aiogram import Bot, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommandScopeChat, Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram_i18n import I18nContext
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    start_kb, get_lang_settings_kb, home_kb, get_menu_item_kb, cart_kb, prepayment_kb
)
from app.bot.keyboards.callback_factory import (
    CartActionCall, LanguageActionCall, LanguageAction,
    StartActionCall, SaveActionCall, HomeActionCall
)
from app.bot.keyboards.menu_button import get_main_menu_commands
from app.bot.enums.roles import UserRole
from app.infrastructure.database.crud.user_crud import (
    add_item_to_cart, get_cart_items, get_user_by_user_id, create_user, update_user_language,
    update_user_alive_status, update_user_role, get_all_menu_items, clear_user_cart,
)

from app.bot.i18n.translator import redis_client


user_router = Router()


# Этот хэндлер срабатывает на команду "/start"
@user_router.message(CommandStart())
async def process_start_command(
    message: Message,
    i18n: I18nContext,
    session: AsyncSession,
    bot: Bot,
    state: FSMContext,
    admin_ids: list[int]
):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username or full_name
    lang_code = await redis_client.get(f"user_lang:{user_id}") or "ru"

    try:
        user = await get_user_by_user_id(session, user_id)
        
        # Определяем роль для текущего апдейта (по списку админов)
        role_for_commands: UserRole = UserRole.ADMIN if user_id in admin_ids else UserRole.USER
        
        if not user:
            await create_user(
                session=session,
                user_id=user_id,
                username=username,
                language=lang_code,
                role=role_for_commands.value,
                is_alive=True,
                banned=False,
            )
        else:
            await update_user_alive_status(session, user_id=user_id, is_alive=True)
            await session.refresh(user)
            
            # Синхронизируем роль в БД при необходимости
            if user.role != role_for_commands.value:
                await update_user_role(session, user_id, role_for_commands.value)
        
        await bot.set_my_commands(
            commands=get_main_menu_commands(i18n=i18n, role=role_for_commands),
            scope=BotCommandScopeChat(
                chat_id=message.from_user.id
            )
        )
        await message.answer(
            i18n("start_message", username=full_name),
            reply_markup=start_kb(i18n, full_name)
        )
        await state.clear()

    except SQLAlchemyError:
        await message.answer(text="Error creating user")
        raise



@user_router.callback_query(StartActionCall.filter(F.action == "open_language"))
@user_router.message(Command("lang"))
async def show_language_keyboard(event: Message | CallbackQuery, i18n: I18nContext):
    if isinstance(event, Message):
        target = event
    else:
        target = event.message
        await event.answer()
    
    user_id = target.from_user.id
    lang_code = await redis_client.get(f"user_lang:{user_id}") or "ru"
    
    await i18n.set_locale(lang_code)

    keyboard = get_lang_settings_kb(
        i18n=i18n,
        locales=["ru", "en"],
        checked=lang_code
    )

    await target.answer(
        i18n.get("choose_language"),
        reply_markup=keyboard
    )

@user_router.callback_query(LanguageActionCall.filter(F.action == LanguageAction.select_lang))
async def select_language(
    call: CallbackQuery,
    callback_data: LanguageActionCall,
    i18n: I18nContext,
    session: AsyncSession
):
    user_id = call.from_user.id
    new_lang = callback_data.language
    old_lang = await redis_client.get(f"user_lang:{user_id}") or "ru"

    if new_lang == old_lang:
        await call.answer()
        return

    await redis_client.set(f"user_lang:{user_id}", new_lang)
    await i18n.set_locale(new_lang)
    
    try:
        await update_user_language(session, user_id, new_lang)
    except SQLAlchemyError:
        await session.rollback()
        

    keyboard = get_lang_settings_kb(
        i18n=i18n,
        locales=["ru", "en"],
        checked=new_lang
    )

    await call.message.edit_text(
        i18n.get("choose_language"),
        reply_markup=keyboard
    )
    await call.answer()


@user_router.callback_query(SaveActionCall.filter(F.action == "save_lang"))
async def show_home_kb(call: CallbackQuery, i18n: I18nContext):
    await call.message.edit_text(
        text=i18n.get("home_menu"),
        reply_markup=home_kb(i18n)
    )
    await call.answer()


# Этот хэндлер срабатывает на команду "/home"
# и выдает клавиатуру в которой идет все взаимодействие с ботом
@user_router.message(Command(commands=["home"]))
async def process_menu_command(message: Message, i18n: I18nContext):
    await message.answer(
        text=i18n.get("home_menu"),
        reply_markup=home_kb(i18n)
    )

# Срабатывает при нажатии на кнопку меню и выдаёт меню пиццы
@user_router.callback_query(HomeActionCall.filter(F.action == "menu" ))
@user_router.message(Command("menu"))
async def show_menu(event: Message | CallbackQuery, i18n: I18nContext, session: AsyncSession):
    if isinstance(event, Message):
        target = event
    else:
        target = event.message
        await event.answer()
    
    items = await get_all_menu_items(session)
    
    if not items:
        await target.answer("В меню пока нет товаров. Загляните позже.")
        return
    
    for item in items:
        caption = (
            f"🍕 <b>{item.name}</b>\n"
            f"📝 {item.description}\n"
            f"💰 Цена: {item.price:.2f}₽\n"
            f"📦 Категория: {item.category}"
        )
        
        # Проверяем, есть ли фото
        if item.photo_id:
            await target.answer_photo(
                photo=item.photo_id,
                caption=caption,
                reply_markup=get_menu_item_kb(i18n, item.id),
                parse_mode="HTML"
            )
        else:
            # Если фото нет, отправляем только текст
            await target.answer(
                text=caption,
                reply_markup=get_menu_item_kb(i18n, item.id),
                parse_mode="HTML"
            )
    


# Этот хэндлер срабатывает на кнопку "❌ Отмена"
# во время просмотра товара
@user_router.callback_query(CartActionCall.filter(F.action == "cansel"))
async def show_menu_cansel(call: CallbackQuery, i18n: I18nContext):
    await call.message.answer(
        text="ghf",
    )
    await call.answer()


# Этот хэндлер срабатывает на кнопку "➕ В корзину"
# во время просмотра товара и добавляет товар в корзину
@user_router.callback_query(CartActionCall.filter(F.action == "add"))
async def add_to_cart_btn(
    call: CallbackQuery,
    callback_data: CartActionCall,
    i18n: I18nContext,
    session: AsyncSession
):
    user_id = call.from_user.id
    item_id = callback_data.item_id
    
    await add_item_to_cart(session=session, user_id=user_id, item_id=item_id, quantity=1)
    
    await call.answer(i18n.get("item_added_to_cart"), show_alert=True)



@user_router.callback_query(CartActionCall.filter(F.action == "go_to_cart"))
async def go_to_cart_btn(
    call: CallbackQuery,
    i18n: I18nContext,
    session: AsyncSession
):
    user_id = call.from_user.id

    # Получаем корзину пользователя
    cart_items = await get_cart_items(session=session, user_id=user_id)

    if not cart_items:
        await call.message.answer(i18n.get("cart_is_empty"))
        await call.answer()
        return

    total_price = 0
    text_lines = [i18n.get("your_cart") + ":\n"]

    for cart_item in cart_items:
        item = cart_item.item
        item_total = cart_item.quantity * item.price
        total_price += item_total

        text_lines.append(
            f"🍕 <b>{item.name}</b> × {cart_item.quantity} — {item_total:.2f}₽"
        )

    text_lines.append(f"\n💰 <b>{i18n.get('total')}:</b> {total_price:.2f}₽")

    # Создаём клавиатуру для корзины
    keyboard = cart_kb(i18n=i18n)

    await call.message.answer(
        "\n".join(text_lines),
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await call.answer()


@user_router.callback_query(CartActionCall.filter(F.action == "clear_cart"))
async def clear_cart_btn(
    call: CallbackQuery,
    i18n: I18nContext,
    session: AsyncSession
):
    user_id = call.from_user.id
    
    items_removed = await clear_user_cart(session=session, user_id=user_id)
    
    if items_removed > 0:
        await call.message.edit_text(
            text=i18n.get("cart_is_empty"),
            reply_markup=cart_kb(i18n=i18n)
        )
        
        await call.answer(
            i18n.get("cart_cleared"), show_alert=True
        )
    else:
        await call.answer(i18n.get("cart_already_empty"), show_alert=True)
    
    await call.answer()


async def update_cart_message(
    call: CallbackQuery,
    i18n: I18nContext,
    session: AsyncSession,
    user_id: int
):
    """Обновляет сообщение корзины после изменений"""
    cart_items = await get_cart_items(session=session, user_id=user_id)
    
    if not cart_items:
        await call.message.edit_text(
            i18n.get("cart_is_empty")
        )
        return
    
    total_price = 0
    text_lines = [i18n.get("your_cart") + ":\n"]

    for cart_item in cart_items:
        item = cart_item.item
        item_total = cart_item.quantity * item.price
        total_price += item_total

        text_lines.append(
            f"🍕 <b>{item.name}</b> × {cart_item.quantity} — {item_total:.2f}₽"
        )

    text_lines.append(f"\n💰 <b>{i18n.get('total')}:</b> {total_price:.2f}₽")

    keyboard = cart_kb(i18n=i18n)

    await call.message.edit_text(
        "\n".join(text_lines),
        parse_mode="HTML",
        reply_markup=keyboard
    )

@user_router.callback_query(CartActionCall.filter(F.action == "confirm"))
async def confirm_order_btn(
    call: CallbackQuery,
    i18n: I18nContext,
    session: AsyncSession
):
    user_id = call.from_user.id

    # Получаем корзину пользователя
    cart_items = await get_cart_items(session=session, user_id=user_id)

    if not cart_items:
        await call.message.answer(i18n.get("cart_is_empty"))
        await call.answer()
        return

    total_price = 0
    text_lines = [i18n.get("your_cart") + ":\n"]

    for cart_item in cart_items:
        item = cart_item.item
        item_total = cart_item.quantity * item.price
        total_price += item_total

        text_lines.append(
            f"🍕 <b>{item.name}</b> × {cart_item.quantity} — {item_total:.2f}₽"
        )

    text_lines.append(f"\n💰 <b>{i18n.get('total')}:</b> {total_price:.2f}₽")

    # Создаём клавиатуру для корзины
    keyboard = prepayment_kb(i18n=i18n)

    await call.message.answer(
        "\n".join(text_lines),
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await call.answer()


@user_router.callback_query(CartActionCall.filter(F.action == "start_payment"))
async def start_payment(call: CallbackQuery, i18n: I18nContext, session: AsyncSession):
    user_id = call.from_user.id
    cart_items = await get_cart_items(session=session, user_id=user_id)
    
    total_price = sum(cart_item.quantity * cart_item.item.price for cart_item in cart_items)
    
    prices = [
        LabeledPrice(label=i18n.get("order_payment"), amount=int(total_price * 100))
    ]
    
    await call.bot.send_invoice(
        chat_id=call.message.chat.id,
        title=i18n.get("order_title"),
        description=i18n.get("order_description"),
        payload=f"order_{user_id}",
        provider_token="1744374395:TEST:636efe9947d55731ae87",
        currency="RUB",
        prices=prices,
        start_parameter="pizza-payment",
    )
    
@user_router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.bot.answer_pre_checkout_query(
        pre_checkout_query_id=pre_checkout_q.id,
        ok=True
    )


@user_router.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.answer("✅ Оплата прошла успешно! Спасибо за заказ 🙌")