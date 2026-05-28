from __future__ import annotations

import argparse
import json
import html.parser
import re
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
REVIEW_REPORT_PATH = ROOT / "data" / "content-assets" / "draft_review_report.json"
RULES_PATH = CONTENT_DIR / "content_rules.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
BATCHES_DIR = ROOT / "data" / "deepseek-batches"
REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "publish_queue_report.json"
REPORT_MD_PATH = ROOT / "docs" / "publish-queue-report.md"

DEFAULT_DAILY_LIMIT = 12
HARD_LIMIT = 20
HIGH_RISK_CLUSTERS = {"crypto-promotion", "loan-leads", "insurance-leads", "immigration-leads", "finance-leads"}


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


def extract_internal_links(body: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", body)


def contains_html(body: str) -> bool:
    parser = BodyHtmlParser()
    try:
        parser.feed(body)
    except Exception:
        return True
    return bool(parser.tags)


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


def load_batch_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for batch_dir in sorted(BATCHES_DIR.glob("batch-*")):
        index_path = batch_dir / f"{batch_dir.name}-index.json"
        if not index_path.exists():
            continue
        for item in load_json(index_path, []):
            content_id = item.get("content_id")
            if content_id:
                lookup[content_id] = batch_dir.name
    return lookup


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


def count_internal_links(content_id: str) -> int:
    path = DRAFTS_DIR / f"{content_id}.md"
    if not path.exists():
        return 0
    _, body = parse_md(path)
    return len(list(dict.fromkeys(extract_internal_links(body))))


def candidate_is_publishable(item: dict, review_item: dict, rules: dict) -> tuple[bool, str]:
    if item.get("internal_only"):
        return False, "internal_only"
    if item.get("status") != "reviewed":
        return False, f"status={item.get('status')}"
    if review_item.get("status") != "pass":
        return False, f"review={review_item.get('status')}"
    if review_item.get("issues") or review_item.get("warnings"):
        return False, "review_has_findings"
    if not item.get("target_url"):
        return False, "missing_target_url"
    draft_path = DRAFTS_DIR / f"{item['content_id']}.md"
    if not draft_path.exists():
        return False, "missing_draft"
    meta, body = parse_md(draft_path)
    if meta.get("status") != "reviewed":
        return False, f"draft_status={meta.get('status', '')}"
    if contains_html(body):
        return False, "contains_html"
    if any(line.strip().startswith("# ") for line in body.splitlines()):
        return False, "contains_h1"
    link_count = count_internal_links(item["content_id"])
    if link_count < max(4, int(rules.get("internal_link_rules", {}).get("minimum_article_links", 4))):
        return False, f"internal_links={link_count}"
    return True, "ok"


def build_candidate(item: dict, review_item: dict, batch_lookup: dict[str, str], rules: dict) -> dict:
    priority = int(item.get("priority", 999))
    priority_score = max(1, 100 - priority)
    risk_level = item.get("risk_level", "unknown")
    if risk_level == "low":
        priority_score += 5
    if infer_content_type(item) in {"core", "service", "platform", "topic"}:
        priority_score += 3
    if item.get("cluster_id") in HIGH_RISK_CLUSTERS:
        priority_score -= 2
    _, reason = candidate_is_publishable(item, review_item, rules)
    return {
        "content_id": item["content_id"],
        "title": item.get("title", ""),
        "target_url": item.get("target_url", ""),
        "primary_keyword": item.get("primary_keyword", ""),
        "content_type": infer_content_type(item),
        "priority_score": priority_score,
        "risk_level": risk_level,
        "publish_status": "publish_candidate",
        "planned_publish_date": "",
        "batch": batch_lookup.get(item["content_id"], ""),
        "review_status": review_item.get("status", "unknown"),
        "internal_link_count": count_internal_links(item["content_id"]),
        "notes": reason,
    }


def merge_existing(existing: list[dict], planned: list[dict]) -> list[dict]:
    existing_by_id = {item["content_id"]: item for item in existing if item.get("content_id")}
    merged: list[dict] = []
    seen: set[str] = set()
    for item in planned:
        current = existing_by_id.get(item["content_id"], {})
        if current.get("publish_status") in {"published", "skipped"}:
            preserved = current.copy()
            preserved.update({key: value for key, value in item.items() if key not in {"publish_status", "planned_publish_date", "notes"}})
            preserved.setdefault("notes", item.get("notes", ""))
            merged.append(preserved)
        else:
            combined = current.copy()
            combined.update(item)
            merged.append(combined)
        seen.add(item["content_id"])
    for item in existing:
        if item.get("content_id") not in seen and item.get("publish_status") in {"published", "skipped"}:
            merged.append(item)
    merged.sort(key=lambda value: (value.get("planned_publish_date") or "9999-12-31", -int(value.get("priority_score", 0)), value.get("content_id", "")))
    return merged


def day_rank(buckets: list[list[dict]], day_index: int, candidate: dict) -> tuple[int, int, int, int]:
    bucket = buckets[day_index]
    same_risk = sum(1 for item in bucket if item.get("risk_level") == candidate.get("risk_level"))
    high_risk_count = sum(1 for item in bucket if item.get("risk_level") in {"medium", "high"})
    return (high_risk_count if candidate.get("risk_level") in {"medium", "high"} else len(bucket), same_risk, len(bucket), day_index)


def schedule_candidates(candidates: list[dict], start_date: date, days: int, daily_limit: int) -> tuple[list[dict], list[dict], list[dict]]:
    buckets: list[list[dict]] = [[] for _ in range(days)]
    scheduled: list[dict] = []
    unscheduled: list[dict] = []
    ordered = sorted(
        candidates,
        key=lambda item: (
            0 if item.get("risk_level") in {"medium", "high"} else 1,
            -int(item.get("priority_score", 0)),
            item.get("content_id", ""),
        ),
    )
    for item in ordered:
        available_days = [day_index for day_index, bucket in enumerate(buckets) if len(bucket) < daily_limit]
        if not available_days:
            unscheduled.append(item)
            continue
        chosen = min(available_days, key=lambda day_index: day_rank(buckets, day_index, item))
        entry = item.copy()
        entry["planned_publish_date"] = (start_date + timedelta(days=chosen)).isoformat()
        entry["publish_status"] = "queued"
        buckets[chosen].append(entry)
        scheduled.append(entry)
    return scheduled, unscheduled, buckets


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
        f"- reviewed_pool: {report['reviewed_pool']}",
        f"- eligible_reviewed: {report['eligible_reviewed']}",
        f"- scheduled: {report['scheduled_count']}",
        f"- unscheduled: {report['unscheduled_count']}",
        "",
        "## Calendar Summary",
        "",
        "| Date | Total | High Risk | Items |",
        "| --- | --- | --- | --- |",
    ]
    for day in report["calendar"]:
        rows.append(
            f"| {day['date']} | {day['count']} | {day['high_risk_count']} | "
            f"{', '.join(item['content_id'] for item in day['items']) or '-'} |"
        )
    rows.extend(
        [
            "",
            "## Queue Preview",
            "",
            "| Date | content_id | Status | Type | Risk | Links | Batch | URL | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in report["queue_preview"]:
        rows.append(
            f"| {item.get('planned_publish_date') or '-'} | {item['content_id']} | {item['publish_status']} | "
            f"{item['content_type']} | {item['risk_level']} | {item['internal_link_count']} | {item.get('batch') or '-'} | "
            f"{item['target_url']} | {item.get('notes', '') or '-'} |"
        )
    REPORT_MD_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    require_limit(args.daily_limit, args.force)
    start_date = datetime.strptime(normalize_date(args.date), "%Y-%m-%d").date()
    queue = load_json(QUEUE_PATH, [])
    rules = load_json(RULES_PATH, {})
    existing_publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    review_by_id = load_review_status()
    batch_lookup = load_batch_lookup()

    review_pool = [item for item in queue if item.get("status") == "reviewed" and not item.get("internal_only")]
    published_urls = {
        item.get("target_url")
        for item in queue
        if item.get("status") == "published" and item.get("target_url")
    }
    seen_urls: set[str] = set()
    eligible: list[dict] = []
    blocked: list[dict] = []
    for item in queue:
        review_item = review_by_id.get(item.get("content_id", ""))
        if not review_item:
            continue
        ok, reason = candidate_is_publishable(item, review_item, rules)
        if not ok:
            if item.get("status") == "reviewed":
                blocked.append({"content_id": item.get("content_id"), "reason": reason})
            continue
        if item.get("target_url") in published_urls:
            blocked.append({"content_id": item.get("content_id"), "reason": "already_published"})
            continue
        if item.get("target_url") in seen_urls:
            raise SystemExit(f"[FAIL] duplicate reviewed target_url: {item.get('target_url')}")
        seen_urls.add(item.get("target_url"))
        eligible.append(build_candidate(item, review_item, batch_lookup, rules))

    scheduled, unscheduled, buckets = schedule_candidates(eligible, start_date, args.days, args.daily_limit)
    merged_queue = merge_existing(existing_publish_queue, scheduled + unscheduled)
    report = {
        "start_date": start_date.isoformat(),
        "days": args.days,
        "daily_limit": args.daily_limit,
        "hard_limit": HARD_LIMIT,
        "reviewed_pool": len(review_pool),
        "eligible_reviewed": len(eligible),
        "scheduled_count": len(scheduled),
        "unscheduled_count": len(unscheduled),
        "blocked_reviewed": blocked,
        "calendar": [
            {
                "date": (start_date + timedelta(days=index)).isoformat(),
                "count": len(bucket),
                "high_risk_count": sum(1 for item in bucket if item.get("risk_level") in {"medium", "high"}),
                "items": bucket,
            }
            for index, bucket in enumerate(buckets)
            if bucket
        ],
        "queue_preview": merged_queue,
        "dry_run": args.dry_run,
    }
    write_report(report)
    if not args.dry_run:
        PUBLISH_QUEUE_PATH.write_text(json.dumps(merged_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"[OK] publish queue planned: reviewed_pool={len(review_pool)} eligible={len(eligible)} "
        f"scheduled={len(scheduled)} unscheduled={len(unscheduled)} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
