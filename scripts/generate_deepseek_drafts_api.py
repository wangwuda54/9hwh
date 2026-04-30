from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY9_ROOT = Path("E:/py9")
BATCH_ROOT = ROOT / "data" / "deepseek-batches"
INBOX_ROOT = ROOT / "data" / "deepseek-inbox"
ASSETS = ROOT / "data" / "content-assets"
DOCS = ROOT / "docs"

CONFIG_FIELD_NAMES = (
    "AI_PROVIDER",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_THINKING_ENABLED",
)
REQUIRED_CONFIG_FIELDS = ("DEEPSEEK_BASE_URL", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL")
REQUIRED_META_FIELDS = (
    "content_id",
    "title",
    "description",
    "target_url",
    "primary_keyword",
    "secondary_keywords",
    "status",
)
FORBIDDEN_TERMS = [
    "保证过审",
    "保证不限号",
    "保证效果",
    "保证转化",
    "保证收益",
    "绕过平台政策",
    "规避审核",
    "抗风控",
    "Cloak",
    "仿牌",
    "博彩",
    "黑五类",
    "三不限",
    "违规业务也能做",
    "任何平台都能过",
    "任何行业都能投",
]
SYSTEM_PROMPT = """项目定位：
9HWH 是面向出海项目的海外流量推广与获客支持服务站，围绕 TK、FB、Google 等渠道，提供海外推广、引流获客、广告投放支持、拉新买量、投流代投和代运营协助。

硬性要求：
- 按当前 content_id 输出
- 不要修改 content_id
- 不要修改 title
- 不要修改 target_url
- 不要修改 primary_keyword
- 不要修改 secondary_keywords
- 必须完整输出 front matter
- status 必须是 draft_received
- description 填写 80-150 字
- 正文标题从 ## 开始
- 不要输出 HTML
- 不要使用代码块包裹输出
- 不要编造案例、团队、办公室、联系方式
- 不要出现微信、WhatsApp、Telegram 或任何具体联系方式
- 不要写保证过审、保证效果、保证转化、保证收益
- 不要写绕过平台政策、规避审核、抗风控
- 不要写违法违规承诺
- 不要写 Cloak、仿牌、博彩、黑五类、三不限、违规业务也能做、任何平台都能过、任何行业都能投
- 上述禁用词不要以正面、反面、举例、提醒或复述清单的形式出现在最终成文中，统一改写为“受限或违规项目”“不合规承诺”等泛化表述
- 内容适合长期官网，不要像灰色落地页
- 每篇必须包含服务边界和咨询准备建议
- 至少加入 2 个来自任务包内链建议的站内 Markdown 链接
- 不要额外解释
- 不要输出任务分析
- 不要输出总结
"""


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text.strip()
    try:
        _, front, body = text.split("---", 2)
    except ValueError:
        return {}, text.strip()
    meta: dict[str, str] = {}
    for line in front.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body.strip()


def normalize_secondary_keywords(value: object) -> str:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = [item.strip() for item in str(value or "").split(",") if item.strip()]
    return ", ".join(items)


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


def discover_deepseek_config() -> tuple[dict[str, object], Path]:
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
            raw = load_json(path)
            if isinstance(raw, dict) and "deepseek" in raw and isinstance(raw["deepseek"], dict):
                raw = raw["deepseek"]
            fields = {name: raw.get(name) for name in CONFIG_FIELD_NAMES if isinstance(raw, dict)}
        if all(fields.get(name) not in {None, ""} for name in REQUIRED_CONFIG_FIELDS):
            return fields, path
    missing = ", ".join(REQUIRED_CONFIG_FIELDS)
    raise SystemExit(f"[FAIL] unable to discover DeepSeek config in E:/py9; missing required fields: {missing}")


def batch_paths(batch_id: str) -> tuple[Path, Path]:
    batch_dir = BATCH_ROOT / batch_id
    return batch_dir / f"{batch_id}-tasks.md", batch_dir / f"{batch_id}-index.json"


def load_batch(batch_id: str) -> tuple[str, list[dict]]:
    tasks_path, index_path = batch_paths(batch_id)
    if not tasks_path.exists():
        raise SystemExit(f"[FAIL] missing batch tasks file: {tasks_path}")
    if not index_path.exists():
        raise SystemExit(f"[FAIL] missing batch index file: {index_path}")
    return tasks_path.read_text(encoding="utf-8-sig"), load_json(index_path)


def load_task_texts(batch_text: str, index_items: list[dict]) -> dict[str, str]:
    task_texts: dict[str, str] = {}
    for item in index_items:
        content_id = item["content_id"]
        if f"# 任务：{content_id}" not in batch_text:
            raise SystemExit(f"[FAIL] batch tasks file is missing section marker for {content_id}")
        task_file = ROOT / item["task_file"]
        if not task_file.exists():
            raise SystemExit(f"[FAIL] missing batch task file: {item['task_file']}")
        task_texts[content_id] = task_file.read_text(encoding="utf-8-sig").strip()
    return task_texts


def select_items(index_items: list[dict], only: str | None, limit: int | None) -> list[dict]:
    selected = index_items
    if only:
        selected = [item for item in selected if item["content_id"] == only]
        if not selected:
            raise SystemExit(f"[FAIL] content_id not found in batch index: {only}")
    if limit is not None:
        selected = selected[:limit]
    if not selected:
        raise SystemExit("[FAIL] no batch items selected")
    return selected


def build_messages(task_text: str) -> list[dict[str, str]]:
    user_prompt = (
        "以下是当前 content_id 的完整写作任务。请直接输出最终 Markdown 成品，只输出文章本身。任务里的“禁止表达”部分只用于约束，不要在最终文章中逐项复述或举例这些词。\n\n"
        + task_text
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def extract_message_content(response_payload: dict) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("DeepSeek response missing choices")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part.strip() for part in parts if part.strip()).strip()
    raise RuntimeError("DeepSeek response content format is unsupported")


def call_deepseek(messages: list[dict[str, str]], config_fields: dict[str, object], timeout_sec: int = 240) -> tuple[str, dict]:
    base_url = str(config_fields["DEEPSEEK_BASE_URL"]).rstrip("/")
    api_key = str(config_fields["DEEPSEEK_API_KEY"])
    model_name = str(config_fields["DEEPSEEK_MODEL"]).strip() or "deepseek-v4-flash"
    payload: dict[str, object] = {"model": model_name, "messages": messages}
    if not bool(config_fields.get("DEEPSEEK_THINKING_ENABLED", False)):
        payload["thinking"] = {"type": "disabled"}
    request = urllib.request.Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"DeepSeek request failed: {exc}") from exc
    payload_json = json.loads(response_body)
    return extract_message_content(payload_json), payload_json


