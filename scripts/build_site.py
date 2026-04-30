from __future__ import annotations

import html
import csv
import json
import re
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site_src"
DATA = SRC / "data"
TEMPLATES = SRC / "templates"
PARTIALS = TEMPLATES / "partials"
PUBLIC = ROOT / "site" / "public"
DOCS = ROOT / "docs"
KEYWORD_DATA = DATA / "keywords"
KEYWORD_ASSETS = ROOT / "data" / "keyword-assets"


def load_json(name: str):
    with (DATA / name).open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def load_keyword_json(name: str):
    path = KEYWORD_DATA / name
    if not path.exists():
        return [] if name.endswith(".json") else {}
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{ " + key + " }}", value)
    return template


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug_to_label(slug: str) -> str:
    return slug.replace("-", " ").title()


def url_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return path


def page_file(path: str) -> str:
    path = url_path(path)
    if path == "/":
        return "index.html"
    if path.endswith(".html"):
        return path.lstrip("/")
    return path.strip("/") + "/index.html"


def output_file(path: str) -> Path:
    return PUBLIC / page_file(path)


def canonical(path: str, base_url: str) -> str:
    path = url_path(path)
    return base_url.rstrip("/") + ("/" if path == "/" else path)


def write_file(relative: str, content: str) -> None:
    target = PUBLIC / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def clean_public() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for path in PUBLIC.rglob("*.html"):
        path.unlink()
    for filename in ("sitemap.xml", "robots.txt"):
        path = PUBLIC / filename
        if path.exists():
            path.unlink()
    css = PUBLIC / "assets" / "css" / "styles.css"
    if css.exists():
        css.unlink()


def partial(name: str, values: dict[str, str] | None = None) -> str:
    values = values or {}
    return render(read_text(PARTIALS / name), values)


def list_items(items: list[str], class_name: str = "checklist") -> str:
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def nav_html(items: list[dict]) -> str:
    return "".join(f'<a href="{esc(item["url"])}">{esc(item["label"])}</a>' for item in items)


def card_grid(items: list[dict], columns: int = 3) -> str:
    cards = []
    for item in items:
        url = item.get("url", "#")
        title = item.get("title", item.get("label", ""))
        summary = item.get("summary", item.get("description", ""))
        cards.append(partial("card_grid.html", {"url": esc(url), "title": esc(title), "summary": esc(summary)}))
    return f'<div class="grid grid-{columns}">' + "".join(cards) + "</div>"


def breadcrumb_items(path: str, title: str, base_url: str) -> list[dict]:
    path = url_path(path)
    items = [{"name": "首页", "url": canonical("/", base_url)}]
    if path != "/":
        parts = [p for p in path.strip("/").split("/") if p and not p.endswith(".html")]
        current = ""
        for index, part in enumerate(parts):
            current += "/" + part + "/"
            name = title if index == len(parts) - 1 else slug_to_label(part)
            items.append({"name": name, "url": canonical(current, base_url)})
    return items


def breadcrumb_html(items: list[dict]) -> str:
    links = []
    for index, item in enumerate(items):
        if index == len(items) - 1:
            links.append(f"<span>{esc(item['name'])}</span>")
        else:
            links.append(f'<a href="{esc(item["url"].replace(BASE_URL, "") or "/")}">{esc(item["name"])}</a>')
    return partial("breadcrumb.html", {"items": " / ".join(links)})


def json_script(data: dict) -> str:
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "</script>"


def organization_schema(site: dict) -> dict:
    return {"@context": "https://schema.org", "@type": "Organization", "name": site["site_name"], "url": site["base_url"], "description": site["default_description"]}


def website_schema(site: dict) -> dict:
    return {"@context": "https://schema.org", "@type": "WebSite", "name": site["site_name"], "url": site["base_url"], "description": site["default_description"]}


def breadcrumb_schema(items: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": item["name"], "item": item["url"]} for i, item in enumerate(items)],
    }


