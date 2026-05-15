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
REVIEW_REPORT_PATH = ROOT / "data" / "content-assets" / "draft_review_report.json"
RULES_PATH = CONTENT_DIR / "content_rules.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "pre_publish_audit_report.json"
REPORT_MD_PATH = ROOT / "docs" / "pre-publish-audit-report.md"

DEFAULT_LIMIT = 3
DEFAULT_MODE = "normal"
SENSITIVE_CLUSTERS = {"crypto-promotion", "loan-leads", "insurance-leads", "immigration-leads", "finance-leads"}
SOCIAL_GAME_CLUSTERS = {"game-promotion", "fb-promotion"}
SENSITIVE_URL_MARKERS = ("crypto", "loan", "insurance", "immigration", "finance")


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


def extract_internal_links(body: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", body)


def contains_html(body: str) -> bool:
    parser = BodyHtmlParser()
    try:
        parser.feed(body)
    except Exception:
        return True
    return bool(parser.tags)


def load_review_by_id() -> dict[str, dict]:
    report = load_json(REVIEW_REPORT_PATH, {"articles": []})
    return {item["content_id"]: item for item in report.get("articles", []) if item.get("content_id")}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit publish queue items before the first staged publication.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Audit date in YYYY-MM-DD format.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="How many items to recommend.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only. Default behavior for this stage.")
    parser.add_argument("--only", help="Audit a single content_id only.")
    parser.add_argument("--mode", choices=["conservative", "normal", "aggressive"], default=DEFAULT_MODE, help="Selection policy.")
    return parser.parse_args()


def classify_shape(item: dict) -> str:
    if item.get("content_type") in {"service", "platform"}:
        return "service_or_platform"
    target_url = item.get("target_url", "")
    if "/blog/topics/" in target_url or item.get("cluster_id") in SOCIAL_GAME_CLUSTERS:
        return "social_or_game_topic"
    return "ordinary_long_tail"


def is_sensitive_theme(item: dict) -> bool:
    target_url = item.get("target_url", "").lower()
    cluster_id = item.get("cluster_id", "")
    return cluster_id in SENSITIVE_CLUSTERS or any(marker in target_url for marker in SENSITIVE_URL_MARKERS)


def score_candidate(item: dict) -> tuple:
    cluster = item.get("cluster_id", "")
    content_type = item.get("content_type", "")
    risk_level = item.get("risk_level", "")
    target_url = item.get("target_url", "")
    risk_rank = {"low": 0, "medium": 1, "high": 2}.get(risk_level, 3)
    shape_bonus = 0
    if content_type in {"service", "platform"}:
        shape_bonus += 3
    if "/blog/topics/" not in target_url:
        shape_bonus += 2
    if cluster in SOCIAL_GAME_CLUSTERS:
        shape_bonus += 1
    if is_sensitive_theme(item):
        shape_bonus -= 5
    return (risk_rank, -shape_bonus, item.get("planned_publish_date", "9999-12-31"), -int(item.get("priority_score", 0)), item.get("content_id", ""))


def can_add(selection: list[dict], candidate: dict, mode: str) -> tuple[bool, str]:
    cluster = candidate.get("cluster_id", "")
    risk_level = candidate.get("risk_level", "")
    sensitive_count = sum(1 for item in selection if is_sensitive_theme(item))
    medium_or_high_count = sum(1 for item in selection if item.get("risk_level") in {"medium", "high"})
    same_cluster_count = sum(1 for item in selection if item.get("cluster_id") == cluster)

    if same_cluster_count:
        return False, "same_cluster"
    if mode == "conservative":
        if is_sensitive_theme(candidate):
            return False, "sensitive_cluster_blocked"
        if risk_level in {"medium", "high"} and medium_or_high_count >= 1:
            return False, "too_many_medium_or_high"
    elif mode == "normal":
        if is_sensitive_theme(candidate) and sensitive_count >= 1:
            return False, "too_many_sensitive_clusters"
        if risk_level in {"medium", "high"} and medium_or_high_count >= 1:
            return False, "too_many_medium_or_high"
    else:
        if is_sensitive_theme(candidate) and sensitive_count >= 1:
            return False, "too_many_sensitive_clusters"
        if risk_level == "high" and medium_or_high_count >= 2:
            return False, "too_many_high_risk"
    return True, "ok"


