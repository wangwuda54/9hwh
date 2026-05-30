from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from pre_publish_audit import classify_shape, select_candidates


ROOT = Path(__file__).resolve().parents[1]
PYTHON_EXE = "E:/python/python.exe"

CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_STATUS_PATH = CONTENT_DIR / "content_status.json"
CONTENT_QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
DRAFTS_DIR = ROOT / "site_src" / "content_drafts"
BLOG_INDEX_PATH = ROOT / "site" / "public" / "blog" / "index.html"
SITEMAP_PATH = ROOT / "site" / "public" / "sitemap.xml"
REVIEW_REPORT_PATH = ROOT / "data" / "content-assets" / "draft_review_report.json"
DAILY_REPORT_PATH = ROOT / "data" / "content-assets" / "daily_publish_report.json"
BACKUP_BASE = ROOT / "data" / "content-assets" / "manual-publish-backups"

BACKUP_FILES = [
    CONTENT_STATUS_PATH,
    CONTENT_QUEUE_PATH,
    PUBLISH_QUEUE_PATH,
    BLOG_INDEX_PATH,
    SITEMAP_PATH,
]

ALLOWED_ADD_PATHS = [
    "scripts/manual_expand_tasks_safe.py",
    "scripts/manual_generate_safe.py",
    "scripts/manual_daily_safe.py",
    "scripts/manual_publish_safe.py",
    "site_src/data/content",
    "site_src/content_drafts",
    "site/public",
    "data/content-assets",
    "data/deepseek-batches/batch-001/batch-001-index.json",
    "data/deepseek-batches/batch-001/batch-001-tasks.md",
    "data/deepseek-batches/batch-001/tasks",
    "docs",
]
FORBIDDEN_ADD_PATHS = [
    "data/deepseek-inbox",
    "data/deepseek-reviewed",
]

STATIC_SITE_OK_LINES = [
    "[OK] sitemap checks completed",
    "[OK] robots checks completed",
    "[OK] HTML quality checks completed",
    "[OK] video page checks completed",
    "[OK] keyword asset checks completed",
    "[OK] content pipeline checks completed",
    "[OK] DeepSeek batch checks completed",
]
STATIC_SITE_ALLOWED_FAILS = {
    "[FAIL] review_content_drafts.py failed",
    "[FAIL] 1 issue(s) found",
}

PLACEHOLDER_RE = re.compile(r"\?{8,}")
MARKDOWN_LINK_RE = re.compile(r"\]\((/[^)\s]+)\)")
BLOG_LOC_RE = re.compile(r"<loc>[^<]*/blog/[^<]*</loc>")


class PublishError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="9HWH safe manual publisher.")
    parser.add_argument("--limit", type=int, default=7, help="Maximum articles to publish.")
    parser.add_argument(
        "--mode",
        choices=["conservative", "normal", "growth", "aggressive"],
        default="normal",
        help="Publish selection mode.",
    )
    parser.add_argument("--no-push", action="store_true", help="Commit locally but do not push.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only; do not write, commit, or push.")
    parser.add_argument("--allow-warning", action="store_true", help="Allow warning review status if all hard checks pass.")
    parser.add_argument("--verbose", action="store_true", help="Print command output details.")
    return parser.parse_args()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def print_header() -> None:
    print("9HWH 安全手动发布")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def count_published() -> int:
    status = load_json(CONTENT_STATUS_PATH, {})
    return int(status.get("published", 0) or 0)


def count_blog_cards() -> int:
    if not BLOG_INDEX_PATH.exists():
        return 0
    return BLOG_INDEX_PATH.read_text(encoding="utf-8-sig").count("<article")


def count_sitemap_blog_urls() -> int:
    if not SITEMAP_PATH.exists():
        return 0
    return len(BLOG_LOC_RE.findall(SITEMAP_PATH.read_text(encoding="utf-8-sig")))


