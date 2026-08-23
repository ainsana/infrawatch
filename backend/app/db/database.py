from sqlalchemy import URL, create_engine, text

from backend.app.core.config import get_settings


def build_database_url() -> URL:
    settings = get_settings()

    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )


engine = create_engine(
    build_database_url(),
    pool_pre_ping=True,
)


def check_database_connection() -> int:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one()
