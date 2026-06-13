import argparse
import asyncio

from sentiment_analysis.config import setup_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Unified sentiment analysis pipeline for web articles and YouTube videos.",
    )
    root = parser.add_subparsers(dest="service", required=True)

    root.add_parser("init", help="Initialise database schemas and run migrations")

    p_articles = root.add_parser("articles", help="Article ingestion commands")
    articles_sub = p_articles.add_subparsers(dest="command", required=True)
    p_ingest = articles_sub.add_parser("ingest", help="Ingest an article URL into the KG")
    p_ingest.add_argument("url")

    p_discover = articles_sub.add_parser(
        "discover",
        help="Discover and ingest articles from a source"
    )
    p_discover.add_argument("--source", required=True)
    p_discover.add_argument(
        "--method",
        choices=["rss", "sitemap"],
        default="rss"
    )
    p_discover.add_argument(
        "--limit",
        type=int,
        default=10
    )

    p_youtube = root.add_parser("youtube", help="YouTube ingestion commands")
    youtube_sub = p_youtube.add_subparsers(dest="command", required=True)

    p_add = youtube_sub.add_parser("add-channel", help="Register a YouTube channel")
    p_add.add_argument("--channel-id", required=True)
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--url", required=True)

    p_scrape = youtube_sub.add_parser("scrape", help="Queue a channel scrape")
    p_scrape.add_argument("--channel-id", required=True)
    p_scrape.add_argument("--limit", type=int, default=None)

    youtube_sub.add_parser("status", help="Show YouTube processing status")

    p_retry = youtube_sub.add_parser("retry", help="Retry pending or processing videos")
    p_retry.add_argument("--channel-id", required=True)

    return parser


def main() -> None:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.service == "init":
        from sentiment_analysis.db_migrations import run_migrations

        run_migrations()
        return

    if args.service == "articles":

        if args.command == "ingest":
            from playwright.async_api import async_playwright
            from sentiment_analysis.articles.service import ingest_url

            async def run_ingest():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    try:
                        article_hash = await ingest_url(args.url, browser)
                        print(f"Ingested article: {article_hash}")
                    finally:
                        await browser.close()

            asyncio.run(run_ingest())

        elif args.command == "discover":
            from sentiment_analysis.articles.discover import discover_articles

            asyncio.run(
                discover_articles(
                    source_name=args.source,
                    method=args.method,
                    limit=args.limit,
                )
            )

        return

    from sentiment_analysis.youtube import service as youtube_service

    commands = {
        "add-channel": youtube_service.cmd_add_channel,
        "scrape": youtube_service.cmd_scrape,
        "status": youtube_service.cmd_status,
        "retry": youtube_service.cmd_retry,
    }
    commands[args.command](args)

if __name__ == "__main__":
    main()