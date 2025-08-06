from sqlalchemy import select
from typing import List, Optional, Dict, Any

from database.profile.models import Profile
from database.user.models import User
from logger import db_query_logger as logger
from database.db import async_session_maker

async def create_profile(profile: Profile) -> Profile:
    async with async_session_maker() as session:
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        logger.info(f"Profile created: {profile.__dict__}") # Улучшенное логирование
        return profile

async def find_profile_by_id(profile_id: int) -> Optional[Profile]:
    """Find a profile by its ID."""
    async with async_session_maker() as session:
        stmt = select(Profile).where(Profile.id == profile_id)
        result = await session.execute(stmt)
        profile = result.scalars().first()
        logger.info(f"Profile fetched by ID {profile_id}: {profile}")
        return profile

async def find_profiles_by_user_id(user_id: int) -> List[Profile]:
    async with async_session_maker() as session:
        stmt = select(Profile).where(Profile.user_id == user_id)
        result = await session.execute(stmt)
        profiles = result.scalars().all()
        logger.info(f"Profiles fetched for user ID {user_id}: {profiles}")
        return profiles

async def find_current_profile_by_user_id(user_id: int) -> Optional[Profile]:
    async with async_session_maker() as session:
        stmt = (
            select(Profile)
            .join(User, Profile.user_id == User.user_id)
            .where(Profile.id == User.current_profile_id, User.user_id == user_id)
        )
        result = await session.execute(stmt)
        profile = result.scalars().first()
        logger.info(f"Current profile fetched for user ID {user_id}: {profile}")
        return profile

async def update_profile(profile_id: int, update_data: Dict[str, Any]) -> Optional[Profile]:
    async with async_session_maker() as session:
        stmt = select(Profile).where(Profile.id == profile_id)
        result = await session.execute(stmt)
        existing_profile = result.scalars().first()

        if not existing_profile:
            logger.warning(f"Profile with ID {profile_id} not found for update.")
            return None

        for key, value in update_data.items():
            if hasattr(existing_profile, key):
                setattr(existing_profile, key, value)
            else:
                logger.warning(f"Attempted to update non-existent attribute '{key}' on Profile.")
        
        await session.commit()
        await session.refresh(existing_profile)
        logger.info(f"Profile updated: {existing_profile.__dict__}") # Улучшенное логирование
        return existing_profile


async def delete_profile(profile_id: int) -> Optional[Profile]:
    async with async_session_maker() as session:
        stmt = select(Profile).where(Profile.id == profile_id)
        result = await session.execute(stmt)
        profile = result.scalars().first()

        if profile is None:
            logger.warning(f"Profile with ID {profile_id} not found for deletion.")
            return None

        stmt = select(User).where(User.current_profile_id == profile_id)
        result = await session.execute(stmt)
        users = result.scalars().all()
        for user in users:
            user.current_profile_id = None

        await session.delete(profile)
        await session.commit()
        logger.info(f"Profile deleted: {profile}")
        return profile