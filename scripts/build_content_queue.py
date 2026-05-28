from __future__ import annotations

import json
import re
import hashlib
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DATA = ROOT / "site_src" / "data" / "content"
KEYWORD_ASSETS = ROOT / "data" / "keyword-assets"
CONTENT_ASSETS = ROOT / "data" / "content-assets"
DOCS = ROOT / "docs"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def slugify(text: str) -> str:
    mapping = {
        "TK": "tk",
        "FB": "fb",
        "谷歌": "google",
        "虚拟币": "crypto",
        "币圈": "crypto",
        "交易所": "exchange",
        "交友": "dating",
        "游戏": "game",
        "贷款": "loan",
        "保险": "insurance",
        "移民": "immigration",
        "网赚": "online-work",
        "兼职": "part-time",
        "推广": "promotion",
        "引流": "traffic",
        "获客": "leads",
        "拉新": "acquisition",
        "投放": "ads",
        "买量": "media-buying",
        "费用": "cost",
        "价格": "price",
        "渠道": "channels",
        "平台": "platforms",
        "怎么做": "how-to",
        "怎么投": "how-to-run",
        "怎么找": "how-to-find",
        "多少钱": "cost",
        "报价": "quote",
        "哪家好": "provider",
        "靠谱吗": "reliable",
        "怎么收费": "pricing"
    }
    result = text
    for key, value in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(key, "-" + value + "-")
    result = re.sub(r"[^a-zA-Z0-9-]+", "-", result).strip("-").lower()
    result = re.sub(r"-+", "-", result)
    return result or "content"


