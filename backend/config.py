import os
from dotenv import load_dotenv

load_dotenv()

APP_MODE = os.getenv("APP_MODE", "demo").strip().lower()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "textgrader")
JWT_SECRET = os.getenv("JWT_SECRET", "quintana-demo-secret")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "8"))
ANALYTICS_CACHE_TTL_SECONDS = int(os.getenv("ANALYTICS_CACHE_TTL_SECONDS", "300"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
PASSWORD_RESET_DEV_MODE = os.getenv("PASSWORD_RESET_DEV_MODE", "true").strip().lower() == "true"
PASSWORD_RESET_EXPIRATION_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRATION_MINUTES", "30"))
PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_WINDOW_MINUTES", "15"))
PASSWORD_RESET_RATE_LIMIT_EMAIL_MAX = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_EMAIL_MAX", "3"))
PASSWORD_RESET_RATE_LIMIT_IP_MAX = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_IP_MAX", "10"))
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER).strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() == "true"


def get_cors_origins():
    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    if APP_MODE == "demo":
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    return []


def should_expose_errors():
    return APP_MODE == "demo" or os.getenv("FLASK_DEBUG", "false").lower() == "true"
