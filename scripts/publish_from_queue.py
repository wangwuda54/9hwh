from __future__ import annotations

import argparse
import html.parser
import json
import re
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
CONTENT_STATUS_PATH = CONTENT_DIR / "content_status.json"
REVIEW_REPORT_PATH = ROOT / "data" / "content-assets" / "draft_review_report.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
RULES_PATH = CONTENT_DIR / "content_rules.json"
REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "publish_dry_run_report.json"
REPORT_MD_PATH = ROOT / "docs" / "publish-dry-run-report.md"

DEFAULT_DAILY_LIMIT = 12
HARD_LIMIT = 20


class BodyHtmlParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.append(tag)


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish reviewed content from publish_queue.json.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Publish date in YYYY-MM-DD format.")
    parser.add_argument("--daily-limit", type=int, default=DEFAULT_DAILY_LIMIT, help="Maximum items to publish in one run.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying content status.")
    parser.add_argument("--force", action="store_true", help="Allow daily limit above the hard limit.")
    return parser.parse_args()


def require_limit(limit: int, force: bool) -> None:
    if limit > HARD_LIMIT and not force:
        raise SystemExit(f"[FAIL] daily limit {limit} exceeds hard limit {HARD_LIMIT}; rerun with --force to override")


def parse_md(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}, text.strip()
    _, front, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in front.splitlines():
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body.strip()


def contains_html(body: str) -> bool:
    parser = BodyHtmlParser()
    try:
        parser.feed(body)
    except Exception:
        return True
    return bool(parser.tags)