def run(command: list[str], *, check: bool = True, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if verbose:
        print(f"$ {' '.join(command)}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
    if check and completed.returncode != 0:
        raise PublishError(f"命令失败：{' '.join(command)}")
    return completed


def git_output(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        raise PublishError(completed.stderr.strip() or completed.stdout.strip() or "git 命令失败")
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
        status = line[:2]
        path = normalize_git_path(line[3:])
        rows.append((status, path, line))
    return rows


def starts_with_any(path: str, prefixes: list[str]) -> bool:
    clean = normalize_git_path(path)
    return any(clean == prefix or clean.startswith(prefix + "/") for prefix in prefixes)


def staged_rows(rows: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    return [row for row in rows if row[0][0] not in {" ", "?"}]


def check_git_status(dry_run: bool) -> None:
    remotes = git_output(["remote", "-v"])
    if "wangwuda54/9hwh" not in remotes:
        raise PublishError("当前目录不是 wangwuda54/9hwh，已停止。")

    rows = parse_git_status()
    if dry_run:
        if rows:
            warn("当前有未提交变化；dry-run 不会写入或提交。")
        else:
            ok("Git 状态干净")
        return

    staged = staged_rows(rows)
    if staged:
        details = ", ".join(path for _, path, _ in staged[:8])
        raise PublishError(f"检测到已暂存文件，避免误提交，已停止：{details}")

    if rows:
        warn("存在未提交变化；本脚本最终只会提交白名单目录，且会拒绝 staged 的 DeepSeek 运行目录。")
    else:
        ok("Git 状态干净")
    return

    forbidden_dirty = [path for _, path, _ in rows if starts_with_any(path, FORBIDDEN_ADD_PATHS)]
    if forbidden_dirty:
        details = ", ".join(forbidden_dirty[:8])
        raise PublishError(f"DeepSeek 运行目录有变化，禁止发布：{details}")

    allowed_dirty = [path for _, path, _ in rows if starts_with_any(path, ALLOWED_ADD_PATHS)]
    if allowed_dirty:
        details = ", ".join(allowed_dirty[:8])
        raise PublishError(f"发布白名单目录已有未提交变化，避免混入本次发布：{details}")

    if rows:
        warn("存在非发布目录未提交变化，本脚本不会提交它们。")
    else:
        ok("Git 状态干净")


def check_recovery_protection() -> None:
    tags = git_output(["tag", "--list", "blog-restored-2026-05-30"]).splitlines()
    if "blog-restored-2026-05-30" not in tags:
        raise PublishError("缺少恢复标签 blog-restored-2026-05-30，已停止。")
    published = count_published()
    if published <= 0:
        raise PublishError("published 不是大于 0，已停止，防止重建覆盖。")
    ok(f"published 保护开启：{published}")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    front = parts[1]
    body = parts[2]
    meta: dict[str, str] = {}
    current_key = ""
    for raw_line in front.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            meta[current_key] = value.strip().strip('"').strip("'")
        elif current_key:
            meta[current_key] = (meta[current_key] + " " + line).strip()
    return meta, body


def internal_links(body: str) -> list[str]:
    return list(dict.fromkeys(MARKDOWN_LINK_RE.findall(body)))


def review_map() -> dict[str, dict]:
    report = load_json(REVIEW_REPORT_PATH, {"articles": []})
    return {item.get("content_id", ""): item for item in report.get("articles", []) if item.get("content_id")}


def validate_candidate(
    entry: dict,
    content_by_id: dict[str, dict],
    reviews: dict[str, dict],
    allow_warning: bool,
) -> tuple[dict | None, list[str]]:
    reasons: list[str] = []
    content_id = entry.get("content_id", "")
    content_item = content_by_id.get(content_id, {})
    review = reviews.get(content_id, {})

    if not content_id:
        return None, ["missing content_id"]
    if entry.get("publish_status") == "published":
        return None, ["already published"]
    if not content_item:
        reasons.append("content_queue missing")
    elif content_item.get("status") != "reviewed":
        reasons.append("content_queue status is not reviewed")

    entry_review_status = entry.get("review_status")
    review_status = review.get("status") or entry_review_status
    if allow_warning:
        if review_status not in {"pass", "warning"}:
            reasons.append("review_status is not pass or warning")
    elif review_status != "pass" or entry_review_status not in {None, "pass"}:
        reasons.append("review_status is not pass")

    issues = []
    for source in (entry, review):
        value = source.get("issues") if isinstance(source, dict) else None
        if isinstance(value, list):
            issues.extend(value)
        elif value:
            issues.append(value)
    if issues:
        reasons.append("issues is not empty")

    draft_path = DRAFTS_DIR / f"{content_id}.md"
    if not draft_path.exists():
        reasons.append("draft missing")
        return None, reasons

    meta, body = parse_frontmatter(draft_path)
    if meta.get("status") != "reviewed":
        reasons.append("draft status is not reviewed")

    description = meta.get("description", "").strip()
    if not description:
        reasons.append("description missing")
    if PLACEHOLDER_RE.search(description):
        reasons.append("description has question placeholder")
    if PLACEHOLDER_RE.search(body):
        reasons.append("body has question placeholder")

    links = internal_links(body)
    if len(links) < 4:
        reasons.append("internal links fewer than 4")
    if int(entry.get("internal_link_count", len(links)) or 0) < 4:
        reasons.append("publish_queue internal_link_count fewer than 4")

    if reasons:
        return None, reasons

    merged = {**content_item, **entry}
    target_url = entry.get("target_url") or content_item.get("target_url", "")
    candidate = {
        "content_id": content_id,
        "title": meta.get("title") or entry.get("title") or content_item.get("title", ""),
        "target_url": target_url,
        "primary_keyword": meta.get("primary_keyword") or entry.get("primary_keyword") or content_item.get("primary_keyword", ""),
        "description": description,
        "risk_level": entry.get("risk_level") or content_item.get("risk_level", ""),
        "content_type": entry.get("content_type") or content_item.get("content_type", ""),
        "cluster_id": content_item.get("cluster_id", ""),
        "planned_publish_date": entry.get("planned_publish_date", ""),
        "priority_score": int(entry.get("priority_score", content_item.get("priority_score", 0)) or 0),
        "internal_link_count": len(links),
        "shape": classify_shape(merged),
    }
    return candidate, []


def find_publish_candidates(limit: int, mode: str, allow_warning: bool) -> tuple[list[dict], int]:
    content_queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    reviews = review_map()
    content_by_id = {item.get("content_id", ""): item for item in content_queue if item.get("content_id")}

    eligible_entries = [item for item in publish_queue if item.get("publish_status") != "published"]
    valid: list[dict] = []
    skipped: list[tuple[str, list[str]]] = []
    for entry in eligible_entries:
        candidate, reasons = validate_candidate(entry, content_by_id, reviews, allow_warning)
        if candidate:
            valid.append(candidate)
        else:
            skipped.append((entry.get("content_id", ""), reasons))

    selected, _ = select_candidates(valid, limit, "aggressive" if mode == "growth" else mode)
    return selected, len(valid)


def create_backup() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
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


def read_daily_report() -> dict:
    return load_json(DAILY_REPORT_PATH, {})


def is_allowed_daily_failure(report: dict) -> bool:
    if int(report.get("published_count", 0) or 0) <= 0:
        return False
    checks = report.get("post_publish_checks", [])
    failed = [item for item in checks if item.get("returncode")]
    if len(failed) != 1:
        return False
    failed_check = failed[0]
    if "check_static_site.py" not in failed_check.get("command", ""):
        return False
    stdout = failed_check.get("stdout", "")
    if not all(line in stdout for line in STATIC_SITE_OK_LINES):
        return False
    fail_lines = [line.strip() for line in stdout.splitlines() if "[FAIL]" in line]
    return bool(fail_lines) and all(line in STATIC_SITE_ALLOWED_FAILS for line in fail_lines)


def run_daily_publish(limit: int, mode: str, verbose: bool) -> int:
    command = [PYTHON_EXE, "scripts/daily_publish.py", "--mode", mode, "--limit", str(limit)]
    completed = run(command, check=False, verbose=verbose)
    report = read_daily_report()
    if completed.returncode == 0:
        return int(report.get("published_count", 0) or 0)
    if is_allowed_daily_failure(report):
        warn("daily_publish 的静态检查只有草稿复审旧问题，继续执行最终保护检查。")
        return int(report.get("published_count", 0) or 0)
    restore_count = int(report.get("published_count", 0) or 0)
    if restore_count == 0:
        raise PublishError("daily_publish 未成功发布文章，已停止。")
    raise PublishError("daily_publish 失败，已停止。")


def run_final_checks(verbose: bool) -> None:
    run([PYTHON_EXE, "scripts/build_site.py"], verbose=verbose)
    ok("构建通过")
    run([PYTHON_EXE, "scripts/check_sitemap_readiness.py"], verbose=verbose)
    ok("sitemap 检查通过")
    run([PYTHON_EXE, "scripts/check_placeholder_text.py"], verbose=verbose)
    ok("问号占位检查通过")


def anti_rollback_check(before_published: int, before_cards: int, before_sitemap: int, backup_dir: Path) -> tuple[int, int, int]:
    after_published = count_published()
    after_cards = count_blog_cards()
    after_sitemap = count_sitemap_blog_urls()

    if before_published > 0 and after_published == 0:
        restore_backup(backup_dir)
        raise PublishError("published 数量下降，已恢复备份，禁止提交。")
    if after_published < before_published:
        restore_backup(backup_dir)
        raise PublishError("published 数量下降，已恢复备份，禁止提交。")
    if after_cards < before_cards:
        restore_backup(backup_dir)
        raise PublishError("/blog/ 卡片数量下降，已恢复备份，禁止提交。")
    if after_sitemap < before_sitemap:
        restore_backup(backup_dir)
        raise PublishError("sitemap blog URL 数下降，已恢复备份，禁止提交。")

    ok(f"published: {before_published} -> {after_published}")
    ok(f"blog cards: {before_cards} -> {after_cards}")
    ok(f"sitemap blog URLs: {before_sitemap} -> {after_sitemap}")
    return after_published, after_cards, after_sitemap


def configure_git_identity() -> None:
    git_output(["config", "user.name", "9hwh-local-publisher"])
    git_output(["config", "user.email", "9hwh-local-publisher@users.noreply.github.com"])


def git_add_allowed() -> None:
    subprocess.run(["git", "add", "--", *ALLOWED_ADD_PATHS], cwd=ROOT, check=True)


def ensure_staged_files_allowed() -> list[str]:
    rows = parse_git_status()
    staged = staged_rows(rows)
    staged_paths = [path for _, path, _ in staged]
    forbidden = [path for path in staged_paths if starts_with_any(path, FORBIDDEN_ADD_PATHS)]
    if forbidden:
        raise PublishError("检测到禁止提交目录已暂存：" + ", ".join(forbidden[:8]))
    outside = [path for path in staged_paths if not starts_with_any(path, ALLOWED_ADD_PATHS)]
    if outside:
        raise PublishError("检测到白名单外文件已暂存：" + ", ".join(outside[:8]))
    return staged_paths


def commit_changes() -> bool:
    configure_git_identity()
    git_add_allowed()
    staged = ensure_staged_files_allowed()
    if not staged:
        ok("没有需要提交的变化")
        return False
    message = f"manual safe publish content {date.today().isoformat()}"
    completed = subprocess.run(["git", "commit", "-m", message], cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        raise PublishError(completed.stderr.strip() or completed.stdout.strip() or "commit 失败")
    ok("commit 成功")
    return True


def push_changes(no_push: bool, did_commit: bool) -> None:
    if no_push:
        ok("已按 --no-push 跳过推送")
        return
    if not did_commit:
        ok("没有新 commit，跳过推送")
        return
    run(["git", "push", "origin", "main"])
    ok("push 成功")


def dry_run(limit: int, mode: str, allow_warning: bool, before_published: int, before_cards: int, before_sitemap: int) -> int:
    selected, valid_count = find_publish_candidates(limit, mode, allow_warning)
    print(f"当前已发布：{before_published} 篇")
    print(f"当前 /blog/ 卡片：{before_cards} 个")
    print(f"当前 sitemap blog URL：{before_sitemap} 个")
    print(f"可发布候选数量：{valid_count} 篇")
    ids = [item["content_id"] for item in selected]
    print("将会发布的候选 content_id：" + (", ".join(ids) if ids else "无"))
    return 0


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        fail("limit 不能小于 0")
        return 1

    print_header()
    before_published = count_published()
    before_cards = count_blog_cards()
    before_sitemap = count_sitemap_blog_urls()

    if args.dry_run:
        try:
            check_git_status(dry_run=True)
            check_recovery_protection()
            return dry_run(args.limit, args.mode, args.allow_warning, before_published, before_cards, before_sitemap)
        except PublishError as exc:
            fail(str(exc))
            return 1

    print(f"当前已发布：{before_published} 篇")
    print(f"当前 /blog/ 卡片：{before_cards} 个")
    print(f"当前 sitemap blog URL：{before_sitemap} 个")
    print()

    backup_dir: Path | None = None
    try:
        print("[1/8] 检查保护状态")
        check_git_status(dry_run=False)
        check_recovery_protection()
        print()

        print("[2/8] 查找可发布候选")
        selected, valid_count = find_publish_candidates(args.limit, args.mode, args.allow_warning)
        if not selected:
            ok("可发布候选：0 篇，本次无需发布。")
            return 0
        ok(f"可发布候选：{valid_count} 篇")
        if args.verbose:
            print("本次候选：" + ", ".join(item["content_id"] for item in selected))
        print()

        print("[3/8] 备份关键文件")
        backup_dir = create_backup()
        ok(f"已备份到 {rel(backup_dir)}")
        print()

        print("[4/8] 发布文章")
        published_count = run_daily_publish(min(args.limit, len(selected)), args.mode, args.verbose)
        if published_count <= 0:
            raise PublishError("本次发布数量为 0，禁止继续提交。")
        ok(f"本次发布：{published_count} 篇")
        print()

        print("[5/8] 构建和检查")
        try:
            run_final_checks(args.verbose)
        except Exception:
            if backup_dir:
                restore_backup(backup_dir)
            raise
        print()

        print("[6/8] 防回退检查")
        assert backup_dir is not None
        anti_rollback_check(before_published, before_cards, before_sitemap, backup_dir)
        print()

        print("[7/8] 提交")
        did_commit = commit_changes()
        print()

        print("[8/8] 推送")
        push_changes(args.no_push, did_commit)
        return 0
    except PublishError as exc:
        message = str(exc)
        if backup_dir and "已恢复备份" not in message:
            restore_backup(backup_dir)
            message = f"{message} 已恢复备份，禁止提交。"
        fail(message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