def validate_candidate(entry: dict, content_by_id: dict[str, dict], review_by_id: dict[str, dict], rules: dict, queue_by_url: dict[str, dict]) -> tuple[list[str], dict]:
    errors: list[str] = []
    content_id = entry.get("content_id", "")
    content_item = content_by_id.get(content_id)
    if not content_item:
        return [f"{content_id}: missing content_queue item"], {}
    if content_id.startswith("c045-"):
        errors.append(f"{content_id}: c045 cannot be published")
    if content_item.get("status") != "reviewed":
        errors.append(f"{content_id}: content status must be reviewed")
    if content_item.get("status") == "published":
        errors.append(f"{content_id}: already published")
    if content_item.get("status") == "draft_received":
        errors.append(f"{content_id}: still draft_received")
    if content_item.get("internal_only"):
        errors.append(f"{content_id}: internal_only content cannot be published")

    review_item = review_by_id.get(content_id)
    if not review_item:
        errors.append(f"{content_id}: review report missing")
    else:
        if review_item.get("status") not in {"pass", "warning"}:
            errors.append(f"{content_id}: review must be pass or warning")
        if review_item.get("issues"):
            errors.append(f"{content_id}: review fail issues must be 0")

    target_url = entry.get("target_url") or content_item.get("target_url", "")
    if not target_url:
        errors.append(f"{content_id}: missing target_url")

    draft_path = DRAFTS_DIR / f"{content_id}.md"
    if not draft_path.exists():
        errors.append(f"{content_id}: draft file missing")
        return errors, {}

    meta, body = parse_md(draft_path)
    full_text = json.dumps(meta, ensure_ascii=False) + "\n" + body
    links = list(dict.fromkeys(extract_internal_links(body)))

    if meta.get("status") != "reviewed":
        errors.append(f"{content_id}: draft front matter status must be reviewed")
    if contains_html(body):
        errors.append(f"{content_id}: HTML is not allowed")
    if any(line.strip().startswith("# ") for line in body.splitlines()):
        errors.append(f"{content_id}: body cannot contain H1")
    if len(links) < 4:
        errors.append(f"{content_id}: needs at least 4 internal links")

    has_service_or_platform = any(link.startswith("/platforms/") or (link.startswith("/services/") and link != "/services/") for link in links)
    has_topic = any(link.startswith("/topics/") and link != "/topics/" for link in links)
    has_listing = any(link in {"/services/", "/topics/"} for link in links)
    has_contact = "/contact/" in links
    if not has_service_or_platform:
        errors.append(f"{content_id}: missing service/platform link")
    if not has_topic:
        errors.append(f"{content_id}: missing topic link")
    if not has_listing:
        errors.append(f"{content_id}: missing listing link")
    if not has_contact:
        errors.append(f"{content_id}: missing contact link")

    for link in links:
        linked_item = queue_by_url.get(link)
        if not linked_item:
            continue
        if linked_item.get("internal_only"):
            errors.append(f"{content_id}: links internal_only page {link}")
        elif linked_item.get("status") != "published":
            errors.append(f"{content_id}: links unpublished article page {link}")

    description = meta.get("description", "").strip()
    title = meta.get("title", "").strip() or content_item.get("title", "").strip()
    primary_keyword = meta.get("primary_keyword", "").strip() or content_item.get("primary_keyword", "").strip()
    if not title:
        errors.append(f"{content_id}: title missing")
    if not description:
        errors.append(f"{content_id}: description missing")
    if not primary_keyword:
        errors.append(f"{content_id}: primary_keyword missing")

    validated = {
        "content_id": content_id,
        "title": title,
        "target_url": target_url,
        "primary_keyword": primary_keyword,
        "description": description,
        "risk_level": entry.get("risk_level", content_item.get("risk_level", "")),
        "content_type": entry.get("content_type", ""),
        "cluster_id": content_item.get("cluster_id", ""),
        "planned_publish_date": entry.get("planned_publish_date", ""),
        "internal_link_count": len(links),
        "shape": classify_shape({**entry, **content_item}),
        "notes": entry.get("notes", ""),
    }
    return errors, validated


