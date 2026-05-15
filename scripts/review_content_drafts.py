from __future__ import annotations

import html.parser
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "site_src" / "content_drafts"
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
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
LEGAL_DRAFT_STATUSES = {"draft_received", "reviewed", "published"}


class BodyHtmlParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.append(tag)


def parse_md(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}, text.strip()
    try:
        _, front, body = text.split("---", 2)
    except ValueError:
        return {}, text.strip()
    meta: dict[str, str] = {}
    for line in front.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body.strip()


def normalize_url(url: str) -> str:
    return url.strip()


def load_json(path: Path):
    if not path.exists():
        return [] if path.name.endswith(".json") else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def contains_html(body: str) -> bool:
    parser = BodyHtmlParser()
    try:
        parser.feed(body)
    except Exception:
        return True
    allowed_inline = set()
    return any(tag not in allowed_inline for tag in parser.tags)


def extract_internal_links(body: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", body)


def is_article_draft(meta: dict[str, str]) -> bool:
    return meta.get("target_url", "").startswith("/blog/")


def review_internal_links(meta: dict[str, str], queue_item: dict | None, body: str) -> list[str]:
    if not is_article_draft(meta):
        return []
    links = list(dict.fromkeys(extract_internal_links(body)))
    warnings: list[str] = []
    if len(links) < 4:
        warnings.append("less than 4 internal links")
    if not any(link.startswith("/platforms/") or (link.startswith("/services/") and link != "/services/") for link in links):
        warnings.append("missing platform or service internal link")
    if not any(link.startswith("/topics/") and link != "/topics/" for link in links):
        warnings.append("missing topic internal link")
    if not any(link in {"/services/", "/topics/"} for link in links):
        warnings.append("missing services/topics listing internal link")
    if "/contact/" not in links:
        warnings.append("missing contact internal link")
    if queue_item:
        target_service = (queue_item.get("target_service") or "").strip()
        target_topic = (queue_item.get("target_topic") or "").strip()
        if target_service and target_service not in links:
            warnings.append(f"missing preferred service link: {target_service}")
        if target_topic and target_topic not in links:
            warnings.append(f"missing preferred topic link: {target_topic}")
    return warnings


def check_markdown_headings(body: str) -> list[str]:
    issues = []
    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("# "):
            issues.append(f"body heading starts with # on line {line_no}; use ## or lower")
    return issues


def review_one(path: Path, queue_by_id: dict[str, dict]) -> dict:
    meta, body = parse_md(path)
    issues: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if not meta.get(field):
            issues.append(f"missing {field}")

    status = meta.get("status", "")
    if status and status not in LEGAL_DRAFT_STATUSES:
        issues.append(f"invalid status: {status}")

    content_id = meta.get("content_id", "")
    queue_item = queue_by_id.get(content_id)
    if content_id and not queue_item:
        issues.append("content_id not found in content_queue")
    if queue_item and queue_item.get("status") == "draft_received" and status != "draft_received":
        issues.append("DeepSeek import-stage draft must keep status draft_received")
    if queue_item and queue_item.get("status") in LEGAL_DRAFT_STATUSES and status and status != queue_item.get("status"):
        warnings.append(f"front matter status differs from queue status {queue_item.get('status')}")

    title = meta.get("title", "").strip()
    description = meta.get("description", "").strip()
    target_url = normalize_url(meta.get("target_url", ""))
    primary_keyword = meta.get("primary_keyword", "").strip()

    if not title:
        issues.append("title is empty")
    if not description:
        issues.append("description is empty")
    elif len(description) < 40:
        warnings.append("description may be too short")
    elif len(description) > 160:
        warnings.append("description may be too long")
    if not target_url:
        issues.append("target_url is empty")
    if target_url and (not target_url.startswith("/") or not target_url.endswith("/")):
        issues.append("target_url must start and end with /")

    if len(body) < 800:
        issues.append("body too short")
    if not body.strip():
        issues.append("body is empty")
    issues.extend(check_markdown_headings(body))
    if contains_html(body):
        issues.append("HTML body is not allowed")

    keyword_area = f"{title}\n{description}\n{body[:1000]}"
    if primary_keyword and primary_keyword not in keyword_area:
        issues.append("primary_keyword does not appear in title, description, or opening body")
    if primary_keyword and body.count(primary_keyword) > 12:
        warnings.append("possible keyword stuffing")

    warnings.extend(review_internal_links(meta, queue_item, body))

    return {
        "file": path.name,
        "content_id": content_id,
        "target_url": target_url,
        "status": "fail" if issues else "warning" if warnings else "pass",
        "issues": issues,
        "warnings": warnings,
    }


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    queue = load_json(QUEUE_PATH)
    queue_by_id = {item["content_id"]: item for item in queue}
    draft_paths = [path for path in sorted(DRAFTS.glob("*.md")) if path.name.upper() != "README.MD"]

    results = [review_one(path, queue_by_id) for path in draft_paths]
    ids: dict[str, str] = {}
    urls: dict[str, str] = {}
    for result in results:
        content_id = result["content_id"]
        target_url = result["target_url"]
        if content_id:
            if content_id in ids:
                result["issues"].append(f"duplicate content_id also in {ids[content_id]}")
                result["status"] = "fail"
            ids[content_id] = result["file"]
        if target_url:
            if target_url in urls:
                result["issues"].append(f"duplicate target_url also in {urls[target_url]}")
                result["status"] = "fail"
            urls[target_url] = result["file"]

    failures = [item for item in results if item["issues"]]
    warnings = [item for item in results if item["warnings"]]
    report = {
        "draft_count": len(results),
        "pass_count": sum(1 for item in results if item["status"] == "pass"),
        "warning_count": sum(1 for item in results if item["status"] == "warning"),
        "fail_count": len(failures),
        "articles": results,
    }
    (ASSETS / "draft_review_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    rows = [
        "# Content Draft Review Report",
        "",
        f"- drafts: {len(results)}",
        f"- pass: {report['pass_count']}",
        f"- warning: {report['warning_count']}",
        f"- fail: {report['fail_count']}",
        "",
        "| File | content_id | Result | Issues | Warnings |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in results:
        rows.append(
            f"| {item['file']} | {item['content_id']} | {item['status']} | "
            f"{'; '.join(item['issues']) or '-'} | {('; '.join(item['warnings']) or '-')} |"
        )
    if not results:
        rows.extend(["", "No content drafts found. Review gate is ready for imported DeepSeek drafts."])
    (DOCS / "content-draft-review-report.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

    print(f"[OK] reviewed {len(results)} drafts, failures {len(failures)}, warnings {len(warnings)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
