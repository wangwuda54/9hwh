from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY9_ROOT = Path("E:/py9")
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_QUEUE_PATH = CONTENT_DIR / "content_queue.json"
CONTENT_RULES_PATH = CONTENT_DIR / "content_rules.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
INBOX_DIR = ROOT / "data" / "deepseek-inbox"
ASSETS_DIR = ROOT / "data" / "content-assets"
DOCS_DIR = ROOT / "docs"
REPORT_JSON = ASSETS_DIR / "deepseek_generation_report.json"
REPORT_MD = DOCS_DIR / "deepseek-generation-report.md"

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
CONFIG_FIELD_NAMES = ("DEEPSEEK_BASE_URL", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate 9HWH SEO content drafts with DeepSeek API.")
    parser.add_argument("--limit", type=int, default=30, help="Maximum prompt_ready tasks to generate.")
    parser.add_argument("--dry-run", action="store_true", help="Preview selected tasks without API calls or writes.")
    parser.add_argument("--only-content-id", help="Generate one content_id only.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing inbox files or draft files.")
    parser.add_argument("--model", help="DeepSeek model name. Defaults to env/config model.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Sleep between successful generations.")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum API attempts per item.")
    return parser.parse_args()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_python_config_fields(path: Path) -> dict[str, object]:
    module = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    fields: dict[str, object] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name not in CONFIG_FIELD_NAMES:
            continue
        try:
            fields[name] = ast.literal_eval(node.value)
        except Exception:
            continue
    return fields


def discover_deepseek_config() -> tuple[dict[str, object], str]:
    env_config = {
        "DEEPSEEK_BASE_URL": os.environ.get("DEEPSEEK_BASE_URL", ""),
        "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
        "DEEPSEEK_MODEL": os.environ.get("DEEPSEEK_MODEL", ""),
    }
    if env_config["DEEPSEEK_API_KEY"]:
        return env_config, "environment"

    candidates = [
        PY9_ROOT / "config.py",
        PY9_ROOT / "系统配置" / "deepseek.json",
        PY9_ROOT / "deepseek.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        if path.suffix.lower() == ".py":
            fields = read_python_config_fields(path)
        else:
            raw = read_json(path)
            if isinstance(raw, dict) and isinstance(raw.get("deepseek"), dict):
                raw = raw["deepseek"]
            fields = {name: raw.get(name, "") for name in CONFIG_FIELD_NAMES if isinstance(raw, dict)}
        if fields.get("DEEPSEEK_API_KEY"):
            return fields, str(path)
    return env_config, "not_found"


def normalize_endpoint(base_url: str) -> str:
    base_url = (base_url or DEFAULT_BASE_URL).strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return base_url + "/chat/completions"


def normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def front_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(normalize_list(value))
    return str(value or "").strip()


def load_tasks(args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    queue = read_json(CONTENT_QUEUE_PATH)
    candidates = [item for item in queue if item.get("status") == "prompt_ready"]
    if args.only_content_id:
        candidates = [item for item in candidates if item.get("content_id") == args.only_content_id]

    selected: list[dict] = []
    skipped: list[dict] = []
    for item in candidates:
        content_id = item["content_id"]
        inbox_path = INBOX_DIR / f"{content_id}.md"
        draft_path = DRAFTS_DIR / f"{content_id}.md"
        if not args.overwrite and inbox_path.exists():
            skipped.append({"content_id": content_id, "reason": "inbox file already exists"})
            continue
        if not args.overwrite and draft_path.exists():
            skipped.append({"content_id": content_id, "reason": "draft file already exists"})
            continue
        selected.append(item)
        if len(selected) >= args.limit:
            break
    return selected, skipped


def system_prompt(rules: dict) -> str:
    prompt_rules = "\n".join(f"- {rule}" for rule in rules.get("deepseek_prompt_rules", []))
    return f"""你是 9HWH 自建站 SEO 内容写手。

当前内容规则：
{prompt_rules}

写作边界：
- 这是自建站 SEO 内容，不是广告平台投放素材。
- 不设置禁词，不做词级回避，不把客户真实搜索词当成禁止内容。
- 不要套用旧批次的固定服务边界、禁词或合规免责声明口径。
- 不要输出 HTML，只输出完整 Markdown。
"""


def user_prompt(item: dict) -> str:
    internal_links = normalize_list(item.get("internal_links"))
    target_service = (item.get("target_service") or "").strip()
    target_topic = (item.get("target_topic") or "").strip()
    preferred_links = []
    if target_service:
        preferred_links.append(target_service)
    if target_topic:
        preferred_links.append(target_topic)
    preferred_links.extend(internal_links)
    preferred_links = list(dict.fromkeys(link for link in preferred_links if link))

    return f"""请为 9HWH 官网生成一篇完整 Markdown 文章。

必须保留以下字段，不允许改写：
- content_id: {item['content_id']}
- title: {item['title']}
- description: {item.get('description', '')}
- target_url: {item['target_url']}
- primary_keyword: {item['primary_keyword']}
- secondary_keywords: {front_value(item.get('secondary_keywords'))}

Front matter 必须完全使用以下格式，status 必须是 draft_received：
---
content_id: {item['content_id']}
title: {item['title']}
description: {item.get('description', '')}
target_url: {item['target_url']}
primary_keyword: {item['primary_keyword']}
secondary_keywords: {front_value(item.get('secondary_keywords'))}
status: draft_received
---

正文要求：
- 正文从 ## 开始，不要使用 # 一级标题。
- 至少 800 个中文字符。
- 多写客户真实问题、推广准备、素材准备、落地页承接、预算测试、线索质量、渠道判断、怎么开始测试。
- 至少 4 个站内 Markdown 链接。
- 必须包含 /contact/。
- 必须包含 /services/ 或具体服务页。
- 必须包含 /topics/ 或具体 topic 页。
- 优先使用这些内链：{', '.join(preferred_links)}
- 保留客户真实搜索词：{item['primary_keyword']}
- 不输出 HTML。
"""


def call_deepseek(api_key: str, endpoint: str, model: str, messages: list[dict], timeout: int = 120) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def split_front_matter(markdown: str) -> tuple[dict[str, str], str]:
    text = markdown.strip()
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"(?s)^---\s*\n(.*?)\n---\s*\n?(.*)$", text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, match.group(2).strip()


def canonical_markdown(item: dict, generated: str) -> tuple[str, list[str]]:
    _, body = split_front_matter(generated)
    issues: list[str] = []
    if body.startswith("# "):
        issues.append("body starts with H1")
    if len(body) < 800:
        issues.append("body shorter than 800 characters")
    links = set(re.findall(r"\]\((/[^)\s]+)\)", body))
    if len(links) < 4:
        issues.append("less than 4 internal links")
    if "/contact/" not in links:
        issues.append("missing /contact/ link")
    if not any(link == "/services/" or link.startswith("/services/") for link in links):
        issues.append("missing service link")
    if not any(link == "/topics/" or link.startswith("/topics/") for link in links):
        issues.append("missing topic link")
    if item.get("primary_keyword") and item["primary_keyword"] not in body[:1200] and item["primary_keyword"] not in item["title"]:
        issues.append("primary keyword missing from opening body")

    markdown = "\n".join(
        [
            "---",
            f"content_id: {item['content_id']}",
            f"title: {item['title']}",
            f"description: {item.get('description', '')}",
            f"target_url: {item['target_url']}",
            f"primary_keyword: {item['primary_keyword']}",
            f"secondary_keywords: {front_value(item.get('secondary_keywords'))}",
            "status: draft_received",
            "---",
            "",
            body,
            "",
        ]
    )
    return markdown, issues


def write_report(report: dict) -> None:
    write_json(REPORT_JSON, report)
    rows = [
        "# DeepSeek Generation Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- dry_run: {report['dry_run']}",
        f"- requested_limit: {report['requested_limit']}",
        f"- selected_count: {report['selected_count']}",
        f"- generated_count: {report['generated_count']}",
        f"- skipped_count: {report['skipped_count']}",
        f"- failed_count: {report['failed_count']}",
        f"- model: {report['model']}",
        "",
        "## Generated Items",
        "",
        "| content_id | title | output |",
        "| --- | --- | --- |",
    ]
    for item in report["generated_items"]:
        rows.append(f"| {item['content_id']} | {item['title']} | {item['output_file']} |")
    rows.extend(["", "## Skipped Items", "", "| content_id | reason |", "| --- | --- |"])
    for item in report["skipped_items"]:
        rows.append(f"| {item.get('content_id', '')} | {item.get('reason', '')} |")
    rows.extend(["", "## Failed Items", "", "| content_id | reason |", "| --- | --- |"])
    for item in report["failed_items"]:
        rows.append(f"| {item.get('content_id', '')} | {item.get('reason', '')} |")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        print("[FAIL] limit must be non-negative")
        return 1
    rules = read_json(CONTENT_RULES_PATH)
    selected, skipped = load_tasks(args)
    config, config_source = discover_deepseek_config()
    model = args.model or str(config.get("DEEPSEEK_MODEL") or DEFAULT_MODEL)

    dry_report = {
        "dry_run": True,
        "requested_limit": args.limit,
        "selected_count": len(selected),
        "generated_count": 0,
        "skipped_count": len(skipped),
        "failed_count": 0,
        "selected_items": [
            {"content_id": item["content_id"], "title": item["title"], "target_url": item["target_url"]}
            for item in selected
        ],
        "generated_items": [],
        "skipped_items": skipped,
        "failed_items": [],
        "model": model,
        "config_source": config_source,
    }
    if args.dry_run:
        print(json.dumps(dry_report, ensure_ascii=False, indent=2))
        return 0

    api_key = str(config.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        print("[FAIL] DEEPSEEK_API_KEY is not set in environment or supported config.")
        return 1
    endpoint = normalize_endpoint(str(config.get("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL))

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    generated_items: list[dict] = []
    failed_items: list[dict] = []
    prompts = [{"role": "system", "content": system_prompt(rules)}]

    for item in selected:
        content_id = item["content_id"]
        last_error = ""
        for attempt in range(1, args.max_retries + 1):
            try:
                generated = call_deepseek(
                    api_key,
                    endpoint,
                    model,
                    prompts + [{"role": "user", "content": user_prompt(item)}],
                )
                markdown, issues = canonical_markdown(item, generated)
                if issues:
                    last_error = "; ".join(issues)
                    continue
                output_path = INBOX_DIR / f"{content_id}.md"
                output_path.write_text(markdown, encoding="utf-8", newline="\n")
                generated_items.append(
                    {
                        "content_id": content_id,
                        "title": item["title"],
                        "target_url": item["target_url"],
                        "output_file": output_path.relative_to(ROOT).as_posix(),
                    }
                )
                last_error = ""
                break
            except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
                last_error = f"attempt {attempt}: {exc}"
                time.sleep(max(args.sleep_seconds, 0))
        if last_error:
            failed_items.append({"content_id": content_id, "title": item["title"], "reason": last_error})
        time.sleep(max(args.sleep_seconds, 0))

    report = {
        "generated_at": iso_now(),
        "dry_run": False,
        "requested_limit": args.limit,
        "selected_count": len(selected),
        "generated_count": len(generated_items),
        "skipped_count": len(skipped),
        "failed_count": len(failed_items),
        "generated_items": generated_items,
        "skipped_items": skipped,
        "failed_items": failed_items,
        "model": model,
        "config_source": config_source,
    }
    write_report(report)
    print(
        f"[OK] selected {len(selected)}, generated {len(generated_items)}, "
        f"skipped {len(skipped)}, failed {len(failed_items)}"
    )
    return 1 if failed_items and not generated_items else 0


if __name__ == "__main__":
    sys.exit(main())
