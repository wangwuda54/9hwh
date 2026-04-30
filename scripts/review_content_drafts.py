from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "site_src" / "content_drafts"
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
RULES_PATH = ROOT / "site_src" / "data" / "content" / "content_rules.json"
ASSETS = ROOT / "data" / "content-assets"
DOCS = ROOT / "docs"


def parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}, text
    _, front, body = text.split("---", 2)
    meta = {}
    for line in front.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, body.strip()


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    queue = {item["content_id"]: item for item in json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))}
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8-sig"))
    failures = []
    warnings = []
    urls = set()
    for path in DRAFTS.glob("*.md"):
        if path.name.upper() == "README.MD":
            continue
        meta, body = parse_md(path)
        cid = meta.get("content_id", "")
        issues = []
        warns = []
        for field in ("content_id", "title", "description", "target_url", "status", "primary_keyword"):
            if not meta.get(field):
                issues.append(f"missing {field}")
        if cid and cid not in queue:
            issues.append("content_id not in queue")
        if meta.get("target_url") in urls:
            issues.append("duplicate target_url")
        urls.add(meta.get("target_url", ""))
        if len(meta.get("title", "")) < 8:
            issues.append("title too short")
        if len(meta.get("description", "")) < 40:
            warns.append("description may be too short")
        if len(body) < 1200:
            issues.append("body too short")
        for term in rules.get("blocked_terms", []):
            if term and term in body:
                issues.append(f"blocked term: {term}")
        if "service_" in body or "/service_" in body:
            issues.append("contains old service link")
        internal_links = len(re.findall(r"\]\(/", body))
        if internal_links < 2:
            warns.append("less than 2 internal links")
        if "服务边界" not in body:
            issues.append("missing service boundary section")
        if "联系" not in body and "咨询" not in body:
            warns.append("missing contact CTA wording")
        keyword = meta.get("primary_keyword", "")
        if keyword and body.count(keyword) > 12:
            warns.append("possible keyword stuffing")
        if issues:
            failures.append({"file": path.name, "issues": issues})
        if warns:
            warnings.append({"file": path.name, "warnings": warns})
    report = {"failures": failures, "warnings": warnings, "draft_count": len(list(DRAFTS.glob('*.md'))) - 1}
    (ASSETS / "draft_review_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = ["# 内容草稿审核报告", "", f"- failures: {len(failures)}", f"- warnings: {len(warnings)}", ""]
    for item in failures:
        rows.append(f"- FAIL {item['file']}: {', '.join(item['issues'])}")
    for item in warnings:
        rows.append(f"- WARN {item['file']}: {', '.join(item['warnings'])}")
    (DOCS / "content-draft-review-report.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] reviewed drafts, failures {len(failures)}, warnings {len(warnings)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
