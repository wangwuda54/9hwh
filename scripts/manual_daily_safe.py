from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import manual_generate_safe as generate_safe
import manual_publish_safe as publish_safe


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = "E:/python/python.exe"


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
    parser.add_argument("--prepare-count", type=int, default=21)
    parser.add_argument("--expand-count", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--publish-only", action="store_true")
    parser.add_argument("--allow-rebuild-batch", action="store_true", help="Kept for compatibility; safe expansion is now automatic.")
    return parser.parse_args()


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


def final_check(before: tuple[int, int, int]) -> tuple[int, int, int]:
    after = counts()
    labels = ("published", "/blog/ 卡片", "sitemap blog URL")
    for label, before_value, after_value in zip(labels, before, after):
        if after_value < before_value:
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


def publish_candidate_count(limit: int, mode: str) -> int:
    _selected, valid_count = publish_safe.find_publish_candidates(limit, mode, False)
    return valid_count


def generate_available_count(limit: int) -> int:
    _tasks, available = generate_safe.find_tasks(limit, False)
    return available


def run_publish_dry_run(limit: int, mode: str, verbose: bool) -> int:
    run_child([PYTHON_EXE, "scripts/manual_publish_safe.py", "--dry-run", "--limit", str(limit), "--mode", mode], verbose)
    return publish_candidate_count(limit, mode)


def run_generate_dry_run(limit: int, expand_count: int, rebuild_batch: bool, verbose: bool) -> int:
    command = [PYTHON_EXE, "scripts/manual_generate_safe.py", "--dry-run", "--limit", str(limit)]
    if rebuild_batch:
        command.extend(["--rebuild-batch", "--expand-count", str(expand_count)])
    run_child(command, verbose)
    return generate_available_count(limit)


def run_generate(limit: int, expand_count: int, rebuild_batch: bool, verbose: bool) -> None:
    command = [PYTHON_EXE, "scripts/manual_generate_safe.py", "--limit", str(limit)]
    if rebuild_batch:
        command.extend(["--rebuild-batch", "--expand-count", str(expand_count)])
    if verbose:
        command.append("--verbose")
    run_child(command, verbose)


def run_publish(limit: int, mode: str, no_push: bool, verbose: bool) -> None:
    command = [PYTHON_EXE, "scripts/manual_publish_safe.py", "--limit", str(limit), "--mode", mode]
    if no_push:
        command.append("--no-push")
    if verbose:
        command.append("--verbose")
    run_child(command, verbose)


def main() -> int:
    args = parse_args()
    if args.limit < 0 or args.prepare_count < 0 or args.expand_count < 0:
        fail("limit / prepare-count / expand-count 不能小于 0")
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
        publish_candidates = run_publish_dry_run(args.limit, args.mode, args.verbose)
        info(f"可发布候选：{publish_candidates} 篇")
        print()

        if args.publish_only:
            if args.dry_run:
                info("dry-run：只检查发布，不执行真实发布。")
                return 0
            if publish_candidates <= 0:
                warn("当前没有可发布候选。")
                return 0
            run_publish(min(args.limit, publish_candidates), args.mode, args.no_push, args.verbose)
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

        print("[3/7] 检查可生成任务")
        generate_available = generate_available_count(args.prepare_count)
        info(f"可生成任务：{generate_available} 篇")
        rebuild_batch = generate_available < args.prepare_count
        if rebuild_batch:
            info(f"任务池不足，准备安全追加任务：{args.expand_count} 篇")
        print()

        if args.dry_run:
            print("[4/7] dry-run 生成预览")
            run_generate_dry_run(args.prepare_count, args.expand_count, rebuild_batch, args.verbose)
            print()
            print("[结果]")
            info("dry-run 不写入、不生成、不发布、不提交。")
            return 0

        print("[4/7] 安全生成草稿")
        run_generate(args.prepare_count, args.expand_count, rebuild_batch, args.verbose)
        final_check(before)
        print()

        if args.generate_only:
            info("--generate-only 已完成，不执行发布。")
            return 0

        print("[5/7] 生成后检查可发布候选")
        publish_candidates = run_publish_dry_run(args.limit, args.mode, args.verbose)
        info(f"可发布候选：{publish_candidates} 篇")
        print()

        if publish_candidates <= 0:
            warn("生成后仍无可发布候选，安全退出。")
            final_check(before)
            return 0

        publish_limit = min(args.limit, publish_candidates)
        print("[6/7] 安全发布")
        run_publish(publish_limit, args.mode, args.no_push, args.verbose)
        print()

        print("[7/7] 最终保护检查")
        final_check(before)
        return 0
    except DailyError as exc:
        fail(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
