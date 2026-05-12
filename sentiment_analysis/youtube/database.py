from sentiment_analysis.database import get_session  # noqa: F401
from sentiment_analysis.db_migrations import run_migrations


def init_db() -> None:
    run_migrations()