def stable_suffix(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def page_type_for(record: dict) -> str:
    if record["public_status"] == "future_blog":
        return "blog_article"
    if record["cluster_id"].endswith("promotion") or record["cluster_id"].endswith("traffic") or record["cluster_id"].endswith("leads"):
        return "topic_expansion"
    if record["cluster_id"] in {"traffic-acquisition", "ad-campaign-support", "media-buying", "overseas-promotion"}:
        return "service_support"
    if record["cluster_id"] in {"tk-promotion", "fb-promotion", "google-promotion"}:
        return "platform_support"
    return "blog_article"


def base_path_for(page_type: str, cluster_id: str) -> str:
    if page_type == "blog_article":
        return "/blog/"
    if page_type == "service_support":
        return "/blog/services/"
    if page_type == "platform_support":
        return "/blog/platforms/"
    if page_type == "topic_expansion":
        return "/blog/topics/"
    return "/blog/"


def title_for(keyword: str, cluster_id: str) -> str:
    if any(suffix in keyword for suffix in ("怎么做", "怎么投", "怎么找")):
        return f"{keyword}：推广路径、渠道判断和准备清单"
    if any(suffix in keyword for suffix in ("费用", "价格", "多少钱", "报价", "怎么收费")):
        return f"{keyword}：影响因素、预算准备和沟通要点"
    if "哪家好" in keyword or "靠谱吗" in keyword:
        return f"{keyword}：选择判断、合规评估和风险提示"
    return f"{keyword}：海外推广与获客准备指南"


def choose_records(records: list[dict], rules: dict) -> list[dict]:
    suffix_priority = ["怎么做", "费用", "价格", "渠道", "哪家好", "靠谱吗", "怎么收费", "怎么投", "怎么找", "多少钱", "报价"]
    allowed = [item for item in records if item["public_status"] in {"future_blog", "public_secondary"} and item["cluster_id"] not in {"blocked", "unmapped"}]
    scored = []
    for item in allowed:
        score = 0
        for index, suffix in enumerate(suffix_priority):
            if suffix in item["keyword"]:
                score += 100 - index
        if item["public_status"] == "future_blog":
            score += 20
        if item["intent"] in rules.get("high_priority_intents", []):
            score += 10
        scored.append((score, item["cluster_id"], item["keyword"], item))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    max_count = int(rules.get("max_new_content_per_batch", 60))
    per_cluster_limit = max(3, max_count // 10)
    selected = []
    cluster_counts = Counter()
    for _, _, _, item in scored:
        if len(selected) >= max_count:
            break
        if cluster_counts[item["cluster_id"]] >= per_cluster_limit:
            continue
        cluster_counts[item["cluster_id"]] += 1
        selected.append(item)
    return selected


def build_queue(selected: list[dict], clusters: list[dict], rules: dict) -> list[dict]:
    cluster_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
    queue = []
    for index, record in enumerate(selected, start=1):
        cluster = cluster_by_id.get(record["cluster_id"], {})
        page_type = page_type_for(record)
        slug = f"{slugify(record['keyword'])}-{stable_suffix(record['keyword'])}"
        content_id = f"c{index:03d}-{record['cluster_id']}-{slug}"[:110]
        target_url = base_path_for(page_type, record["cluster_id"]) + slug + "/"
        secondary = [record["category"], record["platform"], record["country"], record["action"], record["suffix"]]
        secondary = [item for item in secondary if item and item != record["keyword"]][:6]
        status = "prompt_ready" if index <= 20 else "planned"
        queue.append({
            "content_id": content_id,
            "target_url": target_url,
            "title": title_for(record["keyword"], record["cluster_id"]),
            "h1": title_for(record["keyword"], record["cluster_id"]),
            "intent": record["intent"],
            "cluster_id": record["cluster_id"],
            "primary_keyword": record["keyword"],
            "secondary_keywords": secondary,
            "source_keywords": [record["keyword"]],
            "page_type": page_type,
            "status": status,
            "priority": index,
            "word_count_target": rules.get("default_word_count", 1800),
            "deepseek_required": true_value(),
            "target_service": cluster.get("target_url", "") if cluster.get("page_type") == "service" else "",
            "target_topic": cluster.get("target_url", "") if cluster.get("page_type") == "topic" else "",
            "internal_links": [cluster.get("target_url", ""), "/services/", "/topics/", "/contact/"],
            "risk_level": "low" if record["public_status"] == "future_blog" else "medium",
            "notes": "内容任务，不等于公开页面；正文后续由 DeepSeek 生成，Codex 负责接入和检查。"
        })
    return queue


def true_value() -> bool:
    return True


def write_outputs(queue: list[dict]) -> None:
    CONTENT_DATA.mkdir(parents=True, exist_ok=True)
    CONTENT_ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    (CONTENT_DATA / "content_queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    status_counts = Counter(item["status"] for item in queue)
    cluster_counts = Counter(item["cluster_id"] for item in queue)
    summary = {
        "total": len(queue),
        "status_counts": dict(status_counts),
        "cluster_counts": dict(cluster_counts),
        "last_generated_at": date.today().isoformat()
    }
    (CONTENT_ASSETS / "content_queue_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    status = {
        "total_planned": len(queue),
        "prompt_ready": status_counts.get("prompt_ready", 0),
        "writing": status_counts.get("writing", 0),
        "draft_received": status_counts.get("draft_received", 0),
        "reviewed": status_counts.get("reviewed", 0),
        "published": status_counts.get("published", 0),
        "paused": status_counts.get("paused", 0),
        "last_generated_at": date.today().isoformat()
    }
    (CONTENT_DATA / "content_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = ["# 内容机会报告", "", f"- 任务总数：{len(queue)}", f"- prompt_ready：{status_counts.get('prompt_ready', 0)}", f"- planned：{status_counts.get('planned', 0)}", "", "| content_id | primary_keyword | cluster_id | status | target_url |", "| --- | --- | --- | --- | --- |"]
    for item in queue:
        rows.append(f"| {item['content_id']} | {item['primary_keyword']} | {item['cluster_id']} | {item['status']} | {item['target_url']} |")
    (DOCS / "content-opportunity-report.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    rules = load_json(CONTENT_DATA / "content_rules.json")
    clusters = load_json(ROOT / "site_src" / "data" / "keywords" / "clusters.json")
    records = read_jsonl(KEYWORD_ASSETS / "keyword_pool.jsonl")
    selected = choose_records(records, rules)
    queue = build_queue(selected, clusters, rules)
    write_outputs(queue)
    print(f"[OK] generated {len(queue)} content tasks")
    print(f"[OK] prompt_ready: {sum(1 for item in queue if item['status'] == 'prompt_ready')}")
    print(f"[OK] planned: {sum(1 for item in queue if item['status'] == 'planned')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