def faq_schema(faqs: list[dict]) -> dict:
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]}


def service_schema(item: dict, site: dict) -> dict:
    return {"@context": "https://schema.org", "@type": "Service", "name": item["title"], "description": item["description"], "provider": {"@type": "Organization", "name": site["site_name"], "url": site["base_url"]}, "areaServed": "Global"}


def faq_html(faqs: list[dict]) -> str:
    if not faqs:
        return ""
    body = "".join(f'<article class="faq-item"><h3>{esc(item["q"])}</h3><p>{esc(item["a"])}</p></article>' for item in faqs)
    return partial("faq.html", {"items": body})


def cta_html(title: str, text: str) -> str:
    return partial("cta.html", {"title": esc(title), "text": esc(text)})


def boundary_html(text: str) -> str:
    return partial("boundary.html", {"text": esc(text)})


def keyword_context() -> dict:
    clusters = load_keyword_json("clusters.json")
    url_map = load_keyword_json("url_map.json")
    rules_path = KEYWORD_DATA / "rules.json"
    rules = json.loads(rules_path.read_text(encoding="utf-8-sig")) if rules_path.exists() else {}
    by_url: dict[str, list[str]] = {}
    for item in url_map:
        if item.get("status") in {"public_primary", "public_secondary"}:
            by_url.setdefault(item["target_url"], []).append(item["keyword"])
    for cluster in clusters:
        target = cluster.get("target_url")
        if not target:
            continue
        for term in cluster.get("include_actions", []) + cluster.get("include_categories", []) + cluster.get("include_platforms", []) + cluster.get("include_countries", []):
            by_url.setdefault(target, []).append(term)
    summary = {}
    summary_path = KEYWORD_ASSETS / "cluster_summary.csv"
    if summary_path.exists():
        with summary_path.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                summary[row["cluster_id"]] = row
    return {"clusters": clusters, "url_map": url_map, "rules": rules, "by_url": by_url, "summary": summary}


def keyword_block(path: str, context: dict, title: str = "关键词承接方向") -> str:
    terms = context.get("by_url", {}).get(path, [])
    blocked = set(context.get("rules", {}).get("sensitive_internal_categories", []) + context.get("rules", {}).get("blocked_promise_terms", []))
    visible = []
    for term in terms:
        if not term or term in visible:
            continue
        if any(blocked_term and blocked_term in term for blocked_term in blocked):
            continue
        visible.append(term)
    visible = visible[:12]
    if not visible:
        return ""
    pills = "".join(f'<span class="pill">{esc(term)}</span>' for term in visible)
    return f'<article class="card keyword-block"><h2>{esc(title)}</h2><p>本页只展示代表性搜索方向，完整关键词先进入内部资产库和聚类映射，不直接生成大量公开页面。</p><div class="pill-list">{pills}</div></article>'


def resolve_faqs(faq_data: dict, refs: list[str] | None, fallback_group: str) -> list[dict]:
    pool = []
    for group in ("global", fallback_group):
        pool.extend(faq_data.get(group, []))
    if refs:
        by_id = {item.get("id"): item for group in faq_data.values() for item in group if item.get("id")}
        selected = [by_id[ref] for ref in refs if ref in by_id]
        if selected:
            pool = selected
    seen = set()
    result = []
    for item in pool:
        key = item["q"]
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result[:6]


def sections_html(sections: list[tuple[str, str]]) -> str:
    return "".join(f'<article class="card"><h2>{esc(title)}</h2>{content}</article>' for title, content in sections)


