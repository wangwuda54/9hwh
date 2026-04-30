from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "site" / "public"
BASE_URL = "https://www.9hwh.com"
FAILURES: list[str] = []
WARNINGS: list[str] = []
FORBIDDEN = [
    "service_",
    "/service_",
    "legacy-source",
    "Cloak",
    "规避审核",
    "仿牌",
    "博彩",
    "黑五类",
    "三不限",
    "抗风控",
    "绕过平台",
    "保证过审",
    "保证不限号",
    "保证效果",
    "保证转化",
    "保证收益",
    "违规业务也能做",
    "任何平台都能过",
    "任何行业都能投",
]
REQUIRED_PATHS = [
    "/",
    "/services/",
    "/services/overseas-promotion/",
    "/services/traffic-acquisition/",
    "/services/ad-campaign-support/",
    "/services/media-buying/",
    "/platforms/",
    "/platforms/tk/",
    "/platforms/fb/",
    "/platforms/google/",
    "/topics/",
    "/topics/crypto-promotion/",
    "/topics/dating-traffic/",
    "/topics/game-promotion/",
    "/topics/finance-leads/",
    "/topics/loan-leads/",
    "/topics/insurance-leads/",
    "/topics/immigration-leads/",
    "/topics/online-work-leads/",
    "/markets/",
    "/blog/",
    "/contact/",
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.title = False
        self.has_description = False
        self.has_viewport = False
        self.canonical = ""
        self.h1_count = 0
        self.has_nav = False
        self.has_footer = False

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"])
        if tag == "title":
            self.title = True
        if tag == "meta" and attrs_dict.get("name") == "description":
            self.has_description = True
        if tag == "meta" and attrs_dict.get("name") == "viewport":
            self.has_viewport = True
        if tag == "link" and attrs_dict.get("rel") == "canonical":
            self.canonical = attrs_dict.get("href", "")
        if tag == "h1":
            self.h1_count += 1
        if tag == "nav":
            self.has_nav = True
        if tag == "footer":
            self.has_footer = True


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")
    WARNINGS.append(message)


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    FAILURES.append(message)


def path_to_file(path: str) -> Path:
    if path == "/":
        return PUBLIC / "index.html"
    if path.endswith(".html"):
        return PUBLIC / path.lstrip("/")
    return PUBLIC / path.strip("/") / "index.html"


def file_to_url(path: Path) -> str:
    rel = path.relative_to(PUBLIC).as_posix()
    if rel == "index.html":
        return BASE_URL + "/"
    if rel.endswith("/index.html"):
        return BASE_URL + "/" + rel[: -len("index.html")]
    return BASE_URL + "/" + rel


def sitemap_urls() -> set[str]:
    text = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    return set(re.findall(r"<loc>(.*?)</loc>", text))


def check_html(sitemap: set[str]) -> None:
    for path in PUBLIC.rglob("*.html"):
        rel = path.relative_to(PUBLIC).as_posix()
        text = path.read_text(encoding="utf-8")
        parser = LinkParser()
        parser.feed(text)
        expected_url = file_to_url(path)
        indexable = rel != "404.html"
        if not parser.title:
            fail(f"{rel} missing title")
        if not parser.has_description:
            fail(f"{rel} missing meta description")
        if not parser.has_viewport:
            fail(f"{rel} missing viewport")
        if not parser.canonical:
            fail(f"{rel} missing canonical")
        if parser.canonical and parser.canonical != expected_url:
            fail(f"{rel} canonical mismatch: {parser.canonical} != {expected_url}")
        if parser.h1_count != 1:
            fail(f"{rel} has {parser.h1_count} h1 tags")
        if not parser.has_nav:
            fail(f"{rel} missing nav")
        if rel != "404.html" and not parser.has_footer:
            fail(f"{rel} missing footer")
        if not parser.links:
            fail(f"{rel} has no links")
        if indexable and expected_url not in sitemap:
            fail(f"{rel} is indexable but missing from sitemap")
        if not indexable and expected_url in sitemap:
            fail(f"{rel} should not be in sitemap")
        if (rel.startswith("services/") or rel.startswith("topics/")) and "服务边界" not in text:
            fail(f"{rel} missing service boundary")
        if rel == "contact/index.html" and "咨询前需要提供" not in text:
            fail("contact page missing consultation checklist")
        for term in FORBIDDEN:
            if term in text:
                fail(f"{rel} contains forbidden term: {term}")
        check_links(rel, parser.links)
    ok("HTML quality checks completed")


def check_links(rel: str, links: list[str]) -> None:
    for link in links:
        if link.startswith("#") or link.startswith("mailto:") or link.startswith("tel:"):
            continue
        parsed = urlparse(link)
        if parsed.scheme and parsed.netloc and parsed.netloc != "www.9hwh.com":
            continue
        target = parsed.path if parsed.scheme else link.split("#", 1)[0]
        if not target or target == "#":
            continue
        if target.startswith("https://www.9hwh.com"):
            target = urlparse(target).path
        if target.startswith("/"):
            if not path_to_file(target).exists():
                fail(f"{rel} dead internal link: {link}")


def check_sitemap(sitemap: set[str]) -> None:
    text = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    for term in ("service_", "legacy-source", "404"):
        if term in text:
            fail(f"sitemap contains {term}")
    if "<lastmod>" not in text:
        fail("sitemap missing lastmod")
    for url in sitemap:
        if not url.startswith(BASE_URL + "/"):
            fail(f"sitemap URL outside base: {url}")
        local_path = url.replace(BASE_URL, "")
        if not path_to_file(local_path).exists():
            fail(f"sitemap URL missing local file: {url}")
    ok("sitemap checks completed")


def check_robots() -> None:
    text = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://www.9hwh.com/sitemap.xml" not in text:
        fail("robots missing sitemap")
    if "Disallow: /service" in text or "Disallow: /service_" in text:
        fail("robots blocks service paths")
    ok("robots checks completed")


def main() -> int:
    if not PUBLIC.exists():
        fail("site/public does not exist")
        return 1
    for required in REQUIRED_PATHS:
        if not path_to_file(required).exists():
            fail(f"missing required page: {required}")
    sitemap = sitemap_urls()
    check_sitemap(sitemap)
    check_robots()
    check_html(sitemap)
    if FAILURES:
        print(f"[FAIL] {len(FAILURES)} issue(s) found")
        return 1
    if WARNINGS:
        print(f"[WARN] {len(WARNINGS)} warning(s) found")
    ok("static site checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
