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


class KGElement(ArticleBase):
    __tablename__ = "kg_elements"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('PERSON','ORGANIZATION','LOCATION','COUNTRY','COMPANY','EVENT')",
            name="ck_kg_elements_entity_type",
        ),
        UniqueConstraint("article_hash", "name", "entity_type"),
        Index("idx_kg_elements_hash", "article_hash"),
        Index("idx_kg_elements_type", "entity_type"),
        Index("idx_kg_elements_name", "name"),
        {"schema": ARTICLES_SCHEMA},
    )

    id = Column(BigInteger, primary_key=True)
    article_hash = Column(
        String(80),
        ForeignKey(f"{ARTICLES_SCHEMA}.articles.hash", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(Text, nullable=False)
    entity_type = Column(String(30), nullable=False)


class KGRelation(ArticleBase):
    __tablename__ = "kg_relations"
    __table_args__ = (
        UniqueConstraint("article_hash", "subject_id", "object_id", "relation"),
        Index("idx_kg_relations_hash", "article_hash"),
        Index("idx_kg_relations_subject", "subject_id"),
        Index("idx_kg_relations_object", "object_id"),
        {"schema": ARTICLES_SCHEMA},
    )

    id = Column(BigInteger, primary_key=True)
    article_hash = Column(
        String(80),
        ForeignKey(f"{ARTICLES_SCHEMA}.articles.hash", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id = Column(
        BigInteger,
        ForeignKey(f"{ARTICLES_SCHEMA}.kg_elements.id", ondelete="CASCADE"),
        nullable=False,
    )
    object_id = Column(
        BigInteger,
        ForeignKey(f"{ARTICLES_SCHEMA}.kg_elements.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation = Column(String(100), nullable=False)
