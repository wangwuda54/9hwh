from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
LOG_PATH = ROOT / "data" / "content-assets" / "status_update_log.jsonl"
ALLOWED = ["planned", "prompt_ready", "writing", "draft_received", "reviewed", "ready_to_publish", "published", "paused"]
ORDER = {status: index for index, status in enumerate(ALLOWED)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--status", required=True, choices=ALLOWED)
    args = parser.parse_args()
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))
    for item in queue:
        if item["content_id"] != args.content_id:
            continue
        old = item["status"]
        if old == "planned" and args.status == "published":
            raise SystemExit("[FAIL] cannot jump planned -> published")
        if args.status == "published" and old not in {"ready_to_publish", "published"}:
            raise SystemExit("[FAIL] published requires ready_to_publish first")
        if args.status != "paused" and ORDER[args.status] < ORDER.get(old, 0):
            raise SystemExit("[FAIL] cannot move status backwards unless pausing manually")
        item["status"] = args.status
        QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "content_id": args.content_id, "old": old, "new": args.status}, ensure_ascii=False) + "\n")
        print(f"[OK] {args.content_id}: {old} -> {args.status}")
        return 0
    raise SystemExit("[FAIL] content_id not found")


if __name__ == "__main__":
    raise SystemExit(main())