def extract_internal_links(body: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", body)


def has_forbidden_terms(text: str, rules: dict) -> list[str]:
    terms = list(rules.get("blocked_terms", []))
    return [term for term in terms if term and term in text]


def load_review_by_id() -> dict[str, dict]:
    report = load_json(REVIEW_REPORT_PATH, {"articles": []})
    return {item["content_id"]: item for item in report.get("articles", []) if item.get("content_id")}


def validate_selection(entries: list[dict], content_by_id: dict[str, dict], review_by_id: dict[str, dict], rules: dict) -> tuple[list[str], list[dict]]:
    errors: list[str] = []
    validated: list[dict] = []
    published_urls = {
        item.get("target_url")
        for item in content_by_id.values()
        if item.get("status") == "published" and item.get("target_url")
    }
    selected_urls: set[str] = set()
    for entry in entries:
        content_id = entry.get("content_id", "")
        content_item = content_by_id.get(content_id)
        if not content_item:
            errors.append(f"{content_id}: missing content_queue item")
            continue
        review_item = review_by_id.get(content_id)
        if entry.get("publish_status") not in {"queued", "publish_candidate"}:
            errors.append(f"{content_id}: invalid publish_status {entry.get('publish_status')}")
        if content_item.get("status") != "reviewed":
            errors.append(f"{content_id}: content status must be reviewed")
        if content_item.get("internal_only") or entry.get("internal_only"):
            errors.append(f"{content_id}: internal_only content cannot be published")
        if not review_item or review_item.get("status") != "pass" or review_item.get("warnings") or review_item.get("issues"):
            errors.append(f"{content_id}: review must be pass without warning/fail")
        target_url = content_item.get("target_url", "")
        if not target_url:
            errors.append(f"{content_id}: missing target_url")
        if target_url in published_urls:
            errors.append(f"{content_id}: target_url already published {target_url}")
        if target_url in selected_urls:
            errors.append(f"{content_id}: duplicate target_url in selection {target_url}")
        selected_urls.add(target_url)
        draft_path = DRAFTS_DIR / f"{content_id}.md"
        if not draft_path.exists():
            errors.append(f"{content_id}: draft file missing")
            continue
        meta, body = parse_md(draft_path)
        if meta.get("status") != "reviewed":
            errors.append(f"{content_id}: draft front matter status must be reviewed")
        if contains_html(body):
            errors.append(f"{content_id}: HTML body is not allowed")
        if any(line.strip().startswith("# ") for line in body.splitlines()):
            errors.append(f"{content_id}: body cannot contain level-1 heading")
        forbidden = has_forbidden_terms(json.dumps(meta, ensure_ascii=False) + "\n" + body, rules)
        if forbidden:
            errors.append(f"{content_id}: forbidden terms found: {', '.join(sorted(set(forbidden)))}")
        links = list(dict.fromkeys(extract_internal_links(body)))
        if len(links) < 4:
            errors.append(f"{content_id}: requires at least 4 internal links")
        if not any(link.startswith("/platforms/") or (link.startswith("/services/") and link != "/services/") for link in links):
            errors.append(f"{content_id}: missing platform/service link")
        if not any(link.startswith("/topics/") and link != "/topics/" for link in links):
            errors.append(f"{content_id}: missing topic link")
        if not any(link in {"/services/", "/topics/"} for link in links):
            errors.append(f"{content_id}: missing services/topics listing link")
        if "/contact/" not in links:
            errors.append(f"{content_id}: missing contact link")
        validated.append(
            {
                "content_id": content_id,
                "title": content_item.get("title", ""),
                "target_url": target_url,
                "planned_publish_date": entry.get("planned_publish_date", ""),
                "risk_level": entry.get("risk_level", ""),
                "content_type": entry.get("content_type", ""),
                "internal_link_count": len(links),
            }
        )
    return errors, validated


def update_content_status_summary(queue: list[dict]) -> dict:
    counts = {
        "total_planned": len(queue),
        "prompt_ready": 0,
        "writing": 0,
        "draft_received": 0,
        "reviewed": 0,
        "published": 0,
        "paused": 0,
        "last_generated_at": date.today().isoformat(),
    }
    for item in queue:
        status = item.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def write_report(report: dict) -> None:
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = [
        "# Publish Dry Run Report",
        "",
        f"- date: {report['date']}",
        f"- daily_limit: {report['daily_limit']}",
        f"- selected_count: {report['selected_count']}",
        f"- dry_run: {report['dry_run']}",
        "",
    ]
    if report["errors"]:
        rows.extend(["## Errors", ""])
        for error in report["errors"]:
            rows.append(f"- {error}")
        rows.append("")
    rows.extend(
        [
            "## Selected Items",
            "",
            "| Date | content_id | Type | Risk | Links | URL |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["selected_items"]:
        rows.append(
            f"| {item.get('planned_publish_date') or '-'} | {item['content_id']} | {item['content_type']} | "
            f"{item['risk_level']} | {item['internal_link_count']} | {item['target_url']} |"
        )
    REPORT_MD_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    require_limit(args.daily_limit, args.force)
    publish_date = datetime.strptime(args.date, "%Y-%m-%d").date().isoformat()
    content_queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    review_by_id = load_review_by_id()
    rules = load_json(RULES_PATH, {})
    content_by_id = {item["content_id"]: item for item in content_queue if item.get("content_id")}

    eligible = [
        item
        for item in publish_queue
        if item.get("publish_status") in {"queued", "publish_candidate"}
        and item.get("planned_publish_date", publish_date) <= publish_date
        and item.get("planned_publish_date")
    ]
    eligible.sort(key=lambda value: (value.get("planned_publish_date", ""), -int(value.get("priority_score", 0)), value.get("content_id", "")))
    selected = eligible[: args.daily_limit]
    errors, validated = validate_selection(selected, content_by_id, review_by_id, rules)
    report = {
        "date": publish_date,
        "daily_limit": args.daily_limit,
        "selected_count": len(validated),
        "selected_items": validated,
        "errors": errors,
        "dry_run": args.dry_run,
    }
    write_report(report)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    if args.dry_run:
        print(f"[OK] publish dry-run passed for {len(validated)} item(s) on {publish_date}")
        return 0

    selected_ids = {item["content_id"] for item in validated}
    for item in content_queue:
        if item.get("content_id") in selected_ids:
            item["status"] = "published"
    for item in publish_queue:
        if item.get("content_id") in selected_ids:
            item["publish_status"] = "published"
            item["planned_publish_date"] = publish_date
            notes = item.get("notes", "")
            item["notes"] = (notes + f" published_at={publish_date}").strip()
    write_json(CONTENT_QUEUE_PATH, content_queue)
    write_json(PUBLISH_QUEUE_PATH, publish_queue)
    write_json(CONTENT_STATUS_PATH, update_content_status_summary(content_queue))
    print(f"[OK] published {len(validated)} item(s) on {publish_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
