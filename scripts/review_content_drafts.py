from __future__ import annotations

import html.parser
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "site_src" / "content_drafts"
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
RULES_PATH = ROOT / "site_src" / "data" / "content" / "content_rules.json"
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
FORBIDDEN_TERMS = [
    "保证过审",
    "保证不限号",
    "保证效果",
    "保证转化",
    "保证收益",
    "绕过平台政策",
    "规避审核",
    "抗风控",
    "Cloak",
    "仿牌",
    "博彩",
    "黑五类",
    "三不限",
    "违规业务也能做",
    "任何平台都能过",
    "任何行业都能投",
]
FABRICATION_PATTERNS = [
    r"办公室",
    r"办公地址",
    r"总部位于",
    r"团队规模",
    r"上百人团队",
    r"(我们的|本团队的|公司已做过的)客户案例",
    r"(我们的|本团队的|公司已做过的)成功案例",
    r"联系电话",
    r"联系.*手机号",
    r"手机号.{0,8}(联系|咨询|添加|提交)",
    r"微信.{0,8}(联系|咨询|添加)",
    r"WhatsApp.{0,8}(contact|message|consult|chat|number)",
    r"Telegram.{0,8}(contact|message|consult|group|channel)",
]
HIGH_RISK_MARKERS = [
    "虚拟币",
    "加密货币",
    "币圈",
    "交易所",
    "贷款",
    "保险",
    "移民",
    "理财",
    "博彩",
]
SERVICE_BOUNDARY_MARKERS = ["服务边界", "不承诺", "平台政策", "地区法规", "行业限制"]


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


def has_service_boundary(meta: dict[str, str], body: str) -> bool:
    text = " ".join([meta.get("title", ""), meta.get("description", ""), body])
    return any(marker in text for marker in SERVICE_BOUNDARY_MARKERS)


def is_high_risk(meta: dict[str, str], queue_item: dict | None) -> bool:
    if queue_item and queue_item.get("risk_level") in {"medium", "high"}:
        return True
    text = " ".join(meta.values())
    return any(marker in text for marker in HIGH_RISK_MARKERS)


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

    full_text = json.dumps(meta, ensure_ascii=False) + "\n" + body
    for term in FORBIDDEN_TERMS:
        if term in full_text:
            issues.append(f"forbidden term: {term}")
    rules = load_json(RULES_PATH)
    for term in rules.get("blocked_terms", []):
        if term and term in full_text:
            issues.append(f"blocked term from content_rules: {term}")
    for pattern in FABRICATION_PATTERNS:
        if re.search(pattern, body, flags=re.IGNORECASE):
            issues.append(f"possible fabricated company/contact claim: {pattern}")
    if "service_" in body or "/service_" in body:
        issues.append("contains old service link")
    internal_links = len(re.findall(r"\]\(/", body))
    if internal_links < 2:
        warnings.append("less than 2 internal links")
    if is_high_risk(meta, queue_item) and not has_service_boundary(meta, body):
        issues.append("high-risk topic missing service boundary wording")
    elif not has_service_boundary(meta, body):
        warnings.append("missing service boundary wording")

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
