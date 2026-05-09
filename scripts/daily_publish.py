from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import traceback
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from pre_publish_audit import load_json as audit_load_json
from pre_publish_audit import load_review_by_id as audit_load_review_by_id
from pre_publish_audit import select_candidates, validate_candidate


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
CONTENT_STATUS_PATH = CONTENT_DIR / "content_status.json"
RULES_PATH = CONTENT_DIR / "content_rules.json"
POLICY_PATH = CONTENT_DIR / "publish_policy.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "daily_publish_report.json"
REPORT_MD_PATH = ROOT / "docs" / "daily-publish-report.md"
DRY_RUN_REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "daily_publish_dry_run_report.json"
DRY_RUN_REPORT_MD_PATH = ROOT / "docs" / "daily-publish-dry-run-report.md"
DEFAULT_SITE_URL = "https://www.9hwh.com"

MODE_LIMITS = {
    "conservative": 1,
    "normal": 3,
    "growth": 5,
    "aggressive": 10,
}
DEFAULT_MODE = "normal"
DEFAULT_DAILY_LIMIT = 3
HARD_LIMIT = 10
POST_PUBLISH_CHECKS = [
    ["python", "scripts/build_site.py"],
    ["python", "scripts/check_static_site.py"],
    ["python", "scripts/check_sitemap_readiness.py"],
]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def full_url(site_url: str, target_url: str) -> str:
    return urljoin(site_url.rstrip("/") + "/", target_url.lstrip("/"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish reviewed 9HWH content according to the daily policy.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Publish date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, help="Number of reviewed items to publish.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing content status.")
    parser.add_argument(
        "--mode",
        choices=["conservative", "normal", "growth", "aggressive"],
        default=DEFAULT_MODE,
        help="Daily publishing pace.",
    )
    parser.add_argument("--force", action="store_true", help="Allow a limit above the hard cap after manual confirmation.")
    return parser.parse_args()


def load_policy() -> dict:
    return audit_load_json(
        POLICY_PATH,
        {
            "initial_daily_limit": DEFAULT_DAILY_LIMIT,
            "stable_daily_limit": MODE_LIMITS["growth"],
            "hard_daily_limit": HARD_LIMIT,
        },
    )


def resolve_limit(args: argparse.Namespace, policy: dict) -> int:
    if args.limit is not None:
        return args.limit
    if args.mode == "normal":
        return int(policy.get("initial_daily_limit", DEFAULT_DAILY_LIMIT))
    if args.mode == "growth":
        return int(policy.get("stable_daily_limit", MODE_LIMITS["growth"]))
    return MODE_LIMITS[args.mode]


def require_limit(limit: int, hard_limit: int, force: bool) -> None:
    if limit < 0:
        raise SystemExit("[FAIL] limit must be non-negative")
    if limit > hard_limit and not force:
        raise SystemExit(
            f"[FAIL] daily limit {limit} exceeds hard limit {hard_limit}; "
            "manual confirmation is required via --force"
        )


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


def validate_publish_pool(content_queue: list[dict], publish_queue: list[dict], rules: dict) -> tuple[list[str], list[dict]]:
    review_by_id = audit_load_review_by_id()
    content_by_id = {item["content_id"]: item for item in content_queue if item.get("content_id")}
    queue_by_url = {item.get("target_url"): item for item in content_queue if item.get("target_url")}

    validation_errors: list[str] = []
    validated_candidates: list[dict] = []
    seen_urls: set[str] = set()
    eligible = [item for item in publish_queue if item.get("publish_status") in {"queued", "publish_candidate"}]

    for entry in eligible:
        content_id = entry.get("content_id", "")
        if content_id.startswith("c045-"):
            validation_errors.append(f"{content_id}: c045 cannot be published")
            continue
        target_url = entry.get("target_url", "")
        if target_url:
            if target_url in seen_urls:
                validation_errors.append(f"{content_id}: duplicate target_url in publish queue {target_url}")
                continue
            seen_urls.add(target_url)

        errors, candidate = validate_candidate(entry, content_by_id, review_by_id, rules, queue_by_url)
        validation_errors.extend(errors)
        if candidate and not errors:
            validated_candidates.append(candidate)

    return validation_errors, validated_candidates


def run_post_publish_checks() -> list[dict]:
    checks: list[dict] = []
    for command in POST_PUBLISH_CHECKS:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        checks.append(
            {
                "command": " ".join(command),
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
        if completed.returncode != 0:
            break
    return checks


def summarize_total_published(queue: list[dict]) -> int:
    return sum(1 for item in queue if item.get("status") == "published")


def report_paths(report: dict) -> tuple[Path, Path]:
    if report.get("dry_run"):
        return DRY_RUN_REPORT_JSON_PATH, DRY_RUN_REPORT_MD_PATH
    return REPORT_JSON_PATH, REPORT_MD_PATH


def write_report(report: dict) -> None:
    report_json_path, report_md_path = report_paths(report)
    write_json(report_json_path, report)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    title = "# Daily Publish Dry-Run Report" if report.get("dry_run") else "# Daily Publish Report"
    rows = [
        title,
        "",
        f"- status: {report['status']}",
        f"- run_date: {report['run_date']}",
        f"- mode: {report['mode']}",
        f"- daily_limit: {report['daily_limit']}",
        f"- hard_limit: {report['hard_limit']}",
        f"- dry_run: {report['dry_run']}",
        f"- selected_count: {report['selected_count']}",
        f"- published_count: {report['published_count']}",
        f"- total_published: {report['total_published']}",
        f"- site_url: {report['site_url']}",
        f"- message: {report['message']}",
        "",
        "## Published Items",
        "",
        "| content_id | Title | URL |",
        "| --- | --- | --- |",
    ]
    for item in report["published_items"]:
        rows.append(f"| {item['content_id']} | {item['title']} | {item['full_url']} |")
    if report["errors"]:
        rows.extend(["", "## Errors", ""])
        rows.extend(f"- {error}" for error in report["errors"])
    if report["post_publish_checks"]:
        rows.extend(["", "## Post Publish Checks", "", "| Command | Return code |", "| --- | --- |"])
        for check in report["post_publish_checks"]:
            rows.append(f"| `{check['command']}` | {check['returncode']} |")
    report_md_path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def write_unhandled_failure_report(exc: Exception) -> None:
    dry_run = "--dry-run" in sys.argv[1:]
    today = date.today().isoformat()
    message = f"Daily publish failed before completion: {exc}"
    report = {
        "status": "failure",
        "run_date": today,
        "date": today,
        "mode": DEFAULT_MODE,
        "daily_limit": DEFAULT_DAILY_LIMIT,
        "hard_limit": HARD_LIMIT,
        "dry_run": dry_run,
        "reviewed_candidate_count": 0,
        "selected_count": 0,
        "published_count": 0,
        "total_published": 0,
        "selected_items": [],
        "published_items": [],
        "skipped_items": [],
        "errors": [message, traceback.format_exc()],
        "post_publish_checks": [],
        "site_url": os.environ.get("SITE_URL", DEFAULT_SITE_URL),
        "message": message,
        "generated_at": iso_now(),
    }
    write_report(report)


def main() -> int:
    args = parse_args()
    publish_date = datetime.strptime(args.date, "%Y-%m-%d").date().isoformat()
    site_url = os.environ.get("SITE_URL", DEFAULT_SITE_URL)
    policy = load_policy()
    hard_limit = int(policy.get("hard_daily_limit", HARD_LIMIT))
    limit = resolve_limit(args, policy)
    require_limit(limit, hard_limit, args.force)

    content_queue = audit_load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = audit_load_json(PUBLISH_QUEUE_PATH, [])
    rules = audit_load_json(RULES_PATH, {})

    errors, validated_candidates = validate_publish_pool(content_queue, publish_queue, rules)
    selected, skipped = select_candidates(validated_candidates, limit, "aggressive" if args.mode == "growth" else args.mode)
    selected_ids = {item["content_id"] for item in selected}

    selected_items = [
        {
            "content_id": item["content_id"],
            "title": item["title"],
            "target_url": item["target_url"],
            "full_url": full_url(site_url, item["target_url"]),
            "planned_publish_date": publish_date,
            "risk_level": item["risk_level"],
            "content_type": item["content_type"],
            "internal_link_count": item["internal_link_count"],
        }
        for item in selected
    ]

    report = {
        "status": "success" if selected_items else "no_changes",
        "run_date": publish_date,
        "date": publish_date,
        "mode": args.mode,
        "daily_limit": limit,
        "hard_limit": hard_limit,
        "dry_run": args.dry_run,
        "reviewed_candidate_count": len(validated_candidates),
        "selected_count": len(selected_items),
        "published_count": 0,
        "total_published": summarize_total_published(content_queue),
        "selected_items": selected_items,
        "published_items": [],
        "skipped_items": skipped,
        "errors": errors,
        "post_publish_checks": [],
        "site_url": site_url,
        "message": "",
        "generated_at": iso_now(),
    }
    report["message"] = (
        f"Dry-run selected {len(selected_items)} reviewed item(s)."
        if args.dry_run and selected_items
        else "Dry-run found no reviewed content to publish."
        if args.dry_run
        else ""
    )

    if errors:
        report["status"] = "failure"
        report["message"] = "Daily publish validation failed."
        report["generated_at"] = iso_now()
        write_report(report)
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    if args.dry_run:
        report["generated_at"] = iso_now()
        write_report(report)
        print(f"[OK] daily publish dry-run passed for {len(selected_items)} item(s) on {publish_date}")
        return 0

    for item in content_queue:
        if item.get("content_id") in selected_ids:
            if item.get("status") != "reviewed":
                report["errors"].append(f"{item.get('content_id')}: expected reviewed before publish")
                continue
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
        if not text.startswith("---"):
            continue
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith("status:"):
                lines[index] = "status: published"
                break
        draft_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    write_json(CONTENT_QUEUE_PATH, content_queue)
    write_json(PUBLISH_QUEUE_PATH, publish_queue)
    write_json(CONTENT_STATUS_PATH, update_content_status_summary(content_queue))

    report["published_count"] = len(selected_items)
    report["published_items"] = selected_items
    report["total_published"] = summarize_total_published(content_queue)
    report["status"] = "success" if selected_items else "no_changes"
    report["message"] = (
        f"Published {len(selected_items)} reviewed item(s)."
        if selected_items
        else "No reviewed content was available for publication."
    )
    report["post_publish_checks"] = run_post_publish_checks()
    failed_checks = [check for check in report["post_publish_checks"] if check["returncode"] != 0]
    if failed_checks:
        report["status"] = "failure"
        report["errors"].append(f"post publish check failed: {failed_checks[0]['command']}")
        report["message"] = f"Post publish check failed: {failed_checks[0]['command']}"
    report["generated_at"] = iso_now()
    write_report(report)
    if failed_checks:
        print(f"[FAIL] post publish check failed: {failed_checks[0]['command']}")
        return failed_checks[0]["returncode"] or 1

    print(f"[OK] daily publish completed for {len(selected_items)} item(s) on {publish_date}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        write_unhandled_failure_report(exc)
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
