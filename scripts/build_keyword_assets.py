from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KEYWORD_DATA = ROOT / "site_src" / "data" / "keywords"
OUTPUT = ROOT / "data" / "keyword-assets"
DOCS = ROOT / "docs"


def load_json(name: str):
    return json.loads((KEYWORD_DATA / name).read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_if_clean(records: dict[str, dict], record: dict) -> None:
    keyword = record["keyword"].strip()
    if not keyword:
        return
    records.setdefault(keyword, record)


def join_keyword(*parts: str) -> str:
    keyword = "".join(part for part in parts if part)
    for dup in ("推广推广", "引流引流", "获客获客", "拉新拉新", "投放投放", "买量买量", "投流投流", "代投代投"):
        keyword = keyword.replace(dup, dup[: len(dup) // 2])
    return keyword


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term and term in text for term in terms)


def cluster_for(keyword: str, category: str, platform: str, country: str, action: str, suffix: str, clusters: list[dict], explicit_map: dict[str, dict]) -> dict | None:
    if keyword in explicit_map:
        mapped = explicit_map[keyword]
        for cluster in clusters:
            if cluster["cluster_id"] == mapped["cluster_id"]:
                return cluster
    candidates = []
    for cluster in clusters:
        score = 0
        if category and category in cluster.get("include_categories", []):
            score += 4
        if platform and platform in cluster.get("include_platforms", []):
            score += 3
        if country and country in cluster.get("include_countries", []):
            score += 2
        if action and action in cluster.get("include_actions", []):
            score += 2
        if suffix and suffix in cluster.get("include_suffixes", []):
            score += 1
        if score:
            candidates.append((score, cluster.get("priority", 0), cluster))
    if not candidates and country:
        candidates.append((1, 0, next(cluster for cluster in clusters if cluster["cluster_id"] == "markets")))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item[0], item[1]), reverse=True)[0][2]


def status_for(keyword: str, category: str, suffix: str, rules: dict, explicit_map: dict[str, dict]) -> str:
    if contains_any(keyword, rules["blocked_promise_terms"]):
        return "blocked"
    if keyword in explicit_map:
        return explicit_map[keyword].get("status", "public_primary")
    if category in rules["sensitive_internal_categories"]:
        return "internal_only"
    if suffix in rules["blog_future_terms"]:
        return "future_blog"
    if category and category not in rules["public_allowed_categories"]:
        return "internal_only"
    return "public_secondary"


def intent_for(cluster: dict | None, suffix: str) -> str:
    if suffix:
        return "long_tail_question"
    if cluster:
        return cluster.get("intent", "")
    return "unmapped"


def make_record(keyword: str, category: str, platform: str, country: str, action: str, suffix: str, clusters: list[dict], rules: dict, explicit_map: dict[str, dict]) -> dict:
    cluster = cluster_for(keyword, category, platform, country, action, suffix, clusters, explicit_map)
    status = status_for(keyword, category, suffix, rules, explicit_map)
    if status == "blocked":
        cluster_id = "blocked"
        target_url = ""
    elif cluster:
        cluster_id = cluster["cluster_id"]
        target_url = cluster["target_url"]
    else:
        cluster_id = "unmapped"
        target_url = ""
        if status != "internal_only":
            status = "future_blog" if suffix else "internal_only"
    return {
        "keyword": keyword,
        "category": category,
        "platform": platform,
        "country": country,
        "action": action,
        "suffix": suffix,
        "intent": intent_for(cluster, suffix),
        "cluster_id": cluster_id,
        "target_url": target_url,
        "public_status": status,
    }


def build_records(seed: dict, rules: dict, clusters: list[dict], url_map: list[dict]) -> list[dict]:
    explicit_map = {item["keyword"]: item for item in url_map}
    records: dict[str, dict] = {}

    for item in url_map:
        append_if_clean(records, make_record(item["keyword"], "", "", "", "", "", clusters, rules, explicit_map))

    for action in rules["homepage_allowed_terms"] + rules["service_allowed_terms"] + rules["topic_allowed_terms"]:
        append_if_clean(records, make_record(action, "", "", "", action, "", clusters, rules, explicit_map))

    for platform in seed["platforms"]:
        for action in seed["actions"]:
            append_if_clean(records, make_record(join_keyword(platform, action), "", platform, "", action, "", clusters, rules, explicit_map))

    for category in seed["categories"]:
        for action in seed["actions"]:
            append_if_clean(records, make_record(join_keyword(category, action), category, "", "", action, "", clusters, rules, explicit_map))
        for platform in seed["platforms"]:
            for action in ("推广", "引流", "获客", "投放", "买量"):
                append_if_clean(records, make_record(join_keyword(platform, category, action), category, platform, "", action, "", clusters, rules, explicit_map))
        for country in seed["countries"]:
            for action in ("推广", "引流", "获客", "投放"):
                append_if_clean(records, make_record(join_keyword(country, category, action), category, "", country, action, "", clusters, rules, explicit_map))
        for suffix in seed["question_suffixes"]:
            append_if_clean(records, make_record(join_keyword(category, suffix), category, "", "", "", suffix, clusters, rules, explicit_map))

    for country in seed["countries"]:
        for action in ("海外推广", "引流获客", "广告投放", "买量投流"):
            append_if_clean(records, make_record(join_keyword(country, action), "", "", country, action, "", clusters, rules, explicit_map))

    for term in rules["blocked_promise_terms"]:
        append_if_clean(records, make_record(term, "", "", "", "", "", clusters, rules, explicit_map))

    return sorted(records.values(), key=lambda item: (item["cluster_id"], item["public_status"], item["keyword"]))


