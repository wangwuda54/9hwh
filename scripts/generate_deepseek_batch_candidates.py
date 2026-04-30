from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
BATCH_ROOT = ROOT / "data" / "deepseek-batches"

PREFERRED_CLUSTERS = [
    "crypto-promotion",
    "dating-traffic",
    "traffic-acquisition",
    "media-buying",
    "game-promotion",
    "loan-leads",
    "insurance-leads",
    "immigration-leads",
    "fb-promotion",
    "google-promotion",
    "markets",
]
ELIGIBLE_STATUSES = {"planned", "prompt_ready"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def used_batch_items() -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    urls: set[str] = set()
    if not BATCH_ROOT.exists():
        return ids, urls
    for index_path in sorted(BATCH_ROOT.glob("batch-*/batch-*-index.json")):
        for item in load_json(index_path):
            ids.add(item.get("content_id", ""))
            urls.add(item.get("target_url", ""))
    return ids, urls


def score(item: dict) -> tuple[int, int, str]:
    status_score = 50 if item.get("status") == "prompt_ready" else 20
    risk_score = 10 if item.get("risk_level") == "low" else 0
    priority_score = max(0, 100 - int(item.get("priority", 999)))
    return status_score + risk_score + priority_score, -len(item.get("primary_keyword", "")), item.get("content_id", "")


def select_candidates(queue: list[dict], limit: int) -> list[dict]:
    used_ids, used_urls = used_batch_items()
    eligible = [
        item
        for item in queue
        if item.get("status") in ELIGIBLE_STATUSES
        and not item.get("internal_only")
        and item.get("content_id") not in used_ids
        and item.get("target_url") not in used_urls
    ]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in eligible:
        grouped[item.get("cluster_id", "")].append(item)
    for items in grouped.values():
        items.sort(key=score, reverse=True)

    selected: list[dict] = []
    seen_ids: set[str] = set()
    cluster_counts: Counter[str] = Counter()
    max_per_cluster = 2
    for cluster in PREFERRED_CLUSTERS:
        for item in grouped.get(cluster, [])[:max_per_cluster]:
            if item["content_id"] in seen_ids:
                continue
            selected.append(item)
            seen_ids.add(item["content_id"])
            cluster_counts[cluster] += 1
            if len(selected) >= limit:
                return selected
    if len(selected) < limit:
        for item in sorted(eligible, key=score, reverse=True):
            if item["content_id"] in seen_ids:
                continue
            if cluster_counts[item.get("cluster_id", "")] >= max_per_cluster:
                continue
            selected.append(item)
            seen_ids.add(item["content_id"])
            cluster_counts[item.get("cluster_id", "")] += 1
            if len(selected) >= limit:
                break
    return selected


def candidate_record(item: dict, batch_id: str) -> dict:
    return {
        "batch_id": batch_id,
        "candidate_only": True,
        "content_id": item["content_id"],
        "target_url": item["target_url"],
        "title": item["title"],
        "primary_keyword": item["primary_keyword"],
        "secondary_keywords": item.get("secondary_keywords", []),
        "cluster_id": item.get("cluster_id", ""),
        "status": item.get("status", ""),
        "risk_level": item.get("risk_level", ""),
        "page_type": item.get("page_type", ""),
        "internal_links": item.get("internal_links", []),
        "reason": "candidate for next DeepSeek batch; not a formal task package",
    }


def write_candidates(batch_id: str, candidates: list[dict]) -> None:
    out_dir = BATCH_ROOT / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)
    records = [candidate_record(item, batch_id) for item in candidates]
    (out_dir / f"{batch_id}-candidates.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    rows = [
        f"# DeepSeek {batch_id} Candidate List",
        "",
        f"- generated_at: {date.today().isoformat()}",
        f"- candidate_count: {len(records)}",
        "- status: candidate_only",
        "- note: this is not a formal DeepSeek task package and should not be sent directly.",
        "",
        "| content_id | title | cluster | risk | target_url |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in records:
        rows.append(f"| {item['content_id']} | {item['title']} | {item['cluster_id']} | {item['risk_level']} | {item['target_url']} |")
    (out_dir / f"{batch_id}-candidates.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate candidate-only DeepSeek batch lists.")
    parser.add_argument("--batch-id", default="batch-002")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()
    if args.limit < 1:
        raise SystemExit("[FAIL] --limit must be positive")
    queue = load_json(QUEUE_PATH)
    candidates = select_candidates(queue, args.limit)
    write_candidates(args.batch_id, candidates)
    print(f"[OK] generated {len(candidates)} candidates for {args.batch_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
