"""add articles schema

Revision ID: f2c7b1e4a8d3
Revises: e1b5a7c9d2f0
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f2c7b1e4a8d3"
down_revision: Union[str, Sequence[str], None] = "e1b5a7c9d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ARTICLES_SCHEMA = "articles"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {ARTICLES_SCHEMA}")

    for table_name in ("articles", "kg_elements", "kg_relations"):
        op.execute(
            f"""
            DO $$
            BEGIN
                IF to_regclass('public.{table_name}') IS NOT NULL
                   AND to_regclass('{ARTICLES_SCHEMA}.{table_name}') IS NULL THEN
                    EXECUTE 'ALTER TABLE public.{table_name} SET SCHEMA {ARTICLES_SCHEMA}';
                END IF;
            END
            $$;
            """
        )

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names(schema=ARTICLES_SCHEMA))

    if "articles" not in existing:
        op.create_table(
            "articles",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("hash", sa.String(length=80), nullable=False),
            sa.Column("source_url", sa.Text(), nullable=False),
            sa.Column("headline", sa.Text(), nullable=False),
            sa.Column("reporters", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
            sa.Column("body_text", sa.Text(), nullable=False),
            sa.Column("media_urls", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
            sa.Column("headline_original", sa.Text(), nullable=True),
            sa.Column("body_text_original", sa.Text(), nullable=True),
            sa.Column("reporters_original", postgresql.ARRAY(sa.Text()), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("hash"),
            sa.UniqueConstraint("source_url"),
            schema=ARTICLES_SCHEMA,
        )

    for col, definition in (
        ("language", "VARCHAR(10) NOT NULL DEFAULT 'en'"),
        ("headline_original", "TEXT"),
        ("body_text_original", "TEXT"),
        ("reporters_original", "TEXT[]"),
    ):
        op.execute(
            f"""
            ALTER TABLE {ARTICLES_SCHEMA}.articles
            ADD COLUMN IF NOT EXISTS {col} {definition}
            """
        )

    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_articles_hash
        ON {ARTICLES_SCHEMA}.articles USING hash (hash)
        """
    )
    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_articles_fts
        ON {ARTICLES_SCHEMA}.articles
        USING GIN(to_tsvector('english', headline || ' ' || body_text))
        """
    )

    if "kg_elements" not in existing:
        op.create_table(
            "kg_elements",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("article_hash", sa.String(length=80), nullable=False),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("entity_type", sa.String(length=30), nullable=False),
            sa.ForeignKeyConstraint(["article_hash"], [f"{ARTICLES_SCHEMA}.articles.hash"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("article_hash", "name", "entity_type"),
            sa.CheckConstraint(
                "entity_type IN ('PERSON','ORGANIZATION','LOCATION','COUNTRY','COMPANY','EVENT')",
                name="ck_kg_elements_entity_type",
            ),
            schema=ARTICLES_SCHEMA,
        )

    op.execute(f"CREATE INDEX IF NOT EXISTS idx_kg_elements_hash ON {ARTICLES_SCHEMA}.kg_elements (article_hash)")
    op.execute(f"CREATE INDEX IF NOT EXISTS idx_kg_elements_type ON {ARTICLES_SCHEMA}.kg_elements (entity_type)")
    op.execute(f"CREATE INDEX IF NOT EXISTS idx_kg_elements_name ON {ARTICLES_SCHEMA}.kg_elements (name)")

    if "kg_relations" not in existing:
        op.create_table(
            "kg_relations",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("article_hash", sa.String(length=80), nullable=False),
            sa.Column("subject_id", sa.BigInteger(), nullable=False),
            sa.Column("object_id", sa.BigInteger(), nullable=False),
            sa.Column("relation", sa.String(length=100), nullable=False),
            sa.ForeignKeyConstraint(["article_hash"], [f"{ARTICLES_SCHEMA}.articles.hash"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["subject_id"], [f"{ARTICLES_SCHEMA}.kg_elements.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["object_id"], [f"{ARTICLES_SCHEMA}.kg_elements.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("article_hash", "subject_id", "object_id", "relation"),
            schema=ARTICLES_SCHEMA,
        )

    op.execute(f"CREATE INDEX IF NOT EXISTS idx_kg_relations_hash ON {ARTICLES_SCHEMA}.kg_relations (article_hash)")
    op.execute(f"CREATE INDEX IF NOT EXISTS idx_kg_relations_subject ON {ARTICLES_SCHEMA}.kg_relations (subject_id)")
    op.execute(f"CREATE INDEX IF NOT EXISTS idx_kg_relations_object ON {ARTICLES_SCHEMA}.kg_relations (object_id)")


def downgrade() -> None:
    op.drop_index("idx_kg_relations_object", schema=ARTICLES_SCHEMA, table_name="kg_relations")
    op.drop_index("idx_kg_relations_subject", schema=ARTICLES_SCHEMA, table_name="kg_relations")
    op.drop_index("idx_kg_relations_hash", schema=ARTICLES_SCHEMA, table_name="kg_relations")
    op.drop_index("idx_kg_elements_name", schema=ARTICLES_SCHEMA, table_name="kg_elements")
    op.drop_index("idx_kg_elements_type", schema=ARTICLES_SCHEMA, table_name="kg_elements")
    op.drop_index("idx_kg_elements_hash", schema=ARTICLES_SCHEMA, table_name="kg_elements")
    op.drop_index("idx_articles_fts", schema=ARTICLES_SCHEMA, table_name="articles")
    op.drop_index("idx_articles_hash", schema=ARTICLES_SCHEMA, table_name="articles")
    op.drop_table("kg_relations", schema=ARTICLES_SCHEMA)
    op.drop_table("kg_elements", schema=ARTICLES_SCHEMA)
    op.drop_table("articles", schema=ARTICLES_SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {ARTICLES_SCHEMA}")
