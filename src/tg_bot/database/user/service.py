from sqlalchemy import select
from typing import Optional, List

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


async def update_user(user_id: int, updated_user: User) -> Optional[User]:
    """Update a user's data dynamically without explicitly naming columns."""
    async with async_session_maker() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if not existing_user:
            logger.warning(f"User with ID {user_id} not found for update.")
            return None

        for key, value in updated_user.__dict__.items():
            if key != "_sa_instance_state" and hasattr(User, key) and key != "id":
                setattr(existing_user, key, value)

        await session.commit()
        await session.refresh(existing_user)
        logger.info(f"User updated: {existing_user}")
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
    async with async_session_maker() as session:
        # Ensure the profile belongs to the user
        stmt = select(Profile).where(
            Profile.id == profile_id, Profile.user_id == user_id
        )
        result = await session.execute(stmt)
        profile = result.scalars().first()

        if not profile:
            logger.warning(
                f"Profile with ID {profile_id} does not belong to User {user_id}."
            )
            return None

        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            logger.warning(f"User with ID {user_id} not found.")
            return None

        user.current_profile_id = profile_id

        await session.commit()
        await session.refresh(user)
        logger.info(f"User {user_id} current_profile_id set to {profile_id}.")
        return user
