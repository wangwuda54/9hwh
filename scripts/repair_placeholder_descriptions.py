from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
REPORT_JSON = ROOT / "data" / "content-assets" / "placeholder_description_repair.json"
REPORT_MD = ROOT / "docs" / "placeholder-description-repair-report.md"
PLACEHOLDER_RE = re.compile(r"\?{8,}")


def is_bad_description(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    compact = re.sub(r"\s+", "", text)
    return bool(compact) and set(compact) == {"?"}


def has_placeholder_text(value: str) -> bool:
    return bool(PLACEHOLDER_RE.search(str(value or "")))


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str], str]:
    if not text.startswith("---"):
        return {}, [], text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, [], text
    front = parts[1]
    body = parts[2]
    meta: dict[str, str] = {}
    lines = front.splitlines()
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, lines, body


def render_frontmatter(lines: list[str], key: str, value: str) -> list[str]:
    output = []
    replaced = False
    for line in lines:
        if line.startswith(f"{key}:"):
            output.append(f"{key}: {value}")
            replaced = True
        else:
            output.append(line)
    if not replaced:
        insert_at = 0
        for index, line in enumerate(output):
            if line.startswith("title:"):
                insert_at = index + 1
                break
        output.insert(insert_at, f"{key}: {value}")
    return output


def make_description(meta: dict[str, str]) -> str:
    title = meta.get("title") or meta.get("h1") or meta.get("primary_keyword") or "海外推广内容"
    keyword = meta.get("primary_keyword") or title.split("：", 1)[0]

    if "费用" in title or "价格" in title or "成本" in title:
        return (
            f"{title}，围绕真实搜索需求梳理影响费用的核心因素、测试预算、渠道选择、素材与落地页准备，"
            "帮助出海团队合理评估推广成本和咨询沟通重点。"
        )

    if "怎么做" in title:
        return (
            f"{title}，围绕真实搜索需求梳理推广路径、渠道判断、素材测试、落地页承接和咨询转化准备，"
            "帮助出海团队先小预算测试再持续优化。"
        )

    if keyword and keyword != title:
        return (
            f"本文围绕{keyword}，梳理海外推广与获客测试的准备重点、渠道判断、素材方向和落地页承接方式，"
            "帮助团队在咨询前形成清晰执行路径。"
        )

    return (
        f"{title}，梳理海外推广与获客测试的准备重点、渠道判断、素材方向和落地页承接方式，"
        "帮助团队在咨询前形成清晰执行路径。"
    )


def repair_file(path: Path, write: bool) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    meta, lines, body = parse_frontmatter(text)
    old_description = meta.get("description", "")
    needs_repair = is_bad_description(old_description) or has_placeholder_text(old_description)

    result = {
        "file": path.relative_to(ROOT).as_posix(),
        "content_id": meta.get("content_id", ""),
        "title": meta.get("title", ""),
        "old_description": old_description,
        "new_description": "",
        "repaired": False,
        "reason": "",
    }

    if not meta:
        result["reason"] = "missing frontmatter"
        return result
    if not needs_repair:
        result["reason"] = "description ok"
        return result

    new_description = make_description(meta)
    new_lines = render_frontmatter(lines, "description", new_description)
    new_text = "---\n" + "\n".join(new_lines).strip() + "\n---" + body
    result["new_description"] = new_description
    result["repaired"] = True
    result["reason"] = "placeholder description repaired"

    if write:
        path.write_text(new_text, encoding="utf-8", newline="\n")
    return result


def write_report(results: list[dict], write: bool) -> None:
    repaired = [item for item in results if item.get("repaired")]
    remaining = [item for item in results if item.get("repaired") and has_placeholder_text(item.get("new_description", ""))]
    report = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "write": write,
        "checked_count": len(results),
        "repaired_count": len(repaired),
        "remaining_placeholder_count": len(remaining),
        "repaired_items": repaired,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "# Placeholder Description Repair Report",
        "",
        f"- write: {write}",
        f"- checked_count: {len(results)}",
        f"- repaired_count: {len(repaired)}",
        f"- remaining_placeholder_count: {len(remaining)}",
        "",
        "| File | Title | New Description |",
        "| --- | --- | --- |",
    ]
    for item in repaired:
        rows.append(f"| {item['file']} | {item.get('title', '')} | {item.get('new_description', '')} |")
    REPORT_MD.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair placeholder article descriptions in 9HWH markdown drafts.")
    parser.add_argument("--write", action="store_true", help="Write repaired descriptions back to files.")
    parser.add_argument("--fail-on-remaining", action="store_true", help="Fail if placeholder descriptions remain after repair.")
    args = parser.parse_args()

    if not DRAFTS_DIR.exists():
        print(f"[OK] drafts directory does not exist: {DRAFTS_DIR}")
        return 0

    results = []
    for path in sorted(DRAFTS_DIR.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        results.append(repair_file(path, args.write))

    write_report(results, args.write)
    repaired_count = sum(1 for item in results if item.get("repaired"))
    print(f"[OK] checked {len(results)} draft(s); repaired {repaired_count} placeholder description(s)")

    if args.fail_on_remaining:
        remaining = []
        for path in sorted(DRAFTS_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8-sig")
            meta, _, _ = parse_frontmatter(text)
            description = meta.get("description", "")
            if is_bad_description(description) or has_placeholder_text(description):
                remaining.append(path.relative_to(ROOT).as_posix())
        if remaining:
            for item in remaining:
                print(f"[FAIL] placeholder description remains: {item}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
