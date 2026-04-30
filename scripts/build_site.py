from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "site_src"
DATA = SRC / "data"
TEMPLATES = SRC / "templates"
PUBLIC = ROOT / "site" / "public"
BASE_URL = "https://www.9hwh.com"


def load_json(name: str):
    with (DATA / name).open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def read_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace("{{ " + key + " }}", value)
    return output


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def url_path(path: str) -> str:
    return path if path.startswith("/") else "/" + path


def canonical(path: str) -> str:
    path = url_path(path)
    if path == "/":
        return BASE_URL + "/"
    return BASE_URL + path


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


def nav_html(nav_items: list[dict]) -> str:
    return "".join(f'<a href="{esc(item["url"])}">{esc(item["label"])}</a>' for item in nav_items)


def footer_html(nav_items: list[dict], site: dict) -> str:
    return f"""
<div class="container footer-grid">
  <div><h2>服务入口</h2><ul class="footer-list">
    <li><a href="/services/overseas-promotion/">海外推广服务</a></li>
    <li><a href="/services/traffic-acquisition/">引流获客服务</a></li>
    <li><a href="/services/ad-campaign-support/">广告投放支持</a></li>
    <li><a href="/services/media-buying/">买量投流支持</a></li>
  </ul></div>
  <div><h2>平台入口</h2><ul class="footer-list">
    <li><a href="/platforms/tk/">TK 推广支持</a></li>
    <li><a href="/platforms/fb/">FB 推广支持</a></li>
    <li><a href="/platforms/google/">Google 推广支持</a></li>
    <li><a href="/markets/">市场方向</a></li>
  </ul></div>
  <div><h2>主题入口</h2><ul class="footer-list">
    <li><a href="/topics/">主题总览</a></li>
    <li><a href="/topics/crypto-promotion/">虚拟币推广</a></li>
    <li><a href="/topics/dating-traffic/">交友引流</a></li>
    <li><a href="/topics/game-promotion/">游戏推广</a></li>
  </ul></div>
  <div><h2>联系与边界</h2><ul class="footer-list">
    <li><a href="/blog/">内容中心</a></li>
    <li><a href="/contact/">联系咨询</a></li>
  </ul><p class="footer-note">{esc(site["service_boundary_short"])}</p></div>
</div>"""


