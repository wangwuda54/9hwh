from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg"}
DEFAULT_BGM_DIR = "E:/ceshhi/input/bgm"
DEFAULT_TELEGRAM_TEXT = "Telegram 咨询"
DEFAULT_DURATION = 45
BASE_SITE_URL = "https://www.9hwh.com"
FORBIDDEN_VISUAL_TERMS = [
    "9HWH",
    "9hwh",
    "9hwh.com",
    "查看完整页面",
    "不承诺",
    "不保证",
    "保证排名",
    "保证审核",
    "保证过审",
    "保证转化",
    "审核或转化结果",
]
REQUIRED_TOPIC_FIELDS = ("slug", "title", "h1", "primary_keyword", "description", "summary", "tags")


@dataclass
class Assets:
    centers: list[Path]
    sucai: list[Path]
    bgm: list[Path]
    font_name: str


@dataclass
class TargetPaths:
    target: str
    video: Path
    thumbnail: Path
    remote_video: str
    remote_thumbnail: str
    video_url: str
    thumbnail_url: str


def path_arg(value: str | os.PathLike[str]) -> Path:
    return Path(str(value).replace("\\", "/")).expanduser()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_command(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    logger: logging.Logger,
    summary: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    logger.info("%s: %s", summary, command_summary(cmd))
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
    if result.stdout:
        logger.info("%s stdout: %s", summary, result.stdout.strip())
    if result.stderr:
        logger.info("%s stderr: %s", summary, result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"{summary} failed with exit code {result.returncode}: {result.stderr.strip()}")
    return result


def command_summary(cmd: list[str]) -> str:
    return " ".join(str(part) for part in cmd[:18]) + (" ..." if len(cmd) > 18 else "")


def setup_logger(output_dir: Path, dry_run: bool) -> logging.Logger:
    logger = logging.getLogger("video_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    if not dry_run:
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(logs_dir / f"pipeline_{stamp}.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def require_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"missing dependency: {name}")
    return found


def target_includes_site(args: argparse.Namespace) -> bool:
    return args.target in {"site", "both"}


def target_includes_platform(args: argparse.Namespace) -> bool:
    return args.target in {"platform", "both"}


def upload_required(args: argparse.Namespace) -> bool:
    return target_includes_site(args) and not args.skip_upload and not args.dry_run


def validate_path_value(args: argparse.Namespace, label: str) -> Path:
    value = str(getattr(args, label, "")).strip()
    if not value:
        raise RuntimeError(f"{label.replace('_', '-')} is required")
    return path_arg(value)


def validate_dependencies(args: argparse.Namespace, logger: logging.Logger) -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required")

    topics_json = validate_path_value(args, "topics_json")
    videos_json = validate_path_value(args, "videos_json")
    site_root = validate_path_value(args, "site_root")
    input_dir = validate_path_value(args, "input_dir")
    validate_path_value(args, "output_dir")

    for label, path in (("topics-json", topics_json), ("videos-json", videos_json)):
        if not path.is_file():
            raise RuntimeError(f"{label} does not exist: {path}")

    if args.dry_run:
        logger.info("dry-run dependency check: skipped ffmpeg/ffprobe/scp/ssh and media asset checks")
        return

    for label, path in (("site-root", site_root), ("input-dir", input_dir)):
        if not path.exists():
            raise RuntimeError(f"{label} does not exist: {path}")

    tools = {name: require_tool(name) for name in ("ffmpeg", "ffprobe")}
    if upload_required(args):
        tools.update({name: require_tool(name) for name in ("scp", "ssh")})
    for name, exe in tools.items():
        logger.info("dependency ok: %s -> %s", name, exe)

    assets = collect_assets(path_arg(args.input_dir), path_arg(args.bgm_dir), logger)
    if not assets.centers:
        raise RuntimeError("no center video found: use input/centers/*.mp4 or input/center.mp4")
    if len(assets.sucai) < 2:
        raise RuntimeError("input/sucai must contain at least 2 usable video files")
    logger.info(
        "assets ok: centers=%s sucai=%s bgm=%s font=%s",
        len(assets.centers),
        len(assets.sucai),
        len(assets.bgm),
        assets.font_name,
    )


def list_files(path: Path, exts: set[str]) -> list[Path]:
    if not path.exists():
        return []
    return sorted([item for item in path.iterdir() if item.is_file() and item.suffix.lower() in exts], key=lambda p: p.name.lower())


def collect_assets(input_dir: Path, bgm_dir: Path, logger: logging.Logger) -> Assets:
    centers_dir = input_dir / "centers"
    centers = list_files(centers_dir, VIDEO_EXTS)
    fallback_center = input_dir / "center.mp4"
    if not centers and fallback_center.is_file():
        centers = [fallback_center]
    sucai = list_files(input_dir / "sucai", VIDEO_EXTS)
    bgm = list_files(bgm_dir, AUDIO_EXTS)
    font_name = find_font_name(input_dir / "fonts", logger)
    return Assets(centers=centers, sucai=sucai, bgm=bgm, font_name=font_name)


def find_font_name(fonts_dir: Path, logger: logging.Logger) -> str:
    local_fonts = []
    if fonts_dir.exists():
        local_fonts = [item for item in fonts_dir.iterdir() if item.suffix.lower() in {".ttf", ".ttc", ".otf"}]
    if local_fonts:
        logger.info("local fonts detected; ASS renderer will still use font family fallback: %s", local_fonts[0])
    candidates = [
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            if candidate.name.lower().startswith("msyh"):
                return "Microsoft YaHei"
            if candidate.name.lower().startswith("simhei"):
                return "SimHei"
            return "SimSun"
    return "Arial Unicode MS"


def validate_topic(topic: dict[str, Any], index: int) -> None:
    label = str(topic.get("slug") or f"index {index}").strip()
    for field in REQUIRED_TOPIC_FIELDS:
        if field == "tags":
            continue
        value = topic.get(field)
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"topic validation failed: {label} field {field} must be a non-empty string")

    tags = topic.get("tags")
    if not isinstance(tags, list):
        raise RuntimeError(f"topic validation failed: {label} field tags must be a non-empty array")
    clean_tags = [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]
    if len(clean_tags) < 2:
        raise RuntimeError(f"topic validation failed: {label} field tags must contain at least 2 non-empty strings")

    for field in ("title", "h1", "description", "summary"):
        text = topic[field]
        for term in FORBIDDEN_VISUAL_TERMS:
            if term.lower() in text.lower():
                raise RuntimeError(f"topic validation failed: {label} field {field} contains forbidden term: {term}")


def load_topics(path: Path, start_index: int, limit: int | None, logger: logging.Logger) -> list[dict[str, Any]]:
    if not path.is_file():
        raise RuntimeError(f"video_topics.json does not exist: {path}")
    data = read_json(path)
    if not isinstance(data, list):
        raise RuntimeError("video_topics.json top-level value must be a list")
    zero_based_start = start_index - 1
    selected = data[zero_based_start:]
    if limit is not None:
        selected = selected[:limit]

    topics: list[dict[str, Any]] = []
    for index, item in enumerate(selected, start=start_index):
        if not isinstance(item, dict):
            raise RuntimeError(f"topic validation failed: index {index} must be an object")
        validate_topic(item, index)
        topics.append(item)
    return topics


def target_paths(args: argparse.Namespace, slug: str, target: str) -> TargetPaths:
    output_dir = path_arg(args.output_dir)
    base_url = str(args.asset_base_url).rstrip("/")
    remote_root = str(args.remote_root).rstrip("/")
    if target == "site":
        video_name = f"{slug}.mp4"
        thumb_name = f"{slug}.jpg"
        return TargetPaths(
            target=target,
            video=output_dir / "site" / "videos" / video_name,
            thumbnail=output_dir / "site" / "thumbnails" / thumb_name,
            remote_video=f"{remote_root}/videos/{video_name}",
            remote_thumbnail=f"{remote_root}/thumbnails/{thumb_name}",
            video_url=f"{base_url}/videos/{video_name}",
            thumbnail_url=f"{base_url}/thumbnails/{thumb_name}",
        )
    video_name = f"{slug}-platform.mp4"
    thumb_name = f"{slug}.jpg"
    return TargetPaths(
        target=target,
        video=output_dir / "platform" / "videos" / video_name,
        thumbnail=output_dir / "platform" / "thumbnails" / thumb_name,
        remote_video="",
        remote_thumbnail="",
        video_url="",
        thumbnail_url="",
    )


def selected_targets(target: str) -> list[str]:
    if target == "both":
        return ["site", "platform"]
    return [target]


def dry_run(args: argparse.Namespace, topics: list[dict[str, Any]], logger: logging.Logger) -> None:
    logger.info("[DRY-RUN] topics to process: %s", len(topics))
    logger.info("[DRY-RUN] target=%s build=%s upload=%s", args.target, not args.skip_build, not args.skip_upload)
    for item in topics:
        slug = str(item["slug"]).strip()
        logger.info("[DRY-RUN] %s | title=%s | h1=%s", slug, item.get("title", ""), item.get("h1", ""))
        for target in selected_targets(args.target):
            paths = target_paths(args, slug, target)
            logger.info("[DRY-RUN] %s local video: %s", target, paths.video)
            logger.info("[DRY-RUN] %s local thumbnail: %s", target, paths.thumbnail)
            if target == "site":
                logger.info("[DRY-RUN] site remote video: %s:%s", args.server, paths.remote_video)
                logger.info("[DRY-RUN] site remote thumbnail: %s:%s", args.server, paths.remote_thumbnail)
                logger.info("[DRY-RUN] videos.json update: slug=%s video_file=%s", slug, paths.video_url)
    logger.info("[DRY-RUN] no files generated, uploaded, updated, built, committed, or pushed")


def rng_for(args: argparse.Namespace, slug: str, target: str) -> random.Random:
    if args.seed is None:
        return random.Random()
    return random.Random(f"{args.seed}:{slug}:{target}")


def probe_duration(path: Path, logger: logging.Logger) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = run_command(cmd, logger=logger, summary=f"ffprobe {path.name}", check=False)
    try:
        value = float((result.stdout or "").strip())
        return value if value > 0 else 0.0
    except ValueError:
        return 0.0


def probe_duration_seconds(path: Path, fallback: int, logger: logging.Logger) -> int:
    if path.exists():
        seconds = probe_duration(path, logger)
        if seconds > 0:
            return max(1, int(round(seconds)))
    logger.warning("could not probe output duration for %s; fallback to %s seconds", path, fallback)
    return max(1, int(fallback))


def visual_width(char: str) -> int:
    return 2 if ord(char) > 127 else 1


def wrap_title(text: str, max_width: int = 28, max_lines: int = 2) -> str:
    lines: list[str] = []
    current = ""
    width = 0
    for char in text.strip():
        next_width = visual_width(char)
        if current and width + next_width > max_width:
            lines.append(current)
            current = char
            width = next_width
            if len(lines) == max_lines:
                break
        else:
            current += char
            width += next_width
    if len(lines) < max_lines and current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    original_width = sum(visual_width(c) for c in text)
    used_width = sum(sum(visual_width(c) for c in line) for line in lines)
    if used_width < original_width and lines:
        lines[-1] = lines[-1].rstrip(".")[: max(0, len(lines[-1]) - 3)] + "..."
    return "\\N".join(lines[:max_lines])


def ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def safe_visual_text(text: str, label: str) -> str:
    for term in FORBIDDEN_VISUAL_TERMS:
        if term.lower() in text.lower():
            raise RuntimeError(f"forbidden visual term in {label}: {term}")
    return text


def topic_tags(topic: dict[str, Any]) -> list[str]:
    tags = topic.get("tags")
    if isinstance(tags, list):
        clean = [str(tag).strip() for tag in tags if str(tag).strip()]
        if clean:
            return clean
    fallback = str(topic.get("primary_keyword") or topic.get("h1") or topic.get("title") or "").strip()
    return [fallback] if fallback else []


def write_ass_file(args: argparse.Namespace, topic: dict[str, Any], target: str, paths: TargetPaths, assets: Assets) -> Path:
    slug = str(topic["slug"]).strip()
    work_dir = path_arg(args.output_dir) / "_work" / target
    work_dir.mkdir(parents=True, exist_ok=True)
    ass_path = work_dir / f"{slug}.ass"

    duration = int(args.duration)
    title = safe_visual_text(str(topic.get("h1") or topic.get("title")).strip(), "title")
    subtitle = safe_visual_text(" / ".join(topic_tags(topic)[:3]), "tags")
    telegram = safe_visual_text(str(args.telegram_text).strip() or DEFAULT_TELEGRAM_TEXT, "telegram-text")

    if target == "platform":
        title_end = min(duration, 7)
        subtitle_start = 4
        subtitle_end = max(subtitle_start + 1, duration - 10)
        cta_start = max(0, duration - 10)
    else:
        title_end = max(1, duration - 3)
        subtitle_start = 0.8
        subtitle_end = max(subtitle_start + 1, duration - 3)
        cta_start = max(0, duration - 3)

    title_text = ass_escape(wrap_title(title))
    subtitle_text = ass_escape(wrap_title(subtitle, max_width=36, max_lines=2))
    telegram_text = ass_escape(wrap_title(telegram, max_width=22, max_lines=1))
    font = assets.font_name

    content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{font},58,&H00FFFFFF,&H000000FF,&HAA000000,&H7A000000,1,0,0,0,100,100,0,0,1,3,1,2,220,220,200,1
Style: Subtitle,{font},34,&H00F3F7FA,&H000000FF,&HAA000000,&H64000000,0,0,0,0,100,100,0,0,1,2,1,2,260,260,130,1
Style: CTA,{font},62,&H00FFFFFF,&H000000FF,&HAA000000,&H7A000000,1,0,0,0,100,100,0,0,1,3,1,2,260,260,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ass_time(0.35)},{ass_time(title_end)},Title,,0,0,0,,{{\\fad(200,300)}}{title_text}
Dialogue: 0,{ass_time(subtitle_start)},{ass_time(subtitle_end)},Subtitle,,0,0,0,,{{\\fad(200,300)}}{subtitle_text}
Dialogue: 0,{ass_time(cta_start)},{ass_time(duration)},CTA,,0,0,0,,{{\\fad(180,200)}}{telegram_text}
"""
    ass_path.write_text(content, encoding="utf-8")
    return ass_path


def ffmpeg_filter_path(path: Path) -> str:
    value = path.resolve().as_posix()
    return value.replace(":", "\\:")


def build_ffmpeg_command(
    args: argparse.Namespace,
    center: Path,
    left: Path,
    right: Path,
    bgm: Path | None,
    ass_path: Path,
    output: Path,
    rng: random.Random,
    logger: logging.Logger,
) -> list[str]:
    duration = int(args.duration)
    left_speed = round(rng.uniform(0.75, 1.65), 3)
    right_speed = round(rng.uniform(0.75, 1.65), 3)
    left_start = min(10.0, max(0.0, probe_duration(left, logger) - 1.0))
    right_start = min(10.0, max(0.0, probe_duration(right, logger) - 1.0))

    cmd = ["ffmpeg", "-y" if args.overwrite else "-n", "-hide_banner", "-loglevel", "error"]
    cmd += ["-stream_loop", "-1", "-i", str(center)]
    cmd += ["-ss", f"{left_start:.2f}", "-i", str(left)]
    cmd += ["-ss", f"{right_start:.2f}", "-i", str(right)]
    if bgm and not args.no_audio:
        cmd += ["-stream_loop", "-1", "-i", str(bgm)]
        audio_input = "3:a"
        audio_filter = f"[{audio_input}]atrim=0:{duration},asetpts=PTS-STARTPTS,volume=0.18[a]"
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
        audio_filter = f"[3:a]atrim=0:{duration},asetpts=PTS-STARTPTS[a]"

    ass = ffmpeg_filter_path(ass_path)
    filter_complex = (
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
        "fps=30,setsar=1,format=yuv420p[bg];"
        f"[1:v]setpts=(PTS-STARTPTS)/{left_speed},scale=560:640:force_original_aspect_ratio=increase,"
        "crop=560:640,fps=30,setsar=1,format=yuv420p[left];"
        f"[2:v]setpts=(PTS-STARTPTS)/{right_speed},scale=560:640:force_original_aspect_ratio=increase,"
        "crop=560:640,fps=30,setsar=1,format=yuv420p[right];"
        "[bg]drawbox=x=0:y=710:w=iw:h=340:color=black@0.32:t=fill[base];"
        "[base][left]overlay=80:150:shortest=0:eof_action=repeat[tmp1];"
        "[tmp1][right]overlay=W-w-80:150:shortest=0:eof_action=repeat[tmp2];"
        f"[tmp2]ass='{ass}'[v];"
        f"{audio_filter}"
    )
    cmd += [
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-t",
        str(duration),
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "28",
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-movflags",
        "+faststart",
        str(output),
    ]
    return cmd


def local_assets_ready(paths: TargetPaths) -> bool:
    return paths.video.exists() and paths.video.stat().st_size > 0 and paths.thumbnail.exists() and paths.thumbnail.stat().st_size > 0


def ensure_can_generate(paths: TargetPaths, args: argparse.Namespace) -> None:
    if paths.video.exists() and not args.overwrite:
        raise RuntimeError(f"local output exists; use --overwrite or --only-missing: {paths.video}")
    if paths.thumbnail.exists() and not args.overwrite:
        raise RuntimeError(f"local thumbnail exists; use --overwrite or --only-missing: {paths.thumbnail}")
    paths.video.parent.mkdir(parents=True, exist_ok=True)
    paths.thumbnail.parent.mkdir(parents=True, exist_ok=True)


def generate_video(
    args: argparse.Namespace,
    topic: dict[str, Any],
    target: str,
    paths: TargetPaths,
    assets: Assets,
    logger: logging.Logger,
) -> bool:
    ensure_can_generate(paths, args)
    rng = rng_for(args, str(topic["slug"]), target)
    center = rng.choice(assets.centers)
    left, right = rng.sample(assets.sucai, 2)
    bgm = rng.choice(assets.bgm) if assets.bgm and not args.no_audio else None
    ass_path = write_ass_file(args, topic, target, paths, assets)
    cmd = build_ffmpeg_command(args, center, left, right, bgm, ass_path, paths.video, rng, logger)
    logger.info(
        "generate %s/%s center=%s left=%s right=%s bgm=%s",
        target,
        topic["slug"],
        center.name,
        left.name,
        right.name,
        bgm.name if bgm else "silent-aac",
    )
    run_command(cmd, logger=logger, summary=f"ffmpeg {target} {topic['slug']}")
    if not paths.video.exists() or paths.video.stat().st_size <= 0:
        raise RuntimeError(f"ffmpeg did not create video: {paths.video}")
    return True


def generate_thumbnail(args: argparse.Namespace, paths: TargetPaths, logger: logging.Logger) -> bool:
    if paths.thumbnail.exists() and not args.overwrite:
        if args.only_missing:
            logger.info("skip existing thumbnail because --only-missing: %s", paths.thumbnail)
            return False
        raise RuntimeError(f"local thumbnail exists; use --overwrite: {paths.thumbnail}")
    paths.thumbnail.parent.mkdir(parents=True, exist_ok=True)
    for seek in ("2", "0.5"):
        cmd = [
            "ffmpeg",
            "-y" if args.overwrite else "-n",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            seek,
            "-i",
            str(paths.video),
            "-frames:v",
            "1",
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
            "-q:v",
            "3",
            str(paths.thumbnail),
        ]
        result = run_command(cmd, logger=logger, summary=f"thumbnail {paths.target} {paths.video.name} @{seek}s", check=False)
        if result.returncode == 0 and paths.thumbnail.exists() and paths.thumbnail.stat().st_size > 0:
            return True
    raise RuntimeError(f"could not generate thumbnail: {paths.thumbnail}")


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def remote_exists(args: argparse.Namespace, remote_path: str, logger: logging.Logger) -> bool:
    cmd = ["ssh", str(args.server), f"test -e {sh_quote(remote_path)} && echo exists || echo missing"]
    result = run_command(cmd, logger=logger, summary=f"remote exists {remote_path}", check=False)
    return "exists" in result.stdout


def remote_assets_state(args: argparse.Namespace, paths: TargetPaths, logger: logging.Logger) -> tuple[bool, bool]:
    return (
        remote_exists(args, paths.remote_video, logger),
        remote_exists(args, paths.remote_thumbnail, logger),
    )


def upload_site(args: argparse.Namespace, paths: TargetPaths, logger: logging.Logger) -> bool:
    if args.skip_upload:
        logger.info("skip upload for %s because --skip-upload is set", paths.video.name)
        return False
    if not local_assets_ready(paths):
        raise RuntimeError(f"local site video/thumbnail missing or empty: {paths.video} / {paths.thumbnail}")
    remote_dirs = f"mkdir -p {sh_quote(str(args.remote_root).rstrip('/') + '/videos')} {sh_quote(str(args.remote_root).rstrip('/') + '/thumbnails')}"
    run_command(["ssh", str(args.server), remote_dirs], logger=logger, summary="ensure remote video directories")
    for remote_path in (paths.remote_video, paths.remote_thumbnail):
        if remote_exists(args, remote_path, logger) and not args.overwrite:
            raise RuntimeError(f"remote file exists; use --overwrite to replace: {remote_path}")
    run_command(["scp", str(paths.video), f"{args.server}:{paths.remote_video}"], logger=logger, summary=f"scp video {paths.video.name}")
    run_command(["scp", str(paths.thumbnail), f"{args.server}:{paths.remote_thumbnail}"], logger=logger, summary=f"scp thumbnail {paths.thumbnail.name}")
    root = str(args.remote_root).rstrip("/")
    fix_permissions = f"chown -R www-data:www-data {sh_quote(root)} && chmod -R 755 {sh_quote(root)}"
    run_command(["ssh", str(args.server), fix_permissions], logger=logger, summary="remote ownership and permissions")
    return True


def update_videos_json(args: argparse.Namespace, topic: dict[str, Any], paths: TargetPaths, logger: logging.Logger) -> bool:
    videos_path = path_arg(args.videos_json)
    videos = read_json(videos_path)
    if not isinstance(videos, list):
        raise RuntimeError("videos.json top-level value must be a list")
    slug = str(topic["slug"])
    upload_date = datetime.now().strftime("%Y-%m-%d")
    duration_seconds = probe_duration_seconds(paths.video, int(args.duration), logger)
    asset_fields = {
        "video_file": paths.video_url,
        "thumbnail": paths.thumbnail_url,
        "duration_seconds": duration_seconds,
        "upload_date": upload_date,
        "source_filename": f"{slug}.mp4",
    }
    for item in videos:
        if isinstance(item, dict) and item.get("slug") == slug:
            status = str(item.get("status", "")).strip().lower()
            item.update(asset_fields)
            if args.force_published or status not in {"draft", "rejected"}:
                item["status"] = "published"
            logger.info("updated videos.json record: %s", slug)
            write_json(videos_path, videos)
            return True

    record = {
        "id": f"auto-{slug}",
        "status": "published",
        "slug": slug,
        **asset_fields,
    }
    videos.append(record)
    logger.info("inserted videos.json record: %s", slug)
    write_json(videos_path, videos)
    return True


def append_manifest_row(rows: list[dict[str, str]], topic: dict[str, Any], paths: TargetPaths, status: str) -> None:
    rows.append(
        {
            "slug": str(topic.get("slug", "")),
            "title": str(topic.get("title", "")),
            "h1": str(topic.get("h1", "")),
            "target": paths.target,
            "local_video": str(paths.video),
            "local_thumbnail": str(paths.thumbnail),
            "remote_video_path": paths.remote_video,
            "remote_thumbnail_path": paths.remote_thumbnail,
            "video_url": paths.video_url,
            "thumbnail_url": paths.thumbnail_url,
            "status": status,
        }
    )


def write_manifest(output_dir: Path, rows: list[dict[str, str]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "manifest.csv"
    fields = [
        "slug",
        "title",
        "h1",
        "target",
        "local_video",
        "local_thumbnail",
        "remote_video_path",
        "remote_thumbnail_path",
        "video_url",
        "thumbnail_url",
        "status",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_state(output_dir: Path, states: list[dict[str, Any]]) -> None:
    path = output_dir / "pipeline_state.json"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": len(states),
            "failed": sum(1 for item in states if item.get("error")),
            "generated": sum(1 for item in states if item.get("generated")),
            "used_existing_local": sum(1 for item in states if item.get("used_existing_local")),
            "uploaded": sum(1 for item in states if item.get("uploaded")),
            "remote_reused": sum(1 for item in states if item.get("remote_reused")),
        },
        "items": states,
    }
    write_json(path, payload)


def platform_description(topic: dict[str, Any]) -> str:
    slug = str(topic["slug"])
    site_url = f"{BASE_SITE_URL}/v/{slug}/"
    summary = str(topic.get("summary") or topic.get("description") or topic.get("title") or "").strip()
    return f"{summary}\n更多内容可查看对应页面：{site_url}\nTelegram 咨询"


def write_platform_csv(output_dir: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    platform_dir = output_dir / "platform"
    platform_dir.mkdir(parents=True, exist_ok=True)
    path = platform_dir / "platform_publish.csv"
    fields = ["slug", "platform_title", "platform_description", "tags", "video_path", "thumbnail_path", "site_url", "status"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_platform_row(topic: dict[str, Any], paths: TargetPaths, status: str) -> dict[str, str]:
    slug = str(topic["slug"])
    tags = topic_tags(topic)
    return {
        "slug": slug,
        "platform_title": str(topic.get("title", "")),
        "platform_description": platform_description(topic),
        "tags": ",".join(tags),
        "video_path": str(paths.video),
        "thumbnail_path": str(paths.thumbnail),
        "site_url": f"{BASE_SITE_URL}/v/{slug}/",
        "status": status,
    }


def ensure_local_assets(
    args: argparse.Namespace,
    topic: dict[str, Any],
    target: str,
    paths: TargetPaths,
    assets: Assets,
    logger: logging.Logger,
) -> str:
    if local_assets_ready(paths) and args.only_missing and not args.overwrite:
        logger.info("reuse existing local %s assets: %s / %s", target, paths.video, paths.thumbnail)
        return "existing"

    if paths.video.exists() and not args.overwrite:
        if args.only_missing:
            if not paths.thumbnail.exists():
                logger.info("reuse existing local %s video and generate missing thumbnail: %s", target, paths.video)
                generate_thumbnail(args, paths, logger)
                return "existing"
            raise RuntimeError(f"local {target} assets are incomplete or empty: {paths.video} / {paths.thumbnail}")
        raise RuntimeError(f"local output exists; use --overwrite or --only-missing: {paths.video}")

    generate_video(args, topic, target, paths, assets, logger)
    generate_thumbnail(args, paths, logger)
    return "generated"


def run_build_check(args: argparse.Namespace, states: list[dict[str, Any]], logger: logging.Logger) -> bool:
    if args.skip_build:
        logger.info("skip build/check because --skip-build is set")
        return False
    if args.target == "platform" and not args.force_build:
        logger.info("skip build/check for platform-only target; pass --force-build to run it")
        return False
    site_root = path_arg(args.site_root)
    run_command(["python", "scripts/build_site.py"], cwd=site_root, logger=logger, summary="build site")
    run_command(["python", "scripts/check_static_site.py"], cwd=site_root, logger=logger, summary="check static site")
    for state in states:
        state["build_checked"] = True
    return True


def maybe_commit_push(args: argparse.Namespace, logger: logging.Logger) -> None:
    site_root = path_arg(args.site_root)
    if args.commit:
        run_command(["git", "status", "--short"], cwd=site_root, logger=logger, summary="git status before commit")
        add_paths = [
            "site_src/data/videos.json",
            "site/public/v",
            "site/public/sitemap.xml",
            "site/public/video-sitemap.xml",
            "site/public/robots.txt",
            "docs/site-url-inventory.md",
        ]
        for rel in add_paths:
            full = site_root / rel
            if full.exists():
                run_command(["git", "add", rel], cwd=site_root, logger=logger, summary=f"git add {rel}")
        cached_names = run_command(["git", "diff", "--cached", "--name-only"], cwd=site_root, logger=logger, summary="git cached names")
        forbidden_exts = VIDEO_EXTS | {".jpg", ".jpeg"}
        forbidden_files = [
            name
            for name in cached_names.stdout.splitlines()
            if Path(name).suffix.lower() in forbidden_exts or name.startswith("output/")
        ]
        if forbidden_files:
            raise RuntimeError("refuse to commit generated media/output files: " + ", ".join(forbidden_files))
        diff = run_command(["git", "diff", "--cached", "--quiet"], cwd=site_root, logger=logger, summary="git staged diff", check=False)
        if diff.returncode == 0:
            logger.info("no staged changes for commit")
        else:
            run_command(["git", "commit", "-m", "Update video landing pages"], cwd=site_root, logger=logger, summary="git commit")
    if args.push:
        run_command(["git", "-c", "http.proxy=", "-c", "https.proxy=", "push", "origin", "main"], cwd=site_root, logger=logger, summary="git push origin main")


def process(args: argparse.Namespace, logger: logging.Logger) -> int:
    validate_dependencies(args, logger)
    topics = load_topics(path_arg(args.topics_json), int(args.start_index), args.limit, logger)
    if args.dry_run:
        dry_run(args, topics, logger)
        return 0

    assets = collect_assets(path_arg(args.input_dir), path_arg(args.bgm_dir), logger)
    output_dir = path_arg(args.output_dir)
    manifest_rows: list[dict[str, str]] = []
    platform_rows: list[dict[str, str]] = []
    states: list[dict[str, Any]] = []
    failures = 0

    for topic in topics:
        slug = str(topic["slug"])
        for target in selected_targets(args.target):
            paths = target_paths(args, slug, target)
            state = {
                "slug": slug,
                "target": target,
                "generated": False,
                "used_existing_local": False,
                "uploaded": False,
                "remote_reused": False,
                "videos_json_updated": False,
                "build_checked": False,
                "error": "",
            }
            manifest_status = "ok"
            try:
                if target == "site":
                    if upload_required(args) and args.reuse_remote and not args.overwrite:
                        remote_video_exists, remote_thumbnail_exists = remote_assets_state(args, paths, logger)
                        if remote_video_exists and remote_thumbnail_exists:
                            state["remote_reused"] = True
                            state["used_existing_local"] = local_assets_ready(paths)
                            state["videos_json_updated"] = update_videos_json(args, topic, paths, logger)
                            manifest_status = "reused remote"
                            append_manifest_row(manifest_rows, topic, paths, manifest_status)
                            states.append(state)
                            continue
                        if remote_video_exists != remote_thumbnail_exists:
                            missing = "thumbnail" if remote_video_exists else "video"
                            raise RuntimeError(f"remote resources incomplete for {slug}; missing {missing}")

                    local_status = ensure_local_assets(args, topic, target, paths, assets, logger)
                    state["generated"] = local_status == "generated"
                    state["used_existing_local"] = local_status == "existing"
                    manifest_status = "skipped existing" if local_status == "existing" else "ok"

                    if upload_required(args):
                        state["uploaded"] = upload_site(args, paths, logger)
                        state["videos_json_updated"] = update_videos_json(args, topic, paths, logger)
                        if local_status == "existing":
                            manifest_status = "existing local uploaded"
                    append_manifest_row(manifest_rows, topic, paths, manifest_status)
                else:
                    local_status = ensure_local_assets(args, topic, target, paths, assets, logger)
                    state["generated"] = local_status == "generated"
                    state["used_existing_local"] = local_status == "existing"
                    manifest_status = "skipped existing" if local_status == "existing" else "ok"
                    platform_rows.append(build_platform_row(topic, paths, "existing" if local_status == "existing" else "ok"))
                    append_manifest_row(manifest_rows, topic, paths, manifest_status)
            except Exception as exc:
                failures += 1
                state["error"] = str(exc)
                append_manifest_row(manifest_rows, topic, paths, f"error: {exc}")
                if target == "platform":
                    platform_rows.append(build_platform_row(topic, paths, "error"))
                logger.exception("failed %s/%s: %s", target, slug, exc)
            states.append(state)

    write_manifest(output_dir, manifest_rows)
    write_platform_csv(output_dir, platform_rows)
    write_state(output_dir, states)

    if failures:
        logger.error("pipeline finished with failures: %s", failures)
        return 1
    run_build_check(args, states, logger)
    write_state(output_dir, states)
    maybe_commit_push(args, logger)
    logger.info("pipeline finished successfully")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Keyword-driven 9HWH video production pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Generate site/platform videos from video_topics.json")
    run.add_argument("--topics-json", required=True)
    run.add_argument("--videos-json", required=True)
    run.add_argument("--site-root", required=True)
    run.add_argument("--input-dir", required=True)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--asset-base-url", required=True)
    run.add_argument("--server", required=True)
    run.add_argument("--remote-root", required=True)
    run.add_argument("--target", choices=["site", "platform", "both"], default="site")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--limit", type=int, default=None)
    run.add_argument("--start-index", type=int, default=1, help="1-based topic index; 1 means the first item in video_topics.json")
    run.add_argument("--only-missing", action="store_true")
    run.add_argument("--seed", type=int, default=None)
    run.add_argument("--overwrite", action="store_true")
    run.add_argument("--reuse-remote", action="store_true")
    run.add_argument("--skip-upload", action="store_true")
    run.add_argument("--skip-build", action="store_true")
    run.add_argument("--force-build", action="store_true")
    run.add_argument("--commit", action="store_true")
    run.add_argument("--push", action="store_true")
    run.add_argument("--no-audio", action="store_true")
    run.add_argument("--bgm-dir", default=DEFAULT_BGM_DIR)
    run.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    run.add_argument("--telegram-text", default=DEFAULT_TELEGRAM_TEXT)
    run.add_argument("--force-published", action="store_true")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.start_index < 1:
        parser.error("--start-index is 1-based and must be >= 1")
    if args.duration <= 0:
        parser.error("--duration must be > 0")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    logger = setup_logger(path_arg(args.output_dir), args.dry_run)
    logger.info("args: %s", vars(args))
    try:
        return process(args, logger)
    except Exception as exc:
        logger.exception("pipeline failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
