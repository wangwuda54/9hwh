from __future__ import annotations

import hashlib
import html
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
CONTENT_DATA = DATA / "content"
DRAFTS = SRC / "content_drafts"
SEO_DATA = ROOT / "data" / "seo"

BASE_URL = "https://www.9hwh.com"
TELEGRAM_URL = "https://tg.9hwh.com/"
TELEGRAM_BUTTON_LABEL = "Telegram 咨询"
LEGACY_FALLBACK_PATH = "/services/legacy/"
LEGACY_EXACT_SOURCE_LIMIT = 900
DEFAULT_CTA_TITLE = "想确认你的项目适合怎么跑？"
DEFAULT_CTA_TEXT = "可以通过 Telegram 联系 9HWH，先简单说明项目类型、目标地区、预算范围和现有素材情况，我们会一起判断适合从哪个渠道开始测试。"
TOPIC_DEFAULT_ARTICLE_NOTE = "相关内容将逐步更新，你也可以先通过 Telegram 说一下项目情况。"


def load_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{ " + key + " }}", value)
    return template


def partial(name: str, values: dict[str, str] | None = None) -> str:
    return render(read_text(PARTIALS / name), values or {})


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def css_asset_version() -> str:
    css = SRC / "assets" / "css" / "styles.css"
    return hashlib.sha1(css.read_bytes()).hexdigest()[:8]


def url_path(path: str) -> str:
    return path if path.startswith("/") else "/" + path


def page_file(path: str) -> str:
    path = url_path(path)
    if path == "/":
        return "index.html"
    if path.endswith(".html"):
        return path.lstrip("/")
    return path.strip("/") + "/index.html"


def output_file(path: str) -> Path:
    return PUBLIC / page_file(path)


def canonical(path: str, base_url: str = BASE_URL) -> str:
    path = url_path(path)
    return base_url.rstrip("/") + ("/" if path == "/" else path)


def write_file(relative: str, content: str) -> None:
    target = PUBLIC / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")


def clean_public() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for path in PUBLIC.rglob("*"):
        if path.is_file():
            path.unlink()


def is_placeholder(value: str) -> bool:
    text = value.strip()
    return bool(text) and set(text) == {"?"}


def clean_items(items: list[str], fallback: list[str] | None = None) -> list[str]:
    cleaned = []
    for item in items:
        text = str(item).strip()
        if not text or is_placeholder(text):
            continue
        cleaned.append(text)
    if cleaned:
        return cleaned
    return fallback or []


def list_items(items: list[str], class_name: str = "checklist") -> str:
    cleaned = clean_items(items)
    if not cleaned:
        return '<ul class="' + class_name + '"><li>相关内容将逐步更新</li></ul>'
    return f'<ul class="{class_name}">' + "".join(f"<li>{esc(item)}</li>" for item in cleaned) + "</ul>"


def nav_html(items: list[dict]) -> str:
    links = []
    for item in items:
        url = item["url"]
        label = item["label"]
        is_external = url.startswith("http://") or url.startswith("https://")
        attrs = ' target="_blank" rel="noopener noreferrer"' if is_external else ""
        extra_class = ' class="nav-contact"' if "Telegram" in label or url == TELEGRAM_URL else ""
        links.append(f'<a{extra_class} href="{esc(url)}"{attrs}>{esc(label)}</a>')
    return "".join(links)


def home_hero_buttons_html() -> str:
    return (
        f'<a class="button button-telegram" href="{TELEGRAM_URL}" target="_blank" rel="noopener noreferrer">Telegram 咨询推广方案</a>'
        f'<a class="button button-secondary" href="{TELEGRAM_URL}" target="_blank" rel="noopener noreferrer">Telegram 看看适合跑哪些渠道</a>'
    )


def floating_telegram_html() -> str:
    return (
        f'<a class="floating-telegram" href="{TELEGRAM_URL}" target="_blank" rel="noopener noreferrer" aria-label="通过 Telegram 咨询 9HWH">'
        '<span class="floating-telegram-icon" aria-hidden="true"></span>'
        '<span class="floating-telegram-label">Telegram 咨询</span>'
        "</a>"
    )


def card_grid(items: list[dict], columns: int = 3) -> str:
    cards = []
    for item in items:
        url = item.get("url", "#")
        title = item.get("title", item.get("label", ""))
        summary = item.get("summary", item.get("description", ""))
        cards.append(partial("card_grid.html", {"url": esc(url), "title": esc(title), "summary": esc(summary)}))
    if not cards:
        return ""
    return f'<div class="grid grid-{columns}">' + "".join(cards) + "</div>"


