# Sentiment Analysis

This is a single unified project for two ingestion services:

- web article scraping plus knowledge graph extraction
- YouTube channel scraping plus linked article discovery

The canonical code lives in `sentiment_analysis/` and is run through the root `main.py` CLI.

## Structure

- `sentiment_analysis/articles/`: article scraping, translation, and KG extraction
- `sentiment_analysis/youtube/`: YouTube channel, video, comments, and related metadata ingestion
- `alembic/`: YouTube schema migrations
- `main.py`: unified entrypoint
- `requirements.txt`: combined dependencies for the full project
- `.env.example`: shared environment template

## Database Layout

The project uses one PostgreSQL database with service-owned schemas:

- `articles.articles`
- `articles.kg_elements`
- `articles.kg_relations`
- `youtube.channels`
- `youtube.videos`
- `youtube.comments`
- `youtube.related_videos`
- `youtube.linked_articles`

Both schema families are now migration-managed through Alembic.
The article runtime still uses `asyncpg` for queries and inserts, but schema creation no longer happens in application code.
The migration chain also includes schema-move steps for legacy `public.*` tables.

## Common commands

```bash
python3 main.py init all
python3 main.py articles ingest "https://example.com/article"
python3 main.py youtube add-channel --channel-id UCxxxx --name "Channel Name" --url "https://www.youtube.com/@channel"
python3 main.py youtube scrape --channel-id UCxxxx
python3 main.py youtube status
```
