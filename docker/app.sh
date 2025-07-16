#!/bin/bash
cd ./src/tg_bot
alembic revision --autogenerate -m "update_tables"
alembic upgrade head

pybabel compile -f -d ./locales &
uvicorn server.main:app --host ${SERVER_HOST} --port ${SERVER_PORT} &
exec python3 main.py