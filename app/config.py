import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://radius:radius@localhost:5432/radius"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FERNET_KEY = os.environ.get("FERNET_KEY")
    RADIUS_SSH_HOST = os.environ.get("RADIUS_SSH_HOST", "192.168.38.3")
    RADIUS_SSH_USER = os.environ.get("RADIUS_SSH_USER", "tecser")
    RADIUS_SSH_PASSWORD = os.environ.get("RADIUS_SSH_PASSWORD")

    # Session cookie - allow cross-domain redirect (Google OAuth)
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True

    # Google OAuth (Portal Registro)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    WIFI_SSID_NAME = os.environ.get("WIFI_SSID_NAME", "Gaman-WiFi")
