SOURCES = {
    "bbc": {
        "domain": "https://www.bbc.com",
        "rss_url": "http://feeds.bbci.co.uk/news/rss.xml",
        "include_patterns": ["/articles/"],
        "exclude_patterns": [
            "/video/",
            "/audio/",
            "/topics/"
        ]
    },

    "indianexpress": {
        "domain": "https://indianexpress.com",
        "rss_url": "https://indianexpress.com/feed/",
        "include_patterns": ["/article/"],
        "exclude_patterns": [
            "/section/",
            "/trending/"
        ]
    }
}