import requests
import asyncio
from bs4 import BeautifulSoup
from sentiment_analysis.articles.service import ingest_url
from sentiment_analysis.articles.sources import SOURCES

def fetch_sitemap_urls(sitemap_index):
    response = requests.get(sitemap_index)

    print("status: ",response.status_code)

    soup = BeautifulSoup(response.text,"xml")
    sitemap_tags = soup.find_all("loc")

    sitemap_urls = []

    for tag in sitemap_tags[:5]:
        sitemap_urls.append(tag.text)
    return sitemap_urls

def fetch_article_urls(sitemap_url, article_pattern):
    response = requests.get(sitemap_url)

    print("\nFetching:", sitemap_url)
    print("status:", response.status_code)

    soup = BeautifulSoup(response.text,"xml")

    url_tags = soup.find_all("url")
    #storing both date and url
    article_data = []

    for url_tag in url_tags:

        loc_tag = url_tag.find("loc")
        publication_tag = url_tag.find("news:publication_date")

        if not loc_tag or not publication_tag:
            continue
        url = loc_tag.text
        publication_date = publication_tag.text

        if article_pattern in url:
            article_data.append({
                "url": url,
                "publication_date": publication_date
            })
    return article_data

async def discover_articles(source_name, target_date):
    source = SOURCES[source_name]
    
    sitemap_index = source["sitemap"]
    article_pattern = source["article_pattern"]

    sitemap_urls = fetch_sitemap_urls(sitemap_index)

    filtered_articles = []

    for sitemap in sitemap_urls:
        article_data = fetch_article_urls(sitemap,article_pattern)

        for article in article_data:
            publication_date = article["publication_date"]

            if publication_date.startswith(target_date):
                filtered_articles.append(article)

    print(f"\nFound {len(filtered_articles)} matching articles")
        
    for article in filtered_articles[:5]:

        url = article["url"]
        publication_date = article["publication_date"]

        print("\nIngesting article:")
        print(url)
        print("Publication Date:", publication_date)

        try:
            article_hash = await ingest_url(url)

            print("\nSuccessfully ingested:")
            print(article_hash)
        except Exception as e:
            print("\nFailed to ingest:")
            print(url)
            print("Error:", e)
    
async def main():
    await discover_articles("bbc","2026-05-20")

if __name__ == "__main__":
    asyncio.run(main())