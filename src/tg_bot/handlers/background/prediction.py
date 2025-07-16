from datetime import datetime
import pytz

from database.predictions.service import find_all_predictions, delete_prediction
from logger import bot_logger


async def check_predictions():
    bot_logger.info("Checking predictions expiration")
    predictions = await find_all_predictions()
    utc_now = datetime.now(pytz.utc)
    for prediction in predictions:
        if not prediction.expiration_time or prediction.expiration_time < utc_now:
            await delete_prediction(prediction.id)