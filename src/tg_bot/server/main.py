import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from config import settings
from database.db import engine
from server.admin_auth import AdminAuth
from database.predictions.admin import PredictionAdmin
from database.profile.admin import ProfileAdmin
from database.user.admin import UserAdmin


app = FastAPI()
server_settings = settings.server

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin = Admin(app=app, engine=engine, authentication_backend=AdminAuth(secret_key=server_settings.SERVER_SECRET_KEY))
admin_views = [UserAdmin, ProfileAdmin, PredictionAdmin]
[admin.add_view(view) for view in admin_views]


def start_server():
    uvicorn.run("server.main:app", host=server_settings.SERVER_HOST, port=server_settings.SERVER_PORT)