def list_items(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def card_grid(items: list[dict], columns: int = 3) -> str:
    cards = []
    for item in items:
        cards.append(
            f'<article class="card"><h3><a href="{esc(item["url"])}">{esc(item["title"])}</a></h3>'
            f'<p>{esc(item.get("summary", item.get("description", "")))}</p></article>'
        )
    return f'<div class="grid grid-{columns}">' + "".join(cards) + "</div>"


def render_base(title: str, description: str, path: str, content: str, site: dict, nav: list[dict]) -> str:
    return render(
        read_template("base.html"),
        {
            "title": esc(title),
            "description": esc(description),
            "canonical": esc(canonical(path)),
            "site_name": esc(site["site_name"]),
            "nav": nav_html(nav),
            "content": content,
            "footer": footer_html(nav, site),
        },
    )


def page_file(path: str) -> str:
    path = url_path(path)
    if path == "/":
        return "index.html"
    if path.endswith(".html"):
        return path.lstrip("/")
    return path.strip("/") + "/index.html"


def render_home(site: dict, nav: list[dict], pages: dict, services: list[dict], platforms: list[dict], topics: list[dict], markets: dict) -> tuple[str, str, str]:
    content = render(
        read_template("home.html"),
        {
            "h1": esc(pages["home"]["h1"]),
            "description": esc(pages["home"]["description"]),
            "service_cards": card_grid(services, 4),
            "platform_cards": card_grid(platforms, 3),
            "topic_cards": card_grid(topics, 4),
            "market_pills": "".join(f'<span class="pill">{esc(m)}</span>' for m in markets["markets"]),
            "service_boundary": esc(site["service_boundary"]),
        },
    )
    return pages["home"]["title"], pages["home"]["description"], content


def listing_content(kind: str, page: dict, items: list[dict], extra: str = "") -> str:
    return render(
        read_template("listing.html"),
        {
            "eyebrow": esc(page.get("eyebrow", kind)),
            "h1": esc(page["h1"]),
            "description": esc(page["description"]),
            "cards": card_grid(items, 3 if len(items) <= 3 else 4),
            "extra": extra,
        },
    )


def detail_content(item: dict, item_type: str) -> str:
    if item_type == "service":
        sections = [
            ("适合项目", list_items(item["suitable_for"])),
            ("常见需求", list_items(item["common_needs"])),
            ("支持内容", list_items(item["support_items"])),
            ("执行流程", list_items(item["process"])),
            ("需要准备什么", list_items(item["preparation"])),
            ("不适合什么", list_items(item["not_suitable_for"])),
            ("服务边界", list_items(item["boundaries"])),
        ]
    elif item_type == "platform":
        sections = [
            ("平台适合场景", list_items(item["traffic_scenes"])),
            ("投放前准备", list_items(item["preparation"])),
            ("适合项目类型", list_items(item["suitable_for"])),
            ("服务边界", list_items(item["boundaries"])),
        ]
    else:
        sections = [
            ("主题说明", f"<p>{esc(item['summary'])}</p>"),
            ("常见推广需求", list_items(item["common_needs"])),
            ("可用渠道", list_items(item["recommended_channels"])),
            ("推广前准备", list_items(item["preparation"])),
            ("服务边界", list_items(item["boundaries"])),
        ]

    body = "".join(f'<article class="card"><h2>{esc(title)}</h2>{content}</article>' for title, content in sections)
    related_services = card_grid(item.get("related_services", []), 2) if item.get("related_services") else ""
    related_topics = card_grid(item.get("related_topics", []), 2) if item.get("related_topics") else ""
    related_platforms = card_grid(item.get("related_platforms", []), 2) if item.get("related_platforms") else ""
    return render(
        read_template("page.html"),
        {
            "eyebrow": esc(item.get("eyebrow", "页面")),
            "h1": esc(item["h1"]),
            "description": esc(item["description"]),
            "body": body,
            "related_services": related_services,
            "related_topics": related_topics,
            "related_platforms": related_platforms,
            "cta": esc(item["cta"]),
        },
    )


def build() -> None:
    site = load_json("site.json")
    nav = load_json("nav.json")
    pages = load_json("pages.json")
    services = load_json("services.json")
    platforms = load_json("platforms.json")
    topics = load_json("topics.json")
    markets = load_json("markets.json")

    clean_public()
    shutil.copyfile(SRC / "assets" / "css" / "styles.css", PUBLIC / "assets" / "css" / "styles.css")

    generated: list[dict[str, str]] = []

    def emit(path: str, title: str, description: str, content: str, index: bool = True) -> None:
        write_file(page_file(path), render_base(title, description, path, content, site, nav))
        if index:
            generated.append({"url": canonical(path)})

    title, desc, content = render_home(site, nav, pages, services, platforms, topics, markets)
    emit("/", title, desc, content)

    emit("/services/", pages["services"]["title"], pages["services"]["description"], listing_content("服务", pages["services"], services))
    for item in services:
        emit(item["url"], item["title"], item["description"], detail_content(item, "service"))

    emit("/platforms/", pages["platforms"]["title"], pages["platforms"]["description"], listing_content("平台", pages["platforms"], platforms))
    for item in platforms:
        emit(item["url"], item["title"], item["description"], detail_content(item, "platform"))

    emit("/topics/", pages["topics"]["title"], pages["topics"]["description"], listing_content("主题", pages["topics"], topics))
    for item in topics:
        emit(item["url"], item["title"], item["description"], detail_content(item, "topic"))

    market_extra = '<div class="pill-list">' + "".join(f'<span class="pill">{esc(m)}</span>' for m in markets["markets"]) + "</div>"
    market_extra += card_grid([{"url": "/markets/", "title": d["title"], "summary": d["summary"]} for d in markets["dimensions"]], 3)
    emit("/markets/", pages["markets"]["title"], pages["markets"]["description"], listing_content("市场", pages["markets"], [], market_extra))

    blog_extra = card_grid(pages["blog"]["categories"], 3)
    emit("/blog/", pages["blog"]["title"], pages["blog"]["description"], listing_content("内容中心", pages["blog"], [], blog_extra))

    contact_extra = '<div class="grid grid-2"><article class="card"><h2>咨询前需要提供</h2>' + list_items(pages["contact"]["checklist"]) + '</article><article class="card"><h2>联系方式</h2><p>' + esc(site["contact_placeholder"]) + '</p><p>' + esc(site["service_boundary_short"]) + "</p></article></div>"
    emit("/contact/", pages["contact"]["title"], pages["contact"]["description"], listing_content("联系", pages["contact"], [], contact_extra))

    emit("/404.html", pages["404"]["title"], pages["404"]["description"], listing_content("404", pages["404"], [], '<p><a class="button button-primary" href="/">返回首页</a> <a class="button button-secondary" href="/services/">查看服务</a> <a class="button button-secondary" href="/contact/">联系咨询</a></p>'), index=False)

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap.extend(f'  <url><loc>{item["url"]}</loc></url>' for item in generated)
    sitemap.append("</urlset>")
    write_file("sitemap.xml", "\n".join(sitemap) + "\n")
    write_file("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: https://www.9hwh.com/sitemap.xml\n")
    print(f"[OK] Generated {len(generated)} indexed pages into {PUBLIC}")


if __name__ == "__main__":
    build()
