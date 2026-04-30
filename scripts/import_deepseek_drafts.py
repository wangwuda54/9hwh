from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data" / "deepseek-inbox"
ARCHIVE = ROOT / "data" / "deepseek-reviewed"
DRAFTS = ROOT / "site_src" / "content_drafts"
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
BATCH_ROOT = ROOT / "data" / "deepseek-batches"
ASSETS = ROOT / "data" / "content-assets"
DOCS = ROOT / "docs"

REQUIRED_FIELDS = (
    "content_id",
    "title",
    "description",
    "target_url",
    "primary_keyword",
    "secondary_keywords",
    "status",
)
LOCKED_FIELDS = ("title", "target_url", "primary_keyword", "secondary_keywords")
DRAFT_STATUS = "draft_received"
PROTECTED_STATUSES = {"reviewed", "published"}


def parse_front_matter(front: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in front.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def split_articles(text: str) -> list[tuple[dict[str, str], str]]:
    pattern = re.compile(r"(?ms)^---\s*\n(.*?)\n---\s*\n(.*?)(?=^---\s*$|\Z)")
    articles = []
    for match in pattern.finditer(text):
        meta = parse_front_matter(match.group(1))
        body = match.group(2).strip()
        articles.append((meta, body))
    return articles


def normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def normalize_value(field: str, value: object) -> str:
    if field == "secondary_keywords":
        return ", ".join(normalize_list(value))
    return str(value or "").strip()


def load_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))


def load_batch_specs() -> dict[str, dict]:
    specs: dict[str, dict] = {}
    if BATCH_ROOT.exists():
        for index_path in sorted(BATCH_ROOT.glob("batch-*/batch-*-index.json")):
            for item in json.loads(index_path.read_text(encoding="utf-8-sig")):
                spec = dict(item)
                spec["batch_index"] = index_path.relative_to(ROOT).as_posix()
                specs[item["content_id"]] = spec
    return specs


def canonical_article(meta: dict[str, str], body: str) -> str:
    lines = ["---"]
    for field in REQUIRED_FIELDS:
        value = meta.get(field, "")
        if field == "status":
            value = DRAFT_STATUS
        lines.append(f"{field}: {value}")
    lines.extend(["---", "", body.strip(), ""])
    return "\n".join(lines)


def update_queue_status(queue: list[dict], content_id: str, meta: dict[str, str]) -> bool:
    for item in queue:
        if item.get("content_id") != content_id:
            continue
        item["status"] = DRAFT_STATUS
        item["target_url"] = meta["target_url"]
        item["title"] = meta["title"]
        item["h1"] = meta["title"]
        item["primary_keyword"] = meta["primary_keyword"]
        item["secondary_keywords"] = normalize_list(meta["secondary_keywords"])
        return True
    return False


def validate_article(meta: dict[str, str], body: str, specs: dict[str, dict], queue_by_id: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if not meta.get(field):
            errors.append(f"missing {field}")
    content_id = meta.get("content_id", "")
    spec = specs.get(content_id) or queue_by_id.get(content_id)
    if not spec:
        errors.append("content_id not found in batch index or content_queue")
        return errors
    if meta.get("status") != DRAFT_STATUS:
        errors.append("imported draft status must be draft_received")
    for field in LOCKED_FIELDS:
        expected = normalize_value(field, spec.get(field))
        actual = normalize_value(field, meta.get(field))
        if actual != expected:
            errors.append(f"{field} mismatch: expected {expected!r}, got {actual!r}")
    if len(body.strip()) < 200:
        errors.append("body too short for import")
    return errors


def should_skip_existing(target: Path, queue_item: dict | None, allow_overwrite: bool) -> str:
    if queue_item and queue_item.get("status") in PROTECTED_STATUSES and not allow_overwrite:
        return f"existing queue status is {queue_item.get('status')}"
    if target.exists() and not allow_overwrite:
        return "draft file already exists"
    return ""


def iter_inbox_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(INBOX.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        if path.name.endswith("-deepseek-output.md"):
            continue
        if "failed" in {part.lower() for part in path.parts}:
            continue
        files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Import DeepSeek Markdown drafts into site_src/content_drafts.")
    parser.add_argument("--allow-overwrite", action="store_true", help="Allow replacing existing draft files and reviewed queue items. Published items are still protected.")
    args = parser.parse_args()

    INBOX.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    queue = load_queue()
    queue_by_id = {item["content_id"]: item for item in queue}
    specs = load_batch_specs()
    imported: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    inbox_files = iter_inbox_files()
    for path in inbox_files:
        text = path.read_text(encoding="utf-8-sig")
        articles = split_articles(text)
        if not articles:
            failed.append({"file": path.name, "content_id": "", "reason": "no front matter article found"})
            continue
        file_imported = 0
        for index, (meta, body) in enumerate(articles, start=1):
            content_id = meta.get("content_id", "")
            errors = validate_article(meta, body, specs, queue_by_id)
            target = DRAFTS / f"{content_id}.md" if content_id else DRAFTS / f"{path.stem}-{index}.md"
            queue_item = queue_by_id.get(content_id)
            if queue_item and queue_item.get("status") == "published":
                errors.append("published content cannot be overwritten by import")
            if errors:
                failed.append({"file": path.name, "article": index, "content_id": content_id, "reason": "; ".join(errors)})
                continue
            skip_reason = should_skip_existing(target, queue_item, args.allow_overwrite)
            if skip_reason:
                skipped.append({"file": path.name, "article": index, "content_id": content_id, "reason": skip_reason})
                continue
            normalized = canonical_article(meta, body)
            target.write_text(normalized, encoding="utf-8", newline="\n")
            update_queue_status(queue, content_id, meta)
            imported.append({"file": path.name, "article": index, "content_id": content_id, "target": target.relative_to(ROOT).as_posix()})
            file_imported += 1
        if file_imported:
            shutil.copyfile(path, ARCHIVE / path.name)

    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
    }
    (ASSETS / "import_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = [
        "# Content Import Report",
        "",
        f"- imported: {len(imported)}",
        f"- skipped: {len(skipped)}",
        f"- failed: {len(failed)}",
        "",
        "## Imported",
        "",
    ]
    rows.extend(f"- {item['content_id']} from {item['file']} -> {item['target']}" for item in imported)
    rows.extend(["", "## Skipped", ""])
    rows.extend(f"- {item.get('content_id', '')} from {item['file']}: {item['reason']}" for item in skipped)
    rows.extend(["", "## Failed", ""])
    rows.extend(f"- {item.get('content_id', '')} from {item['file']}: {item['reason']}" for item in failed)
    (DOCS / "content-import-report.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

    print(f"[OK] imported {len(imported)} drafts, skipped {len(skipped)}, failed {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
