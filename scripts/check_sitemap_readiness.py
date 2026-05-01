from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
SITEMAP_PATH = ROOT / "site" / "public" / "sitemap.xml"
ROBOTS_PATH = ROOT / "site" / "public" / "robots.txt"
REPORT_JSON_PATH = ROOT / "data" / "content-assets" / "sitemap_readiness_report.json"
REPORT_MD_PATH = ROOT / "docs" / "sitemap-readiness-report.md"
EXPECTED_SITEMAP_URL = "https://www.9hwh.com/sitemap.xml"
MAX_URLS_PER_SITEMAP = 50000


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def extract_locs(xml_text: str) -> list[str]:
    return re.findall(r"<loc>(.*?)</loc>", xml_text)


def path_from_url(url: str) -> str:
    if "://" not in url:
        return url
    _, _, tail = url.partition("://")
    _, _, path = tail.partition("/")
    path = "/" + path
    if not path.endswith("/"):
        path += "/"
    return path


def main() -> int:
    issues: list[str] = []
    warnings: list[str] = []

    if not SITEMAP_PATH.exists():
        raise SystemExit(f"[FAIL] sitemap missing: {SITEMAP_PATH}")
    if not ROBOTS_PATH.exists():
        raise SystemExit(f"[FAIL] robots.txt missing: {ROBOTS_PATH}")

    queue = load_json(CONTENT_QUEUE_PATH, [])
    sitemap_urls = extract_locs(SITEMAP_PATH.read_text(encoding="utf-8-sig"))
    sitemap_paths = {path_from_url(url) for url in sitemap_urls}
    robots_text = ROBOTS_PATH.read_text(encoding="utf-8-sig")

    queue_urls = {}
    published_urls: set[str] = set()
    reviewed_urls: set[str] = set()
    draft_urls: set[str] = set()
    internal_only_urls: set[str] = set()

    for item in queue:
        target_url = item.get("target_url")
        if not target_url:
            continue
        queue_urls[target_url] = item.get("content_id", "")
        if item.get("internal_only"):
            internal_only_urls.add(target_url)
            continue
        status = item.get("status")
        if status == "published":
            published_urls.add(target_url)
        elif status == "reviewed":
            reviewed_urls.add(target_url)
        elif status == "draft_received":
            draft_urls.add(target_url)

    queue_urls_in_sitemap = sorted(path for path in sitemap_paths if path in queue_urls)
    unexpected_queue_urls = sorted(
        path
        for path in queue_urls_in_sitemap
        if path not in published_urls
    )
    if unexpected_queue_urls:
        issues.append("sitemap contains non-published queue URLs")
    if reviewed_urls & sitemap_paths:
        issues.append("reviewed content found in sitemap")
    if draft_urls & sitemap_paths:
        issues.append("draft_received content found in sitemap")
    if internal_only_urls & sitemap_paths:
        issues.append("internal_only content found in sitemap")

    robots_has_sitemap = EXPECTED_SITEMAP_URL in robots_text
    if not robots_has_sitemap:
        issues.append("robots.txt missing sitemap declaration")

    if len(sitemap_urls) > MAX_URLS_PER_SITEMAP:
        warnings.append("sitemap exceeds 50000 URLs; prepare a sitemap index split")

    report = {
        "status": "pass" if not issues else "fail",
        "sitemap_exists": True,
        "robots_exists": True,
        "robots_has_sitemap": robots_has_sitemap,
        "expected_sitemap_url": EXPECTED_SITEMAP_URL,
        "sitemap_url_count": len(sitemap_urls),
        "queue_url_count": len(queue_urls),
        "published_queue_url_count": len(published_urls),
        "queue_urls_in_sitemap": queue_urls_in_sitemap,
        "non_published_queue_urls_in_sitemap": unexpected_queue_urls,
        "reviewed_urls_in_sitemap": sorted(reviewed_urls & sitemap_paths),
        "draft_urls_in_sitemap": sorted(draft_urls & sitemap_paths),
        "internal_only_urls_in_sitemap": sorted(internal_only_urls & sitemap_paths),
        "only_published_content_in_sitemap": not unexpected_queue_urls,
        "warnings": warnings,
        "issues": issues,
    }

    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    rows = [
        "# Sitemap Readiness Report",
        "",
        f"- status: {report['status']}",
        f"- sitemap_exists: {report['sitemap_exists']}",
        f"- robots_exists: {report['robots_exists']}",
        f"- robots_has_sitemap: {report['robots_has_sitemap']}",
        f"- sitemap_url_count: {report['sitemap_url_count']}",
        f"- published_queue_url_count: {report['published_queue_url_count']}",
        f"- only_published_content_in_sitemap: {report['only_published_content_in_sitemap']}",
        "",
    ]
    if warnings:
        rows.extend(["## Warnings", ""])
        rows.extend(f"- {warning}" for warning in warnings)
        rows.append("")
    if issues:
        rows.extend(["## Issues", ""])
        rows.extend(f"- {issue}" for issue in issues)
        rows.append("")
    rows.extend(
        [
            "## Queue URL Audit",
            "",
            f"- queue_urls_in_sitemap: {len(report['queue_urls_in_sitemap'])}",
            f"- reviewed_urls_in_sitemap: {len(report['reviewed_urls_in_sitemap'])}",
            f"- draft_urls_in_sitemap: {len(report['draft_urls_in_sitemap'])}",
            f"- internal_only_urls_in_sitemap: {len(report['internal_only_urls_in_sitemap'])}",
        ]
    )
    REPORT_MD_PATH.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 1
    print(f"[OK] sitemap readiness passed: urls={len(sitemap_urls)} published_queue_urls={len(published_urls)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
