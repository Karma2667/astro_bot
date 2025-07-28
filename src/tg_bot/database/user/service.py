from sqlalchemy import select
from typing import Optional, List, Dict, Any

from database.user.models import User
from database.profile.models import Profile
from logger import db_query_logger as logger
from database.db import async_session_maker

async def create_user(user: User) -> User:
    """Create a new user record."""
    async with async_session_maker() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"User created: {user}")
        return user

async def find_user_by_id(user_id: int) -> Optional[User]:
    """Find a user by their ID."""
    async with async_session_maker() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        logger.info(f"User fetched by ID {user_id}: {user}")
        return user

async def find_all_users() -> List[User]:
    """Retrieve all users."""
    async with async_session_maker() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        logger.info(f"All users fetched: {users}")
        return users


# === ГЛАВНОЕ ИСПРАВЛЕНИЕ: ПЕРЕПИСАННАЯ ФУНКЦИЯ UPDATE_USER ===
async def update_user(user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
    """
    Update a user's data using a dictionary of changes.
    """
    async with async_session_maker() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if not existing_user:
            logger.warning(f"User with ID {user_id} not found for update.")
            return None

        for key, value in update_data.items():
            if hasattr(existing_user, key):
                setattr(existing_user, key, value)
            else:
                logger.warning(f"Attempted to update non-existent attribute '{key}' on User.")

        await session.commit()
        await session.refresh(existing_user)
        logger.info(f"User updated: {existing_user.__dict__}")
        return existing_user


async def delete_user(user_id: int) -> Optional[User]:
    """Delete a user by their ID."""
    async with async_session_maker() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if user is None:
            logger.warning(f"User with ID {user_id} not found for deletion.")
            return None
        await session.delete(user)
        await session.commit()
        logger.info(f"User deleted: {user}")
        return user

async def set_current_profile(user_id: int, profile_id: int) -> Optional[User]:
    """Set the current profile ID for a user."""
    # Используем нашу новую надежную функцию
    return await update_user(user_id=user_id, update_data={"current_profile_id": profile_id})

async def add_admin(telegram_id: int, username: str = None, locale: str = "ru") -> User:
    """Add or update an admin user in the database."""
    async with async_session_maker() as session:
        stmt = select(User).where(User.user_id == telegram_id)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user and existing_user.is_admin:
            logger.info(f"Admin with Telegram ID {telegram_id} already exists.")
            return existing_user

        if existing_user:
            # Если пользователь есть, но он не админ, обновляем его
            update_data = {"is_admin": True}
            if username:
                update_data["name"] = username
            return await update_user(user_id=telegram_id, update_data=update_data)
        else:
            # Если пользователя нет, создаем нового
            new_admin = User(
                user_id=telegram_id,
                name=username or f"Admin_{telegram_id}",
                locale=locale,
                is_admin=True,
                is_mail_subscribed=True
            )
            return await create_user(new_admin)