def simple_cards(items: list[dict], columns: int = 3, extra_class: str = "") -> str:
    body = []
    for item in items:
        body.append(
            '<article class="card'
            + (f" {extra_class}" if extra_class else "")
            + '">'
            + f"<h3>{esc(item['title'])}</h3>"
            + f"<p>{esc(item['text'])}</p>"
            + "</article>"
        )
    return f'<div class="grid grid-{columns}">' + "".join(body) + "</div>"


def process_cards_html() -> str:
    items = [
        {"title": "项目沟通", "text": "先确认项目类型、目标地区、预算范围和现有准备情况。"},
        {"title": "渠道判断", "text": "结合市场、素材和落地页情况，判断更适合先跑哪个渠道。"},
        {"title": "准备测试", "text": "把账户、素材、落地页和承接链路一起整理清楚。"},
        {"title": "持续优化", "text": "根据阶段反馈继续调整渠道、素材和预算节奏。"},
    ]
    return simple_cards(items, 4, "step")


def home_service_cards_html() -> str:
    items = [
        {"title": "推广方向梳理", "text": "先判断项目更适合先跑哪类渠道，再安排第一轮测试顺序。"},
        {"title": "投放准备协作", "text": "一起看账户、素材、落地页和转化路径是否准备到位。"},
        {"title": "获客测试支持", "text": "围绕咨询、注册、转化等目标推进测试，而不是只停留在建议层。"},
        {"title": "阶段反馈优化", "text": "根据测试反馈继续调整渠道、素材和承接方式。"},
    ]
    cards = []
    for index, item in enumerate(items, start=1):
        cards.append(
            '<article class="home-service-card">'
            f"<span>{index:02d}</span>"
            f"<h3>{esc(item['title'])}</h3>"
            f"<p>{esc(item['text'])}</p>"
            "</article>"
        )
    return '<div class="home-service-grid">' + "".join(cards) + "</div>"


def home_advantage_cards_html() -> str:
    items = [
        {"title": "少走弯路", "text": "先把测试方向理顺，再进入更具体的执行安排。"},
        {"title": "降低试错成本", "text": "小预算先测，尽量把钱花在更可能出效果的方向上。"},
        {"title": "持续一起推进", "text": "不是给一份建议就结束，而是根据反馈继续调整。"},
    ]
    return simple_cards(items, 3, "advantage-card")


def fit_cards_html() -> str:
    items = [
        {"title": "项目刚准备启动", "text": "还没确定先跑哪个渠道，想先把方向判断清楚。"},
        {"title": "已有素材和落地页", "text": "想尽快进入测试，但不想一开始就乱花预算。"},
        {"title": "已经在做推广", "text": "希望有人一起看渠道组合、素材方向和后续优化。"},
    ]
    return simple_cards(items, 3)


def extract_markdown_links(markdown: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", markdown)


def markdown_to_html(markdown: str) -> str:
    def inline_html(text: str) -> str:
        escaped = esc(text)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\[(.+?)\]\((/[^)\s]+)\)", r'<a href="\2">\1</a>', escaped)
        return escaped

    blocks = []
    in_list = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            if in_list:
                blocks.append("</ul>")
                in_list = False
            continue
        if line.startswith("### "):
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<h3>{inline_html(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<h2>{inline_html(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li>{inline_html(line[2:])}</li>")
        else:
            if in_list:
                blocks.append("</ul>")
                in_list = False
            blocks.append(f"<p>{inline_html(line)}</p>")
    if in_list:
        blocks.append("</ul>")
    return "".join(blocks)


def breadcrumb_items(path: str, title: str) -> list[dict]:
    path = url_path(path)
    items = [{"name": "首页", "url": canonical("/")}]
    if path == "/":
        return items
    parts = [part for part in path.strip("/").split("/") if part and not part.endswith(".html")]
    current = ""
    for index, part in enumerate(parts):
        current = current.rstrip("/") + "/" + part + "/"
        name = title if index == len(parts) - 1 else part.replace("-", " ").title()
        if current == "/blog/topics/":
            current = "/topics/"
        items.append({"name": name, "url": canonical(current)})
    return items


def breadcrumb_html(items: list[dict]) -> str:
    parts = []
    for index, item in enumerate(items):
        if index == len(items) - 1:
            parts.append(f"<span>{esc(item['name'])}</span>")
        else:
            local_url = item["url"].replace(BASE_URL, "") or "/"
            parts.append(f'<a href="{esc(local_url)}">{esc(item["name"])}</a>')
    return partial("breadcrumb.html", {"items": " / ".join(parts)})


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
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}} for item in faqs]}


