import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BACKEND_DIR / "campus_gym.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


class Config:
    """Flask 项目的集中配置。所有敏感配置均优先从环境变量读取。"""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "72"))
    )
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DATABASE_URL", "").strip() or DEFAULT_DATABASE_URL
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WECHAT_MOCK_LOGIN = os.getenv("WECHAT_MOCK_LOGIN", "true").lower() == "true"
    WECHAT_APPID = os.getenv("WECHAT_APPID", "")
    WECHAT_SECRET = os.getenv("WECHAT_SECRET", "")

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    JSON_AS_ASCII = False
