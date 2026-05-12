from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from sentiment_analysis.config import DATABASE_URL


def _ensure_database_exists() -> None:
    url = make_url(DATABASE_URL)
    db_name = url.database
    maintenance_url = url.set(database="postgres")
    maint_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    with maint_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db"),
            {"db": db_name},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    maint_engine.dispose()


def run_migrations() -> None:
    _ensure_database_exists()
    alembic_cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