def select_candidates(validated: list[dict], limit: int, mode: str) -> tuple[list[dict], list[dict]]:
    ordered = sorted(validated, key=score_candidate)
    selected: list[dict] = []
    skipped: list[dict] = []

    desired_shapes = ["ordinary_long_tail", "service_or_platform", "social_or_game_topic"]
    for shape in desired_shapes:
        if len(selected) >= limit:
            break
        for candidate in ordered:
            if candidate in selected:
                continue
            if candidate.get("shape") != shape:
                continue
            ok, reason = can_add(selected, candidate, mode)
            if ok:
                selected.append(candidate)
                break
            skipped.append({**candidate, "skip_reason": reason})

    for candidate in ordered:
        if len(selected) >= limit:
            break
        if candidate in selected:
            continue
        ok, reason = can_add(selected, candidate, mode)
        if ok:
            selected.append(candidate)
        else:
            skipped.append({**candidate, "skip_reason": reason})
    return selected, skipped


def build_report(report: dict) -> None:
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = [
        "# Pre-Publish Audit Report",
        "",
        f"- date: {report['date']}",
        f"- mode: {report['mode']}",
        f"- limit: {report['limit']}",
        f"- dry_run: {report['dry_run']}",
        f"- queue_pool: {report['queue_pool']}",
        f"- valid_candidates: {report['valid_candidates']}",
        f"- recommended_count: {report['recommended_count']}",
        "",
        "## Recommended First Publish Set",
        "",
        "| content_id | shape | type | cluster | risk | links | target_url |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["recommended_items"]:
        rows.append(
            f"| {item['content_id']} | {item['shape']} | {item['content_type']} | {item['cluster_id']} | "
            f"{item['risk_level']} | {item['internal_link_count']} | {item['target_url']} |"
        )
    if report["errors"]:
        rows.extend(["", "## Errors", ""])
        rows.extend(f"- {error}" for error in report["errors"])
    REPORT_MD_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    audit_date = datetime.strptime(args.date, "%Y-%m-%d").date().isoformat()
    content_queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    review_by_id = load_review_by_id()
    rules = load_json(RULES_PATH, {})
    content_by_id = {item["content_id"]: item for item in content_queue if item.get("content_id")}
    queue_by_url = {item.get("target_url"): item for item in content_queue if item.get("target_url")}

    target_entries = [item for item in publish_queue if item.get("publish_status") in {"queued", "publish_candidate"}]
    if args.only:
        target_entries = [item for item in target_entries if item.get("content_id") == args.only]

    all_errors: list[str] = []
    validated: list[dict] = []
    seen_urls: set[str] = set()

    for entry in target_entries:
        target_url = entry.get("target_url", "")
        if target_url:
            if target_url in seen_urls:
                all_errors.append(f"{entry.get('content_id', '')}: duplicate target_url in publish queue {target_url}")
                continue
            seen_urls.add(target_url)
        errors, candidate = validate_candidate(entry, content_by_id, review_by_id, rules, queue_by_url)
        all_errors.extend(errors)
        if candidate and not errors:
            validated.append(candidate)

    recommended, skipped = select_candidates(validated, args.limit, args.mode)
    medium_or_high_count = sum(1 for item in recommended if item.get("risk_level") in {"medium", "high"})
    sensitive_count = sum(1 for item in recommended if is_sensitive_theme(item))
    if args.mode in {"conservative", "normal"} and medium_or_high_count > 1:
        all_errors.append("same day medium/high risk topics are too concentrated")
    if args.mode != "aggressive" and sensitive_count > 1:
        all_errors.append("same day sensitive clusters are too concentrated")

    report = {
        "date": audit_date,
        "mode": args.mode,
        "limit": args.limit,
        "dry_run": True if args.dry_run or not args.only else args.dry_run,
        "queue_pool": len(target_entries),
        "valid_candidates": len(validated),
        "recommended_count": len(recommended),
        "recommended_items": recommended,
        "skipped_items": skipped,
        "errors": all_errors,
    }
    build_report(report)
    if all_errors:
        for error in all_errors:
            print(f"[FAIL] {error}")
        return 1
    print(f"[OK] pre-publish audit passed: recommended={len(recommended)} mode={args.mode} limit={args.limit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