def write_outputs(records: list[dict], clusters: list[dict], url_map: list[dict]) -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    with (OUTPUT / "keyword_pool.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    status_counts = Counter(record["public_status"] for record in records)
    cluster_counts = defaultdict(Counter)
    url_counts = Counter()
    for record in records:
        cluster_counts[record["cluster_id"]][record["public_status"]] += 1
        if record["target_url"]:
            url_counts[record["target_url"]] += 1

    summary = {
        "total_keywords": len(records),
        "status_counts": dict(status_counts),
        "cluster_count": len(clusters),
        "url_mapping_count": len(url_map),
        "target_url_counts": dict(sorted(url_counts.items())),
    }
    write_json(OUTPUT / "keyword_summary.json", summary)

    with (OUTPUT / "keyword_to_url.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["keyword", "cluster_id", "target_url", "public_status", "intent"])
        writer.writeheader()
        for record in records:
            writer.writerow({key: record[key] for key in writer.fieldnames})

    with (OUTPUT / "cluster_summary.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = ["cluster_id", "target_url", "keyword_count", "public_count", "internal_count", "future_blog_count", "blocked_count", "notes"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        cluster_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
        for cluster_id in sorted(cluster_counts):
            counts = cluster_counts[cluster_id]
            cluster = cluster_by_id.get(cluster_id, {})
            writer.writerow({
                "cluster_id": cluster_id,
                "target_url": cluster.get("target_url", ""),
                "keyword_count": sum(counts.values()),
                "public_count": counts["public_primary"] + counts["public_secondary"],
                "internal_count": counts["internal_only"],
                "future_blog_count": counts["future_blog"],
                "blocked_count": counts["blocked"],
                "notes": cluster.get("notes", ""),
            })

    internal = [record["keyword"] for record in records if record["public_status"] == "internal_only"]
    (OUTPUT / "internal_only_keywords.txt").write_text("\n".join(internal) + "\n", encoding="utf-8", newline="\n")

    samples = [record["keyword"] for record in records if record["public_status"] in {"public_primary", "public_secondary"}][:200]
    (OUTPUT / "public_keyword_samples.txt").write_text("\n".join(samples) + "\n", encoding="utf-8", newline="\n")

    write_keyword_docs(records, clusters, url_map, cluster_counts)
    return summary


def write_keyword_docs(records: list[dict], clusters: list[dict], url_map: list[dict], cluster_counts: dict[str, Counter]) -> None:
    rows = ["# 关键词到 URL 映射表", "", "| Keyword / Pattern | Cluster | Target URL | Status | Notes |", "| --- | --- | --- | --- | --- |"]
    for item in url_map:
        rows.append(f"| {item['keyword']} | {item['cluster_id']} | {item['target_url']} | {item['status']} | {item.get('notes', '')} |")
    (DOCS / "keyword-to-url-map.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")

    cluster_by_id = {cluster["cluster_id"]: cluster for cluster in clusters}
    rows = ["# 关键词聚类统计", "", "| cluster_id | target_url | keyword_count | public_count | internal_count | future_blog_count | blocked_count | notes |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for cluster_id in sorted(cluster_counts):
        counts = cluster_counts[cluster_id]
        cluster = cluster_by_id.get(cluster_id, {})
        rows.append(
            f"| {cluster_id} | {cluster.get('target_url', '')} | {sum(counts.values())} | {counts['public_primary'] + counts['public_secondary']} | {counts['internal_only']} | {counts['future_blog']} | {counts['blocked']} | {cluster.get('notes', '')} |"
        )
    (DOCS / "keyword-cluster-summary.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    seed = load_json("seed.json")
    rules = load_json("rules.json")
    clusters = load_json("clusters.json")
    url_map = load_json("url_map.json")
    records = build_records(seed, rules, clusters, url_map)
    summary = write_outputs(records, clusters, url_map)
    print(f"[OK] generated {summary['total_keywords']} keyword assets")
    for status, count in sorted(summary["status_counts"].items()):
        print(f"[OK] {status}: {count}")
    print(f"[OK] clusters: {summary['cluster_count']}")
    print(f"[OK] URL mappings: {summary['url_mapping_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
