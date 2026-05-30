from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = "E:/python/python.exe"

CONTENT_STATUS_PATH = ROOT / "site_src" / "data" / "content" / "content_status.json"
CONTENT_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
PUBLISH_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "publish_queue.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
BATCH_ID = "batch-001"
BATCH_DIR = ROOT / "data" / "deepseek-batches" / BATCH_ID
BATCH_INDEX_PATH = BATCH_DIR / f"{BATCH_ID}-index.json"
BATCH_TASKS_PATH = BATCH_DIR / f"{BATCH_ID}-tasks.md"
INBOX_DIR = ROOT / "data" / "deepseek-inbox" / BATCH_ID
BLOG_INDEX_PATH = ROOT / "site" / "public" / "blog" / "index.html"
SITEMAP_PATH = ROOT / "site" / "public" / "sitemap.xml"
BACKUP_BASE = ROOT / "data" / "content-assets" / "manual-generate-backups"

NORMAL_BACKUP_FILES = [
    CONTENT_STATUS_PATH,
    CONTENT_QUEUE_PATH,
    PUBLISH_QUEUE_PATH,
]
REBUILD_BACKUP_FILES = [
    CONTENT_STATUS_PATH,
    CONTENT_QUEUE_PATH,
    PUBLISH_QUEUE_PATH,
    BATCH_INDEX_PATH,
    BATCH_TASKS_PATH,
]

ALLOWED_ADD_PATHS = [
    "site_src/content_drafts",
    "data/content-assets",
    "docs",
]
FORBIDDEN_ADD_PATHS = [
    "data/deepseek-batches",
    "data/deepseek-inbox",
    "data/deepseek-reviewed",
]

BLOG_LOC_RE = re.compile(r"<loc>[^<]*/blog/[^<]*</loc>")
GENERATE_OK_RE = re.compile(r"generated\s+(\d+)\s+drafts,\s+skipped\s+(\d+),\s+failed\s+(\d+)", re.I)
IMPORT_RE = re.compile(r"imported\s+(\d+)\s+drafts,\s+skipped\s+(\d+),\s+failed\s+(\d+)", re.I)
REVIEW_RE = re.compile(r"reviewed\s+(\d+)\s+drafts,\s+failures\s+(\d+),\s+warnings\s+(\d+)", re.I)