def service_schema(item: dict, site: dict) -> dict:
    return {"@context": "https://schema.org", "@type": "Service", "name": item["title"], "description": item["description"], "provider": {"@type": "Organization", "name": site["site_name"], "url": site["base_url"]}, "areaServed": "Global"}


def faq_html(faqs: list[dict]) -> str:
    if not faqs:
        return ""
    items = "".join(f'<article class="faq-item"><h3>{esc(item["q"])}</h3><p>{esc(item["a"])}</p></article>' for item in faqs)
    return partial("faq.html", {"items": items})


def cta_html(title: str, text: str, button_label: str = TELEGRAM_BUTTON_LABEL, url: str = TELEGRAM_URL) -> str:
    return partial("cta.html", {"title": esc(title), "text": esc(text), "button_label": esc(button_label), "url": esc(url)})


def boundary_html(text: str) -> str:
    return partial("boundary.html", {"text": esc(text)})


def keyword_context() -> dict:
    by_url: dict[str, list[str]] = {}
    rules = {}
    url_map_path = KEYWORD_DATA / "url_map.json"
    rules_path = KEYWORD_DATA / "rules.json"
    clusters_path = KEYWORD_DATA / "clusters.json"
    if url_map_path.exists():
        for item in json.loads(url_map_path.read_text(encoding="utf-8")):
            if item.get("status") in {"public_primary", "public_secondary"} and item.get("target_url") and item.get("keyword"):
                by_url.setdefault(item["target_url"], []).append(item["keyword"])
    if clusters_path.exists():
        for cluster in json.loads(clusters_path.read_text(encoding="utf-8")):
            target = cluster.get("target_url")
            if not target:
                continue
            for key in ("include_actions", "include_categories", "include_platforms", "include_countries"):
                for term in cluster.get(key, []):
                    if term:
                        by_url.setdefault(target, []).append(term)
    if rules_path.exists():
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
    return {"by_url": by_url, "rules": rules}


def keyword_block(path: str, context: dict, title: str = "相关搜索方向") -> str:
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
    return f'<article class="card keyword-block"><h2>{esc(title)}</h2><p>以下内容代表当前页面相关的常见搜索方向，用于帮助理解主题，不代表全部投放场景。</p><div class="pill-list">{pills}</div></article>'


def resolve_faqs(faq_data: dict, refs: list[str] | None, fallback_group: str) -> list[dict]:
    pool = faq_data.get("global", []) + faq_data.get(fallback_group, [])
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


def load_content_queue() -> list[dict]:
    path = CONTENT_DATA / "content_queue.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def parse_draft(path: Path) -> tuple[dict, str]:
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


