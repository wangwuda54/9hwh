from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import manual_generate_safe as generate_safe
import manual_publish_safe as publish_safe


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = "E:/python/python.exe"

CONTENT_STATUS_PATH = ROOT / "site_src" / "data" / "content" / "content_status.json"
CONTENT_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
PUBLISH_QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "publish_queue.json"
BATCH_INDEX_PATH = ROOT / "data" / "deepseek-batches" / "batch-001" / "batch-001-index.json"
BATCH_TASKS_PATH = ROOT / "data" / "deepseek-batches" / "batch-001" / "batch-001-tasks.md"
BLOG_INDEX_PATH = ROOT / "site" / "public" / "blog" / "index.html"
SITEMAP_PATH = ROOT / "site" / "public" / "sitemap.xml"
BACKUP_BASE = ROOT / "data" / "content-assets" / "manual-daily-backups"

BACKUP_FILES = [
    CONTENT_STATUS_PATH,
    CONTENT_QUEUE_PATH,
    PUBLISH_QUEUE_PATH,
    BATCH_INDEX_PATH,
    BATCH_TASKS_PATH,
    BLOG_INDEX_PATH,
    SITEMAP_PATH,
]


class DailyError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="9HWH safe daily local publish entry.")
    parser.add_argument("--limit", type=int, default=7)
    parser.add_argument(
        "--mode",
        choices=["conservative", "normal", "growth", "aggressive"],
        default="normal",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--allow-rebuild-batch", action="store_true")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--publish-only", action="store_true")
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


def counts() -> tuple[int, int, int]:
    return (
        publish_safe.count_published(),
        publish_safe.count_blog_cards(),
        publish_safe.count_sitemap_blog_urls(),
    )


def require_good_state() -> tuple[int, int, int]:
    published, blog_cards, sitemap_blog_urls = counts()
    if published <= 0:
        raise DailyError("published <= 0，已停止。")
    if blog_cards <= 0:
        raise DailyError("/blog/ 卡片数 <= 0，已停止。")
    if sitemap_blog_urls <= 0:
        raise DailyError("sitemap blog URL <= 0，已停止。")
    ok(f"published 保护开启：{published}")
    ok(f"blog cards 保护开启：{blog_cards}")
    ok(f"sitemap blog URL 保护开启：{sitemap_blog_urls}")
    return published, blog_cards, sitemap_blog_urls


def create_backup() -> Path:
    stamp = generate_safe.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_BASE / stamp
    for source in BACKUP_FILES:
        target = backup_dir / rel(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.copy2(source, target)
    return backup_dir


def restore_backup(backup_dir: Path) -> None:
    for source in BACKUP_FILES:
        backup_file = backup_dir / rel(source)
        if not backup_file.exists():
            continue
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_file, source)


def final_check(before: tuple[int, int, int], backup_dir: Path | None = None) -> tuple[int, int, int]:
    after = counts()
    labels = ("published", "/blog/ 卡片", "sitemap blog URL")
    for label, before_value, after_value in zip(labels, before, after):
        if after_value < before_value:
            if backup_dir:
                restore_backup(backup_dir)
            raise DailyError(f"{label} 数量下降：{before_value} -> {after_value}")
    ok(f"published 未下降：{before[0]} -> {after[0]}")
    ok(f"/blog/ 卡片未下降：{before[1]} -> {after[1]}")
    ok(f"sitemap blog URL 未下降：{before[2]} -> {after[2]}")
    return after


