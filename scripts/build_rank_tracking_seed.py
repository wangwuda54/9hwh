from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
PUBLISH_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "publish_queue.json"
OUTPUT_PATH = ROOT / "data" / "seo" / "rank_tracking_seed.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def infer_content_type(item: dict) -> str:
    if item.get("page_type") == "topic_expansion":
        return "topic"
    if item.get("target_service"):
        return "service"
    if item.get("target_topic"):
        return "topic"
    if any(link.startswith("/platforms/") for link in item.get("internal_links", [])):
        return "platform"
    if item.get("intent") == "long_tail_question":
        return "long_tail"
    return "expert"


def main() -> int:
    queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = {item.get("content_id"): item for item in load_json(PUBLISH_QUEUE_PATH, []) if item.get("content_id")}
    seed = []
    for item in queue:
        if item.get("internal_only"):
            continue
        if item.get("status") not in {"reviewed", "published"}:
            continue
        publish_item = publish_queue.get(item.get("content_id"), {})
        published_date = ""
        index_status = "not_published"
        if item.get("status") == "published":
            published_date = publish_item.get("planned_publish_date", "")
            index_status = "published_not_checked"
        seed.append(
            {
                "content_id": item.get("content_id", ""),
                "target_url": item.get("target_url", ""),
                "primary_keyword": item.get("primary_keyword", ""),
                "secondary_keywords": item.get("secondary_keywords", []),
                "cluster": item.get("cluster_id", ""),
                "content_type": infer_content_type(item),
                "published_date": published_date,
                "index_status": index_status,
                "impressions": None,
                "clicks": None,
                "avg_position": None,
                "conversions": None,
                "checked_at": "",
                "notes": "Seed only. Waiting for manual publication and later Search Console ingestion.",
            }
        )
    seed.sort(key=lambda row: (row["cluster"], row["content_id"]))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] rank tracking seed built: items={len(seed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
