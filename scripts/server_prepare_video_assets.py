#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
DEFAULT_DESCRIPTION = (
    "本页面展示 AI 数字人短视频生成效果，适合需要批量制作短视频、广告素材、产品展示视频和推广内容的项目参考。"
    "如需了解视频制作、批量生成或 Google 搜索获客页面，可以通过联系页提交项目信息。"
)
DEFAULT_SUMMARY = "展示 AI 数字人视频生成效果，并提供视频制作、素材准备和推广页面承接说明。"
DEFAULT_TAGS = ["AI视频生成", "数字人视频", "短视频制作"]
DEFAULT_CONTACT_NOTE = "如需了解视频制作、批量生成或推广页面承接，可以通过联系页提交项目信息。"
DEFAULT_RELATED_LINKS = [
    "/services/traffic-acquisition/",
    "/services/ad-campaign-support/",
    "/platforms/google/",
    "/contact/",
]


@dataclass
class PlanItem:
    source_path: Path
    target_path: Path
    thumbnail_path: Path
    slug: str
    index: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare uploaded video assets on the RN server.")
    parser.add_argument("--videos-dir", required=True, help="Directory containing uploaded videos.")
    parser.add_argument("--thumbnails-dir", required=True, help="Directory for generated thumbnails.")
    parser.add_argument("--base-slug", required=True, help="Base slug, for example ai-video-service.")
    parser.add_argument("--title-prefix", required=True, help="Title prefix for generated JSON records.")
    parser.add_argument("--asset-base-url", required=True, help="Public asset base URL, for example https://video.9hwh.com.")
    parser.add_argument("--output-json", required=True, help="Path to write JSON import records.")
    parser.add_argument("--output-csv", required=True, help="Path to write CSV import records.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of unnormalized videos to process.")
    parser.add_argument("--start-index", type=int, default=1, help="First numeric suffix to try. Default: 1.")
    parser.add_argument("--overwrite-thumbnails", action="store_true", help="Overwrite thumbnails when they already exist.")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without renaming, thumbnailing, or writing output.")
    return parser.parse_args()


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"[FAIL] required binary not found: {name}")


def validate_args(args: argparse.Namespace) -> tuple[Path, Path]:
    require_binary("ffmpeg")
    require_binary("ffprobe")
    videos_dir = Path(args.videos_dir)
    thumbnails_dir = Path(args.thumbnails_dir)
    if not videos_dir.exists() or not videos_dir.is_dir():
        raise SystemExit(f"[FAIL] videos-dir does not exist: {videos_dir}")
    if args.start_index < 1:
        raise SystemExit("[FAIL] --start-index must be >= 1")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("[FAIL] --limit must be >= 1")
    if not args.dry_run:
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
    return videos_dir, thumbnails_dir


def conforming_pattern(base_slug: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(base_slug)}-(\d{{3}})\.mp4$")


def is_video_file(path: Path) -> bool:
    return path.is_file() and not path.name.startswith(".") and path.suffix.lower() in VIDEO_EXTENSIONS and path.stat().st_size > 0


def scan_videos(videos_dir: Path) -> list[Path]:
    return sorted((path for path in videos_dir.iterdir() if is_video_file(path)), key=lambda item: item.name.lower())


def collect_used_indices(files: list[Path], base_slug: str) -> set[int]:
    pattern = conforming_pattern(base_slug)
    used = set()
    for path in files:
        match = pattern.fullmatch(path.name)
        if match:
            used.add(int(match.group(1)))
    return used


def next_available_index(start: int, used: set[int], videos_dir: Path, base_slug: str) -> int:
    index = start
    while index in used or (videos_dir / f"{base_slug}-{index:03d}.mp4").exists():
        used.add(index)
        index += 1
    used.add(index)
    return index


def build_plan(args: argparse.Namespace, videos_dir: Path, thumbnails_dir: Path) -> list[PlanItem]:
    files = scan_videos(videos_dir)
    pattern = conforming_pattern(args.base_slug)
    used = collect_used_indices(files, args.base_slug)
    plan = []
    start = args.start_index

    for source_path in files:
        if pattern.fullmatch(source_path.name):
            print(f"[SKIP] already normalized: {source_path.name}")
            continue
        if args.limit is not None and len(plan) >= args.limit:
            break
        index = next_available_index(start, used, videos_dir, args.base_slug)
        start = index + 1
        slug = f"{args.base_slug}-{index:03d}"
        plan.append(
            PlanItem(
                source_path=source_path,
                target_path=videos_dir / f"{slug}.mp4",
                thumbnail_path=thumbnails_dir / f"{slug}.jpg",
                slug=slug,
                index=index,
            )
        )
    return plan


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def probe_duration(video_path: Path) -> int:
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
    )
    if result.returncode != 0:
        raise SystemExit(f"[FAIL] ffprobe failed for {video_path}: {result.stderr.strip()}")
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise SystemExit(f"[FAIL] invalid ffprobe duration for {video_path}: {result.stdout.strip()}") from exc
    return max(1, int(math.ceil(duration)))


