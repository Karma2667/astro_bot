from sqlalchemy import select
from typing import Optional

from logger import db_query_logger as logger
from database.predictions.models import Prediction, PredictionType
from database.db import async_session_maker


async def create_prediction(prediction: Prediction) -> Prediction:
    """Create a new prediction record."""
    async with async_session_maker() as session:
        session.add(prediction)
        await session.commit()
        await session.refresh(prediction)
        logger.info(f"Prediction created: {prediction}")
        return prediction


async def delete_prediction(prediction_id: int) -> Optional[Prediction]:
    """Delete a prediction by its ID."""
    async with async_session_maker() as session:
        prediction = await find_prediction_by_id(prediction_id)
        if prediction is None:
            logger.warning(
                f"Prediction with ID {prediction_id} not found for deletion."
            )
            return None

        await session.delete(prediction)
        await session.commit()
        logger.info(f"Prediction deleted: {prediction}")
        return prediction


async def find_all_predictions() -> list[Prediction]:
    """Find all predictions."""
    async with async_session_maker() as session:
        stmt = select(Prediction)
        result = await session.execute(stmt)
        predictions = result.scalars().all()
        logger.info(f"All predictions fetched: {predictions}")
        return predictions
    

async def find_prediction_by_id(prediction_id: int) -> Optional[Prediction]:
    """Find a prediction by its ID."""
    async with async_session_maker() as session:
        stmt = select(Prediction).where(Prediction.id == prediction_id)
        result = await session.execute(stmt)
        prediction = result.scalars().first()
        logger.info(f"Prediction fetched by ID {prediction_id}: {prediction}")
        return prediction


async def find_prediction_by_recognition_and_type(recognition_str: str, prediction_type: PredictionType) -> Optional[Prediction]:
    """Find a prediction by its recognition string and prediction type."""
    async with async_session_maker() as session:
        stmt = select(Prediction).where(
            Prediction.recognition_str == recognition_str,
            Prediction.prediction_type == prediction_type
        )
        result = await session.execute(stmt)
        prediction = result.scalars().first()
        logger.info(f"Prediction fetched by recognition string {recognition_str} and prediction type {prediction_type}: {prediction}")
        return prediction
