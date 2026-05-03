import os
from dotenv import load_dotenv

load_dotenv()

APP_MODE = os.getenv("APP_MODE", "demo").strip().lower()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "textgrader")
JWT_SECRET = os.getenv("JWT_SECRET", "quintana-demo-secret")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "8"))


def get_cors_origins():
    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    if APP_MODE == "demo":
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    return []


def should_expose_errors():
    return APP_MODE == "demo" or os.getenv("FLASK_DEBUG", "false").lower() == "true"
