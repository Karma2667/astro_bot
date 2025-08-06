from datetime import date
from sqlalchemy import select, update, insert # type: ignore
from sqlalchemy.exc import SQLAlchemyError # type: ignore
from typing import Optional

from database.db import async_session_maker
from database.usage.models import UserUsage
from logger import db_query_logger as logger 

async def get_user_usage(user_id: int, feature_type: str, usage_date: date) -> Optional[UserUsage]:
    async with async_session_maker() as session:
        try:
            stmt = select(UserUsage).where(
                UserUsage.user_id == user_id,
                UserUsage.feature_type == feature_type,
                UserUsage.usage_date == usage_date
            )
            result = await session.execute(stmt)
            usage_record = result.scalars().first()
            logger.debug(f"UserUsage fetched for user {user_id}, feature {feature_type}, date {usage_date}: {'Found' if usage_record else 'Not found'}")
            return usage_record
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching UserUsage for user {user_id}, feature {feature_type}, date {usage_date}: {e}")
            return None

async def increment_user_usage(user_id: int, feature_type: str, usage_date: date) -> bool:
    async with async_session_maker() as session:
        try:
            stmt = update(UserUsage).where(
                UserUsage.user_id == user_id,
                UserUsage.feature_type == feature_type,
                UserUsage.usage_date == usage_date
            ).values(usage_count=UserUsage.usage_count + 1)
            
            result = await session.execute(stmt)
            
            if result.rowcount == 0:
                new_record = UserUsage(
                    user_id=user_id,
                    feature_type=feature_type,
                    usage_date=usage_date,
                    usage_count=1
                )
                session.add(new_record)
            
            await session.commit()
            logger.info(f"UserUsage incremented/created for user {user_id}, feature {feature_type}, date {usage_date}")
            return True
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error incrementing UserUsage for user {user_id}, feature {feature_type}, date {usage_date}: {e}")
            return False
