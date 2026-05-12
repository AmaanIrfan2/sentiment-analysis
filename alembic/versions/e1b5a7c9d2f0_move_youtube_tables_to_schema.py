"""move youtube tables to youtube schema

Revision ID: e1b5a7c9d2f0
Revises: c4d3e2f10a87
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e1b5a7c9d2f0"
down_revision: Union[str, Sequence[str], None] = "c4d3e2f10a87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

YOUTUBE_SCHEMA = "youtube"
TABLES = [
    "channels",
    "videos",
    "comments",
    "linked_articles",
    "related_videos",
]


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {YOUTUBE_SCHEMA}")
    for table_name in TABLES:
        op.execute(
            f"""
            DO $$
            BEGIN
                IF to_regclass('public.{table_name}') IS NOT NULL
                   AND to_regclass('{YOUTUBE_SCHEMA}.{table_name}') IS NULL THEN
                    EXECUTE 'ALTER TABLE public.{table_name} SET SCHEMA {YOUTUBE_SCHEMA}';
                END IF;
            END
            $$;
            """
        )


def downgrade() -> None:
    for table_name in reversed(TABLES):
        op.execute(
            f"""
            DO $$
            BEGIN
                IF to_regclass('{YOUTUBE_SCHEMA}.{table_name}') IS NOT NULL
                   AND to_regclass('public.{table_name}') IS NULL THEN
                    EXECUTE 'ALTER TABLE {YOUTUBE_SCHEMA}.{table_name} SET SCHEMA public';
                END IF;
            END
            $$;
            """
        )
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.schemata
                WHERE schema_name = '{YOUTUBE_SCHEMA}'
            ) THEN
                EXECUTE 'DROP SCHEMA IF EXISTS {YOUTUBE_SCHEMA}';
            END IF;
        END
        $$;
        """
    )
