from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase

ARTICLES_SCHEMA = "articles"


class ArticleBase(DeclarativeBase):
    pass


class Article(ArticleBase):
    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("hash"),
        UniqueConstraint("source_url"),
        Index("idx_articles_hash", "hash", postgresql_using="hash"),
        Index(
            "idx_articles_fts",
            text("to_tsvector('english', headline || ' ' || body_text)"),
            postgresql_using="gin",
        ),
        {"schema": ARTICLES_SCHEMA},
    )

    id = Column(BigInteger, primary_key=True)
    hash = Column(String(80), nullable=False)
    source_url = Column(Text, nullable=False)
    headline = Column(Text, nullable=False)
    reporters = Column(ARRAY(Text), nullable=False, server_default=text("'{}'"))
    body_text = Column(Text, nullable=False)
    media_urls = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    language = Column(String(10), nullable=False, server_default=text("'en'"))
    headline_original = Column(Text)
    body_text_original = Column(Text)
    reporters_original = Column(ARRAY(Text))
