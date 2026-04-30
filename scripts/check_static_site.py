from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "site" / "public"
KEYWORDS = ROOT / "site_src" / "data" / "keywords"
KEYWORD_ASSETS = ROOT / "data" / "keyword-assets"
CONTENT_DATA = ROOT / "site_src" / "data" / "content"
DEEPSEEK_TASKS = ROOT / "data" / "deepseek-tasks"
BATCH_001 = ROOT / "data" / "deepseek-batches" / "batch-001"
DRAFTS = ROOT / "site_src" / "content_drafts"
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


def load_keyword_json(name: str):
    path = KEYWORDS / name
    if not path.exists():
        fail(f"missing keyword data: {path.relative_to(ROOT).as_posix()}")
        return [] if name in {"clusters.json", "url_map.json"} else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_keyword_assets(sitemap: set[str]) -> None:
    summary_path = KEYWORD_ASSETS / "keyword_summary.json"
    cluster_path = KEYWORDS / "clusters.json"
    url_map_path = KEYWORDS / "url_map.json"
    for path in (summary_path, cluster_path, url_map_path):
        if not path.exists():
            fail(f"missing keyword asset file: {path.relative_to(ROOT).as_posix()}")

    rules = load_keyword_json("rules.json")
    clusters = load_keyword_json("clusters.json")
    url_map = load_keyword_json("url_map.json")
    if not clusters:
        return

    cluster_targets = {cluster["target_url"] for cluster in clusters if cluster.get("public_page")}
    known_pages = {
        "/",
        "/services/",
        "/platforms/",
        "/topics/",
        "/markets/",
        "/blog/",
        "/contact/",
    }
    for url in sitemap:
        path = url.replace(BASE_URL, "")
        if path not in cluster_targets and path not in known_pages:
            fail(f"sitemap URL has no cluster or page type note: {url}")

    sensitive = rules.get("sensitive_internal_categories", [])
    home_text = (PUBLIC / "index.html").read_text(encoding="utf-8")
    for term in sensitive:
        if term in home_text:
            fail(f"homepage contains sensitive internal keyword: {term}")

    blocked = rules.get("blocked_promise_terms", [])
    for path in PUBLIC.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(PUBLIC).as_posix()
        for term in blocked:
            if term in text:
                fail(f"{rel} contains blocked promise term from keyword rules: {term}")
        keyword_count = text.count('class="pill"')
        if keyword_count > 48:
            warn(f"{rel} displays many keyword pills: {keyword_count}")

    for cluster in clusters:
        target = cluster.get("target_url", "")
        if target and not path_to_file(target).exists():
            fail(f"cluster target missing local file: {cluster['cluster_id']} -> {target}")
        if cluster.get("page_type") in {"topic", "service"} and not target:
            fail(f"cluster missing target URL: {cluster['cluster_id']}")

    topic_targets = {cluster["target_url"] for cluster in clusters if cluster.get("page_type") == "topic"}
    service_targets = {cluster["target_url"] for cluster in clusters if cluster.get("page_type") == "service"}
    for required in REQUIRED_PATHS:
        if required.startswith("/topics/") and required != "/topics/" and required not in topic_targets:
            fail(f"topic page missing cluster: {required}")
        if required.startswith("/services/") and required != "/services/" and required not in service_targets:
            fail(f"service page missing cluster: {required}")

    for item in url_map:
        if item.get("target_url") and not path_to_file(item["target_url"]).exists():
            fail(f"url_map target missing local file: {item['keyword']} -> {item['target_url']}")

    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8-sig"))
        if summary.get("total_keywords", 0) <= 0:
            fail("keyword summary has no keywords")
    pool_path = KEYWORD_ASSETS / "keyword_pool.jsonl"
    if pool_path.exists() and pool_path.stat().st_size > 20 * 1024 * 1024:
        warn("keyword_pool.jsonl exceeds 20MB")

    ok("keyword asset checks completed")


