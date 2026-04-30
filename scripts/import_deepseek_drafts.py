from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "data" / "deepseek-inbox"
REVIEWED = ROOT / "data" / "deepseek-reviewed"
DRAFTS = ROOT / "site_src" / "content_drafts"
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
RULES_PATH = ROOT / "site_src" / "data" / "content" / "content_rules.json"
ASSETS = ROOT / "data" / "content-assets"
DOCS = ROOT / "docs"


def parse_md(path: Path) -> tuple[dict, str]:
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


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    REVIEWED.mkdir(parents=True, exist_ok=True)
    DRAFTS.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    queue = {item["content_id"]: item for item in json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))}
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8-sig"))
    imported = []
    errors = []
    for path in INBOX.glob("*.md"):
        meta, body = parse_md(path)
        content_id = meta.get("content_id", "")
        task = queue.get(content_id)
        file_errors = []
        if not task:
            file_errors.append("content_id not found in content_queue")
        if task and meta.get("target_url") != task["target_url"]:
            file_errors.append("target_url mismatch")
        for field in ("title", "description", "primary_keyword"):
            if not meta.get(field):
                file_errors.append(f"missing {field}")
        if len(body) < 800:
            file_errors.append("body too short")
        for term in rules.get("blocked_terms", []):
            if term and (term in body or term in json.dumps(meta, ensure_ascii=False)):
                file_errors.append(f"blocked term: {term}")
        if file_errors:
            errors.append({"file": path.name, "errors": file_errors})
            continue
        target = DRAFTS / f"{content_id}.md"
        normalized = path.read_text(encoding="utf-8-sig").replace("status: draft_received", "status: draft_received")
        target.write_text(normalized, encoding="utf-8", newline="\n")
        shutil.copyfile(path, REVIEWED / path.name)
        imported.append({"file": path.name, "content_id": content_id, "target": target.as_posix()})
    report = {"generated_at": datetime.now().isoformat(timespec="seconds"), "imported": imported, "errors": errors}
    (ASSETS / "import_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    rows = ["# 内容导入报告", "", f"- imported: {len(imported)}", f"- errors: {len(errors)}", "", "## Imported", ""]
    rows.extend(f"- {item['content_id']} from {item['file']}" for item in imported)
    rows.extend(["", "## Errors", ""])
    rows.extend(f"- {item['file']}: {', '.join(item['errors'])}" for item in errors)
    (DOCS / "content-import-report.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] imported {len(imported)} drafts, errors {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
