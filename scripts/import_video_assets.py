# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VIDEOS_DATA = ROOT / "site_src" / "data" / "videos.json"
PUBLIC = ROOT / "site" / "public"
PUBLIC_VIDEOS = PUBLIC / "videos"
PUBLIC_THUMBNAILS = PUBLIC / "thumbnails"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

DEFAULT_DESCRIPTION = (
    "本页面展示 AI 数字人短视频生成效果，适合需要批量制作短视频、广告素材、"
    "产品展示视频和推广内容的项目参考。如需了解视频制作、批量生成或 Google "
    "搜索获客页面，可以通过联系页提交项目信息。"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import generated video assets into 9HWH /v/ landing pages")
    parser.add_argument("--input-dir", required=True, help="Directory containing generated video files")
    parser.add_argument("--title-prefix", required=True, help="Title prefix, for example: AI数字人视频生成服务")
    parser.add_argument("--base-slug", required=True, help="Base slug, for example: ai-video-service")
    parser.add_argument("--status", default="published", help="Video status, default: published")
    parser.add_argument("--limit", type=int, default=0, help="Only import the first N new videos")
    parser.add_argument("--dry-run", action="store_true", help="Print import plan without writing files")
    parser.add_argument("--overwrite-assets", action="store_true", help="Allow overwriting existing mp4/jpg assets")
    parser.add_argument("--start-index", type=int, default=0, help="Start numeric suffix; default infers from videos.json")
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def load_videos() -> list[dict[str, Any]]:
    if not VIDEOS_DATA.exists():
        fail(f"videos.json does not exist: {VIDEOS_DATA}")
    try:
        data = json.loads(VIDEOS_DATA.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        fail(f"invalid videos.json: {exc}")
    if not isinstance(data, list):
        fail("videos.json top-level value must be a list")
    return data


def write_videos(records: list[dict[str, Any]]) -> None:
    VIDEOS_DATA.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        fail(f"{name} not found in PATH")
    return path


def scan_videos(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        fail(f"input-dir does not exist: {input_dir}")
    if not input_dir.is_dir():
        fail(f"input-dir is not a directory: {input_dir}")
    videos = sorted(
        [path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS],
        key=lambda item: [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", item.name)],
    )
    if not videos:
        fail(f"no video files found in input-dir: {input_dir}")
    return videos


def find_sidecar_cover(video_path: Path) -> Path | None:
    for ext in COVER_EXTENSIONS:
        candidate = video_path.with_suffix(ext)
        if candidate.exists() and candidate.is_file():
            return candidate
        upper_candidate = video_path.with_suffix(ext.upper())
        if upper_candidate.exists() and upper_candidate.is_file():
            return upper_candidate
    return None


def ffprobe_duration(ffprobe: str, video_path: Path) -> int:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        fail(f"ffprobe failed for {video_path.name}: {result.stderr.strip() or result.stdout.strip()}")
    try:
        seconds = float(result.stdout.strip())
    except ValueError:
        fail(f"ffprobe returned invalid duration for {video_path.name}: {result.stdout.strip()}")
    duration = int(math.ceil(seconds))
    if duration <= 0:
        fail(f"duration_seconds must be positive for {video_path.name}")
    return duration


def run_ffmpeg(cmd: list[str], label: str) -> bool:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True
    sys.stderr.write(f"[WARN] {label} failed: {result.stderr.strip() or result.stdout.strip()}\n")
    return False


def generate_thumbnail(ffmpeg: str, video_path: Path, output_path: Path, *, overwrite: bool) -> None:
    flag = "-y" if overwrite else "-n"
    for seek in ("2", "0.5"):
        cmd = [
            ffmpeg,
            flag,
            "-ss",
            seek,
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ]
        if run_ffmpeg(cmd, f"thumbnail at {seek}s for {video_path.name}"):
            return
    fail(f"could not generate thumbnail for {video_path.name}")


def write_video_asset(ffmpeg: str, video_path: Path, output_path: Path, *, overwrite: bool) -> None:
    if video_path.suffix.lower() == ".mp4":
        if output_path.exists() and not overwrite:
            fail(f"video asset already exists: {output_path}")
        shutil.copy2(video_path, output_path)
        return

    flag = "-y" if overwrite else "-n"
    remux_cmd = [ffmpeg, flag, "-i", str(video_path), "-c", "copy", str(output_path)]
    if run_ffmpeg(remux_cmd, f"video remux for {video_path.name}"):
        return

    transcode_cmd = [
        ffmpeg,
        flag,
        "-i",
        str(video_path),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    if run_ffmpeg(transcode_cmd, f"video transcode for {video_path.name}"):
        return

    fail(f"could not convert video to mp4: {video_path.name}")


def convert_cover(ffmpeg: str, cover_path: Path, output_path: Path, *, overwrite: bool) -> None:
    if cover_path.suffix.lower() in {".jpg", ".jpeg"}:
        if output_path.exists() and not overwrite:
            fail(f"thumbnail already exists: {output_path}")
        shutil.copy2(cover_path, output_path)
        return
    flag = "-y" if overwrite else "-n"
    cmd = [ffmpeg, flag, "-i", str(cover_path), "-frames:v", "1", "-q:v", "2", str(output_path)]
    if not run_ffmpeg(cmd, f"cover conversion for {cover_path.name}"):
        fail(f"could not convert sidecar cover: {cover_path.name}")


def used_auto_ids(records: list[dict[str, Any]]) -> set[int]:
    out: set[int] = set()
    for item in records:
        raw = str(item.get("id", ""))
        if raw.startswith("auto-"):
            suffix = raw.removeprefix("auto-")
            if suffix.isdigit():
                out.add(int(suffix))
    return out


def next_auto_id(used: set[int], start_at: int = 1) -> str:
    index = max(1, start_at)
    while index in used:
        index += 1
    used.add(index)
    return f"auto-{index:03d}"


def existing_slug_numbers(records: list[dict[str, Any]], base_slug: str) -> set[int]:
    prefix = f"{base_slug}-"
    out: set[int] = set()
    for item in records:
        slug = str(item.get("slug", ""))
        if slug.startswith(prefix):
            suffix = slug[len(prefix) :]
            if suffix.isdigit():
                out.add(int(suffix))
    return out


def next_slug(base_slug: str, used_slugs: set[str], used_numbers: set[int], start_at: int) -> tuple[str, int]:
    index = max(1, start_at)
    while True:
        slug = f"{base_slug}-{index:03d}"
        if slug not in used_slugs:
            used_slugs.add(slug)
            used_numbers.add(index)
            return slug, index
        index += 1


def infer_start_index(args: argparse.Namespace, records: list[dict[str, Any]], base_slug: str) -> int:
    if int(args.start_index or 0) > 0:
        return int(args.start_index)
    numbers = existing_slug_numbers(records, base_slug)
    return (max(numbers) + 1) if numbers else 1


def source_filenames(records: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("source_filename", "")).strip().lower() for item in records if item.get("source_filename")}


def ensure_asset_can_write(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        fail(f"asset already exists, use --overwrite-assets to replace: {path}")


def build_record(
    *,
    video_path: Path,
    slug: str,
    index: int,
    auto_id: str,
    status: str,
    title_prefix: str,
    duration_seconds: int,
) -> dict[str, Any]:
    title = f"{title_prefix} {index:03d}"
    return {
        "id": auto_id,
        "status": status,
        "slug": slug,
        "title": title,
        "h1": title,
        "description": DEFAULT_DESCRIPTION,
        "summary": DEFAULT_SUMMARY,
        "video_file": f"/videos/{slug}.mp4",
        "thumbnail": f"/thumbnails/{slug}.jpg",
        "duration_seconds": duration_seconds,
        "upload_date": date.today().isoformat(),
        "tags": DEFAULT_TAGS,
        "contact_note": DEFAULT_CONTACT_NOTE,
        "related_links": DEFAULT_RELATED_LINKS,
        "source_filename": video_path.name,
    }


def main() -> int:
    args = parse_args()
    title_prefix = str(args.title_prefix or "").strip()
    base_slug = str(args.base_slug or "").strip()
    if not title_prefix:
        fail("--title-prefix cannot be empty")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", base_slug):
        fail("--base-slug must use lowercase letters, numbers, and hyphens")
    status = str(args.status or "published").strip()
    if status not in {"published", "draft", "noindex", "rejected"}:
        fail("--status must be one of: published, draft, noindex, rejected")
    if int(args.limit or 0) < 0:
        fail("--limit cannot be negative")
    if int(args.start_index or 0) < 0:
        fail("--start-index cannot be negative")

    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    input_dir = Path(args.input_dir).expanduser().resolve()
    video_paths = scan_videos(input_dir)
    records = load_videos()
    imported_sources = source_filenames(records)

    new_videos = [path for path in video_paths if path.name.lower() not in imported_sources]
    if args.limit:
        new_videos = new_videos[: int(args.limit)]
    if not new_videos:
        fail("no new video files to import; all matching source_filename values already exist")

    PUBLIC_VIDEOS.mkdir(parents=True, exist_ok=True)
    PUBLIC_THUMBNAILS.mkdir(parents=True, exist_ok=True)

    used_slugs = {str(item.get("slug", "")).strip() for item in records if item.get("slug")}
    used_slug_numbers = existing_slug_numbers(records, args.base_slug)
    used_ids = used_auto_ids(records)
    next_index = infer_start_index(args, records, base_slug)

    planned: list[tuple[Path, Path, Path, dict[str, Any], Path | None]] = []
    for video_path in new_videos:
        slug, index = next_slug(base_slug, used_slugs, used_slug_numbers, next_index)
        next_index = index + 1
        auto_id = next_auto_id(used_ids, start_at=index)
        duration_seconds = ffprobe_duration(ffprobe, video_path)
        video_output = PUBLIC_VIDEOS / f"{slug}.mp4"
        thumb_output = PUBLIC_THUMBNAILS / f"{slug}.jpg"
        ensure_asset_can_write(video_output, overwrite=bool(args.overwrite_assets))
        ensure_asset_can_write(thumb_output, overwrite=bool(args.overwrite_assets))
        record = build_record(
            video_path=video_path,
            slug=slug,
            index=index,
            auto_id=auto_id,
            status=status,
            title_prefix=title_prefix,
            duration_seconds=duration_seconds,
        )
        planned.append((video_path, video_output, thumb_output, record, find_sidecar_cover(video_path)))

    print(f"Import plan: {len(planned)} video(s)")
    for video_path, video_output, thumb_output, record, cover_path in planned:
        cover_note = f"sidecar_cover={cover_path.name}" if cover_path else "thumbnail=ffmpeg_frame"
        print(
            f"- {video_path.name} -> slug={record['slug']} "
            f"duration={record['duration_seconds']}s video={video_output.relative_to(ROOT).as_posix()} "
            f"thumb={thumb_output.relative_to(ROOT).as_posix()} {cover_note}"
        )

    if args.dry_run:
        print("Dry run only; no files were written.")
        return 0

    for video_path, video_output, thumb_output, record, cover_path in planned:
        write_video_asset(ffmpeg, video_path, video_output, overwrite=bool(args.overwrite_assets))
        if cover_path:
            convert_cover(ffmpeg, cover_path, thumb_output, overwrite=bool(args.overwrite_assets))
        else:
            generate_thumbnail(ffmpeg, video_path, thumb_output, overwrite=bool(args.overwrite_assets))
        records.append(record)

    write_videos(records)
    print(f"Imported {len(planned)} video(s) into {VIDEOS_DATA.relative_to(ROOT).as_posix()}")
    print("Next steps:")
    print("python scripts/build_site.py")
    print("python scripts/check_static_site.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
