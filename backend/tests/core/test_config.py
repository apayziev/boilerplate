from app.core.config import Settings


def test_app_name_override():
    settings = Settings(APP_NAME="Test App")
    assert settings.APP_NAME == "Test App"


def test_postgres_uri_is_assembled():
    settings = Settings(
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="password",
        POSTGRES_SERVER="db_server",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test_db",
    )
    assert settings.POSTGRES_URI == "user:password@db_server:5432/test_db"


def test_redis_url_is_assembled():
    settings = Settings(REDIS_HOST="redis_host", REDIS_PORT=6379)
    assert settings.REDIS_URL == "redis://redis_host:6379"
