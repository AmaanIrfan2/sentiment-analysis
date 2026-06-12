import logging

from langdetect import LangDetectException, detect

from sentiment_analysis.articles import db, scraper, translator
from sentiment_analysis.database import get_session

logger = logging.getLogger(__name__)


async def ingest_url(url: str,browser) -> str:
    with get_session() as session:
        existing_hash = db.already_ingested(session, url)
        if existing_hash:
            logger.info("Already ingested: %s", existing_hash)
            return existing_hash

    logger.info("Scraping %s", url)
    article = await scraper.scrape(url,browser)
    logger.info("Scraped: %s", article["headline"])

    headline_original = None
    body_text_original = None
    reporters_original = None
    language = "en"

    try:
        language = detect(article["body_text"])
    except LangDetectException:
        pass

    if language == "bn":
        logger.info("Bangla article detected, translating to English")
        headline_original = article["headline"]
        body_text_original = article["body_text"]
        reporters_original = article["reporters"]
        article["headline"] = translator.translate_bn_to_en(article["headline"])
        article["body_text"] = translator.translate_bn_to_en(article["body_text"])
        article["reporters"] = [
            translator.translate_bn_to_en(name) for name in article["reporters"]
        ]

    with get_session() as session:
        article_hash = db.save_article(
            session,
            source_url=url,
            source_name=article["source_name"],
            publish_dt=article["publish_dt"],
            headline=article["headline"],
            body_text=article["body_text"],
            reporters=article["reporters"],
            media_urls=article["media_urls"],
            language=language,
            headline_original=headline_original,
            body_text_original=body_text_original,
            reporters_original=reporters_original,
        )

    logger.info("Ingested article %s", article_hash)
    return article_hash
