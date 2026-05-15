from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
CONTENT_STATUS_PATH = CONTENT_DIR / "content_status.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
REVIEW_REPORT_PATH = ROOT / "data" / "content-assets" / "draft_review_report.json"
APPROVAL_REPORT_JSON = ROOT / "data" / "content-assets" / "approved_reviewed_drafts_report.json"
APPROVAL_REPORT_MD = ROOT / "docs" / "approved-reviewed-drafts-report.md"


STATUS_KEYS = ("prompt_ready", "writing", "draft_received", "reviewed", "published", "paused")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Approve reviewed 9HWH content drafts for daily publishing.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of pass drafts to approve.")
    parser.add_argument("--dry-run", action="store_true", help="Preview approvals without writing files.")
    return parser.parse_args()


def read_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"missing required file: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def content_status_summary(queue: list[dict]) -> dict:
    summary = {
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
        if status in STATUS_KEYS:
            summary[status] += 1
    return summary


def update_draft_status(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        raise ValueError(f"draft missing front matter: {path.relative_to(ROOT)}")
    lines = text.splitlines()
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        raise ValueError(f"draft front matter is not closed: {path.relative_to(ROOT)}")

    for index in range(1, closing_index):
        if lines[index].startswith("status:"):
            lines[index] = f"status: {status}"
            break
    else:
        lines.insert(closing_index, f"status: {status}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def publish_queue_entry(queue_item: dict, review_item: dict, template: dict | None) -> dict:
    entry = deepcopy(template or {})
    entry.update(
        {
            "content_id": queue_item["content_id"],
            "title": queue_item.get("title", review_item.get("title", "")),
            "target_url": queue_item.get("target_url", review_item.get("target_url", "")),
            "primary_keyword": queue_item.get("primary_keyword", ""),
            "content_type": queue_item.get("page_type", queue_item.get("content_type", "")),
            "priority_score": queue_item.get("priority", 0),
            "risk_level": queue_item.get("risk_level", "low"),
            "publish_status": "queued",
            "planned_publish_date": queue_item.get("planned_publish_date", ""),
            "batch": queue_item.get("batch", ""),
            "review_status": "pass",
            "internal_link_count": len(queue_item.get("internal_links", [])),
            "notes": "approved_from_review",
        }
    )
    return entry


def write_report(report: dict) -> None:
    write_json(APPROVAL_REPORT_JSON, report)
    rows = [
        "# Approved Reviewed Drafts Report",
        "",
        f"- status: {report['status']}",
        f"- dry_run: {report['dry_run']}",
        f"- limit: {report['limit']}",
        f"- pass_count: {report['pass_count']}",
        f"- eligible_count: {report['eligible_count']}",
        f"- approved_count: {report['approved_count']}",
        f"- skipped_count: {report['skipped_count']}",
        f"- generated_at: {report['generated_at']}",
        "",
        "## Approved Items",
        "",
        "| content_id | title | target_url |",
        "| --- | --- | --- |",
    ]
    for item in report["approved_items"]:
        rows.append(f"| {item['content_id']} | {item.get('title', '')} | {item.get('target_url', '')} |")
    rows.extend(["", "## Skipped Items", "", "| content_id | reason |", "| --- | --- |"])
    for item in report["skipped_items"]:
        rows.append(f"| {item.get('content_id', '')} | {item.get('reason', '')} |")
    if report["errors"]:
        rows.extend(["", "## Errors", ""])
        rows.extend(f"- {error}" for error in report["errors"])
    APPROVAL_REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    APPROVAL_REPORT_MD.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        print("[FAIL] limit must be non-negative")
        return 1

    try:
        review_report = read_json(REVIEW_REPORT_PATH)
        content_queue = read_json(CONTENT_QUEUE_PATH)
        publish_queue = read_json(PUBLISH_QUEUE_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}")
        return 1

    articles = review_report.get("articles")
    if not isinstance(articles, list):
        print("[FAIL] draft_review_report.json missing articles list")
        return 1

    content_by_id = {item.get("content_id"): item for item in content_queue if item.get("content_id")}
    publish_by_id = {item.get("content_id"): item for item in publish_queue if item.get("content_id")}
    template = publish_queue[0] if publish_queue else None

    pass_articles = [item for item in articles if item.get("status") == "pass"]
    approved_items: list[dict] = []
    skipped_items: list[dict] = []
    errors: list[str] = []

    for review_item in pass_articles:
        content_id = review_item.get("content_id")
        if not content_id:
            errors.append("pass review item missing content_id")
            continue
        queue_item = content_by_id.get(content_id)
        if not queue_item:
            errors.append(f"{content_id}: missing from content_queue.json")
            continue

        queue_status = queue_item.get("status")
        if queue_status == "published":
            skipped_items.append({"content_id": content_id, "reason": "already_published"})
            continue
        if queue_status != "draft_received":
            skipped_items.append({"content_id": content_id, "reason": f"status_is_{queue_status}"})
            continue

        draft_path = DRAFTS_DIR / f"{content_id}.md"
        if not draft_path.exists():
            errors.append(f"{content_id}: missing draft file {draft_path.relative_to(ROOT)}")
            continue

        approved_items.append(
            {
                "content_id": content_id,
                "title": queue_item.get("title", ""),
                "target_url": queue_item.get("target_url", review_item.get("target_url", "")),
                "draft_file": str(draft_path.relative_to(ROOT)).replace("\\", "/"),
            }
        )
        if len(approved_items) >= args.limit:
            break

    report = {
        "status": "success" if not errors else "failure",
        "dry_run": args.dry_run,
        "limit": args.limit,
        "pass_count": len(pass_articles),
        "eligible_count": len(approved_items),
        "approved_count": 0 if args.dry_run else len(approved_items),
        "skipped_count": len(skipped_items),
        "approved_items": approved_items,
        "skipped_items": skipped_items,
        "errors": errors,
        "generated_at": iso_now(),
        "message": "",
    }
    if errors:
        report["message"] = "Approval failed because review/content data is inconsistent."
        if not args.dry_run:
            write_report(report)
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    if args.dry_run:
        report["message"] = (
            f"Dry-run found {len(approved_items)} eligible draft(s)."
            if approved_items
            else "Dry-run found no eligible drafts."
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    for item in approved_items:
        content_id = item["content_id"]
        queue_item = content_by_id[content_id]
        queue_item["status"] = "reviewed"
        update_draft_status(DRAFTS_DIR / f"{content_id}.md", "reviewed")
        if content_id in publish_by_id:
            publish_by_id[content_id]["publish_status"] = "queued"
            publish_by_id[content_id]["review_status"] = "pass"
        else:
            new_entry = publish_queue_entry(queue_item, item, template)
            publish_queue.append(new_entry)
            publish_by_id[content_id] = new_entry

    if approved_items:
        write_json(CONTENT_QUEUE_PATH, content_queue)
        write_json(PUBLISH_QUEUE_PATH, publish_queue)
        write_json(CONTENT_STATUS_PATH, content_status_summary(content_queue))
    report["message"] = (
        f"Approved {len(approved_items)} reviewed draft(s)."
        if approved_items
        else "No eligible drafts to approve."
    )
    write_report(report)

    print(
        f"[OK] eligible_count={report['eligible_count']} "
        f"approved_count={report['approved_count']} skipped_count={report['skipped_count']}"
    )
    if not approved_items:
        print("[OK] no eligible drafts")
    for item in approved_items:
        print(f"[OK] approved {item['content_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
