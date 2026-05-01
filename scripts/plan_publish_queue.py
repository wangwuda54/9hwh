from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
REVIEW_REPORT_PATH = ROOT / "data" / "content-assets" / "draft_review_report.json"
REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "publish_queue_report.json"
REPORT_MD_PATH = ROOT / "docs" / "publish-queue-report.md"

DEFAULT_DAILY_LIMIT = 12
HARD_LIMIT = 20


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan publish queue from reviewed content.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Planning start date in YYYY-MM-DD format.")
    parser.add_argument("--days", type=int, default=30, help="Number of days to plan.")
    parser.add_argument("--daily-limit", type=int, default=DEFAULT_DAILY_LIMIT, help="Maximum planned items per day.")
    parser.add_argument("--dry-run", action="store_true", help="Preview plan without updating publish_queue.json.")
    parser.add_argument("--force", action="store_true", help="Allow daily limit above the hard limit.")
    return parser.parse_args()


def require_limit(limit: int, force: bool) -> None:
    if limit > HARD_LIMIT and not force:
        raise SystemExit(f"[FAIL] daily limit {limit} exceeds hard limit {HARD_LIMIT}; rerun with --force to override")


def normalize_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").date().isoformat()


def load_review_status() -> dict[str, dict]:
    report = load_json(REVIEW_REPORT_PATH, {"articles": []})
    return {item["content_id"]: item for item in report.get("articles", []) if item.get("content_id")}


def infer_content_type(item: dict) -> str:
    page_type = item.get("page_type", "")
    intent = item.get("intent", "")
    if page_type == "topic_expansion":
        return "topic"
    if item.get("target_service"):
        return "service"
    if item.get("target_topic"):
        return "topic"
    if any(link.startswith("/platforms/") for link in item.get("internal_links", [])):
        return "platform"
    if item.get("cluster_id") == "markets":
        return "core"
    if intent == "long_tail_question":
        return "long_tail"
    return "expert"


def build_candidate(item: dict, review_item: dict) -> dict:
    priority = int(item.get("priority", 999))
    priority_score = max(1, 100 - priority)
    if item.get("risk_level") == "low":
        priority_score += 5
    if infer_content_type(item) in {"core", "service", "platform", "topic"}:
        priority_score += 3
    return {
        "content_id": item["content_id"],
        "target_url": item["target_url"],
        "title": item.get("title", ""),
        "primary_keyword": item.get("primary_keyword", ""),
        "content_type": infer_content_type(item),
        "priority_score": priority_score,
        "publish_status": "publish_candidate",
        "planned_publish_date": "",
        "risk_level": item.get("risk_level", "unknown"),
        "internal_only": bool(item.get("internal_only")),
        "notes": f"review={review_item.get('status', 'unknown')}; queue_status={item.get('status', '')}",
    }


def merge_existing(existing: list[dict], planned: list[dict]) -> list[dict]:
    existing_by_id = {item["content_id"]: item for item in existing if item.get("content_id")}
    merged: list[dict] = []
    seen: set[str] = set()
    for item in planned:
        existing_item = existing_by_id.get(item["content_id"], {})
        if existing_item.get("publish_status") in {"published", "skipped"}:
            preserved = existing_item.copy()
            preserved.setdefault("planned_publish_date", item["planned_publish_date"])
            preserved.setdefault("notes", item["notes"])
            merged.append(preserved)
        else:
            merged_item = existing_item.copy()
            merged_item.update(item)
            merged.append(merged_item)
        seen.add(item["content_id"])
    for item in existing:
        if item.get("content_id") not in seen and item.get("publish_status") in {"published", "skipped"}:
            merged.append(item)
    merged.sort(key=lambda value: (value.get("planned_publish_date") or "9999-12-31", -int(value.get("priority_score", 0)), value.get("content_id", "")))
    return merged


def write_report(report: dict) -> None:
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = [
        "# Publish Queue Report",
        "",
        f"- start_date: {report['start_date']}",
        f"- days: {report['days']}",
        f"- daily_limit: {report['daily_limit']}",
        f"- hard_limit: {report['hard_limit']}",
        f"- eligible_reviewed: {report['eligible_reviewed']}",
        f"- scheduled: {report['scheduled_count']}",
        f"- unscheduled: {report['unscheduled_count']}",
        f"- published_preserved: {report['published_preserved']}",
        f"- skipped_preserved: {report['skipped_preserved']}",
        "",
        "| Date | content_id | Status | Type | Priority Score | URL | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["queue_preview"]:
        rows.append(
            f"| {item.get('planned_publish_date') or '-'} | {item['content_id']} | {item['publish_status']} | "
            f"{item['content_type']} | {item['priority_score']} | {item['target_url']} | {item.get('notes', '') or '-'} |"
        )
    REPORT_MD_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    require_limit(args.daily_limit, args.force)
    start_date = datetime.strptime(normalize_date(args.date), "%Y-%m-%d").date()
    queue = load_json(QUEUE_PATH, [])
    existing_publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    review_by_id = load_review_status()

    eligible = []
    for item in queue:
        if item.get("internal_only"):
            continue
        if item.get("status") != "reviewed":
            continue
        review_item = review_by_id.get(item.get("content_id", ""))
        if not review_item or review_item.get("status") != "pass":
            continue
        eligible.append(build_candidate(item, review_item))

    eligible.sort(key=lambda value: (-int(value["priority_score"]), value["content_id"]))
    schedule_capacity = args.days * args.daily_limit
    scheduled: list[dict] = []
    unscheduled: list[dict] = []
    for index, item in enumerate(eligible):
        entry = item.copy()
        if index < schedule_capacity:
            day_offset = index // args.daily_limit
            entry["planned_publish_date"] = (start_date + timedelta(days=day_offset)).isoformat()
            entry["publish_status"] = "queued"
            scheduled.append(entry)
        else:
            unscheduled.append(entry)
    merged_queue = merge_existing(existing_publish_queue, scheduled + unscheduled)

    report = {
        "start_date": start_date.isoformat(),
        "days": args.days,
        "daily_limit": args.daily_limit,
        "hard_limit": HARD_LIMIT,
        "eligible_reviewed": len(eligible),
        "scheduled_count": len(scheduled),
        "unscheduled_count": len(unscheduled),
        "published_preserved": sum(1 for item in merged_queue if item.get("publish_status") == "published"),
        "skipped_preserved": sum(1 for item in merged_queue if item.get("publish_status") == "skipped"),
        "queue_preview": merged_queue,
        "dry_run": args.dry_run,
    }
    write_report(report)
    if not args.dry_run:
        PUBLISH_QUEUE_PATH.write_text(json.dumps(merged_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"[OK] publish queue planned: eligible={len(eligible)} scheduled={len(scheduled)} "
        f"unscheduled={len(unscheduled)} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
