from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = [
    ROOT / "site_src" / "content_drafts",
    ROOT / "site" / "public",
]
PLACEHOLDER_RE = re.compile(r"\?{8,}")


def should_check(path: Path) -> bool:
    if path.name.upper() == "README.MD":
        return False
    return path.suffix.lower() in {".html", ".md", ".json", ".xml"}


def scan_file(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return []
    matches: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if PLACEHOLDER_RE.search(line):
            matches.append((line_number, line.strip()[:180]))
    return matches


def iter_files(paths: list[Path]):
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if should_check(path):
                yield path
            continue
        for child in path.rglob("*"):
            if child.is_file() and should_check(child):
                yield child


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail when generated or source text contains long question-mark placeholders.")
    parser.add_argument("paths", nargs="*", help="Optional files or directories to scan.")
    args = parser.parse_args()

    paths = [Path(item) for item in args.paths] if args.paths else DEFAULT_PATHS
    paths = [path if path.is_absolute() else ROOT / path for path in paths]

    failures = []
    for path in iter_files(paths):
        matches = scan_file(path)
        for line_number, snippet in matches:
            failures.append((path.relative_to(ROOT).as_posix(), line_number, snippet))

    if failures:
        for path, line_number, snippet in failures[:200]:
            print(f"[FAIL] placeholder text found: {path}:{line_number}: {snippet}")
        if len(failures) > 200:
            print(f"[FAIL] ... and {len(failures) - 200} more placeholder occurrence(s)")
        return 1

    print("[OK] no long question-mark placeholder text found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
