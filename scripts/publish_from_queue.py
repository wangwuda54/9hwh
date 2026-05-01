from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from pre_publish_audit import parse_md as audit_parse_md
from pre_publish_audit import select_candidates, validate_candidate
from pre_publish_audit import load_json as audit_load_json
from pre_publish_audit import load_review_by_id as audit_load_review_by_id


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

DEFAULT_DAILY_LIMIT = 3
HARD_LIMIT = 20


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish reviewed content from publish_queue.json.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Publish date in YYYY-MM-DD format.")
    parser.add_argument("--daily-limit", type=int, default=DEFAULT_DAILY_LIMIT, help="Maximum items to publish in one run.")
    parser.add_argument("--limit", type=int, help="Alias for how many items to publish in this staged run.")
    parser.add_argument("--mode", choices=["conservative", "normal", "aggressive"], default="normal", help="Selection policy for staged publishing.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying content status.")
    parser.add_argument("--force", action="store_true", help="Allow daily limit above the hard limit.")
    return parser.parse_args()


def require_limit(limit: int, force: bool) -> None:
    if limit > HARD_LIMIT and not force:
        raise SystemExit(f"[FAIL] daily limit {limit} exceeds hard limit {HARD_LIMIT}; rerun with --force to override")


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
    limit = args.limit or args.daily_limit
    require_limit(limit, args.force)
    publish_date = datetime.strptime(args.date, "%Y-%m-%d").date().isoformat()
    content_queue = audit_load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = audit_load_json(PUBLISH_QUEUE_PATH, [])
    review_by_id = audit_load_review_by_id()
    rules = audit_load_json(RULES_PATH, {})
    content_by_id = {item["content_id"]: item for item in content_queue if item.get("content_id")}
    queue_by_url = {item.get("target_url"): item for item in content_queue if item.get("target_url")}

    eligible = [item for item in publish_queue if item.get("publish_status") in {"queued", "publish_candidate"}]
    validation_errors: list[str] = []
    validated_candidates: list[dict] = []
    seen_urls: set[str] = set()
    for entry in eligible:
        target_url = entry.get("target_url", "")
        if target_url:
            if target_url in seen_urls:
                validation_errors.append(f"{entry.get('content_id', '')}: duplicate target_url in publish queue {target_url}")
                continue
            seen_urls.add(target_url)
        errors, candidate = validate_candidate(entry, content_by_id, review_by_id, rules, queue_by_url)
        validation_errors.extend(errors)
        if candidate and not errors:
            validated_candidates.append(candidate)

    selected, _ = select_candidates(validated_candidates, limit, args.mode)
    errors = validation_errors[:]
    validated = [
        {
            "content_id": item["content_id"],
            "title": item["title"],
            "target_url": item["target_url"],
            "planned_publish_date": item.get("planned_publish_date", ""),
            "risk_level": item["risk_level"],
            "content_type": item["content_type"],
            "internal_link_count": item["internal_link_count"],
        }
        for item in selected
    ]
    report = {
        "date": publish_date,
        "daily_limit": limit,
        "mode": args.mode,
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
    for content_id in selected_ids:
        draft_path = DRAFTS_DIR / f"{content_id}.md"
        if not draft_path.exists():
            continue
        text = draft_path.read_text(encoding="utf-8-sig")
        if text.startswith("---"):
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if line.startswith("status:"):
                    lines[index] = "status: published"
                    break
            draft_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    write_json(CONTENT_QUEUE_PATH, content_queue)
    write_json(PUBLISH_QUEUE_PATH, publish_queue)
    write_json(CONTENT_STATUS_PATH, update_content_status_summary(content_queue))
    print(f"[OK] published {len(validated)} item(s) on {publish_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
