import asyncio
import pytz
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from database.base import Base
from database.db import engine

from bot_ import bot, dispatcher
from server.main import app
from handlers import all_routers
from handlers.background.mailing import send_mailing
from handlers.background.prediction import check_predictions
from handlers.background.subscription import check_subscription
from middleware import register_middlewares
from config import settings
from logger import bot_logger

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    bot_logger.info("Database tables created")

async def start_bot():
    bot_logger.info("Bot started")
    register_middlewares(dispatcher)
    dispatcher.include_routers(*all_routers)
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(
        bot, allowed_updates=["message", "callback_query", "pre_checkout_query"]
    )

async def start_server(host: str, port: int):
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_app():
    await asyncio.gather(
        start_bot(),
        # start_server(settings.server.SERVER_HOST, settings.server.SERVER_PORT),
    )

if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    moscow_timezone = pytz.timezone("Europe/Moscow")
    scheduler.add_job(init_db)  # Добавляем создание таблиц
    scheduler.add_job(run_app)
    scheduler.add_job(
        send_mailing, trigger=CronTrigger(hour=7, minute=0, timezone=moscow_timezone)
    )
    scheduler.add_job(
        check_predictions,
        trigger=CronTrigger(hour=3, minute=0),
        timezone=moscow_timezone,
    )
    scheduler.add_job(
        check_subscription,
        trigger=CronTrigger(hour=2, minute=0),
        timezone=moscow_timezone,
    )
    scheduler.start()
    asyncio.get_event_loop().run_forever()