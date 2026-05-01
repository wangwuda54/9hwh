from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
DEFAULT_OUTPUT = ROOT / "data" / "content-assets" / "deployed_site_verification_report.json"
DEFAULT_MD_OUTPUT = ROOT / "docs" / "deployed-site-verification-report.md"


def load_queue() -> list[dict]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))


def fetch(url: str, timeout: int) -> tuple[int | None, str, str | None]:
    request = Request(url, headers={"User-Agent": "9HWH-stage16-verifier/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace"), None
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return exc.code, body, None
    except URLError as exc:
        return None, "", str(exc)


def extract_sitemap_urls(xml_text: str) -> list[str]:
    return re.findall(r"<loc>(.*?)</loc>", xml_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a deployed 9HWH site after Cloudflare Pages deployment.")
    parser.add_argument("--base-url", required=True, help="Base deployed URL such as https://preview.example.pages.dev")
    parser.add_argument("--expected-published", type=int, default=3, help="Expected number of published article URLs in sitemap.")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout in seconds.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="JSON output path.")
    return parser.parse_args()


def build_markdown(report: dict, md_path: Path) -> None:
    rows = [
        "# Deployed Site Verification Report",
        "",
        f"- base_url: {report['base_url']}",
        f"- expected_published: {report['expected_published']}",
        f"- status: {report['status']}",
        "",
        "## Core Checks",
        "",
        f"- homepage_200: {report['core_checks']['homepage_200']}",
        f"- services_200: {report['core_checks']['services_200']}",
        f"- topics_200: {report['core_checks']['topics_200']}",
        f"- contact_200: {report['core_checks']['contact_200']}",
        f"- robots_200: {report['core_checks']['robots_200']}",
        f"- sitemap_200: {report['core_checks']['sitemap_200']}",
        f"- robots_has_sitemap: {report['core_checks']['robots_has_sitemap']}",
        f"- sitemap_only_published: {report['core_checks']['sitemap_only_published']}",
        "",
        "## Published URLs",
        "",
    ]
    for url in report["published_urls"]:
        rows.append(f"- {url}")
    if report["issues"]:
        rows.extend(["", "## Issues", ""])
        rows.extend(f"- {issue}" for issue in report["issues"])
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/") + "/"
    output_path = Path(args.output)
    md_path = DEFAULT_MD_OUTPUT

    queue = load_queue()
    published = [item for item in queue if item.get("status") == "published" and not item.get("internal_only")]
    reviewed = [item for item in queue if item.get("status") == "reviewed" and not item.get("internal_only")]
    internal_only = [item for item in queue if item.get("internal_only")]

    issues: list[str] = []
    pages_to_check = {
        "homepage": "",
        "services": "services/",
        "topics": "topics/",
        "contact": "contact/",
        "robots": "robots.txt",
        "sitemap": "sitemap.xml",
    }
    page_results = {}
    for key, suffix in pages_to_check.items():
        status, body, error = fetch(urljoin(base_url, suffix), args.timeout)
        page_results[key] = {"status": status, "body": body, "error": error}
        if error:
            issues.append(f"{key} request failed: {error}")
    robots_body = page_results["robots"]["body"]
    sitemap_body = page_results["sitemap"]["body"]
    sitemap_urls = extract_sitemap_urls(sitemap_body)
    sitemap_paths = {
        "/" + url.split("://", 1)[-1].split("/", 1)[-1] if "://" in url else url
        for url in sitemap_urls
    }

    published_paths = {item["target_url"] for item in published}
    reviewed_paths = {item["target_url"] for item in reviewed}
    internal_only_paths = {item["target_url"] for item in internal_only if item.get("target_url")}
    c045_paths = {item["target_url"] for item in internal_only if item.get("content_id", "").startswith("c045-") and item.get("target_url")}

    for item in published:
        url = urljoin(base_url, item["target_url"].lstrip("/"))
        status, body, error = fetch(url, args.timeout)
        if error or status != 200:
            issues.append(f"published page not 200: {item['content_id']} -> {status or error}")
        if "/contact/" not in body and "咨询" not in body and "鑱旂郴" not in body:
            issues.append(f"published page missing contact CTA: {item['content_id']}")
        if "/blog//topics/" in body or 'href="//' in body:
            issues.append(f"published page contains path error: {item['content_id']}")

    if page_results["homepage"]["status"] != 200:
        issues.append("homepage is not 200")
    if page_results["services"]["status"] != 200:
        issues.append("/services/ is not 200")
    if page_results["topics"]["status"] != 200:
        issues.append("/topics/ is not 200")
    if page_results["contact"]["status"] != 200:
        issues.append("/contact/ is not 200")
    if page_results["robots"]["status"] != 200:
        issues.append("/robots.txt is not 200")
    if page_results["sitemap"]["status"] != 200:
        issues.append("/sitemap.xml is not 200")

    if "Sitemap:" not in robots_body:
        issues.append("robots.txt missing sitemap declaration")
    if len([path for path in sitemap_paths if path in published_paths]) != args.expected_published:
        issues.append("sitemap published URL count does not match expected_published")
    if any(path in sitemap_paths for path in reviewed_paths):
        issues.append("reviewed unpublished URL found in sitemap")
    if any(path in sitemap_paths for path in internal_only_paths):
        issues.append("internal_only URL found in sitemap")
    if any(path in sitemap_paths for path in c045_paths):
        issues.append("c045 URL found in sitemap")
    unexpected_queue_paths = [path for path in sitemap_paths if path in {item.get('target_url') for item in queue} and path not in published_paths]
    if unexpected_queue_paths:
        issues.append("sitemap contains non-published queue URLs")

    report = {
        "base_url": base_url.rstrip("/"),
        "expected_published": args.expected_published,
        "status": "pass" if not issues else "fail",
        "core_checks": {
            "homepage_200": page_results["homepage"]["status"] == 200,
            "services_200": page_results["services"]["status"] == 200,
            "topics_200": page_results["topics"]["status"] == 200,
            "contact_200": page_results["contact"]["status"] == 200,
            "robots_200": page_results["robots"]["status"] == 200,
            "sitemap_200": page_results["sitemap"]["status"] == 200,
            "robots_has_sitemap": "Sitemap:" in robots_body,
            "sitemap_only_published": not unexpected_queue_paths and not any(path in sitemap_paths for path in reviewed_paths | internal_only_paths | c045_paths),
        },
        "published_urls": [urljoin(base_url, item["target_url"].lstrip("/")) for item in published],
        "reviewed_unpublished_urls": [urljoin(base_url, item["target_url"].lstrip("/")) for item in reviewed],
        "internal_only_urls": [urljoin(base_url, path.lstrip("/")) for path in internal_only_paths],
        "sitemap_urls": sitemap_urls,
        "issues": issues,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    build_markdown(report, md_path)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 1
    print(f"[OK] deployed site verification passed for {base_url.rstrip('/')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