def validate_generation(text: str, item: dict) -> list[str]:
    issues: list[str] = []
    if not text.startswith("---"):
        issues.append("missing front matter")
        return issues
    if text.startswith("```"):
        issues.append("output is wrapped in a code fence")
    meta, body = parse_front_matter(text)
    for field in REQUIRED_META_FIELDS:
        if not meta.get(field):
            issues.append(f"missing {field}")
    expected_secondary = normalize_secondary_keywords(item.get("secondary_keywords", []))
    actual_secondary = normalize_secondary_keywords(meta.get("secondary_keywords", ""))
    expected_checks = {
        "content_id": item["content_id"],
        "title": item["title"],
        "target_url": item["target_url"],
        "primary_keyword": item["primary_keyword"],
        "secondary_keywords": expected_secondary,
        "status": "draft_received",
    }
    for field, expected in expected_checks.items():
        actual = actual_secondary if field == "secondary_keywords" else str(meta.get(field, "")).strip()
        if actual != str(expected).strip():
            issues.append(f"{field} mismatch")
    if re.search(r"(?m)^#\s+", body):
        issues.append("body contains level-1 heading")
    if re.search(r"<[A-Za-z!/][^>]*>", body):
        issues.append("body contains HTML")
    for term in FORBIDDEN_TERMS:
        if term in text:
            issues.append(f"forbidden term: {term}")
    return issues


