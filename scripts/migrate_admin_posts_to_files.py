import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site_src" / "data"
LEGACY_PATH = DATA / "admin_posts.json"
POSTS_DIR = DATA / "admin_posts"
CATALOG_PATH = DATA / "admin_posts_catalog.json"
CATALOG_FIELDS = (
    "id",
    "slug",
    "title",
    "status",
    "updatedAt",
    "publishedAt",
)


def normalize_slug(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"['\"]", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def post_path(slug: str) -> Path:
    return POSTS_DIR / slug[0] / f"{slug}.json"


def catalog_post(post: dict) -> dict:
    return {field: post.get(field, [] if field == "tags" else "") for field in CATALOG_FIELDS}


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy admin_posts.json to one JSON file per post.")
    parser.add_argument("--write", action="store_true", help="Write per-post files and the metadata catalog")
    parser.add_argument(
        "--remove-legacy",
        action="store_true",
        help="Remove admin_posts.json after all per-post files have been verified",
    )
    args = parser.parse_args()

    if not LEGACY_PATH.exists():
        raise SystemExit(f"[FAIL] legacy source not found: {LEGACY_PATH}")
    data = json.loads(LEGACY_PATH.read_text(encoding="utf-8-sig"))
    posts = data.get("posts", [])
    if not isinstance(posts, list):
        raise SystemExit("[FAIL] legacy posts must be a list")

    normalized = []
    seen = set()
    for post in posts:
        slug = normalize_slug(post.get("slug"))
        if not slug:
            raise SystemExit(f"[FAIL] post missing slug: {post.get('id', '(unknown)')}")
        if slug in seen:
            raise SystemExit(f"[FAIL] duplicate slug: {slug}")
        seen.add(slug)
        next_post = post.copy()
        next_post["slug"] = slug
        normalized.append(next_post)

    catalog = {
        "version": 2,
        "updatedAt": data.get("updatedAt", ""),
        "posts": [catalog_post(post) for post in normalized],
    }
    print(f"legacy_posts={len(posts)}")
    print(f"unique_slugs={len(seen)}")
    print(f"catalog_bytes={len(json.dumps(catalog, ensure_ascii=False).encode('utf-8'))}")

    if not args.write:
        print("[DRY RUN] pass --write to create per-post files")
        return 0

    for post in normalized:
        target = post_path(post["slug"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    written = list(POSTS_DIR.rglob("*.json"))
    if len(written) != len(normalized):
        raise SystemExit(f"[FAIL] expected {len(normalized)} post files, found {len(written)}")
    for post in normalized:
        target = post_path(post["slug"])
        saved = json.loads(target.read_text(encoding="utf-8"))
        if saved.get("slug") != post["slug"]:
            raise SystemExit(f"[FAIL] verification failed: {target}")

    if args.remove_legacy:
        resolved = LEGACY_PATH.resolve()
        if resolved.parent != DATA.resolve() or resolved.name != "admin_posts.json":
            raise SystemExit(f"[FAIL] refusing to remove unexpected path: {resolved}")
        LEGACY_PATH.unlink()
        print(f"[OK] removed {LEGACY_PATH}")

    print(f"[OK] wrote {len(written)} post files and {CATALOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