def create_thumbnail(video_path: Path, thumbnail_path: Path, overwrite: bool) -> None:
    if thumbnail_path.exists() and not overwrite:
        print(f"[SKIP] thumbnail exists: {thumbnail_path}")
        return
    attempts = [
        ["ffmpeg", "-y", "-ss", "2", "-i", str(video_path), "-frames:v", "1", "-q:v", "2", str(thumbnail_path)],
        ["ffmpeg", "-y", "-ss", "0.5", "-i", str(video_path), "-frames:v", "1", "-q:v", "2", str(thumbnail_path)],
    ]
    last_error = ""
    for command in attempts:
        result = run_command(command)
        if result.returncode == 0 and thumbnail_path.exists() and thumbnail_path.stat().st_size > 0:
            return
        last_error = result.stderr.strip()
    raise SystemExit(f"[FAIL] ffmpeg thumbnail failed for {video_path}: {last_error}")


def asset_url(asset_base_url: str, folder: str, filename: str) -> str:
    return asset_base_url.rstrip("/") + f"/{folder}/{filename}"


def record_for_item(args: argparse.Namespace, item: PlanItem, duration_seconds: int) -> dict:
    suffix = f"{item.index:03d}"
    title = f"{args.title_prefix} {suffix}"
    return {
        "id": f"auto-{suffix}",
        "status": "published",
        "slug": item.slug,
        "title": title,
        "h1": title,
        "description": DEFAULT_DESCRIPTION,
        "summary": DEFAULT_SUMMARY,
        "video_file": asset_url(args.asset_base_url, "videos", f"{item.slug}.mp4"),
        "thumbnail": asset_url(args.asset_base_url, "thumbnails", f"{item.slug}.jpg"),
        "duration_seconds": duration_seconds,
        "upload_date": date.today().isoformat(),
        "tags": DEFAULT_TAGS,
        "contact_note": DEFAULT_CONTACT_NOTE,
        "related_links": DEFAULT_RELATED_LINKS,
        "source_filename": item.source_path.name,
    }


def write_json(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["slug", "source_filename", "video_path", "thumbnail_path", "video_url", "thumbnail_url", "duration_seconds", "title"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fix_permissions(root: Path) -> None:
    for command in (
        ["chown", "-R", "www-data:www-data", str(root)],
        ["chmod", "-R", "755", str(root)],
    ):
        result = run_command(command)
        if result.returncode != 0:
            raise SystemExit(f"[FAIL] permission command failed: {' '.join(command)}\n{result.stderr.strip()}")


def main() -> int:
    args = parse_args()
    videos_dir, thumbnails_dir = validate_args(args)
    plan = build_plan(args, videos_dir, thumbnails_dir)
    if not plan:
        print("[OK] no unnormalized videos to process")
        return 0

    print("[PLAN]")
    for item in plan:
        print(f"{item.source_path.name} -> {item.target_path.name}; thumbnail -> {item.thumbnail_path.name}")
    if args.dry_run:
        print(f"[DRY-RUN] planned {len(plan)} rename(s); no files changed")
        return 0

    records = []
    csv_rows = []
    for item in plan:
        if item.target_path.exists():
            raise SystemExit(f"[FAIL] target already exists, refusing to overwrite: {item.target_path}")
        try:
            item.source_path.rename(item.target_path)
        except OSError as exc:
            raise SystemExit(f"[FAIL] rename failed: {item.source_path} -> {item.target_path}: {exc}") from exc
        duration_seconds = probe_duration(item.target_path)
        create_thumbnail(item.target_path, item.thumbnail_path, args.overwrite_thumbnails)
        record = record_for_item(args, item, duration_seconds)
        records.append(record)
        csv_rows.append(
            {
                "slug": item.slug,
                "source_filename": item.source_path.name,
                "video_path": str(item.target_path),
                "thumbnail_path": str(item.thumbnail_path),
                "video_url": record["video_file"],
                "thumbnail_url": record["thumbnail"],
                "duration_seconds": duration_seconds,
                "title": record["title"],
            }
        )

    write_json(Path(args.output_json), records)
    write_csv(Path(args.output_csv), csv_rows)
    fix_permissions(videos_dir.parent)
    print(f"[OK] processed {len(records)} video(s)")
    print(f"[OK] wrote JSON: {args.output_json}")
    print(f"[OK] wrote CSV: {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