def detail_content(item: dict, item_type: str, faq_data: dict, blocks: dict, keyword_ctx: dict) -> tuple[str, list[dict]]:
    if item_type == "service":
        sections = [
            ("服务说明", f"<p>{esc(item.get('intro', item.get('summary', '')))}</p>"),
            ("适合项目", list_items(item.get("suitable_for", []))),
            ("常见需求", list_items(item.get("common_needs", []))),
            ("支持内容", list_items(item.get("support_items", []))),
            ("执行流程", list_items(item.get("process", []))),
            ("需要准备什么", list_items(item.get("preparation", []))),
            ("不适合什么", list_items(item.get("not_suitable", item.get("not_suitable_for", [])))),
            ("服务边界", list_items(item.get("boundaries", []))),
        ]
        faq_group = "services"
    elif item_type == "platform":
        sections = [
            ("平台说明", f"<p>{esc(item.get('intro', item.get('summary', '')))}</p>"),
            ("平台适合场景", list_items(item.get("traffic_scenes", []))),
            ("适合项目类型", list_items(item.get("suitable_projects", item.get("suitable_for", [])))),
            ("投放前准备", list_items(item.get("preparation", []))),
            ("服务适配", list_items(item.get("service_fit", []))),
            ("服务边界", list_items(item.get("boundaries", []))),
        ]
        faq_group = "platforms"
    else:
        sections = [
            ("主题说明", f"<p>{esc(item.get('intro', item.get('summary', '')))}</p>"),
            ("常见推广需求", list_items(item.get("common_needs", []))),
            ("可用渠道", list_items(item.get("recommended_channels", []))),
            ("推广前准备", list_items(item.get("preparation", []))),
            ("服务适配", list_items(item.get("service_fit", []))),
            ("风险提示", list_items(item.get("risk_notes", []))),
            ("服务边界", list_items(item.get("boundaries", []))),
        ]
        faq_group = "topics"
    faqs = resolve_faqs(faq_data, item.get("faq_refs"), faq_group)
    content = render(
        read_text(TEMPLATES / "page.html"),
        {
            "eyebrow": esc(item.get("eyebrow", "详情")),
            "h1": esc(item["h1"]),
            "description": esc(item["description"]),
            "body": sections_html(sections),
            "related_services": card_grid(item.get("related_services", []), 2),
            "related_topics": card_grid(item.get("related_topics", []), 2),
            "related_platforms": card_grid(item.get("related_platforms", []), 2),
            "keyword_block": keyword_block(item["url"], keyword_ctx),
            "faq": faq_html(faqs),
            "boundary": boundary_html(blocks["service_boundary"]),
            "cta": cta_html(item.get("cta_title", "联系咨询"), item.get("cta_text", item.get("cta", ""))),
        },
    )
    return content, faqs


def render_base(page: dict, path: str, content: str, site: dict, nav: list[dict], schemas: list[dict]) -> str:
    crumbs = breadcrumb_items(path, page["h1"], site["base_url"])
    schema_html = "\n".join(json_script(schema) for schema in schemas)
    return render(
        read_text(TEMPLATES / "base.html"),
        {
            "title": esc(page["title"]),
            "description": esc(page["description"]),
            "canonical": esc(canonical(path, site["base_url"])),
            "site_name": esc(site["site_name"]),
            "nav": nav_html(nav),
            "breadcrumb": breadcrumb_html(crumbs),
            "content": content,
            "footer": partial("footer.html", {"boundary": esc(site["service_boundary_short"])}),
            "json_ld": schema_html,
        },
    )


def check_duplicate_urls(records: list[dict]) -> None:
    seen = set()
    duplicates = []
    for record in records:
        if record["url"] in seen:
            duplicates.append(record["url"])
        seen.add(record["url"])
    if duplicates:
        raise SystemExit("[FAIL] duplicate URLs: " + ", ".join(duplicates))


