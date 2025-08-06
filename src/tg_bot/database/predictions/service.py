from sqlalchemy import select
from typing import Optional
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from logger import db_query_logger as logger
from database.predictions.models import Prediction, PredictionType
from database.db import async_session_maker

async def create_prediction(prediction: Prediction) -> Prediction:
    async with async_session_maker() as session:
        if not prediction.prediction or prediction.prediction.strip() == "":
            raise ValueError("Prediction text cannot be None or empty")
        
        try:
            session.add(prediction)
            await session.commit()
            await session.refresh(prediction)
            logger.info(f"Prediction created - ID: {prediction.id}, Type: {prediction.prediction_type}, Text: {prediction.prediction[:50]}...")
            return prediction
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"IntegrityError while creating prediction: {str(e)}")
            raise
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error while creating prediction: {str(e)}")
            raise

async def delete_prediction(prediction_id: int) -> Optional[Prediction]:
    async with async_session_maker() as session:
        try:
            prediction = await find_prediction_by_id(prediction_id)
            if prediction is None:
                logger.warning(f"Prediction with ID {prediction_id} not found for deletion.")
                return None

            await session.delete(prediction)
            await session.commit()
            logger.info(f"Prediction deleted - ID: {prediction.id}, Type: {prediction.prediction_type}")
            return prediction
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error while deleting prediction: {str(e)}")
            raise

async def find_all_predictions() -> list[Prediction]:
    async with async_session_maker() as session:
        try:
            stmt = select(Prediction)
            result = await session.execute(stmt)
            predictions = result.scalars().all()
            logger.info(f"Fetched {len(predictions)} predictions")
            return predictions
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching all predictions: {str(e)}")
            raise

async def find_prediction_by_id(prediction_id: int) -> Optional[Prediction]:
    async with async_session_maker() as session:
        try:
            stmt = select(Prediction).where(Prediction.id == prediction_id)
            result = await session.execute(stmt)
            prediction = result.scalars().first()
            logger.info(f"Prediction fetched by ID {prediction_id}: {'Found' if prediction else 'Not found'}")
            return prediction
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching prediction by ID {prediction_id}: {str(e)}")
            raise

async def find_prediction_by_recognition_and_type(recognition_str: str, prediction_type: PredictionType) -> Optional[Prediction]:
    async with async_session_maker() as session:
        try:
            stmt = select(Prediction).where(
                Prediction.recognition_str == recognition_str,
                Prediction.prediction_type == prediction_type.value
            )
            result = await session.execute(stmt)
            prediction = result.scalars().first()
            logger.info(f"Prediction fetched by recognition '{recognition_str}' and type {prediction_type.value}: {'Found' if prediction else 'Not found'}")
            return prediction
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching prediction by recognition '{recognition_str}' and type '{prediction_type.value}': {str(e)}")
            raise