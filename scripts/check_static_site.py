from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "site" / "public"
BASE_URL = "https://www.9hwh.com/"
REQUIRED_PATHS = [
    "index.html",
    "services/index.html",
    "services/overseas-promotion/index.html",
    "services/traffic-acquisition/index.html",
    "services/ad-campaign-support/index.html",
    "services/media-buying/index.html",
    "platforms/index.html",
    "platforms/tk/index.html",
    "platforms/fb/index.html",
    "platforms/google/index.html",
    "topics/index.html",
    "topics/crypto-promotion/index.html",
    "topics/dating-traffic/index.html",
    "topics/game-promotion/index.html",
    "topics/finance-leads/index.html",
    "topics/loan-leads/index.html",
    "topics/insurance-leads/index.html",
    "topics/immigration-leads/index.html",
    "topics/online-work-leads/index.html",
    "markets/index.html",
    "blog/index.html",
    "contact/index.html",
    "404.html",
    "sitemap.xml",
    "robots.txt",
]
FORBIDDEN = [
    "service_",
    "/service_",
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


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    FAILURES.append(message)


FAILURES: list[str] = []


def check_exists() -> None:
    if not PUBLIC.exists():
        fail("site/public does not exist")
        return
    ok("site/public exists")
    for rel in REQUIRED_PATHS:
        if not (PUBLIC / rel).exists():
            fail(f"missing {rel}")
    if not FAILURES:
        ok("all required output files exist")


def check_html() -> None:
    for path in PUBLIC.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(PUBLIC).as_posix()
        for marker in ("<title>", 'name="description"', 'name="viewport"', 'rel="canonical"'):
            if marker not in text:
                fail(f"{rel} missing {marker}")
        h1_count = len(re.findall(r"<h1\b", text, flags=re.I))
        if h1_count != 1:
            fail(f"{rel} has {h1_count} h1 tags")
        for term in FORBIDDEN:
            if term in text:
                fail(f"{rel} contains forbidden term: {term}")
    ok("HTML checks completed")


def check_sitemap() -> None:
    path = PUBLIC / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    for term in ("service_", "legacy-source", "404"):
        if term in text:
            fail(f"sitemap contains {term}")
    urls = re.findall(r"<loc>(.*?)</loc>", text)
    if not urls:
        fail("sitemap has no URLs")
    for url in urls:
        if not url.startswith(BASE_URL):
            fail(f"sitemap URL does not start with {BASE_URL}: {url}")
    ok("sitemap checks completed")


def check_robots() -> None:
    text = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://www.9hwh.com/sitemap.xml" not in text:
        fail("robots missing sitemap")
    for marker in ("Disallow: /service", "Disallow: /service_"):
        if marker in text:
            fail(f"robots contains {marker}")
    ok("robots checks completed")


def main() -> int:
    check_exists()
    if not PUBLIC.exists():
        return 1
    check_html()
    check_sitemap()
    check_robots()
    if FAILURES:
        print(f"[FAIL] {len(FAILURES)} issue(s) found")
        return 1
    ok("static site checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
