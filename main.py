"""
main.py — YouTube Agent CLI

Usage:
    # Generate a video from a topic
    uv run python main.py create --topic "How an API request works"

    # Re-use a previously validated plan (skips LLM call)
    uv run python main.py create --topic "..." --use-cached-plan data/runs/<id>/plan.json

    # Upload a completed run (private by default)
    uv run python main.py upload --run-id <id>

    # Upload and make public
    uv run python main.py upload --run-id <id> --publish

Pipeline:
    NVIDIA Nemotron (OpenRouter) → VideoPlan → Asset Resolver → TTS
    → Remotion render → quality checks → YouTube upload (separate command)

This project does NOT use text-to-video generation.
Remotion composes licensed/static visual assets, programmatic diagrams,
narration, captions, and overlays into the final MP4.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.utility.load_envs import load_all_env
from src.utility.logging_config import setup_logging

logger = setup_logging()


def cmd_create(args: argparse.Namespace) -> int:
    """Create command: generate plan → assets → TTS → render → quality check."""
    from src.pipeline.run_pipeline import RunPipeline

    OPENROUTER_API_KEY, OPENROUTER_MODEL_NAME, _ = load_all_env()

    cached_plan = Path(args.use_cached_plan) if args.use_cached_plan else None
    if cached_plan and not cached_plan.exists():
        print(f"ERROR: --use-cached-plan file not found: {cached_plan}", file=sys.stderr)
        return 1

    pipeline = RunPipeline(
        topic=args.topic,
        open_router_model_name=OPENROUTER_MODEL_NAME,
        cached_plan_path=cached_plan,
    )


    print("yt-agent — Remotion Video Pipeline")

    print(f"  Topic:     {args.topic}")
    print(f"  Run ID:    {pipeline.run_id}")
    if cached_plan:
        print(f"  Plan:      {cached_plan} (cached)")


    try:
        mp4_path = pipeline.execute()
        print("  ✓ Render complete")
        print(f"  Output: {mp4_path}")
        print(f"  Run ID: {pipeline.run_id}")
        print("\nTo upload:")
        print(f"  uv run python main.py upload --run-id {pipeline.run_id} [for PRIVATE upload]")
        print(f"  uv run python main.py upload --run-id {pipeline.run_id} --publish [for PUBLIC upload]")
        
        return 0
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        logger.exception("Pipeline failed")
        return 1


def cmd_upload(args: argparse.Namespace) -> int:
    """Upload command: quality-check then upload an approved run to YouTube."""
    from pathlib import Path as _Path
    from src.pipeline.quality_checks import assert_run_ready_to_upload, QualityCheckError
    from src.youtube.video_uploader import upload_video

    _, _, youtube_config = load_all_env()

    run_dir = Path("data") / "runs" / args.run_id
    if not run_dir.exists():
        print(f"ERROR: Run directory not found: {run_dir}", file=sys.stderr)
        return 1

    # Quality gate
    try:
        assert_run_ready_to_upload(run_dir)
    except QualityCheckError as exc:
        print(f"\nQuality check failed — upload blocked:\n{exc}", file=sys.stderr)
        return 1

    privacy = "public" if args.publish else "private"

    print("=" * 60)
    print(f"  Uploading run: {args.run_id}")
    print(f"  Privacy:       {privacy.upper()}")
    print("=" * 60)

    try:
        upload_video(
            run_id=args.run_id,
            run_dir=run_dir,
            youtube_config=youtube_config,
            privacy_status=privacy,
        )
        return 0
    except Exception as exc:
        print(f"\nERROR: Upload failed: {exc}", file=sys.stderr)
        logger.exception("Upload failed")
        return 1


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-agent",
        description="YouTube Short generator — Remotion pipeline (no text-to-video APIs).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    create_p = sub.add_parser("create", help="Generate a video from a topic.")
    create_p.add_argument(
        "--topic",
        required=True,
        help='The video topic, e.g. "How an API request works"',
    )
    create_p.add_argument(
        "--use-cached-plan",
        metavar="PATH",
        default=None,
        help="Skip LLM call and use an existing plan.json file.",
    )

    # upload
    upload_p = sub.add_parser("upload", help="Upload a completed run to YouTube.")
    upload_p.add_argument(
        "--run-id",
        required=True,
        help="The UUID of the completed run to upload.",
    )
    upload_p.add_argument(
        "--publish",
        action="store_true",
        default=False,
        help="Make the video public (default: private).",
    )

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        sys.exit(cmd_create(args))
    elif args.command == "upload":
        sys.exit(cmd_upload(args))