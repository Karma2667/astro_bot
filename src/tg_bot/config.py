from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore
from dotenv import load_dotenv # type: ignore

PROJECT_PATH = Path(__file__).parent.parent.parent
TG_BOT_FOLDER = PROJECT_PATH / "src" / "tg_bot"
ASSET_FOLDER = TG_BOT_FOLDER / "assets"
IMAGE_FOLDER = ASSET_FOLDER / "images"
ENV_PATH = PROJECT_PATH / ".env"

if not ENV_PATH.exists():
    raise FileNotFoundError(
        f"{ENV_PATH} does not exist. Please create the .env file with the required variables."
    )

load_dotenv(dotenv_path=ENV_PATH)

class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH), env_file_encoding="utf-8", extra="allow"
    )

class BotSettings(EnvSettings):
    BOT_TOKEN: str
    ADMIN_IDS: list[int]

class LoggingSettings:
    LOG_PATH = PROJECT_PATH / "logs"
class ServerSettings(EnvSettings):
    SERVER_ACTUAL_HOST: str
    SERVER_HOST: str
    SERVER_PORT: int
    SERVER_SECRET_KEY: str

class AdminSettings(EnvSettings):
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_IDS: list[int]

class GPTSettings(EnvSettings):
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str = None

    @property
    def GPT_MODEL(self):
        return "gemini-1.5-flash"

    @property
    def BASE_URL(self):
        return "https://generativelanguage.googleapis.com/v1beta"

    @property
    def GPT_TEMPLATES_PATH(self):
        return TG_BOT_FOLDER / "gpt" / "templates"

class DatabaseSettings(EnvSettings):
    DB_TYPE: str
    DB_USER: str
    DB_PORT: str
    DB_PASS: str
    DB_HOST: str
    DB_NAME: str

    @property
    def SQLITE_PATH(self):
        return PROJECT_PATH / "src" / "tg_bot" / "database" / "tg_bot.db"

    @property
    def DATABASE_URL(self):
        if self.DB_TYPE == "sqlite":
            return f"sqlite:///{self.SQLITE_PATH}"
        else:
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

class LocalesSettings:
    DEFAULT_LOCALE = "ru"
    I18N_DOMAIN = "messages"
    LOCALE_PATH = TG_BOT_FOLDER / "locales"

class PaymentSettings(EnvSettings):
    PROVIDER_TOKEN: str

class Settings:
    admin = AdminSettings()
    bot = BotSettings()
    log = LoggingSettings()
    database = DatabaseSettings()
    locales = LocalesSettings()
    server = ServerSettings()
    gpt = GPTSettings()
    payment = PaymentSettings()

def get_taro_image_path(image_filename: str) -> Path:
    from pathlib import Path
    return ASSET_FOLDER / "images" / "tarot" / image_filename

settings = Settings()