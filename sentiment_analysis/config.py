import logging
import os

from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    def load_dotenv(*args, **kwargs) -> None:
        return None


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

NAS_BASE_PATH = os.getenv("NAS_BASE_PATH", "/Volumes/Downloaded YT Videos")
CAPTIONS_BASE_PATH = os.getenv("CAPTIONS_BASE_PATH", "/Volumes/Captions- YT Videos")
AUDIO_BASE_PATH = os.getenv("AUDIO_BASE_PATH", "/Volumes/YT Audios")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

REQUEST_DELAY_SECONDS = int(os.getenv("REQUEST_DELAY_SECONDS", "3"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
VIDEO_QUALITY = os.getenv("VIDEO_QUALITY", "1080")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-pro")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "8000"))

TRANSLATION_MODEL = os.getenv("TRANSLATION_MODEL", "Helsinki-NLP/opus-mt-bn-en")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
