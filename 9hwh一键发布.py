from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_QUEUE = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE = CONTENT_DIR / "publish_queue.json"
CONTENT_STATUS = CONTENT_DIR / "content_status.json"
DRAFTS = ROOT / "site_src" / "content_drafts"
BATCH_ROOT = ROOT / "data" / "deepseek-batches"
ASSETS = ROOT / "data" / "content-assets"
DOCS = ROOT / "docs"
PYTHON = sys.executable

TRACKED_OUTPUTS = [
    "site_src/data/content",
    "site_src/content_drafts",
    "site/public",
    "data/content-assets",
    "docs",
]

GENERATED_RUNTIME_DIRS = [
    "data/deepseek-inbox",
    "data/deepseek-reviewed",
]

PROTECTED_QUEUE_STATUSES = {"published", "paused"}
PUBLISHABLE_REVIEW_STATUSES = {"pass"}
PLACEHOLDER_RE = re.compile(r"\?{8,}")


class StepError(RuntimeError):
    pass


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def log(message: str = "") -> None:
    print(message, flush=True)


def step(title: str) -> None:
    log("\n" + "=" * 78)
    log(title)
    log("=" * 78)


def run(command: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    log("$ " + " ".join(command))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
    )
    if capture:
        if completed.stdout.strip():
            log(completed.stdout.rstrip())
        if completed.stderr.strip():
            log(completed.stderr.rstrip())
    if check and completed.returncode != 0:
        raise StepError(f"命令失败，退出码 {completed.returncode}: {' '.join(command)}")
    return completed


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_md(path: Path) -> tuple[dict[str, str], list[str], str]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}, [], text.strip()
    try:
        _, front, body = text.split("---", 2)
    except ValueError:
        return {}, [], text.strip()
    meta: dict[str, str] = {}
    lines = front.splitlines()
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, lines, body.strip()