def load_publishable_drafts(queue: list[dict]) -> list[tuple[dict, str]]:
    publishable = {item["content_id"]: item for item in queue if item.get("status") == "published" and not item.get("internal_only")}
    results = []
    if not DRAFTS.exists():
        return results
    for path in sorted(DRAFTS.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        meta, body = parse_draft(path)
        content_id = meta.get("content_id")
        if content_id in publishable:
            task = publishable[content_id].copy()
            task.update({key: value for key, value in meta.items() if value})
            results.append((task, body))
    return results


def article_card(task: dict) -> dict:
    return {"title": task.get("title", ""), "url": task.get("target_url", "#"), "summary": task.get("description", task.get("intent", ""))}


def aggregate_published_articles(published_drafts: list[tuple[dict, str]]) -> dict[str, dict[str, list[dict]]]:
    grouped = {"topics": {}, "services": {}, "platforms": {}}
    for task, body in published_drafts:
        card = article_card(task)
        if task.get("target_topic"):
            grouped["topics"].setdefault(task["target_topic"], []).append(card)
        if task.get("target_service"):
            grouped["services"].setdefault(task["target_service"], []).append(card)
        for link in extract_markdown_links(body):
            if link.startswith("/platforms/") and link != "/platforms/":
                grouped["platforms"].setdefault(link, []).append(card)
    for group in grouped.values():
        for cards in group.values():
            cards.sort(key=lambda item: item["title"])
    return grouped


def blog_article_cards_html(published_drafts: list[tuple[dict, str]]) -> str:
    cards = []
    for task, _ in published_drafts:
        cards.append({"title": task["title"], "url": task["target_url"], "summary": task.get("description", task.get("intent", ""))})
    if not cards:
        return '<article class="card"><h2>内容中心</h2><p>公开内容将逐步更新。</p></article>'
    return card_grid(cards, 3)


def topic_article_block(published_articles: list[dict] | None) -> tuple[str, str]:
    if published_articles:
        return "已发布相关文章", card_grid(published_articles, 2)
    return "相关文章", f"<p>{esc(TOPIC_DEFAULT_ARTICLE_NOTE)}</p>"


def topic_service_fit(item: dict) -> list[str]:
    return clean_items(
        item.get("service_fit", []),
        [
            "适合先判断目标市场、预算范围和落地页承接方式的项目。",
            "适合已经有项目方向，但还没确定先从哪个渠道开始测试的团队。",
            "适合希望把素材、页面和咨询路径一起理顺后再推进推广的项目。",
            "适合希望通过 Telegram 先沟通项目情况，再决定测试节奏的合作方式。",
        ],
    )


def topic_consultation_prep(item: dict) -> list[str]:
    return clean_items(
        item.get("risk_notes", []),
        [
            "先准备项目介绍、目标地区、预算范围和落地页链接。",
            "如果已有素材、账户准备或 App 页面，也建议一并说明。",
            "先确认内容表达边界和咨询承接方式，再决定是否进入测试。",
        ],
    )


def platform_service_fit(item: dict) -> list[str]:
    return clean_items(
        item.get("service_fit", []),
        [
            "适合先做渠道判断和测试顺序梳理。",
            "适合结合素材方向和落地页承接一起评估。",
            "适合小预算先测，再根据反馈继续优化。",
            "适合需要持续沟通测试节奏和阶段反馈的项目。",
        ],
    )


def value_items(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def assessment_title(item: dict, item_type: str) -> str:
    title = item.get("assessment_title")
    if title:
        return title
    fallback_titles = {
        "service": "投放前评估重点",
        "platform": "平台投放评估重点",
        "topic": "项目评估重点",
    }
    return fallback_titles.get(item_type, "投放前评估重点")


def assessment_items(item: dict, item_type: str) -> list[str]:
    explicit = clean_items(item.get("assessment_items", []))
    if explicit:
        return explicit[:4]

    collected: list[str] = []
    seen: set[str] = set()
    fallback_keys = (
        "boundaries",
        "not_suitable",
        "not_suitable_for",
        "risk_notes",
        "service_fit",
    )
    for key in fallback_keys:
        for value in clean_items(value_items(item.get(key, []))):
            if value in seen:
                continue
            collected.append(value)
            seen.add(value)
            if len(collected) >= 4:
                return collected

    defaults = {
        "service": [
            "先确认目标地区、预算节奏、素材方向和落地页承接路径，再制定推广执行方案。",
            "结合账户、广告文案、页面内容和数据反馈，持续调整投放节奏和素材表达。",
        ],
        "platform": [
            "先确认目标地区、受众人群、素材方向和页面承接方式，再判断平台投放优先级。",
            "结合账户结构、审核反馈、转化路径和线索质量，逐步调整预算和素材组合。",
        ],
        "topic": [
            "先确认投放地区、项目资料、广告文案和落地页内容，再判断适合的渠道组合。",
            "结合表单路径、咨询承接、素材角度和账户反馈，降低审核被拒和投放中断风险。",
        ],
    }
    return defaults.get(item_type, defaults["service"])


def assessment_section(item: dict, item_type: str) -> tuple[str, str]:
    return assessment_title(item, item_type), list_items(assessment_items(item, item_type))


def detail_content(item: dict, item_type: str, faq_data: dict, blocks: dict, keyword_ctx: dict, published_articles: list[dict] | None = None) -> tuple[str, list[dict]]:
    detail_eyebrows = {
        "service": "服务详情",
        "platform": "平台详情",
        "topic": "主题详情",
    }
    if item_type == "service":
        sections = [
            ("服务说明", f"<p>{esc(item.get('intro', item.get('summary', '')))}</p>"),
            ("适合什么项目", list_items(item.get("suitable_for", []))),
            ("常见需求", list_items(item.get("common_needs", []))),
            ("支持内容", list_items(item.get("support_items", []))),
            ("执行流程", list_items(item.get("process", []))),
            ("推广前准备", list_items(item.get("preparation", []))),
            assessment_section(item, item_type),
        ]
        faq_group = "services"
    elif item_type == "platform":
        sections = [
            ("平台说明", f"<p>{esc(item.get('intro', item.get('summary', '')))}</p>"),
            ("适合什么项目", list_items(item.get("suitable_projects", item.get("suitable_for", [])))),
            ("适合的流量场景", list_items(item.get("traffic_scenes", []))),
            ("推广前准备", list_items(item.get("preparation", []))),
            assessment_section(item, item_type),
        ]
        faq_group = "platforms"
    else:
        article_title, article_content = topic_article_block(published_articles)
        sections = [
            ("主题说明", f"<p>{esc(item.get('intro', item.get('summary', '')))}</p>"),
            ("适合什么项目", list_items(item.get("suitable_for", []))),
            ("推广前准备", list_items(item.get("preparation", []))),
            ("渠道建议", list_items(item.get("recommended_channels", []))),
            assessment_section(item, item_type),
            (article_title, article_content),
        ]
        faq_group = "topics"
    faqs = resolve_faqs(faq_data, item.get("faq_refs"), faq_group)
    content = render(
        read_text(TEMPLATES / "page.html"),
        {
            "eyebrow": esc(item.get("eyebrow", detail_eyebrows.get(item_type, "详情"))),
            "h1": esc(item["h1"]),
            "description": esc(item["description"]),
            "body": sections_html(sections),
            "related_services": card_grid(item.get("related_services", []), 2),
            "related_topics": card_grid(item.get("related_topics", []), 2),
            "related_platforms": card_grid(item.get("related_platforms", []), 2),
            "keyword_block": keyword_block(item["url"], keyword_ctx),
            "faq": faq_html(faqs),
            "boundary": boundary_html(blocks["service_boundary"]),
            "cta": cta_html(item.get("cta_title", DEFAULT_CTA_TITLE), item.get("cta_text", item.get("cta", DEFAULT_CTA_TEXT))),
        },
    )
    return content, faqs


def render_base(page: dict, path: str, content: str, site: dict, nav: list[dict], schemas: list[dict], indexable: bool = True) -> str:
    crumbs = breadcrumb_items(path, page["h1"])
    return render(
        read_text(TEMPLATES / "base.html"),
        {
            "title": esc(page["title"]),
            "description": esc(page["description"]),
            "robots_meta": "" if indexable else '<meta name="robots" content="noindex,follow">',
            "canonical": esc(canonical(path)),
            "asset_version": css_asset_version(),
            "site_name": esc(site["site_name"]),
            "nav": nav_html(nav),
            "breadcrumb": "" if url_path(path) == "/" else breadcrumb_html(crumbs),
            "content": content,
            "footer": partial("footer.html", {"boundary": esc(site["service_boundary_short"]), "telegram_url": esc(TELEGRAM_URL)}),
            "floating_contact": floating_telegram_html(),
            "json_ld": "\n".join(json_script(schema) for schema in schemas),
        },
    )


def emit(path: str, page: dict, content: str, site: dict, nav: list[dict], schemas: list[dict], records: list[dict], source: str, page_type: str, indexable: bool = True) -> None:
    crumbs = breadcrumb_items(path, page["h1"])
    full_schemas = schemas + [breadcrumb_schema(crumbs)]
    html_text = render_base(page, path, content, site, nav, full_schemas, indexable)
    target = output_file(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_text, encoding="utf-8", newline="\n")
    if indexable:
        records.append({"url": canonical(path), "path": path, "source": source, "output": target.relative_to(ROOT).as_posix(), "type": page_type, "title": page["title"], "description": page["description"], "indexable": "yes"})


def listing_content(page: dict, items: list[dict], extra: str = "") -> str:
    columns = 3 if len(items) <= 3 else 4
    return render(read_text(TEMPLATES / "listing.html"), {"eyebrow": esc(page.get("eyebrow", "")), "h1": esc(page["h1"]), "description": esc(page["description"]), "cards": card_grid(items, columns), "extra": extra})


def write_sitemap(records: list[dict], lastmod: str) -> None:
    rows = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for record in records:
        rows.append(f'  <url><loc>{record["url"]}</loc><lastmod>{lastmod}</lastmod></url>')
    rows.append("</urlset>")
    write_file("sitemap.xml", "\n".join(rows) + "\n")


def load_legacy_redirect_map() -> list[dict]:
    path = SEO_DATA / "legacy_url_redirects.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def legacy_source_number(source_path: str) -> int:
    match = re.search(r"/service_(\d+)$", source_path)
    return int(match.group(1)) if match else 10**12


def legacy_gsc_priority_rank(row: dict) -> tuple[int, float, float, float, int]:
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    priority = priority_order.get(row.get("gsc_priority", ""), 99)
    clicks = float(row.get("gsc_clicks") or 0)
    impressions = float(row.get("gsc_impressions") or 0)
    position = float(row.get("gsc_best_position") or row.get("gsc_position") or 999999)
    return (priority, -clicks, -impressions, position, legacy_source_number(row["source_path"]))


def selected_legacy_exact_redirects(rows: list[dict]) -> list[dict]:
    high_confidence = [
        row
        for row in rows
        if row.get("status") == 301
        and row.get("confidence") == "high"
        and row.get("needs_review") is False
        and re.fullmatch(r"/service_\d+", row.get("source_path", ""))
    ]
    by_target: dict[str, list[dict]] = {}
    for row in sorted(high_confidence, key=lambda item: legacy_source_number(item["source_path"])):
        by_target.setdefault(row["target_path"], []).append(row)

    selected: list[dict] = []
    seen: set[str] = set()
    priority = next((row for row in high_confidence if row["source_path"] == "/service_15209"), None)
    if priority:
        selected.append(priority)
        seen.add(priority["source_path"])

    gsc_priority_rows = [
        row
        for row in high_confidence
        if row.get("gsc_priority") in {"P0", "P1", "P2"} and row["source_path"] not in seen
    ]
    for row in sorted(gsc_priority_rows, key=legacy_gsc_priority_rank):
        if len(selected) >= LEGACY_EXACT_SOURCE_LIMIT:
            break
        selected.append(row)
        seen.add(row["source_path"])

    while len(selected) < LEGACY_EXACT_SOURCE_LIMIT:
        added = False
        for target in sorted(by_target):
            while by_target[target] and by_target[target][0]["source_path"] in seen:
                by_target[target].pop(0)
            if not by_target[target]:
                continue
            row = by_target[target].pop(0)
            selected.append(row)
            seen.add(row["source_path"])
            added = True
            if len(selected) >= LEGACY_EXACT_SOURCE_LIMIT:
                break
        if not added:
            break
    return selected


def legacy_redirect_lines() -> list[str]:
    rows = load_legacy_redirect_map()
    lines = [
        "# Legacy service URL redirects generated from data/seo/legacy_url_redirects.json",
        "# Exact high-confidence 301 rules are first; broad legacy fallback rules stay last.",
    ]
    for row in selected_legacy_exact_redirects(rows):
        source_path = row["source_path"]
        target_path = row["target_path"]
        lines.append(f"{source_path} {target_path} 301")
        lines.append(f"{source_path}.html {target_path} 301")
    lines.extend(
        [
            f"/service_*.html {LEGACY_FALLBACK_PATH} 302",
            f"/service_* {LEGACY_FALLBACK_PATH} 302",
            "",
        ]
    )
    return lines


def write_cloudflare_pages_files() -> None:
    headers = "\n".join(
        [
            "/*",
            "  X-Content-Type-Options: nosniff",
            "  Referrer-Policy: strict-origin-when-cross-origin",
            "  X-Frame-Options: SAMEORIGIN",
            "  Content-Security-Policy: frame-ancestors 'self'",
            "  Permissions-Policy: interest-cohort=()",
            "  Cache-Control: public, max-age=0, must-revalidate",
            "",
            "/assets/*",
            "  Cache-Control: public, max-age=31536000, immutable",
            "",
        ]
    )
    redirects = "\n".join(legacy_redirect_lines())
    write_file("_headers", headers)
    write_file("_redirects", redirects)


def write_inventory(records: list[dict]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    rows = [
        "# Site URL Inventory",
        "",
        "| URL | Source | Output File | Type | Sitemap | Indexable | Title | Description |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        rows.append(f"| {record['url']} | {record['source']} | {record['output']} | {record['type']} | yes | {record['indexable']} | {record['title']} | {record['description']} |")
    (DOCS / "site-url-inventory.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def check_duplicate_urls(records: list[dict]) -> None:
    seen = set()
    duplicates = []
    for record in records:
        if record["url"] in seen:
            duplicates.append(record["url"])
        seen.add(record["url"])
    if duplicates:
        raise SystemExit("[FAIL] duplicate URLs: " + ", ".join(duplicates))


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
    schema_flags = load_json("schema.json")
    blocks = load_json("content_blocks.json")
    keyword_ctx = keyword_context()
    content_queue = load_content_queue()
    published_drafts = load_publishable_drafts(content_queue)
    published_aggregates = aggregate_published_articles(published_drafts)

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

    home_content = render(
        read_text(TEMPLATES / "home.html"),
        {
            "h1": esc(pages["home"]["h1"]),
            "description": esc(pages["home"]["description"]),
            "hero_buttons": home_hero_buttons_html(),
            "home_service_cards": home_service_cards_html(),
            "advantage_cards": home_advantage_cards_html(),
            "process_cards": process_cards_html(),
            "fit_cards": fit_cards_html(),
            "cta": cta_html(DEFAULT_CTA_TITLE, DEFAULT_CTA_TEXT),
        },
    )
    emit("/", pages["home"], home_content, site, nav, global_schemas, records, "pages.json:home", "home")

    services_extra = cta_html("需要先判断适合哪种合作方式？", "先通过 Telegram 说一下项目类型、目标地区和预算范围，我们会一起判断更适合从推广、获客还是投放支持切入。")
    emit("/services/", pages["services"], listing_content(pages["services"], services, services_extra), site, nav, global_schemas, records, "pages.json:services", "listing")
    for item in services:
        content, item_faqs = detail_content(item, "service", faqs, blocks, keyword_ctx, published_aggregates["services"].get(item["url"], []))
        emit(item["url"], item, content, site, nav, global_schemas + [faq_schema(item_faqs), service_schema(item, site)], records, f"services.json:{item['slug']}", "service")

    legacy_page = {
        "title": "服务内容已整合 | 9HWH",
        "h1": "服务内容已整合",
        "description": "旧服务页面已经整合到新版 9HWH 服务体系，可以继续查看服务、主题方向或通过 Telegram 咨询项目情况。",
        "eyebrow": "旧服务承接",
    }
    legacy_extra = (
        '<article class="card"><h2>继续查看新版服务体系</h2>'
        "<p>你访问的旧服务入口已经归并到新版服务与主题页面。可以先查看服务总览和主题方向，也可以直接通过 Telegram 说明项目类型、目标地区和预算范围。</p>"
        '<div class="button-row">'
        '<a class="button button-primary" href="/services/">查看服务</a>'
        '<a class="button button-secondary" href="/topics/">查看主题</a>'
        '<a class="button button-secondary" href="/contact/">联系咨询</a>'
        f'<a class="button button-telegram" href="{TELEGRAM_URL}" target="_blank" rel="noopener noreferrer">Telegram 咨询</a>'
        "</div></article>"
        + cta_html("想确认适合哪个方向？", "先通过 Telegram 说一下项目情况，我们会一起判断更适合从服务、主题还是平台方向继续看。")
    )
    emit(LEGACY_FALLBACK_PATH, legacy_page, listing_content(legacy_page, [], legacy_extra), site, nav, global_schemas, records, "legacy_url_redirects.json:fallback", "legacy", indexable=False)

    platforms_extra = cta_html("想先确认该从哪个平台开始测试？", "可以通过 Telegram 先说明项目类型、素材情况和目标地区，我们会一起判断更适合先跑 TK、FB、Google 还是其他组合。")
    emit("/platforms/", pages["platforms"], listing_content(pages["platforms"], platforms, platforms_extra), site, nav, global_schemas, records, "pages.json:platforms", "listing")
    for item in platforms:
        content, item_faqs = detail_content(item, "platform", faqs, blocks, keyword_ctx, published_aggregates["platforms"].get(item["url"], []))
        emit(item["url"], item, content, site, nav, global_schemas + [faq_schema(item_faqs)], records, f"platforms.json:{item['slug']}", "platform")

    topics_extra = cta_html("主题页看完了，想继续聊你的项目？", "先通过 Telegram 说一下项目情况、市场方向和预算范围，我们会一起拆更适合你的推广路径和测试节奏。")
    emit("/topics/", pages["topics"], listing_content(pages["topics"], topics, topics_extra), site, nav, global_schemas, records, "pages.json:topics", "listing")
    for item in topics:
        content, item_faqs = detail_content(item, "topic", faqs, blocks, keyword_ctx, published_aggregates["topics"].get(item["url"], []))
        emit(item["url"], item, content, site, nav, global_schemas + [faq_schema(item_faqs)], records, f"topics.json:{item['slug']}", "topic")

    market_cards = [{"title": item["title"], "url": "/markets/", "summary": item["summary"]} for item in markets["evaluation_dimensions"]]
    market_extra = (
        '<div class="pill-list">' + "".join(f'<span class="pill">{esc(item)}</span>' for item in markets["market_list"]) + "</div>"
        + card_grid(market_cards, 3)
        + cta_html("还没确定先做哪个国家或地区？", "可以通过 Telegram 先说明目标市场、语言和预算安排，我们会一起判断更适合先从哪个市场开始测试。")
    )
    emit("/markets/", pages["markets"], listing_content(pages["markets"], [], market_extra), site, nav, global_schemas, records, "pages.json:markets", "markets")

    blog_extra = blog_article_cards_html(published_drafts)
    emit("/blog/", pages["blog"], listing_content(pages["blog"], [], blog_extra), site, nav, global_schemas, records, "pages.json:blog", "blog")

    for task, body in published_drafts:
        page = {
            "title": task["title"],
            "h1": task.get("h1", task["title"]),
            "description": task.get("description", task.get("intent", task["title"])),
            "eyebrow": "内容中心",
        }
        article_extra = '<article class="card">' + markdown_to_html(body) + "</article>" + cta_html(DEFAULT_CTA_TITLE, DEFAULT_CTA_TEXT)
        emit(task["target_url"], page, listing_content(page, [], article_extra), site, nav, global_schemas, records, f"content_queue:{task['content_id']}", task.get("page_type", "blog_article"))

    contact_extra = (
        '<article class="card"><h2>通过 Telegram 联系 9HWH</h2><p>'
        + esc(contact["contact_intro"])
        + '</p><h3>适合咨询的问题</h3>'
        + list_items(contact["required_info"])
        + '<p><a class="button button-telegram" href="'
        + TELEGRAM_URL
        + '" target="_blank" rel="noopener noreferrer">打开 Telegram 咨询</a></p>'
        + "<p>该入口为 Telegram 轮换咨询入口，会根据当前可接待账号进行跳转。</p></article>"
        + cta_html("更适合先通过 Telegram 沟通项目情况", "如果你正在准备海外推广、广告投放、引流获客或出海项目冷启动，可以先通过 Telegram 说明项目类型、目标地区、预算范围和现有素材情况。")
        + faq_html(resolve_faqs(faqs, None, "contact"))
    )
    emit("/contact/", pages["contact"], listing_content(pages["contact"], [], contact_extra), site, nav, global_schemas, records, "pages.json:contact", "contact")

    privacy_extra = (
        '<article class="card"><h2>隐私政策</h2><p>9HWH 尊重访问者隐私。本网站不提供站内注册、支付或会员系统。</p>'
        "<p>如果你通过 Telegram 主动发送项目资料，这些信息只会用于沟通海外推广、获客支持和测试准备，不会用于与咨询无关的公开展示。</p>"
        "<p>最后更新：2026-05-06</p></article>"
    )
    emit("/privacy/", pages["privacy"], listing_content(pages["privacy"], [], privacy_extra), site, nav, global_schemas, records, "pages.json:privacy", "legal")

    not_found_extra = f'<p><a class="button button-primary" href="/">返回首页</a> <a class="button button-secondary" href="/services/">查看服务</a> <a class="button button-telegram" href="{TELEGRAM_URL}" target="_blank" rel="noopener noreferrer">Telegram 咨询</a></p>'
    emit("/404.html", pages["404"], listing_content(pages["404"], [], not_found_extra), site, nav, global_schemas, records, "pages.json:404", "utility", indexable=False)

    check_duplicate_urls(records)
    write_sitemap(records, date.today().isoformat())
    write_file("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: https://www.9hwh.com/sitemap.xml\n")
    write_cloudflare_pages_files()
    write_inventory(records)
    print(f"[OK] Generated {len(records)} indexed pages into {PUBLIC}")


if __name__ == "__main__":
    build()
