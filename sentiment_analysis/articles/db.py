import json
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from sentiment_analysis.articles.models import ARTICLES_SCHEMA, Article
from sentiment_analysis.database import get_session  # noqa: F401

logger = logging.getLogger(__name__)


def already_ingested(session: Session, url: str) -> str | None:
    """Return the hash if this URL was already ingested, else None."""
    article = session.query(Article).filter_by(source_url=url).first()
    return article.hash if article else None


def save_article(
    session: Session,
    source_url: str,
    source_name: str,
    publish_dt,
    headline: str,
    body_text: str,
    reporters: list[str],
    media_urls: list[dict],
    language: str = "en",
    headline_original: str | None = None,
    body_text_original: str | None = None,
    reporters_original: list[str] | None = None,
) -> str:
    """
    Generate a unique hash and insert the article row. Returns the hash.
    Uses SELECT ... FOR UPDATE to ensure unique sequences.
    """
    now = datetime.utcnow()
    effective_dt = publish_dt or now
    date_str = effective_dt.strftime("%d%m%Y")
    time_str = effective_dt.strftime("%H%M%S") if publish_dt else "000000"
    prefix = f"{source_name}-{date_str}-{time_str}"

    # Lock matching rows to safely determine next sequence number
    locked_rows = (
        session.query(Article)
        .filter(Article.hash.like(f"{prefix}-%"))
        .with_for_update()
        .all()
    )
    count = len(locked_rows)
    sequence = count + 1
    article_hash = f"{prefix}-{sequence:03d}"

    article = Article(
        hash=article_hash,
        source_url=source_url,
        headline=headline,
        reporters=reporters,
        body_text=body_text,
        media_urls=json.dumps(media_urls),
        language=language,
        headline_original=headline_original,
        body_text_original=body_text_original,
        reporters_original=reporters_original,
    )
    session.add(article)
    session.flush()

    return article_hash


def save_elements_and_relations(
    session: Session,
    article_hash: str,
    elements: list[dict],
    relations: list[dict],
) -> None:
    """Upsert elements then relations."""
    name_to_id: dict[str, int] = {}

    for elem in elements:
        name = elem["name"].strip()
        entity_type = elem["entity_type"].upper()

        stmt = text(f"""
            INSERT INTO {ARTICLES_SCHEMA}.kg_elements (article_hash, name, entity_type)
            VALUES (:article_hash, :name, :entity_type)
            ON CONFLICT (article_hash, name, entity_type) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """)
        result = session.execute(
            stmt,
            {"article_hash": article_hash, "name": name, "entity_type": entity_type},
        )
        row = result.fetchone()
        if row:
            name_to_id[name] = row[0]

    for rel in relations:
        subject_id = name_to_id.get(rel["subject"])
        object_id = name_to_id.get(rel["object"])
        relation = rel["relation"].upper()

        if not subject_id or not object_id or not relation:
            continue

        stmt = text(f"""
            INSERT INTO {ARTICLES_SCHEMA}.kg_relations (article_hash, subject_id, object_id, relation)
            VALUES (:article_hash, :subject_id, :object_id, :relation)
            ON CONFLICT DO NOTHING
        """)
        session.execute(
            stmt,
            {
                "article_hash": article_hash,
                "subject_id": subject_id,
                "object_id": object_id,
                "relation": relation,
            },
        )