def write_report(
    batch_id: str,
    config_path: Path,
    config_fields: dict[str, object],
    selected: list[dict],
    generated: list[dict],
    skipped: list[dict],
    failed: list[dict],
    available_outputs: list[Path],
    dry_run: bool,
    combined_path: Path | None,
    import_result: dict | None,
) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_id": batch_id,
        "dry_run": dry_run,
        "config_source": str(config_path),
        "recognized_config_fields": [name for name in CONFIG_FIELD_NAMES if name in config_fields],
        "selected": [
            {
                "content_id": item["content_id"],
                "target_url": item["target_url"],
                "title": item["title"],
            }
            for item in selected
        ],
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "available_output_count": len(available_outputs),
        "available_outputs": [path.relative_to(ROOT).as_posix() for path in available_outputs],
        "combined_output": str(combined_path) if combined_path else "",
        "run_import_review": import_result or {},
    }
    (ASSETS / "deepseek_api_generation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    rows = [
        "# DeepSeek API Generation Report",
        "",
        f"- batch: {batch_id}",
        f"- dry_run: {dry_run}",
        f"- config_source: {config_path}",
        f"- recognized_config_fields: {', '.join(report['recognized_config_fields'])}",
        f"- selected: {len(selected)}",
        f"- generated: {len(generated)}",
        f"- skipped: {len(skipped)}",
        f"- failed: {len(failed)}",
        f"- available_output_count: {len(available_outputs)}",
        "",
        "## Generated",
        "",
    ]
    rows.extend(f"- {item['content_id']} -> {item['output_file']}" for item in generated)
    rows.extend(["", "## Skipped", ""])
    rows.extend(f"- {item['content_id']}: {item['reason']}" for item in skipped)
    rows.extend(["", "## Failed", ""])
    rows.extend(f"- {item['content_id']}: {item['reason']}" for item in failed)
    rows.extend(["", "## Available Outputs", ""])
    rows.extend(f"- {path.relative_to(ROOT).as_posix()}" for path in available_outputs)
    if combined_path:
        rows.extend(["", "## Combined Output", "", f"- {combined_path}"])
    if import_result:
        rows.extend(
            [
                "",
                "## Import / Review",
                "",
                f"- import_exit_code: {import_result.get('import_exit_code')}",
                f"- review_exit_code: {import_result.get('review_exit_code')}",
            ]
        )
    (DOCS / "deepseek-api-generation-report.md").write_text(
        "\n".join(rows) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_stage_doc() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    doc = """# Stage 9 DeepSeek API Generation Report

## 1. Stage Goal

Stage 9 adds a direct DeepSeek API draft generation loop inside `E:/9HWH`, so batch writing can move from task packages to API-driven draft output without leaving the official website repository.

## 2. DeepSeek API Config Source

The script reads DeepSeek config from `E:/py9` in read-only mode and currently supports the existing Python config structure in `E:/py9/config.py`.

Recognized fields:

- `AI_PROVIDER`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_THINKING_ENABLED`

## 3. Secret Handling

- The API key is never written into `E:/9HWH`.
- The API key is never written into reports or logs.
- Reports only record the config source path and recognized field names.
- The script uses the key only in-memory for the outbound API request.

## 4. Script Usage

```powershell
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --dry-run
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --limit 1
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --resume
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --only c001-ad-campaign-support-how-to-17e66750
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --run-import-review
```

## 5. Resume Rules

- Existing per-article inbox files are preserved by default.
- `--overwrite` allows replacing existing per-article outputs.
- `--resume` keeps existing files and continues missing items in the same batch directory.

## 6. Output Paths

- `data/deepseek-inbox/<batch-id>/`
- `data/deepseek-inbox/<batch-id>/<content_id>.md`
- `data/deepseek-inbox/<batch-id>/failed/<content_id>.md`
- `data/deepseek-inbox/<batch-id>-deepseek-output.md`
- `data/content-assets/deepseek_api_generation_report.json`
- `docs/deepseek-api-generation-report.md`
- `data/deepseek-reviewed/` keeps imported source copies only and is not a content status source

## 7. Import And Review Flow

After generation succeeds, the next manual steps are:

```powershell
python scripts/import_deepseek_drafts.py
python scripts/review_content_drafts.py
```

`--run-import-review` is available for convenience, but default behavior does not auto-run import or review.
`data/deepseek-reviewed/` is only an import archive directory. It does not mean a draft has entered `reviewed`. Official status must be checked in `site_src/data/content/content_status.json`.

## 8. Hard Boundaries

- The script must not auto-publish content.
- The script must not push.
- The script must not deploy.
- The script must not process old service pages.
- Validation failures stay out of the normal inbox import flow.

## 9. Next Manual Checks

- Inspect any files under `failed/`.
- Run import and review for accepted inbox outputs.
- Manually decide whether a reviewed draft should stay reviewed or later move to published.
"""
    (DOCS / "stage-9-deepseek-api-generation-report.md").write_text(doc + "\n", encoding="utf-8", newline="\n")


def maybe_run_import_review() -> dict:
    import_cmd = [sys.executable, str(ROOT / "scripts" / "import_deepseek_drafts.py")]
    review_cmd = [sys.executable, str(ROOT / "scripts" / "review_content_drafts.py")]
    import_result = subprocess.run(import_cmd, cwd=ROOT, text=True)
    review_result = subprocess.run(review_cmd, cwd=ROOT, text=True)
    return {
        "import_exit_code": import_result.returncode,
        "review_exit_code": review_result.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate DeepSeek drafts directly from a batch task package.")
    parser.add_argument("--batch", default="batch-001")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--run-import-review", action="store_true")
    args = parser.parse_args()

    config_fields, config_path = discover_deepseek_config()
    batch_text, index_items = load_batch(args.batch)
    task_texts = load_task_texts(batch_text, index_items)
    selected = select_items(index_items, args.only, args.limit)
    batch_dir = INBOX_ROOT / args.batch
    failed_dir = batch_dir / "failed"
    combined_path = INBOX_ROOT / f"{args.batch}-deepseek-output.md"

    if args.dry_run:
        write_stage_doc()
        write_report(args.batch, config_path, config_fields, selected, [], [], [], [], True, None, None)
        print(f"[OK] dry-run ready for {args.batch}, selected {len(selected)} items")
        return 0

    batch_dir.mkdir(parents=True, exist_ok=True)
    failed_dir.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    generated: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    for index, item in enumerate(selected, start=1):
        content_id = item["content_id"]
        output_path = batch_dir / f"{content_id}.md"
        failed_path = failed_dir / f"{content_id}.md"
        if output_path.exists() and not args.overwrite:
            skipped.append(
                {
                    "content_id": content_id,
                    "reason": "output file already exists; use --overwrite to replace or --resume to continue",
                    "output_file": output_path.relative_to(ROOT).as_posix(),
                }
            )
            continue
        try:
            content, _response_payload = call_deepseek(build_messages(task_texts[content_id]), config_fields)
            issues = validate_generation(content, item)
        except Exception as exc:
            issues = [str(exc)]
            content = ""
        if issues:
            if content:
                failed_path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")
            failed.append(
                {
                    "content_id": content_id,
                    "reason": "; ".join(issues),
                    "failed_file": failed_path.relative_to(ROOT).as_posix() if content else "",
                }
            )
        else:
            output_path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")
            if failed_path.exists():
                failed_path.unlink()
            generated.append(
                {
                    "content_id": content_id,
                    "output_file": output_path.relative_to(ROOT).as_posix(),
                }
            )
        if index < len(selected) and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    combined_parts: list[str] = []
    if args.resume:
        for path in sorted(batch_dir.glob("*.md")):
            combined_parts.append(path.read_text(encoding="utf-8-sig").strip())
    else:
        for item in generated:
            combined_parts.append((ROOT / item["output_file"]).read_text(encoding="utf-8-sig").strip())
    if combined_parts:
        combined_path.write_text("\n\n".join(part for part in combined_parts if part) + "\n", encoding="utf-8", newline="\n")
    elif combined_path.exists() and args.overwrite:
        combined_path.unlink()

    import_result = maybe_run_import_review() if args.run_import_review else None
    available_outputs = sorted(batch_dir.glob("*.md"))
    write_stage_doc()
    write_report(
        args.batch,
        config_path,
        config_fields,
        selected,
        generated,
        skipped,
        failed,
        available_outputs,
        False,
        combined_path if combined_parts else None,
        import_result,
    )

    print(f"[OK] generated {len(generated)} drafts, skipped {len(skipped)}, failed {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
