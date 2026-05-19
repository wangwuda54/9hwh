from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIDEOS_JSON = ROOT / "site_src" / "data" / "videos.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge server-generated video asset JSON into site_src/data/videos.json.")
    parser.add_argument("--input-json", required=True, help="Downloaded JSON file from server_prepare_video_assets.py.")
    parser.add_argument("--videos-json", default=str(DEFAULT_VIDEOS_JSON), help="Target videos.json path.")
    parser.add_argument("--status", default="published", help="Status to set on appended records. Default: published.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts without writing videos.json.")
    return parser.parse_args()


def load_array(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"[FAIL] file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise SystemExit(f"[FAIL] expected JSON array: {path}")
    for item in data:
        if not isinstance(item, dict):
            raise SystemExit(f"[FAIL] expected every array item to be an object: {path}")
    return data


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_json)
    videos_path = Path(args.videos_json)

    incoming = load_array(input_path)
    existing = load_array(videos_path)
    existing_slugs = {item.get("slug") for item in existing if item.get("slug")}
    existing_sources = {item.get("source_filename") for item in existing if item.get("source_filename")}

    appended = []
    skipped = 0
    for item in incoming:
        slug = item.get("slug")
        source_filename = item.get("source_filename")
        if not slug:
            skipped += 1
            print("[SKIP] missing slug")
            continue
        if slug in existing_slugs:
            skipped += 1
            print(f"[SKIP] duplicate slug: {slug}")
            continue
        if source_filename and source_filename in existing_sources:
            skipped += 1
            print(f"[SKIP] duplicate source_filename: {source_filename}")
            continue
        new_item = item.copy()
        new_item["status"] = args.status
        appended.append(new_item)
        existing_slugs.add(slug)
        if source_filename:
            existing_sources.add(source_filename)

    total = len(existing) + len(appended)
    print(f"[OK] new records: {len(appended)}")
    print(f"[OK] skipped records: {skipped}")
    print(f"[OK] total after merge: {total}")

    if args.dry_run:
        print("[DRY-RUN] videos.json not changed")
        return 0

    videos_path.write_text(json.dumps(existing + appended, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] updated: {videos_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