def run_child(command: list[str], verbose: bool, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if verbose:
        print(f"$ {' '.join(command)}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
    if check and completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"命令失败：{' '.join(command)}"
        raise DailyError(message)
    return completed


def publish_dry_run(limit: int, mode: str, verbose: bool) -> int:
    command = [PYTHON_EXE, "scripts/manual_publish_safe.py", "--dry-run", "--limit", str(limit), "--mode", mode]
    run_child(command, verbose=verbose)
    selected, _valid_count = publish_safe.find_publish_candidates(limit, mode, False)
    return len(selected)


def generate_dry_run(limit: int, verbose: bool, rebuild_batch: bool = False) -> int:
    command = [PYTHON_EXE, "scripts/manual_generate_safe.py", "--dry-run", "--limit", str(limit)]
    if rebuild_batch:
        command.append("--rebuild-batch")
    run_child(command, verbose=verbose)
    if rebuild_batch:
        warn("manual_generate_safe.py 的 dry-run + --rebuild-batch 暂不支持安全模拟；本次没有写文件。")
    _tasks, available = generate_safe.find_tasks(limit, False)
    return available


def run_generate(limit: int, verbose: bool, rebuild_batch: bool = False) -> None:
    command = [PYTHON_EXE, "scripts/manual_generate_safe.py", "--limit", str(limit)]
    if rebuild_batch:
        command.append("--rebuild-batch")
    if verbose:
        command.append("--verbose")
    run_child(command, verbose=verbose)


def run_publish(limit: int, mode: str, no_push: bool, verbose: bool) -> None:
    command = [PYTHON_EXE, "scripts/manual_publish_safe.py", "--limit", str(limit), "--mode", mode]
    if no_push:
        command.append("--no-push")
    if verbose:
        command.append("--verbose")
    run_child(command, verbose=verbose)


def print_next_step() -> None:
    print("下一步：")
    print("E:/python/python.exe scripts/manual_daily_safe.py --limit 7 --allow-rebuild-batch --dry-run")
    print()
    print("确认后正式运行：")
    print("E:/python/python.exe scripts/manual_daily_safe.py --limit 7 --allow-rebuild-batch")


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        fail("limit 不能小于 0")
        return 1
    if args.generate_only and args.publish_only:
        fail("--generate-only 和 --publish-only 不能同时使用")
        return 1

    print("9HWH 安全日常发布")
    published, blog_cards, sitemap_blog_urls = counts()
    print(f"当前 published：{published}")
    print(f"当前 /blog/ 卡片：{blog_cards}")
    print(f"当前 sitemap blog URL：{sitemap_blog_urls}")
    print()

    try:
        print("[1/7] 检查保护状态")
        before = require_good_state()
        print()

        print("[2/7] 检查可发布候选")
        publish_candidates = publish_dry_run(args.limit, args.mode, args.verbose)
        info(f"可发布候选：{publish_candidates} 篇")
        print()

        if args.publish_only:
            if args.dry_run:
                info("dry-run：只检查发布，不执行正式发布。")
                return 0
            if publish_candidates <= 0:
                warn("当前没有可发布候选。")
                return 0
            run_publish(args.limit, args.mode, args.no_push, args.verbose)
            final_check(before)
            return 0

        if publish_candidates >= args.limit:
            if args.generate_only:
                info("可发布候选已足够，--generate-only 不再生成。")
                return 0
            if args.dry_run:
                info("dry-run：可发布候选已足够，正式运行会直接发布。")
                return 0
            print("[7/7] 安全发布")
            run_publish(args.limit, args.mode, args.no_push, args.verbose)
            final_check(before)
            return 0

        gap = args.limit - publish_candidates

        print("[3/7] 检查可生成任务")
        generate_available = generate_dry_run(gap, args.verbose)
        info(f"可生成任务：{generate_available} 篇")
        print()

        if generate_available > 0:
            if args.dry_run:
                info("dry-run：正式运行会先生成缺口草稿，再重新检查发布候选。")
                return 0
            print("[4/7] 安全生成草稿")
            run_generate(gap, args.verbose)
            final_check(before)
            print()
        else:
            print("[4/7] 扩展任务池")
            if not args.allow_rebuild_batch:
                warn("当前无可发布候选，且任务池不足。需要确认后用 --allow-rebuild-batch 扩展任务池。")
                print()
                print("[结果]")
                print("没有发布。")
                print("原因：无可发布候选，任务池不足。")
                print_next_step()
                return 0

            generate_dry_run(gap, args.verbose, rebuild_batch=True)
            if args.dry_run:
                warn("dry-run 不执行真实任务池扩展。")
                return 0

            warn("当前暂不执行真实任务池扩展：manual_generate_safe.py 已阻止旧重建脚本写入，避免破坏 published。")
            print()
            print("[结果]")
            print("没有发布。")
            print("原因：无可发布候选，任务池扩展暂未开放真实执行。")
            return 0

            backup_dir = create_backup()
            try:
                run_generate(gap, args.verbose, rebuild_batch=True)
                final_check(before, backup_dir)
            except Exception:
                restore_backup(backup_dir)
                raise
            print()

        if args.generate_only:
            info("--generate-only 已完成，不执行发布。")
            return 0

        print("[5/7] 生成后检查可发布候选")
        publish_candidates = publish_dry_run(args.limit, args.mode, args.verbose)
        info(f"可发布候选：{publish_candidates} 篇")
        print()

        if publish_candidates <= 0:
            warn("生成后仍无可发布候选，已停止。")
            return 0

        if args.dry_run:
            info("dry-run：正式运行会执行安全发布。")
            return 0

        print("[6/7] 安全发布")
        run_publish(args.limit, args.mode, args.no_push, args.verbose)
        print()

        print("[7/7] 最终保护检查")
        final_check(before)
        return 0
    except DailyError as exc:
        fail(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