def update_frontmatter_status(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        raise StepError(f"草稿缺少 front matter: {rel(path)}")
    _, front, body = text.split("---", 2)
    lines = front.splitlines()
    changed = False
    output = []
    for line in lines:
        if line.startswith("status:"):
            output.append(f"status: {status}")
            changed = True
        else:
            output.append(line)
    if not changed:
        output.append(f"status: {status}")
    path.write_text("---\n" + "\n".join(output).strip() + "\n---" + body, encoding="utf-8", newline="\n")


def extract_internal_links(body: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", body)


def is_bad_description(description: str) -> bool:
    text = str(description or "").strip()
    if not text:
        return True
    compact = re.sub(r"\s+", "", text)
    return bool(compact) and set(compact) == {"?"}


def has_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.search(str(value or "")))


def git_status_porcelain() -> list[str]:
    completed = run(["git", "status", "--porcelain"], check=False, capture=True)
    return [line for line in completed.stdout.splitlines() if line.strip()]


def maybe_git_pull(skip_pull: bool) -> None:
    step("[1/10] 检查 Git 状态")
    status = git_status_porcelain()
    if status:
        log(f"[WARN] 当前工作区不是干净状态：{len(status)} 条变更。")
        log("[INFO] 为避免覆盖本地文件，本次跳过 git pull。")
        log("[INFO] 后续只会 git add 站点输出目录，不会主动 add data/deepseek-inbox 或 data/deepseek-reviewed。")
        return
    if skip_pull:
        log("[INFO] 已按参数跳过 git pull。")
        return
    run(["git", "pull", "--ff-only"])


def current_review_report() -> dict:
    return load_json(ASSETS / "draft_review_report.json", {"articles": []})


def build_review_map() -> dict[str, dict]:
    report = current_review_report()
    return {item.get("content_id", ""): item for item in report.get("articles", []) if item.get("content_id")}


def draft_exists(content_id: str) -> bool:
    return (DRAFTS / f"{content_id}.md").exists()


def choose_generation_ids(batch_id: str, limit: int) -> list[str]:
    index_path = BATCH_ROOT / batch_id / f"{batch_id}-index.json"
    if not index_path.exists():
        log(f"[WARN] 任务包不存在，跳过生成：{rel(index_path)}")
        return []

    index_items = load_json(index_path, [])
    queue = load_json(CONTENT_QUEUE, [])
    queue_by_id = {item.get("content_id"): item for item in queue if item.get("content_id")}
    selected: list[str] = []
    for item in index_items:
        content_id = item.get("content_id", "")
        if not content_id:
            continue
        queue_item = queue_by_id.get(content_id, {})
        status = queue_item.get("status", "")
        if status in PROTECTED_QUEUE_STATUSES:
            continue
        if draft_exists(content_id):
            continue
        selected.append(content_id)
        if len(selected) >= limit:
            break
    return selected


def generate_drafts(batch_id: str, limit: int, overwrite_generation: bool, sleep_seconds: float) -> None:
    step("[2/10] 生成 DeepSeek 草稿")
    ids = choose_generation_ids(batch_id, limit)
    if not ids:
        log("[INFO] 没有找到需要生成的新任务，跳过生成。")
        return

    log("[INFO] 本次准备生成：")
    for content_id in ids:
        log(f"  - {content_id}")

    for index, content_id in enumerate(ids, start=1):
        log(f"\n[GEN {index}/{len(ids)}] {content_id}")
        command = [
            PYTHON,
            str(SCRIPTS / "generate_deepseek_drafts_api.py"),
            "--batch",
            batch_id,
            "--only",
            content_id,
            "--sleep-seconds",
            str(sleep_seconds),
        ]
        if overwrite_generation:
            command.append("--overwrite")
        run(command)


def import_and_review() -> None:
    step("[3/10] 导入草稿并审核")
    run([PYTHON, str(SCRIPTS / "import_deepseek_drafts.py")])
    run([PYTHON, str(SCRIPTS / "repair_placeholder_descriptions.py"), "--write", "--fail-on-remaining"])
    run([PYTHON, str(SCRIPTS / "review_content_drafts.py")])


def summarize_content_status(queue: list[dict]) -> dict:
    counts = Counter(item.get("status", "") for item in queue)
    return {
        "total_planned": len(queue),
        "prompt_ready": counts.get("prompt_ready", 0),
        "writing": counts.get("writing", 0),
        "draft_received": counts.get("draft_received", 0),
        "reviewed": counts.get("reviewed", 0),
        "published": counts.get("published", 0),
        "paused": counts.get("paused", 0),
        "last_generated_at": datetime.now().date().isoformat(),
    }


def queue_item_to_publish_entry(queue_item: dict, review_item: dict, internal_link_count: int) -> dict:
    return {
        "content_id": queue_item.get("content_id", ""),
        "title": queue_item.get("title", ""),
        "target_url": queue_item.get("target_url", ""),
        "primary_keyword": queue_item.get("primary_keyword", ""),
        "content_type": queue_item.get("page_type", "blog_article"),
        "priority_score": int(queue_item.get("priority", queue_item.get("priority_score", 0)) or 0),
        "risk_level": queue_item.get("risk_level", "low"),
        "publish_status": "queued",
        "planned_publish_date": datetime.now().date().isoformat(),
        "batch": queue_item.get("batch", ""),
        "review_status": review_item.get("status", "pass"),
        "internal_link_count": internal_link_count,
        "notes": "approved_by_9hwh_one_click_publish",
    }


def promote_reviewed_candidates(limit: int, allow_warning: bool) -> list[str]:
    step("[4/10] 自动放入发布池")
    allowed_review_statuses = set(PUBLISHABLE_REVIEW_STATUSES)
    if allow_warning:
        allowed_review_statuses.add("warning")

    queue = load_json(CONTENT_QUEUE, [])
    publish_queue = load_json(PUBLISH_QUEUE, [])
    review_by_id = build_review_map()
    queue_by_id = {item.get("content_id"): item for item in queue if item.get("content_id")}
    publish_by_id = {item.get("content_id"): item for item in publish_queue if item.get("content_id")}

    candidates: list[tuple[int, str, dict, dict, int]] = []
    for content_id, review_item in review_by_id.items():
        if review_item.get("status") not in allowed_review_statuses:
            continue
        if review_item.get("issues"):
            continue
        queue_item = queue_by_id.get(content_id)
        if not queue_item:
            continue
        if queue_item.get("status") in {"published", "paused"}:
            continue
        draft_path = DRAFTS / f"{content_id}.md"
        if not draft_path.exists():
            continue
        meta, _, body = parse_md(draft_path)
        description = meta.get("description", "")
        if is_bad_description(description) or has_placeholder(description):
            log(f"[SKIP] description 异常：{content_id}")
            continue
        internal_link_count = len(list(dict.fromkeys(extract_internal_links(body))))
        if internal_link_count < 4:
            log(f"[SKIP] 内链不足：{content_id} links={internal_link_count}")
            continue
        priority = int(queue_item.get("priority", queue_item.get("priority_score", 0)) or 0)
        candidates.append((priority, content_id, queue_item, review_item, internal_link_count))

    candidates.sort(key=lambda row: (row[0], row[1]))
    promoted: list[str] = []
    for _, content_id, queue_item, review_item, internal_link_count in candidates:
        if len(promoted) >= limit:
            break
        queue_item["status"] = "reviewed"
        draft_path = DRAFTS / f"{content_id}.md"
        update_frontmatter_status(draft_path, "reviewed")

        entry = publish_by_id.get(content_id)
        new_entry = queue_item_to_publish_entry(queue_item, review_item, internal_link_count)
        if entry:
            if entry.get("publish_status") != "published":
                entry.update(new_entry)
        else:
            publish_queue.append(new_entry)
            publish_by_id[content_id] = new_entry
        promoted.append(content_id)

    write_json(CONTENT_QUEUE, queue)
    write_json(PUBLISH_QUEUE, publish_queue)
    write_json(CONTENT_STATUS, summarize_content_status(queue))

    if promoted:
        log(f"[OK] 已放入发布池：{len(promoted)} 条")
        for content_id in promoted:
            log(f"  - {content_id}")
    else:
        log("[WARN] 没有可放入发布池的草稿。")
    return promoted


def publish(limit: int, mode: str) -> None:
    step("[5/10] 发布文章")
    run([PYTHON, str(SCRIPTS / "daily_publish.py"), "--mode", mode, "--limit", str(limit)])


def build_and_check() -> None:
    step("[6/10] 构建站点")
    run([PYTHON, str(SCRIPTS / "build_site.py")])

    step("[7/10] 检查站点")
    run([PYTHON, str(SCRIPTS / "check_static_site.py")])
    run([PYTHON, str(SCRIPTS / "check_sitemap_readiness.py")])
    run([PYTHON, str(SCRIPTS / "check_placeholder_text.py")])


def read_daily_publish_summary() -> dict:
    return load_json(ASSETS / "daily_publish_report.json", {})


def git_commit_and_push(push: bool, allow_empty_commit: bool) -> None:
    step("[8/10] 提交本次站点变更")
    for item in TRACKED_OUTPUTS:
        run(["git", "add", item])

    status_after_add = git_status_porcelain()
    staged = run(["git", "diff", "--cached", "--name-only"], check=False, capture=True).stdout.splitlines()
    if not staged:
        log("[INFO] 没有需要提交的站点变更。")
        if not allow_empty_commit:
            return

    message = f"manual one-click publish content {datetime.now().date().isoformat()}"
    commit_cmd = ["git", "commit", "-m", message]
    if allow_empty_commit:
        commit_cmd.insert(2, "--allow-empty")
    commit_result = run(commit_cmd, check=False, capture=True)
    if commit_result.returncode != 0:
        output = (commit_result.stdout + "\n" + commit_result.stderr).strip()
        if "nothing to commit" in output.lower() or "no changes added" in output.lower():
            log("[INFO] Git 没有新提交。")
            return
        raise StepError("git commit 失败")

    if push:
        step("[9/10] 推送到 GitHub")
        run(["git", "push", "origin", "main"])
    else:
        log("[INFO] 已提交到本地，但未 push。需要推送时执行：git push origin main")


def final_report() -> None:
    step("[10/10] 结果摘要")
    report = read_daily_publish_summary()
    log(f"发布状态：{report.get('status', 'unknown')}")
    log(f"本次发布：{report.get('published_count', 0)} 条")
    log(f"累计发布：{report.get('total_published', 0)} 条")
    log(f"说明：{report.get('message', '')}")
    items = report.get("published_items") or []
    if items:
        log("\n已发布 URL：")
        for item in items:
            log(f"  - {item.get('content_id')} {item.get('full_url') or item.get('target_url')}")

    status = git_status_porcelain()
    runtime_leftovers = [line for line in status if any(path in line for path in GENERATED_RUNTIME_DIRS)]
    other_leftovers = [line for line in status if line not in runtime_leftovers]
    if runtime_leftovers:
        log(f"\n[INFO] 还有 {len(runtime_leftovers)} 条 DeepSeek 临时/归档文件未提交，这是正常的。")
        log("[INFO] 如需清理，可手动确认后删除 data/deepseek-inbox 和 data/deepseek-reviewed 里的旧文件。")
    if other_leftovers:
        log("\n[WARN] 还有非临时文件处于未提交状态：")
        for line in other_leftovers[:30]:
            log("  " + line)
        if len(other_leftovers) > 30:
            log(f"  ... 还有 {len(other_leftovers) - 30} 条")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="9HWH 本地一键生成、审核、发布、构建、检查、提交。")
    parser.add_argument("--limit", type=int, default=7, help="每天生成/发布数量，默认 7。")
    parser.add_argument("--batch", default="batch-001", help="DeepSeek 任务包，默认 batch-001。")
    parser.add_argument("--mode", choices=["conservative", "normal", "growth", "aggressive"], default="normal", help="发布节奏，默认 normal。")
    parser.add_argument("--no-push", action="store_true", help="只本地提交，不 push。")
    parser.add_argument("--skip-pull", action="store_true", help="跳过 git pull。")
    parser.add_argument("--allow-warning", action="store_true", help="允许 warning 草稿进入发布池。默认只发布 pass 草稿。")
    parser.add_argument("--overwrite-generation", action="store_true", help="允许覆盖 DeepSeek inbox 里的同名生成输出。")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="DeepSeek 生成间隔秒数，默认 1。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(ROOT)
    log("9HWH 一键发布")
    log(f"项目目录：{ROOT}")
    log(f"发布数量：{args.limit}")
    log(f"任务包：{args.batch}")
    log(f"发布模式：{args.mode}")

    maybe_git_pull(args.skip_pull)
    generate_drafts(args.batch, args.limit, args.overwrite_generation, args.sleep_seconds)
    import_and_review()
    promote_reviewed_candidates(args.limit, args.allow_warning)
    publish(args.limit, args.mode)
    build_and_check()
    git_commit_and_push(push=not args.no_push, allow_empty_commit=False)
    final_report()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StepError as exc:
        log("\n[FAIL] 一键发布中断")
        log(str(exc))
        log("\n下一步：把上面 [FAIL] 附近的 20 行输出贴给我。")
        raise SystemExit(1)
    except KeyboardInterrupt:
        log("\n[FAIL] 用户手动中断")
        raise SystemExit(130)
