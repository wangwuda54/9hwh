from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
QUEUE_PATH = CONTENT_DIR / "content_queue.json"
STATUS_PATH = CONTENT_DIR / "content_status.json"
LOG_PATH = ROOT / "data" / "content-assets" / "status_update_log.jsonl"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
BATCHES_DIR = ROOT / "data" / "deepseek-batches"

ALLOWED = ["planned", "prompt_ready", "writing", "draft_received", "reviewed", "published", "paused"]
ORDER = {status: index for index, status in enumerate(ALLOWED)}


def load_queue() -> list[dict]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))


def write_queue(queue: list[dict]) -> None:
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_status_summary(queue: list[dict]) -> None:
    counts = {
        "total_planned": len(queue),
        "prompt_ready": 0,
        "writing": 0,
        "draft_received": 0,
        "reviewed": 0,
        "published": 0,
        "paused": 0,
        "last_generated_at": date.today().isoformat(),
    }
    for item in queue:
        status = item.get("status")
        if status in counts:
            counts[status] += 1
    STATUS_PATH.write_text(json.dumps(counts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_log(content_id: str, old: str, new: str, scope: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(
            json.dumps(
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "content_id": content_id,
                    "old": old,
                    "new": new,
                    "scope": scope,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def validate_transition(old: str, new: str) -> None:
    if new == "published" and old not in {"reviewed", "published"}:
        raise SystemExit("[FAIL] published requires manual reviewed status first")
    if new == "reviewed" and old not in {"draft_received", "reviewed"}:
        raise SystemExit("[FAIL] reviewed requires imported draft_received content first")
    if new != "paused" and ORDER[new] < ORDER.get(old, 0):
        raise SystemExit("[FAIL] cannot move status backwards unless pausing manually")


def parse_md(path: Path) -> tuple[list[str], int | None]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        return lines, None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            break
        if lines[index].startswith("status:"):
            return lines, index
    return lines, None


def update_draft_front_matter(content_id: str, new_status: str) -> None:
    path = DRAFTS_DIR / f"{content_id}.md"
    if not path.exists():
        return
    lines, status_index = parse_md(path)
    if status_index is None:
        return
    lines[status_index] = f"status: {new_status}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def load_batch_content_ids(batch_id: str) -> list[str]:
    batch_dir = BATCHES_DIR / batch_id
    index_path = batch_dir / f"{batch_id}-index.json"
    if not index_path.exists():
        raise SystemExit(f"[FAIL] batch index not found: {index_path}")
    batch_items = json.loads(index_path.read_text(encoding="utf-8-sig"))
    return [item["content_id"] for item in batch_items if item.get("content_id")]


def update_one(queue: list[dict], content_id: str, new_status: str, expected_old: str | None, scope: str) -> str:
    for item in queue:
        if item.get("content_id") != content_id:
            continue
        if item.get("internal_only"):
            raise SystemExit(f"[FAIL] internal_only content cannot change via this flow: {content_id}")
        old = item.get("status", "")
        if expected_old and old != expected_old:
            raise SystemExit(f"[FAIL] {content_id} expected {expected_old}, got {old}")
        validate_transition(old, new_status)
        item["status"] = new_status
        update_draft_front_matter(content_id, new_status)
        append_log(content_id, old, new_status, scope)
        return old
    raise SystemExit(f"[FAIL] content_id not found: {content_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update content status for one item or a whole batch.")
    parser.add_argument("--content-id", help="Single content_id to update.")
    parser.add_argument("--status", choices=ALLOWED, help="Target status for single-item mode.")
    parser.add_argument("--batch", help="Batch id such as batch-001.")
    parser.add_argument("--from", dest="from_status", choices=ALLOWED, help="Required current status for batch mode.")
    parser.add_argument("--to", dest="to_status", choices=ALLOWED, help="Target status for batch mode.")
    args = parser.parse_args()
    if bool(args.content_id) == bool(args.batch):
        raise SystemExit("[FAIL] choose exactly one mode: single content-id or batch")
    if args.content_id and not args.status:
        raise SystemExit("[FAIL] single-item mode requires --status")
    if args.batch and (not args.from_status or not args.to_status):
        raise SystemExit("[FAIL] batch mode requires both --from and --to")
    return args


def main() -> int:
    args = parse_args()
    queue = load_queue()
    changed: list[tuple[str, str, str]] = []

    if args.content_id:
        old = update_one(queue, args.content_id, args.status, None, "single")
        changed.append((args.content_id, old, args.status))
    else:
        content_ids = load_batch_content_ids(args.batch)
        seen_ids = set()
        for content_id in content_ids:
            if content_id in seen_ids:
                raise SystemExit(f"[FAIL] duplicate content_id in batch: {content_id}")
            seen_ids.add(content_id)
            old = update_one(queue, content_id, args.to_status, args.from_status, args.batch)
            changed.append((content_id, old, args.to_status))

    write_queue(queue)
    write_status_summary(queue)
    for content_id, old, new in changed:
        print(f"[OK] {content_id}: {old} -> {new}")
    print(f"[OK] updated {len(changed)} item(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