def check_content_pipeline(sitemap: set[str]) -> None:
    queue_path = CONTENT_DATA / "content_queue.json"
    rules_path = CONTENT_DATA / "content_rules.json"
    if not queue_path.exists():
        fail("missing content_queue.json")
        return
    if not rules_path.exists():
        fail("missing content_rules.json")
        return
    queue = json.loads(queue_path.read_text(encoding="utf-8-sig"))
    rules = json.loads(rules_path.read_text(encoding="utf-8-sig"))
    if len(queue) > 100:
        warn(f"content_queue has more than 100 tasks: {len(queue)}")
    ids = set()
    urls = set()
    for item in queue:
        content_id = item.get("content_id", "")
        target_url = item.get("target_url", "")
        if not content_id:
            fail("content task missing content_id")
        if content_id in ids:
            fail(f"duplicate content_id: {content_id}")
        ids.add(content_id)
        if target_url in urls:
            fail(f"duplicate content target_url: {target_url}")
        urls.add(target_url)
        if not item.get("primary_keyword"):
            fail(f"content task missing primary_keyword: {content_id}")
        status = item.get("status")
        full_url = BASE_URL + target_url.lstrip("/")
        if status in {"planned", "prompt_ready", "writing", "draft_received", "paused"} and full_url in sitemap:
            fail(f"unfinished content entered sitemap: {content_id}")
        if status in {"ready_to_publish", "published"} and full_url not in sitemap:
            warn(f"publishable content not in sitemap, likely missing draft: {content_id}")
        public_text_targets = list(PUBLIC.rglob("*.html"))
        for term in rules.get("blocked_terms", []):
            if term and term in item.get("primary_keyword", ""):
                fail(f"content task uses blocked primary keyword: {content_id}")
    if DEEPSEEK_TASKS.exists():
        task_files = list(DEEPSEEK_TASKS.glob("*.md"))
    else:
        task_files = []
    if not task_files:
        warn("data/deepseek-tasks is empty")
    for path in task_files:
        text = path.read_text(encoding="utf-8-sig")
        if "禁止表达" not in text:
            fail(f"DeepSeek task missing forbidden expression section: {path.name}")
        if "服务边界" not in text:
            fail(f"DeepSeek task missing service boundary: {path.name}")
    blog_text = (PUBLIC / "blog" / "index.html").read_text(encoding="utf-8")
    if blog_text.count("<article") > 30:
        warn("blog page may show too many unfinished content cards")
    for path in PUBLIC.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for term in rules.get("blocked_terms", []) + rules.get("sensitive_terms", []):
            if term and term in text:
                fail(f"public page contains content blocked/internal term: {path.relative_to(PUBLIC).as_posix()} -> {term}")
    ok("content pipeline checks completed")


def check_deepseek_batch(sitemap: set[str]) -> None:
    tasks_path = BATCH_001 / "batch-001-tasks.md"
    index_path = BATCH_001 / "batch-001-index.json"
    if not tasks_path.exists():
        fail("missing batch-001-tasks.md")
        return
    if not index_path.exists():
        fail("missing batch-001-index.json")
        return
    queue = {item["content_id"]: item for item in json.loads((CONTENT_DATA / "content_queue.json").read_text(encoding="utf-8-sig"))}
    batch = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if not 10 <= len(batch) <= 15:
        fail(f"batch-001 task count must be 10-15, got {len(batch)}")
    batch_text = tasks_path.read_text(encoding="utf-8-sig")
    required = ["content_id:", "status: draft_received", "不要省略 front matter", "不要合并多篇文章"]
    for token in required:
        if token not in batch_text:
            fail(f"batch-001 missing DeepSeek output instruction: {token}")
    for item in batch:
        cid = item.get("content_id", "")
        if cid not in queue:
            fail(f"batch task missing from content_queue: {cid}")
        task_file = ROOT / item.get("task_file", "")
        if not task_file.exists():
            fail(f"batch task file missing: {item.get('task_file')}")
        elif "status: draft_received" not in task_file.read_text(encoding="utf-8-sig"):
            fail(f"batch task missing output front matter template: {task_file.name}")
    if DRAFTS.exists() and any(path.name.upper() != "README.MD" for path in DRAFTS.glob("*.md")):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "review_content_drafts.py")], cwd=ROOT, text=True, capture_output=True)
        if result.returncode != 0:
            fail("review_content_drafts.py failed")
    for item in queue.values():
        full_url = BASE_URL + item.get("target_url", "").lstrip("/")
        if item.get("status") in {"draft_received", "reviewed"} and full_url in sitemap:
            fail(f"draft/reviewed content entered sitemap: {item['content_id']}")
    ok("DeepSeek batch checks completed")


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
    check_keyword_assets(sitemap)
    check_content_pipeline(sitemap)
    check_deepseek_batch(sitemap)
    if FAILURES:
        print(f"[FAIL] {len(FAILURES)} issue(s) found")
        return 1
    if WARNINGS:
        print(f"[WARN] {len(WARNINGS)} warning(s) found")
    ok("static site checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
