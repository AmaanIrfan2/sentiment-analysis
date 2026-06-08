import asyncio
import feedparser

from sentiment_analysis.articles.service import ingest_url
from sentiment_analysis.articles.sources import SOURCES
from trafilatura.sitemaps import sitemap_search


def is_article_url(url, source):

    for pattern in source["exclude_patterns"]:
        if pattern in url:
            return False

    for pattern in source["include_patterns"]:
        if pattern in url:
            return True

    return False


def fetch_rss_urls(rss_url):

    feed = feedparser.parse(rss_url)

    urls = []

    for entry in feed.entries:
        urls.append(entry.link)

    return urls


def fetch_sitemap_urls(domain):

    return sitemap_search(domain)


async def discover_articles(source_name, method):

    source = SOURCES[source_name]

    if method == "rss":

        urls = fetch_rss_urls(source["rss_url"])

    elif method == "sitemap":

        urls = fetch_sitemap_urls(source["domain"])

    else:
        raise ValueError("method must be 'rss' or 'sitemap'")

    print(f"Discovered {len(urls)} URLs")

    filtered_urls = []

    for url in urls:
        if is_article_url(url, source):
            filtered_urls.append(url)

    print(f"Filtered to {len(filtered_urls)} URLs")

    MAX_ARTICLES = 10

    for url in filtered_urls[:MAX_ARTICLES]:

        print("\nIngesting article:")
        print(url)

        try:
            article_hash = await ingest_url(url)

            print("\nSuccessfully ingested:")
            print(article_hash)

        except Exception as e:
            print("\nFailed to ingest:")
            print(url)
            print("Error:", e)


async def main():

    # await discover_articles(
    #     source_name="bbc",
    #     method="rss"
    # )

    await discover_articles(
        source_name="indianexpress",
        method="rss"
    )


if __name__ == "__main__":
    asyncio.run(main())