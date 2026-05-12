import re
import json
import logging
import time

import requests

from sentiment_analysis.config import REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

_HEADERS_API  = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
_HEADERS_PAGE = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
_CLIENT       = {"clientName": "WEB", "clientVersion": "2.20231219.04.00"}


def fetch_suggested_video_ids(video_id: str) -> list[str]:
    """
    Fetch sidebar suggested video IDs via the Innertube /next endpoint.
    Returns a list of YouTube video ID strings.
    """
    try:
        resp = requests.post(
            "https://www.youtube.com/youtubei/v1/next",
            headers=_HEADERS_API,
            json={"videoId": video_id, "context": {"client": _CLIENT}},
            timeout=10,
        )
        resp.raise_for_status()
        results = (
            resp.json()
            .get("contents", {})
            .get("twoColumnWatchNextResults", {})
            .get("secondaryResults", {})
            .get("secondaryResults", {})
            .get("results", [])
        )
        ids = [
            item["lockupViewModel"]["contentId"]
            for item in results
            if "lockupViewModel" in item and item["lockupViewModel"].get("contentId")
        ]
        time.sleep(REQUEST_DELAY_SECONDS)
        return ids
    except Exception as exc:
        logger.warning("[%s] fetch_suggested_video_ids failed: %s", video_id, exc)
        return []


def _get_end_screen_elements(video_id: str) -> tuple[list, str | None]:
    """
    Fetch and parse ytInitialPlayerResponse from the watch page.
    Returns (end screen elements list, raw page text for fallback URL extraction).
    """
    resp = requests.get(
        f"https://www.youtube.com/watch?v={video_id}",
        headers=_HEADERS_PAGE,
        timeout=10,
    )
    resp.raise_for_status()
    match = re.search(
        r"ytInitialPlayerResponse\s*=\s*(\{.*?\});\s*(?:var|window|</script)",
        resp.text,
        re.DOTALL,
    )
    if not match:
        return [], resp.text
    player_data = json.loads(match.group(1))
    elements = (
        player_data
        .get("endscreen", {})
        .get("endscreenRenderer", {})
        .get("elements", [])
    )
    return elements, resp.text


def fetch_end_screen_video_ids(video_id: str) -> list[str]:
    """
    Fetch end screen video IDs by scraping ytInitialPlayerResponse from the watch page.
    Only returns elements of style VIDEO (skips CHANNEL, WEBSITE, etc.).
    Returns a list of YouTube video ID strings.
    """
    try:
        elements, _ = _get_end_screen_elements(video_id)
        ids = []
        for el in elements:
            renderer = el.get("endscreenElementRenderer", {})
            if renderer.get("style") != "VIDEO":
                continue
            vid = renderer.get("endpoint", {}).get("watchEndpoint", {}).get("videoId")
            if vid:
                ids.append(vid)
        time.sleep(REQUEST_DELAY_SECONDS)
        return ids
    except Exception as exc:
        logger.warning("[%s] fetch_end_screen_video_ids failed: %s", video_id, exc)
        return []


def fetch_end_screen_urls(video_id: str) -> list[str]:
    """
    Fetch external article/website URLs from end screen WEBSITE elements.
    Returns a list of URL strings.
    """
    try:
        elements, _ = _get_end_screen_elements(video_id)
        urls = []
        for el in elements:
            renderer = el.get("endscreenElementRenderer", {})
            if renderer.get("style") != "WEBSITE":
                continue
            url = (
                renderer.get("endpoint", {})
                .get("urlEndpoint", {})
                .get("url", "")
            )
            # YouTube wraps external links in a redirect — unwrap it
            if "youtube.com/redirect" in url:
                q_match = re.search(r"[?&]q=([^&]+)", url)
                if q_match:
                    from urllib.parse import unquote
                    url = unquote(q_match.group(1))
            if url and url.startswith("http"):
                urls.append(url)
        time.sleep(REQUEST_DELAY_SECONDS)
        return urls
    except Exception as exc:
        logger.warning("[%s] fetch_end_screen_urls failed: %s", video_id, exc)
        return []
