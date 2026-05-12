import argparse
import logging

from sentiment_analysis.youtube.database import get_session, init_db
from sentiment_analysis.youtube.models import Channel, Video

logger = logging.getLogger(__name__)


def cmd_init(_args: argparse.Namespace) -> None:
    logger.info("Initialising YouTube schema")
    init_db()
    logger.info("Done")


def cmd_add_channel(args: argparse.Namespace) -> None:
    with get_session() as session:
        existing = session.query(Channel).filter_by(channel_id=args.channel_id).first()
        if existing:
            print(f"Channel '{args.channel_id}' already registered as '{existing.name}'.")
            return
        session.add(Channel(channel_id=args.channel_id, name=args.name, url=args.url))
    print(f"Added channel: {args.name} ({args.channel_id})")


def cmd_scrape(args: argparse.Namespace) -> None:
    from sentiment_analysis.youtube.tasks import scrape_channel

    with get_session() as session:
        channel = session.query(Channel).filter_by(channel_id=args.channel_id).first()
        if not channel:
            raise SystemExit(
                f"Channel '{args.channel_id}' not found. Register it first with add-channel."
            )
        channel_url = channel.url

    task = scrape_channel.delay(channel_url, limit=args.limit)
    print(f"Queued scrape for '{args.channel_id}' - task ID: {task.id}")


def cmd_status(_args: argparse.Namespace) -> None:
    with get_session() as session:
        channels = session.query(Channel).all()
        if not channels:
            print("No channels registered.")
            return

        for channel in channels:
            videos = channel.videos
            total = len(videos)
            processed = sum(1 for video in videos if video.status == "processed")
            processing = sum(1 for video in videos if video.status == "processing")
            failed = sum(1 for video in videos if video.status == "failed")
            pending = sum(1 for video in videos if video.status == "pending")

            print(
                f"\n{channel.name} ({channel.channel_id})\n"
                f"  total={total}  processed={processed}  "
                f"processing={processing}  failed={failed}  pending={pending}\n"
                f"  last scraped: {channel.last_scraped_at or 'never'}"
            )


def cmd_retry(args: argparse.Namespace) -> None:
    from sentiment_analysis.youtube.tasks import process_video

    with get_session() as session:
        channel = session.query(Channel).filter_by(channel_id=args.channel_id).first()
        if not channel:
            raise SystemExit(f"Channel '{args.channel_id}' not found.")

        stuck = (
            session.query(Video)
            .filter(
                Video.channel_id == channel.id,
                Video.status.in_(["pending", "processing"]),
            )
            .all()
        )
        if not stuck:
            print(f"No stuck videos for {channel.name}.")
            return

        channel_db_id = channel.id
        video_ids = [video.yt_video_id for video in stuck]
        for video in stuck:
            video.status = "pending"

    for index, video_id in enumerate(video_ids, start=1):
        process_video.delay(video_id, channel_db_id, index)

    print(f"Re-queued {len(video_ids)} stuck video(s) for processing.")
