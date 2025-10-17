from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.infrastructure.database.models import User, CartItem, MenuItem


async def get_user_by_user_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Возвращает пользователя по username без '@'."""
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


# Добавление пользователя в базу данных
async def create_user(
    session: AsyncSession,
    user_id: int,
    username: str,
    language: str,
    role: str,
    is_alive: bool = True,
    banned: bool = False,
) -> User:
    user = User(
        user_id=user_id,
        username=username,
        language=language,
        role=role,
        is_alive=is_alive,
        banned=banned,
    )
    session.add(user)
    return user


async def update_user_language(session: AsyncSession, user_id: int, new_language: str) -> bool:
    user = await get_user_by_user_id(session, user_id)
    if user:
        user.language = new_language
        return True
    return False


async def update_user_alive_status(session: AsyncSession, user_id: int, is_alive: bool):
    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(is_alive=is_alive)
    )


async def update_user_role(session: AsyncSession, user_id: int, new_role: str) -> None:
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(role=new_role)
        )


async def get_user_role(session: AsyncSession, user_id: int) -> str | None:
    result = await session.execute(
        select(User.role).where(User.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_all_menu_items(session: AsyncSession):
    result = await session.execute(
        select(MenuItem)
    )
    return result.scalars().all()


async def get_cart_items(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(joinedload(CartItem.item))
    )
    return result.scalars().all()


async def add_item_to_cart(session: AsyncSession, user_id: int, item_id: int, quantity: int = 1):

    # Проверим, есть ли уже такой товар в корзине
    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.item_id == item_id
        )
    )
    cart_item = result.scalar_one_or_none()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, item_id=item_id, quantity=quantity)
        session.add(cart_item)


async def clear_user_cart(session: AsyncSession, user_id: int) -> int:
    """Очищает всю корзину пользователя"""
    result = await session.execute(
        delete(CartItem).where(CartItem.user_id == user_id)
    )
    return result.rowcount



