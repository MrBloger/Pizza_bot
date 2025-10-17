from datetime import date, datetime, timezone
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import Activity, User


async def add_user_activity(session: AsyncSession, user_id: int):
    """Добавляет или обновляет активность пользователя за текущий день."""
    today = date.today()
    now = datetime.now(timezone.utc)

    # Ищем запись за сегодня
    result = await session.execute(
        select(Activity).where(Activity.user_id == user_id, Activity.activity_date == today)
    )
    activity = result.scalar_one_or_none()

    if activity:
        # Если запись есть — увеличиваем счетчик и обновляем last_seen
        activity.actions += 1
        activity.last_seen = now
    else:
        # Если записи нет — создаем новую
        session.add(
            Activity(
                user_id=user_id,
                first_seen=now,
                last_seen=now,
                created_at=now,
                activity_date=today,
                actions=1,
            )
        )


async def get_top_users_statistics(
    session: AsyncSession,
    limit: int = 5,
    since: datetime | None = None
):
    """Возвращает топ пользователей по активности, опционально за период."""
    query = (
        select(
            User.user_id,  # добавляем ID для группировки
            User.username,
            func.sum(Activity.actions).label("total_actions"),
            func.max(Activity.last_seen).label("last_seen"),
        )
        .join(Activity, Activity.user_id == User.user_id)
    )

    if since:
        query = query.where(Activity.last_seen >= since)

    # 👇 добавляем group_by по user_id и username
    query = (
        query.group_by(User.user_id, User.username)
        .order_by(desc("total_actions"))
        .limit(limit)
    )

    result = await session.execute(query)
    return result.all()


async def change_user_banned_status_by_id(session: AsyncSession, user_id: int, banned: bool) -> bool:
    """Меняет статус banned по user_id."""
    await session.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(banned=banned)
    )
    await session.commit()
    return True


async def change_user_banned_status_by_username(session: AsyncSession, username: str, banned: bool) -> bool:
    """Меняет статус banned по username."""
    await session.execute(
        update(User)
        .where(User.username == username)
        .values(banned=banned)
    )
    await session.commit()
    return True


async def get_user_banned_status_by_id(session: AsyncSession, user_id: int) -> bool | None:
    """Возвращает статус бана пользователя по user_id."""
    result = await session.execute(
        select(User.banned).where(User.user_id == user_id)
    )
    banned_status = result.scalar_one_or_none()
    return banned_status


async def get_user_banned_status_by_username(session: AsyncSession, username: str) -> bool | None:
    """Возвращает статус бана пользователя по username."""
    result = await session.execute(
        select(User.banned).where(User.username == username)
    )
    banned_status = result.scalar_one_or_none()
    return banned_status