def emit(path: str, page: dict, content: str, site: dict, nav: list[dict], schemas: list[dict], records: list[dict], source: str, page_type: str, indexable: bool = True) -> None:
    full_schemas = schemas[:]
    crumbs = breadcrumb_items(path, page["h1"], site["base_url"])
    full_schemas.append(breadcrumb_schema(crumbs))
    html_text = render_base(page, path, content, site, nav, full_schemas)
    target = output_file(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8", newline="\n")
    if indexable:
        records.append({"url": canonical(path, site["base_url"]), "path": path, "source": source, "output": target.relative_to(ROOT).as_posix(), "type": page_type, "title": page["title"], "description": page["description"], "indexable": "yes"})


def build() -> None:
    site = load_json("site.json")
    nav = load_json("nav.json")
    pages = load_json("pages.json")
    services = load_json("services.json")
    platforms = load_json("platforms.json")
    topics = load_json("topics.json")
    markets = load_json("markets.json")
    contact = load_json("contact.json")
    faqs = load_json("faqs.json")
    seo = load_json("seo.json")
    schema_flags = load_json("schema.json")
    blocks = load_json("content_blocks.json")
    keyword_ctx = keyword_context()
    today = date.today().isoformat()

    clean_public()
    css_target = PUBLIC / "assets" / "css" / "styles.css"
    css_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "assets" / "css" / "styles.css", css_target)

    records: list[dict] = []
    global_schemas = []
    if schema_flags.get("organization_schema"):
        global_schemas.append(organization_schema(site))
    if schema_flags.get("website_schema"):
        global_schemas.append(website_schema(site))

    home_faqs = resolve_faqs(faqs, pages["home"].get("faq_refs"), "global")
    home_content = render(
        read_text(TEMPLATES / "home.html"),
        {
            "h1": esc(pages["home"]["h1"]),
            "description": esc(pages["home"]["description"]),
            "service_cards": card_grid(services, 4),
            "platform_cards": card_grid(platforms, 3),
            "topic_cards": card_grid(topics, 4),
            "market_pills": "".join(f'<span class="pill">{esc(m)}</span>' for m in markets["market_list"]),
            "process": list_items(blocks["process_steps"], "process-list"),
            "why_9hwh": list_items(blocks["why_9hwh"]),
            "keyword_block": keyword_block("/", keyword_ctx, "首页关键词承接方向"),
            "boundary": boundary_html(blocks["service_boundary"]),
            "faq": faq_html(home_faqs),
            "cta": cta_html("准备开始沟通？", "如果你正在准备海外推广、引流获客、广告投放或买量测试，可以先整理项目资料，再进入咨询。"),
        },
    )
    emit("/", pages["home"], home_content, site, nav, global_schemas + [faq_schema(home_faqs)], records, "pages.json:home", "home")

    services_extra = keyword_block("/services/traffic-acquisition/", keyword_ctx, "服务词承接方向") + boundary_html(blocks["service_boundary"]) + faq_html(resolve_faqs(faqs, None, "services"))
    emit("/services/", pages["services"], listing_content(pages["services"], services, services_extra), site, nav, global_schemas, records, "pages.json:services", "listing")
    for item in services:
        content, item_faqs = detail_content(item, "service", faqs, blocks, keyword_ctx)
        schemas = global_schemas + [faq_schema(item_faqs), service_schema(item, site)]
        emit(item["url"], item, content, site, nav, schemas, records, f"services.json:{item['slug']}", "service")

    platforms_extra = keyword_block("/platforms/tk/", keyword_ctx, "平台词承接方向") + faq_html(resolve_faqs(faqs, None, "platforms"))
    emit("/platforms/", pages["platforms"], listing_content(pages["platforms"], platforms, platforms_extra), site, nav, global_schemas, records, "pages.json:platforms", "listing")
    for item in platforms:
        content, item_faqs = detail_content(item, "platform", faqs, blocks, keyword_ctx)
        emit(item["url"], item, content, site, nav, global_schemas + [faq_schema(item_faqs)], records, f"platforms.json:{item['slug']}", "platform")

    topics_extra = keyword_block("/topics/crypto-promotion/", keyword_ctx, "细分类目承接方向") + boundary_html(blocks["service_boundary"]) + faq_html(resolve_faqs(faqs, None, "topics"))
    emit("/topics/", pages["topics"], listing_content(pages["topics"], topics, topics_extra), site, nav, global_schemas, records, "pages.json:topics", "listing")
    for item in topics:
        content, item_faqs = detail_content(item, "topic", faqs, blocks, keyword_ctx)
        emit(item["url"], item, content, site, nav, global_schemas + [faq_schema(item_faqs)], records, f"topics.json:{item['slug']}", "topic")

    market_cards = [{"title": item["title"], "url": "/markets/", "summary": item["summary"]} for item in markets["evaluation_dimensions"]]
    market_extra = '<div class="pill-list">' + "".join(f'<span class="pill">{esc(m)}</span>' for m in markets["market_list"]) + "</div>" + card_grid(market_cards, 3) + keyword_block("/markets/", keyword_ctx, "市场词承接方向") + faq_html(resolve_faqs(faqs, markets.get("faq_refs"), "markets"))
    emit("/markets/", pages["markets"], listing_content(pages["markets"], [], market_extra), site, nav, global_schemas, records, "pages.json:markets", "markets")

    blog_extra = card_grid(pages["blog"]["categories"], 3) + '<article class="card"><h2>长尾问答词处理方式</h2><p>带有怎么做、费用、价格、渠道、平台等后缀的长尾词先进入 future_blog 队列，后续再按 GSC 反馈和内容质量要求规划正文。</p></article><p class="note">当前不批量生成文章正文，后续文章正文默认由 DeepSeek 负责。</p>'
    emit("/blog/", pages["blog"], listing_content(pages["blog"], [], blog_extra), site, nav, global_schemas, records, "pages.json:blog", "blog")

    contact_extra = partial("boundary.html", {"text": esc(contact["boundary_note"])}) + '<div class="grid grid-2"><article class="card"><h2>咨询前需要提供</h2>' + list_items(contact["required_info"]) + '</article><article class="card"><h2>' + esc(contact["contact_title"]) + '</h2><p>' + esc(contact["contact_intro"]) + '</p><p>' + esc(contact["contact_placeholder"]) + '</p><p>' + esc(contact["response_note"]) + "</p></article></div>" + faq_html(resolve_faqs(faqs, None, "contact"))
    emit("/contact/", pages["contact"], listing_content(pages["contact"], [], contact_extra), site, nav, global_schemas, records, "pages.json:contact", "contact")

    not_found_extra = '<p><a class="button button-primary" href="/">返回首页</a> <a class="button button-secondary" href="/services/">查看服务</a> <a class="button button-secondary" href="/contact/">联系咨询</a></p>'
    emit("/404.html", pages["404"], listing_content(pages["404"], [], not_found_extra), site, nav, global_schemas, records, "pages.json:404", "utility", indexable=False)

    check_duplicate_urls(records)
    write_sitemap(records, today)
    write_file("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: https://www.9hwh.com/sitemap.xml\n")
    write_inventory(records)
    print(f"[OK] Generated {len(records)} indexed pages into {PUBLIC}")


def listing_content(page: dict, items: list[dict], extra: str = "") -> str:
    return render(read_text(TEMPLATES / "listing.html"), {"eyebrow": esc(page.get("eyebrow", "")), "h1": esc(page["h1"]), "description": esc(page["description"]), "cards": card_grid(items, 3 if len(items) <= 3 else 4), "extra": extra})


def write_sitemap(records: list[dict], lastmod: str) -> None:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for record in records:
        lines.append(f'  <url><loc>{record["url"]}</loc><lastmod>{lastmod}</lastmod></url>')
    lines.append("</urlset>")
    write_file("sitemap.xml", "\n".join(lines) + "\n")


def write_inventory(records: list[dict]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = ["# Site URL Inventory", "", "| URL | Source | Output File | Type | Sitemap | Indexable | Title | Description |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for record in records:
        rows.append(f"| {record['url']} | {record['source']} | {record['output']} | {record['type']} | yes | {record['indexable']} | {record['title']} | {record['description']} |")
    (DOCS / "site-url-inventory.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


BASE_URL = "https://www.9hwh.com"


if __name__ == "__main__":
    build()
