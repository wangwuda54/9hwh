import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site_src" / "data"
POSTS_DIR = DATA / "admin_posts"
CATALOG_PATH = DATA / "admin_posts_catalog.json"
ADMIN_POSTS_GIT_PATH = "site_src/data/admin_posts.json"
CATALOG_FIELDS = ("id", "slug", "title", "status", "updatedAt", "publishedAt")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def recover_posts(ref: str) -> tuple[dict, int]:
    commits = [
        line.strip()
        for line in git("log", "--reverse", "--format=%H", ref, "--", ADMIN_POSTS_GIT_PATH).splitlines()
        if line.strip()
    ]
    if not commits:
        raise SystemExit(f"[FAIL] no {ADMIN_POSTS_GIT_PATH} history found at {ref}")

    recovered: dict[str, dict] = {}
    latest_data: dict = {}
    for commit in commits:
        raw = git("show", f"{commit}:{ADMIN_POSTS_GIT_PATH}")
        data = json.loads(raw)
        latest_data = data
        for post in data.get("posts", []):
            slug = str(post.get("slug", "")).strip().lower()
            if slug:
                recovered[slug] = post

    latest_data["version"] = latest_data.get("version", 1)
    latest_data["posts"] = list(recovered.values())
    return latest_data, len(commits)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recover admin blog posts that were replaced in later Git commits."
    )
    parser.add_argument("--ref", default="HEAD", help="Git ref whose history should be scanned")
    parser.add_argument("--write", action="store_true", help="Write the recovered union to admin_posts.json")
    args = parser.parse_args()

    recovered, commit_count = recover_posts(args.ref)
    current_slugs = {path.stem for path in POSTS_DIR.rglob("*.json")} if POSTS_DIR.exists() else set()
    recovered_slugs = {
        str(post.get("slug", "")).strip().lower()
        for post in recovered.get("posts", [])
        if str(post.get("slug", "")).strip()
    }

    print(f"history_commits={commit_count}")
    print(f"current_posts={len(current_slugs)}")
    print(f"recovered_posts={len(recovered_slugs)}")
    print(f"restored_posts={len(recovered_slugs - current_slugs)}")

    if args.write:
        for post in recovered.get("posts", []):
            slug = str(post.get("slug", "")).strip().lower()
            target = POSTS_DIR / slug[0] / f"{slug}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(post, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        catalog = {
            "version": 2,
            "updatedAt": recovered.get("updatedAt", ""),
            "posts": [
                {field: post.get(field, "") for field in CATALOG_FIELDS}
                for post in recovered.get("posts", [])
            ],
        }
        CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] wrote {len(recovered_slugs)} post files and {CATALOG_PATH}")
    else:
        print("[DRY RUN] pass --write to restore per-post files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