class GenerateError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="9HWH safe manual DeepSeek draft generator.")
    parser.add_argument("--limit", type=int, default=7, help="Maximum tasks to generate.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; do not call DeepSeek or write files.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing inbox output files.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Delay passed to the generator between calls.")
    parser.add_argument("--rebuild-batch", action="store_true", help="Rebuild the task batch after protected backup.")
    parser.add_argument("--commit", action="store_true", help="Commit generated drafts and reports.")
    parser.add_argument("--no-push", action="store_true", help="Do not push after --commit.")
    parser.add_argument("--verbose", action="store_true", help="Show subprocess output.")
    return parser.parse_args()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def info(message: str) -> None:
    print(f"[INFO] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def count_published() -> int:
    status = load_json(CONTENT_STATUS_PATH, {})
    return int(status.get("published", 0) or 0)


def count_drafts() -> int:
    if not DRAFTS_DIR.exists():
        return 0
    return sum(1 for path in DRAFTS_DIR.glob("*.md") if path.name.upper() != "README.MD")


def count_batch_tasks() -> int:
    return len(load_json(BATCH_INDEX_PATH, []))


def count_blog_cards() -> int:
    if not BLOG_INDEX_PATH.exists():
        return 0
    return BLOG_INDEX_PATH.read_text(encoding="utf-8-sig").count("<article")


def count_sitemap_blog_urls() -> int:
    if not SITEMAP_PATH.exists():
        return 0
    return len(BLOG_LOC_RE.findall(SITEMAP_PATH.read_text(encoding="utf-8-sig")))


def run(command: list[str], *, check: bool = False, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if verbose:
        print(f"$ {' '.join(command)}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
    if check and completed.returncode != 0:
        raise GenerateError(completed.stderr.strip() or completed.stdout.strip() or f"命令失败：{' '.join(command)}")
    return completed


def git_output(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        raise GenerateError(completed.stderr.strip() or completed.stdout.strip() or "git 命令失败")
    return completed.stdout


def normalize_git_path(path: str) -> str:
    path = path.strip().strip('"').replace("\\", "/")
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip().strip('"')
    return path


def parse_git_status() -> list[tuple[str, str, str]]:
    rows = []
    for line in git_output(["status", "--porcelain=v1"]).splitlines():
        if not line:
            continue
        rows.append((line[:2], normalize_git_path(line[3:]), line))
    return rows


def starts_with_any(path: str, prefixes: list[str]) -> bool:
    clean = normalize_git_path(path)
    return any(clean == prefix or clean.startswith(prefix + "/") for prefix in prefixes)


def staged_rows(rows: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    return [row for row in rows if row[0][0] not in {" ", "?"}]


def check_git_identity() -> None:
    remotes = git_output(["remote", "-v"])
    if "wangwuda54/9hwh" not in remotes:
        raise GenerateError("当前目录不是 wangwuda54/9hwh，已停止。")


def check_git_for_commit() -> None:
    rows = parse_git_status()
    staged = staged_rows(rows)
    if staged:
        raise GenerateError("检测到已有暂存文件，避免误提交，已停止。")


def check_protection() -> int:
    published = count_published()
    if published <= 0:
        raise GenerateError("published 不是大于 0，已停止，防止破坏已恢复状态。")
    ok(f"published 保护开启：{published}")
    return published


def ensure_published_not_down(before: int, backup_dir: Path | None = None) -> int:
    after = count_published()
    if before > 0 and after == 0:
        if backup_dir:
            restore_backup(backup_dir, NORMAL_BACKUP_FILES)
        raise GenerateError("published 变成 0，已停止。")
    if after < before:
        if backup_dir:
            restore_backup(backup_dir, NORMAL_BACKUP_FILES)
        raise GenerateError(f"published 数量下降：{before} -> {after}，已停止。")
    return after


def final_protection_check(
    before_published: int,
    before_blog_cards: int,
    before_sitemap_blog_urls: int,
    backup_dir: Path | None = None,
) -> tuple[int, int, int]:
    after_published = count_published()
    after_blog_cards = count_blog_cards()
    after_sitemap_blog_urls = count_sitemap_blog_urls()

    if before_published > 0 and after_published == 0:
        if backup_dir:
            restore_backup(backup_dir, NORMAL_BACKUP_FILES)
        raise GenerateError(f"published 数量下降：{before_published} -> {after_published}")
    if after_published < before_published:
        if backup_dir:
            restore_backup(backup_dir, NORMAL_BACKUP_FILES)
        raise GenerateError(f"published 数量下降：{before_published} -> {after_published}")
    if after_blog_cards < before_blog_cards:
        if backup_dir:
            restore_backup(backup_dir, NORMAL_BACKUP_FILES)
        raise GenerateError(f"/blog/ 卡片数量下降：{before_blog_cards} -> {after_blog_cards}")
    if after_sitemap_blog_urls < before_sitemap_blog_urls:
        if backup_dir:
            restore_backup(backup_dir, NORMAL_BACKUP_FILES)
        raise GenerateError(f"sitemap blog URL 数量下降：{before_sitemap_blog_urls} -> {after_sitemap_blog_urls}")

    ok(f"published 未下降：{before_published} -> {after_published}")
    ok(f"/blog/ 卡片未下降：{before_blog_cards} -> {after_blog_cards}")
    ok(f"sitemap blog URL 未下降：{before_sitemap_blog_urls} -> {after_sitemap_blog_urls}")
    return after_published, after_blog_cards, after_sitemap_blog_urls


def create_backup(files: list[Path]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_BASE / stamp
    for source in files:
        target = backup_dir / rel(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.copy2(source, target)
    return backup_dir


def restore_backup(backup_dir: Path, files: list[Path]) -> None:
    for source in files:
        backup_file = backup_dir / rel(source)
        if not backup_file.exists():
            continue
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, source)


def maybe_rebuild_batch(before_published: int, verbose: bool) -> None:
    backup_dir = create_backup(REBUILD_BACKUP_FILES)
    try:
        run([PYTHON_EXE, "scripts/build_content_queue.py"], check=True, verbose=verbose)
        run([PYTHON_EXE, "scripts/build_deepseek_batch.py"], check=True, verbose=verbose)
        after = ensure_published_not_down(before_published, backup_dir)
        ok(f"重建任务池完成，published 未下降：{before_published} -> {after}")
    except Exception:
        restore_backup(backup_dir, REBUILD_BACKUP_FILES)
        raise


def find_tasks(limit: int, overwrite: bool) -> tuple[list[dict], int]:
    batch_items = load_json(BATCH_INDEX_PATH, [])
    content_queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    queue_by_id = {item.get("content_id", ""): item for item in content_queue if item.get("content_id")}
    publish_by_id = {item.get("content_id", ""): item for item in publish_queue if item.get("content_id")}

    candidates: list[dict] = []
    for item in batch_items:
        content_id = str(item.get("content_id", "")).strip()
        if not content_id:
            continue
        queue_item = queue_by_id.get(content_id, {})
        if queue_item.get("status") in {"published", "paused"}:
            continue
        if publish_by_id.get(content_id, {}).get("publish_status") == "published":
            continue
        if (DRAFTS_DIR / f"{content_id}.md").exists():
            continue
        if (INBOX_DIR / f"{content_id}.md").exists() and not overwrite:
            continue
        candidates.append(item)

    return candidates[:limit], len(candidates)


def parse_generation_counts(output: str) -> tuple[int, int, int]:
    match = GENERATE_OK_RE.search(output)
    if not match:
        return 0, 0, 1
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def generate_one(content_id: str, overwrite: bool, sleep_seconds: float, verbose: bool) -> tuple[bool, str]:
    command = [
        PYTHON_EXE,
        "scripts/generate_deepseek_drafts_api.py",
        "--batch",
        BATCH_ID,
        "--only",
        content_id,
        "--sleep-seconds",
        str(sleep_seconds),
    ]
    if overwrite:
        command.append("--overwrite")
    completed = run(command, check=False, verbose=verbose)
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    generated, _skipped, failed_count = parse_generation_counts(output)
    if completed.returncode == 0 and generated > 0 and failed_count == 0:
        return True, ""
    reason = "生成失败"
    report = load_json(ROOT / "data" / "content-assets" / "deepseek_api_generation_report.json", {})
    for item in report.get("failed", []):
        if item.get("content_id") == content_id:
            reason = item.get("reason") or reason
            break
    for item in report.get("skipped", []):
        if item.get("content_id") == content_id:
            reason = item.get("reason") or "已跳过"
            break
    if not reason and completed.stderr.strip():
        reason = completed.stderr.strip().splitlines()[-1]
    return False, reason


def generate_tasks(tasks: list[dict], overwrite: bool, sleep_seconds: float, verbose: bool) -> tuple[int, list[tuple[str, str]]]:
    success_count = 0
    failures: list[tuple[str, str]] = []
    for item in tasks:
        content_id = item["content_id"]
        ok_generated, reason = generate_one(content_id, overwrite, sleep_seconds, verbose)
        if ok_generated:
            success_count += 1
        else:
            failures.append((content_id, reason))
    return success_count, failures


def parse_import_output(output: str) -> tuple[int, int, int]:
    match = IMPORT_RE.search(output)
    if not match:
        return 0, 0, 1
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def run_import(verbose: bool) -> tuple[int, int, int, int]:
    completed = run([PYTHON_EXE, "scripts/import_deepseek_drafts.py"], check=False, verbose=verbose)
    imported, skipped, failed_count = parse_import_output((completed.stdout or "") + "\n" + (completed.stderr or ""))
    return imported, skipped, failed_count, completed.returncode


def run_repair(verbose: bool) -> int:
    completed = run(
        [PYTHON_EXE, "scripts/repair_placeholder_descriptions.py", "--write", "--fail-on-remaining"],
        check=False,
        verbose=verbose,
    )
    return completed.returncode


def parse_review_output(output: str) -> tuple[int, int, int]:
    match = REVIEW_RE.search(output)
    if not match:
        return 0, 1, 0
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def run_review(verbose: bool) -> tuple[int, int, int, int]:
    completed = run([PYTHON_EXE, "scripts/review_content_drafts.py"], check=False, verbose=verbose)
    reviewed, failures, warnings = parse_review_output((completed.stdout or "") + "\n" + (completed.stderr or ""))
    return reviewed, failures, warnings, completed.returncode


def configure_git_identity() -> None:
    git_output(["config", "user.name", "9hwh-local-publisher"])
    git_output(["config", "user.email", "9hwh-local-publisher@users.noreply.github.com"])


def commit_changes(no_push: bool) -> None:
    check_git_for_commit()
    configure_git_identity()
    subprocess.run(["git", "add", "--", *ALLOWED_ADD_PATHS], cwd=ROOT, check=True)
    rows = parse_git_status()
    staged = [path for _, path, _ in staged_rows(rows)]
    forbidden = [path for path in staged if starts_with_any(path, FORBIDDEN_ADD_PATHS)]
    if forbidden:
        raise GenerateError("检测到禁止提交目录已暂存：" + ", ".join(forbidden[:8]))
    outside = [path for path in staged if not starts_with_any(path, ALLOWED_ADD_PATHS)]
    if outside:
        raise GenerateError("检测到白名单外文件已暂存：" + ", ".join(outside[:8]))
    if not staged:
        ok("没有需要提交的变化")
        return
    message = f"manual safe generate drafts {date.today().isoformat()}"
    run(["git", "commit", "-m", message], check=True)
    ok("commit 成功")
    if no_push:
        ok("已按 --no-push 跳过推送")
    else:
        run(["git", "push", "origin", "main"], check=True)
        ok("push 成功")


def print_next_step() -> None:
    info("下一步可运行：")
    print("E:/python/python.exe scripts/manual_publish_safe.py --dry-run --limit 7")


def dry_run(limit: int, overwrite: bool, rebuild_batch: bool) -> int:
    before_published = count_published()
    tasks, available = find_tasks(limit, overwrite)
    print(f"当前 published 数：{before_published}")
    print(f"当前已有草稿数：{count_drafts()}")
    print(f"当前 batch 任务数：{count_batch_tasks()}")
    print(f"可生成任务数：{available}")
    print("本次将生成的 content_id：" + (", ".join(item["content_id"] for item in tasks) if tasks else "无"))
    if available < limit:
        warn("可生成任务不足，请人工确认是否需要扩展任务池。")
    if rebuild_batch:
        warn("dry-run + --rebuild-batch 暂不支持安全模拟；本次不会写文件。需要正式扩展时请显式运行非 dry-run 命令。")
    return 0


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        fail("limit 不能小于 0")
        return 1
    if args.commit and args.dry_run:
        fail("--dry-run 不能和 --commit 同时使用")
        return 1

    print("9HWH 安全生成草稿")
    print(f"当前已发布：{count_published()} 篇")
    print(f"当前 batch 任务：{count_batch_tasks()} 个")
    print(f"当前已有草稿：{count_drafts()} 篇")
    print()

    try:
        check_git_identity()
        if args.dry_run:
            check_protection()
            return dry_run(args.limit, args.overwrite, args.rebuild_batch)

        print("[1/6] 检查保护状态")
        before_published = check_protection()
        before_blog_cards = count_blog_cards()
        before_sitemap_blog_urls = count_sitemap_blog_urls()
        if args.rebuild_batch:
            warn("正式 --rebuild-batch 暂停执行：当前旧重建脚本会重建 content_status，需先实现安全模拟后再开放。")
        print()

        print("[2/6] 查找可生成任务")
        tasks, available = find_tasks(args.limit, args.overwrite)
        if available < args.limit:
            warn("可生成任务不足，请人工确认是否需要扩展任务池。")
        if not tasks:
            ok("可生成任务：0 篇，本次无需生成。")
            print()
            print("[6/6] 结果")
            final_protection_check(before_published, before_blog_cards, before_sitemap_blog_urls)
            print_next_step()
            return 0
        ok(f"可生成任务：{len(tasks)} 篇")
        backup_dir = create_backup(NORMAL_BACKUP_FILES)
        print()

        print("[3/6] 生成草稿")
        success_count, failures = generate_tasks(tasks, args.overwrite, args.sleep_seconds, args.verbose)
        ok(f"成功：{success_count} 篇")
        if failures:
            warn(f"失败：{len(failures)} 篇")
            for content_id, reason in failures:
                print(f"* {content_id} {reason}")
        else:
            ok("失败：0 篇")
        ensure_published_not_down(before_published, backup_dir)
        print()

        print("[4/6] 导入草稿")
        imported, skipped, failed_count, import_code = run_import(args.verbose)
        if import_code != 0 or failed_count:
            warn(f"导入部分失败：imported {imported}, skipped {skipped}, failed {failed_count}")
        else:
            ok(f"导入完成：imported {imported}, skipped {skipped}, failed {failed_count}")
        ensure_published_not_down(before_published, backup_dir)
        print()

        print("[5/6] 修复和审核")
        repair_code = run_repair(args.verbose)
        if repair_code != 0:
            warn("description 占位修复后仍有问题，请人工查看报告。")
        reviewed, review_failures, review_warnings, _review_code = run_review(args.verbose)
        if review_failures or review_warnings:
            warn(f"审核完成：reviewed {reviewed}, failures {review_failures}, warnings {review_warnings}")
        else:
            ok(f"审核完成：reviewed {reviewed}, failures {review_failures}, warnings {review_warnings}")
        print()

        print("[6/6] 结果")
        final_protection_check(before_published, before_blog_cards, before_sitemap_blog_urls, backup_dir)
        if args.commit:
            commit_changes(args.no_push)
        print_next_step()
        return 0
    except GenerateError as exc:
        fail(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
