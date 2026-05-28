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
INBOX_ROOT = ROOT / "data" / "deepseek-inbox"
ASSETS = ROOT / "data" / "content-assets"
PYTHON = sys.executable

TRACKED_OUTPUTS = [
    "site_src/data/content",
    "site_src/content_drafts",
    "site/public",
    "data/content-assets",
    "docs",
]

RUNTIME_DIR_MARKERS = [
    "data/deepseek-inbox",
    "data/deepseek-reviewed",
]

PROTECTED_QUEUE_STATUSES = {"published", "paused"}
PUBLISHABLE_REVIEW_STATUSES = {"pass"}
PLACEHOLDER_RE = re.compile(r"\?{8,}")
SKIP_DRAFT_NAMES = {"README.MD"}
VERBOSE = False


class StepError(RuntimeError):
    pass


def log(message: str = "") -> None:
    print(message, flush=True)


def title(message: str) -> None:
    log("\n" + message)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_cmd(
    command: list[str],
    label: str,
    *,
    check: bool = True,
    quiet_success: bool = True,
    show_success: bool = True,
    failure_tail: int = 60,
) -> subprocess.CompletedProcess:
    if VERBOSE:
        log("$ " + " ".join(command))

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    if completed.returncode == 0:
        if not quiet_success or VERBOSE:
            if stdout.strip():
                log(stdout.rstrip())
            if stderr.strip():
                log(stderr.rstrip())
        if show_success:
            log(f"[OK] {label}")
        return completed

    if check:
        log(f"[FAIL] {label}")
        output = (stdout + "\n" + stderr).strip()
        if output:
            lines = output.splitlines()
            if len(lines) > failure_tail:
                lines = lines[-failure_tail:]
                log(f"[INFO] 只显示最后 {failure_tail} 行错误输出：")
            for line in lines:
                log(line)
        raise StepError(f"{label}失败，退出码 {completed.returncode}")

    if VERBOSE:
        if stdout.strip():
            log(stdout.rstrip())
        if stderr.strip():
            log(stderr.rstrip())
    return completed


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_record(report: dict, command_name: str) -> dict:
    for item in report.get("post_publish_checks") or []:
        command = str(item.get("command") or "")
        if command_name in command.replace("\\", "/"):
            return item
    return {}


def is_recoverable_static_site_failure(stdout: str) -> bool:
    required_ok_lines = {
        "[OK] sitemap checks completed",
        "[OK] robots checks completed",
        "[OK] HTML quality checks completed",
        "[OK] video page checks completed",
        "[OK] keyword asset checks completed",
        "[OK] content pipeline checks completed",
        "[OK] DeepSeek batch checks completed",
    }
    lines = [line.strip() for line in str(stdout or "").splitlines() if line.strip()]
    if not required_ok_lines.issubset(set(lines)):
        return False

    allowed_failures = {
        "[FAIL] review_content_drafts.py failed",
        "[FAIL] 1 issue(s) found",
    }
    fail_lines = [line for line in lines if "[FAIL]" in line]
    return bool(fail_lines) and all(line in allowed_failures for line in fail_lines)


def is_recoverable_daily_publish_failure(report: dict) -> bool:
    build_check = check_record(report, "scripts/build_site.py")
    static_check = check_record(report, "scripts/check_static_site.py")
    if int(build_check.get("returncode", 999)) != 0:
        return False
    if int(static_check.get("returncode", 0)) == 0:
        return False
    if not is_recoverable_static_site_failure(str(static_check.get("stdout") or "")):
        return False

    error_text = "\n".join(str(error) for error in report.get("errors") or [])
    message_text = str(report.get("message") or "")
    if "post publish check failed" not in (error_text + "\n" + message_text).lower():
        return False

    if int(report.get("published_count") or 0) > 0:
        return True

    # Some older failed reports were written after content state had already moved,
    # but counters stayed at zero. Treat the post-publish check evidence as enough
    # to enter recovery so reruns do not publish the next batch.
    return True


def detect_pending_recoverable_publish() -> dict | None:
    report = load_json(ASSETS / "daily_publish_report.json", {})
    if report.get("status") == "failure" and is_recoverable_daily_publish_failure(report):
        return report
    return None


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_md_text(text: str) -> tuple[dict[str, str], list[str], str]:
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


def render_frontmatter(lines: list[str], updates: dict[str, str]) -> list[str]:
    output: list[str] = []
    seen = set()

    for line in lines:
        if ":" not in line:
            output.append(line)
            continue
        key = line.split(":", 1)[0].strip()
        if key in updates:
            output.append(f"{key}: {updates[key]}")
            seen.add(key)
        else:
            output.append(line)

    missing = [key for key in updates if key not in seen]
    if missing:
        insert_at = 0
        for index, line in enumerate(output):
            if line.startswith("title:"):
                insert_at = index + 1
                break
        for key in reversed(missing):
            output.insert(insert_at, f"{key}: {updates[key]}")

    return output


def parse_md(path: Path) -> tuple[dict[str, str], list[str], str]:
    return parse_md_text(path.read_text(encoding="utf-8-sig"))


def set_markdown_status(text: str, status: str) -> str:
    if not text.startswith("---"):
        raise StepError("Markdown 缺少 front matter，不能改状态。")

    meta, lines, body = parse_md_text(text)
    new_lines = render_frontmatter(lines, {"status": status})
    return "---\n" + "\n".join(new_lines).strip() + "\n---\n" + body.rstrip() + "\n"


def update_frontmatter_status(path: Path, status: str) -> None:
    path.write_text(
        set_markdown_status(path.read_text(encoding="utf-8-sig"), status),
        encoding="utf-8",
        newline="\n",
    )


def extract_internal_links(body: str) -> list[str]:
    return re.findall(r"\]\((/[^)\s]+)\)", body)


def has_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.search(str(value or "")))


def is_bad_description(description: str) -> bool:
    text = str(description or "").strip()
    if not text:
        return True
    compact = re.sub(r"\s+", "", text)
    return bool(compact) and set(compact) == {"?"}


def make_description(meta: dict[str, str]) -> str:
    title_text = meta.get("title") or meta.get("h1") or meta.get("primary_keyword") or "海外推广内容"
    keyword = meta.get("primary_keyword") or title_text.split("：", 1)[0]

    if any(token in title_text for token in ["费用", "价格", "成本"]):
        return (
            f"{title_text}，围绕真实搜索需求梳理影响预算的关键因素、渠道选择、素材测试和落地页准备，"
            "帮助团队更清楚地评估投放成本和咨询沟通重点。"
        )

    if "怎么做" in title_text:
        return (
            f"{title_text}，梳理海外推广的执行路径、渠道判断、素材测试、落地页承接和转化追踪准备，"
            "帮助团队先小预算测试，再逐步优化获客效果。"
        )

    if keyword and keyword != title_text:
        return (
            f"本文围绕{keyword}，梳理海外推广与获客测试的准备重点、渠道判断、素材方向和落地页承接方式，"
            "帮助团队在咨询前形成清晰执行路径。"
        )

    return (
        f"{title_text}，梳理海外推广与获客测试的准备重点、渠道判断、素材方向和落地页承接方式，"
        "帮助团队在咨询前形成清晰执行路径。"
    )


def repair_placeholder_line(line: str) -> str:
    if not has_placeholder(line):
        return line

    links = re.findall(r"\[([^\]]+)\]\((/[^)]+)\)", line)
    cleaned = PLACEHOLDER_RE.sub("", line)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.strip(" ，,。；;：:")

    # If a line still has readable Chinese text after removing question marks, keep it.
    if re.search(r"[\u4e00-\u9fff]", cleaned) and len(cleaned) >= 12:
        if not cleaned.endswith(("。", "！", "？")):
            cleaned += "。"
        return cleaned

    # If only a link remains, turn it into a normal related-resource sentence.
    if links:
        link_text, href = links[0]
        if has_placeholder(link_text) or is_bad_description(link_text):
            link_text = readable_link_text(href)
        return f"如果需要继续梳理渠道和投放准备，可以先查看 [{link_text}]({href})，再结合预算、素材和落地页做小范围测试。"

    # Otherwise drop the corrupted line.
    return ""


def readable_link_text(href: str) -> str:
    labels = {
        "/services/ad-campaign-support/": "广告投放支持",
        "/services/traffic-acquisition/": "海外引流获客",
        "/services/media-buying/": "海外买量投放",
        "/services/": "服务范围",
        "/topics/crypto-promotion/": "加密货币推广",
        "/topics/dating-traffic/": "交友项目引流",
        "/topics/finance-leads/": "金融线索获客",
        "/topics/game-promotion/": "游戏推广",
        "/topics/immigration-leads/": "移民咨询获客",
        "/topics/insurance-leads/": "保险线索获客",
        "/topics/loan-leads/": "贷款线索获客",
        "/topics/online-work-leads/": "网赚兼职获客",
        "/platforms/fb/": "Facebook 推广",
        "/platforms/google/": "Google 推广",
        "/platforms/tk/": "TikTok 推广",
        "/topics/": "内容专题",
        "/contact/": "联系咨询",
    }
    if href in labels:
        return labels[href]
    slug = href.strip("/").split("/")[-1].replace("-", " ").strip()
    return slug.title() if slug else "相关页面"


def repair_draft_placeholders(path: Path) -> bool:
    if path.name.upper() in SKIP_DRAFT_NAMES:
        return False

    text = path.read_text(encoding="utf-8-sig")
    meta, lines, body = parse_md_text(text)
    if not meta:
        return False

    changed = False
    updates: dict[str, str] = {}

    description = meta.get("description", "")
    if is_bad_description(description) or has_placeholder(description):
        updates["description"] = make_description(meta)
        changed = True

    new_body_lines: list[str] = []
    for line in body.splitlines():
        repaired = repair_placeholder_line(line)
        if repaired != line:
            changed = True
        if repaired.strip():
            new_body_lines.append(repaired.rstrip() if repaired != line else line)
        elif not line.strip():
            new_body_lines.append("")

    if not changed:
        return False

    new_lines = render_frontmatter(lines, updates)
    new_text = "---\n" + "\n".join(new_lines).strip() + "\n---\n" + "\n".join(new_body_lines).strip() + "\n"
    path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def draft_has_placeholder(path: Path) -> bool:
    if not path.exists() or path.name.upper() in SKIP_DRAFT_NAMES:
        return False
    meta, _, body = parse_md(path)
    return (
        is_bad_description(meta.get("description", ""))
        or has_placeholder(meta.get("description", ""))
        or has_placeholder(body)
    )


def repair_all_placeholder_drafts() -> int:
    repaired = 0
    for path in sorted(DRAFTS.glob("*.md")):
        if repair_draft_placeholders(path):
            repaired += 1
    return repaired


def git_status_porcelain() -> list[str]:
    completed = run_cmd(["git", "status", "--porcelain"], "读取 Git 状态", check=False, show_success=False)
    return [line for line in (completed.stdout or "").splitlines() if line.strip()]


def maybe_git_pull(skip_pull: bool) -> None:
    title("[1/12] 检查 Git 状态")
    status = git_status_porcelain()
    if status:
        runtime_count = sum(1 for line in status if any(marker in line for marker in RUNTIME_DIR_MARKERS))
        other_count = len(status) - runtime_count
        log(f"[WARN] 本地已有 {len(status)} 个变更，跳过 git pull，避免覆盖本地文件。")
        log(f"[INFO] DeepSeek 临时文件：{runtime_count} 个；其他文件：{other_count} 个。")
        return

    if skip_pull:
        log("[INFO] 已按参数跳过 git pull。")
        return

    run_cmd(["git", "pull", "--ff-only"], "拉取最新代码")


def batch_index_path(batch_id: str) -> Path:
    return BATCH_ROOT / batch_id / f"{batch_id}-index.json"


def load_batch_items(batch_id: str) -> list[dict]:
    return load_json(batch_index_path(batch_id), [])


def batch_content_ids(batch_id: str) -> set[str]:
    return {item.get("content_id", "") for item in load_batch_items(batch_id) if item.get("content_id")}


def rebuild_task_queue_and_batch(batch_id: str) -> None:
    log("[INFO] 没有可用任务，开始自动重建任务。")

    build_queue = SCRIPTS / "build_content_queue.py"
    build_batch = SCRIPTS / "build_deepseek_batch.py"

    if build_queue.exists():
        run_cmd([PYTHON, str(build_queue)], "重建内容队列")
    else:
        log(f"[WARN] 找不到 {rel(build_queue)}，跳过内容队列重建。")

    if build_batch.exists():
        run_cmd([PYTHON, str(build_batch)], "重建 DeepSeek 任务包")
    else:
        log(f"[WARN] 找不到 {rel(build_batch)}，跳过任务包重建。")

    if not batch_index_path(batch_id).exists():
        raise StepError(f"重建后仍找不到任务包：{rel(batch_index_path(batch_id))}")


def ensure_task_batch(batch_id: str) -> None:
    title("[2/12] 判断任务包")
    items = load_batch_items(batch_id)
    if items:
        log(f"[OK] 任务包存在：{batch_id}，共 {len(items)} 个任务。")
        return

    log(f"[WARN] 任务包不存在或为空：{rel(batch_index_path(batch_id))}")
    rebuild_task_queue_and_batch(batch_id)
    items = load_batch_items(batch_id)
    log(f"[OK] 任务包已重建：{len(items)} 个任务。")


def output_path_for(batch_id: str, content_id: str) -> Path:
    return INBOX_ROOT / batch_id / f"{content_id}.md"


def generation_failure_reason(content_id: str) -> str:
    report = load_json(ASSETS / "deepseek_api_generation_report.json", {})
    for item in report.get("failed") or []:
        if item.get("content_id") == content_id:
            return str(item.get("reason") or "").strip()
    return ""


def generate_one(batch_id: str, content_id: str, *, overwrite: bool, sleep_seconds: float) -> bool:
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
    if overwrite:
        command.append("--overwrite")

    completed = run_cmd(command, f"生成 {content_id}", check=False)
    if completed.returncode == 0:
        return True

    reason = generation_failure_reason(content_id)
    log(f"[WARN] 生成失败，已跳过：{content_id}")
    if reason:
        log(f"[WARN] 原因：{reason}")
    else:
        log("[WARN] 原因未写入报告，可查看 data/content-assets/deepseek_api_generation_report.json。")
    return False


def replace_draft_from_generated(batch_id: str, content_id: str) -> bool:
    output_path = output_path_for(batch_id, content_id)
    draft_path = DRAFTS / f"{content_id}.md"

    if not output_path.exists():
        log(f"[WARN] 生成输出不存在，无法替换坏稿：{rel(output_path)}")
        return False

    old_status = "draft_received"
    if draft_path.exists():
        old_meta, _, _ = parse_md(draft_path)
        old_status = old_meta.get("status", "draft_received") or "draft_received"

    generated_text = output_path.read_text(encoding="utf-8-sig")
    new_meta, _, new_body = parse_md_text(generated_text)

    if new_meta.get("content_id") != content_id:
        log(f"[WARN] 生成输出 content_id 不匹配，跳过替换：{content_id}")
        return False

    if (
        is_bad_description(new_meta.get("description", ""))
        or has_placeholder(new_meta.get("description", ""))
        or has_placeholder(new_body)
    ):
        log(f"[WARN] 重新生成后仍有问号占位，改用本地清理：{content_id}")

    draft_path.write_text(set_markdown_status(generated_text, old_status), encoding="utf-8", newline="\n")
    repair_draft_placeholders(draft_path)
    if draft_has_placeholder(draft_path):
        log(f"[WARN] 替换后仍有问号占位，后续不会发布：{content_id}")
        return False

    log(f"[OK] 已替换坏稿：{content_id}")
    return True


def find_bad_existing_draft_ids(batch_id: str, repair_limit: int) -> tuple[list[str], int]:
    known_ids = batch_content_ids(batch_id)
    in_batch: list[str] = []
    outside_batch_count = 0

    for path in sorted(DRAFTS.glob("*.md")):
        if path.name.upper() in SKIP_DRAFT_NAMES:
            continue
        if not draft_has_placeholder(path):
            continue

        meta, _, _ = parse_md(path)
        content_id = meta.get("content_id", "") or path.stem
        if content_id not in known_ids:
            outside_batch_count += 1
            continue

        in_batch.append(content_id)
        if len(in_batch) >= repair_limit:
            break

    return in_batch, outside_batch_count


def repair_placeholder_drafts(batch_id: str, repair_limit: int, sleep_seconds: float) -> None:
    title("[3/12] 检查和修复坏稿")

    local_repaired = repair_all_placeholder_drafts()
    if local_repaired:
        log(f"[OK] 已本地清理问号占位稿：{local_repaired} 篇。")

    bad_ids, outside_count = find_bad_existing_draft_ids(batch_id, max(repair_limit, 1))
    if outside_count:
        log(f"[INFO] 还有 {outside_count} 篇坏稿不在当前任务包，已尽量本地清理；若仍失败，会在检查阶段汇总。")

    if not bad_ids:
        log("[OK] 当前任务包内没有需要重生的坏稿。")
        return

    log(f"[WARN] 当前任务包内还有 {len(bad_ids)} 篇坏稿，尝试重新生成。")
    success_count = 0
    failed_count = 0

    for index, content_id in enumerate(bad_ids, start=1):
        log(f"[{index}/{len(bad_ids)}] 重生坏稿：{content_id}")
        ok = generate_one(batch_id, content_id, overwrite=True, sleep_seconds=sleep_seconds)
        if ok and replace_draft_from_generated(batch_id, content_id):
            success_count += 1
        else:
            failed_count += 1

    log(f"[INFO] 坏稿重生完成：成功 {success_count} 篇，失败/跳过 {failed_count} 篇。")


def draft_exists(content_id: str) -> bool:
    return (DRAFTS / f"{content_id}.md").exists()


def choose_generation_ids(batch_id: str, limit: int) -> list[str]:
    items = load_batch_items(batch_id)
    queue = load_json(CONTENT_QUEUE, [])
    queue_by_id = {item.get("content_id"): item for item in queue if item.get("content_id")}

    selected: list[str] = []
    for item in items:
        content_id = item.get("content_id", "")
        if not content_id:
            continue

        queue_item = queue_by_id.get(content_id, {})
        if queue_item.get("status", "") in PROTECTED_QUEUE_STATUSES:
            continue

        if draft_exists(content_id):
            continue

        selected.append(content_id)
        if len(selected) >= limit:
            break

    return selected


def generate_missing_drafts(batch_id: str, limit: int, overwrite_generation: bool, sleep_seconds: float) -> None:
    title("[4/12] 生成缺失文章")
    ids = choose_generation_ids(batch_id, limit)

    if not ids:
        log("[INFO] 当前任务包没有缺失草稿，尝试重建任务包再判断。")
        rebuild_task_queue_and_batch(batch_id)
        ids = choose_generation_ids(batch_id, limit)

    if not ids:
        log("[OK] 没有缺失草稿，后续直接审核和发布现有内容。")
        return

    log(f"[INFO] 需要生成 {len(ids)} 篇。")
    success_count = 0
    failed_count = 0

    for index, content_id in enumerate(ids, start=1):
        log(f"[{index}/{len(ids)}] 生成文章：{content_id}")
        ok = generate_one(
            batch_id,
            content_id,
            overwrite=overwrite_generation,
            sleep_seconds=sleep_seconds,
        )
        if ok:
            success_count += 1
        else:
            failed_count += 1

    log(f"[INFO] 生成完成：成功 {success_count} 篇，失败/跳过 {failed_count} 篇。")


def parse_import_counts(output: str) -> tuple[int, int, int]:
    match = re.search(r"imported\s+(\d+)\s+drafts,\s+skipped\s+(\d+),\s+failed\s+(\d+)", output)
    if not match:
        return 0, 0, 0
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def import_drafts_soft() -> tuple[int, int, int]:
    completed = run_cmd(
        [PYTHON, str(SCRIPTS / "import_deepseek_drafts.py")],
        "导入 DeepSeek 草稿",
        check=False,
        show_success=False,
    )
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    imported, skipped, failed = parse_import_counts(output)

    if completed.returncode == 0:
        log(f"[OK] 导入完成：新增 {imported} 篇，跳过 {skipped} 篇。")
    else:
        log(f"[WARN] 导入脚本返回失败，但不中断：新增 {imported} 篇，跳过 {skipped} 篇，失败 {failed} 篇。")
        log("[INFO] 失败项会跳过，不影响已成功导入的文章。")

    return imported, skipped, failed


def review_drafts_soft() -> tuple[int, int, int]:
    repair_result = run_cmd(
        [PYTHON, str(SCRIPTS / "repair_placeholder_descriptions.py"), "--write", "--fail-on-remaining"],
        "修复摘要占位",
        check=False,
        show_success=False,
    )
    if repair_result.returncode == 0:
        log("[OK] 摘要占位修复完成。")
    else:
        log("[WARN] 仍有摘要占位未能自动修复；这些稿件不会进入发布池，最终产物仍会做硬检查。")

    # Local body placeholder cleanup after import, because the upstream repair script only repairs descriptions.
    body_repaired = repair_all_placeholder_drafts()
    if body_repaired:
        log(f"[OK] 已清理正文问号占位：{body_repaired} 篇。")

    review_result = run_cmd(
        [PYTHON, str(SCRIPTS / "review_content_drafts.py")],
        "审核草稿",
        check=False,
        show_success=False,
    )
    review_output = (review_result.stdout or "") + "\n" + (review_result.stderr or "")
    match = re.search(r"reviewed\s+(\d+)\s+drafts,\s+failures\s+(\d+),\s+warnings\s+(\d+)", review_output)

    if match:
        reviewed_count = int(match.group(1))
        failure_count = int(match.group(2))
        warning_count = int(match.group(3))
        if review_result.returncode == 0:
            log(f"[OK] 审核完成：共 {reviewed_count} 篇，通过，无失败。")
        else:
            log(f"[WARN] 审核完成但存在问题稿：共 {reviewed_count} 篇，失败 {failure_count} 篇，警告 {warning_count} 篇。")
            log("[INFO] 失败稿不会进入发布池；脚本会继续发布已通过审核的文章。")
    else:
        if review_result.returncode == 0:
            log("[OK] 审核完成。")
        else:
            log("[WARN] 审核脚本返回失败，但不中断；后续只发布通过审核的文章。")
    return reviewed_count if match else 0, failure_count if match else 0, warning_count if match else 0


def import_and_review() -> None:
    title("[5/12] 导入和审核")
    import_drafts_soft()
    review_drafts_soft()


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


def review_map() -> dict[str, dict]:
    report = load_json(ASSETS / "draft_review_report.json", {"articles": []})
    return {item.get("content_id", ""): item for item in report.get("articles", []) if item.get("content_id")}


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


def promote_passed_drafts(limit: int, allow_warning: bool = False) -> list[str]:
    title("[6/12] 放入发布池")
    allowed = set(PUBLISHABLE_REVIEW_STATUSES)
    if allow_warning:
        log("[WARN] --allow-warning 已保留兼容，但当前安全规则只发布 pass 且无 issues 的草稿。")

    queue = load_json(CONTENT_QUEUE, [])
    publish_queue = load_json(PUBLISH_QUEUE, [])
    reviews = review_map()
    queue_by_id = {item.get("content_id"): item for item in queue if item.get("content_id")}
    publish_by_id = {item.get("content_id"): item for item in publish_queue if item.get("content_id")}

    candidates: list[tuple[int, str, dict, dict, int]] = []
    skipped_placeholder = 0
    skipped_links = 0

    for content_id, review_item in reviews.items():
        if review_item.get("status") not in allowed:
            continue
        if review_item.get("issues"):
            continue

        queue_item = queue_by_id.get(content_id)
        if not queue_item or queue_item.get("status") in {"published", "paused"}:
            continue

        draft_path = DRAFTS / f"{content_id}.md"
        if not draft_path.exists():
            continue

        meta, _, body = parse_md(draft_path)
        description = meta.get("description", "")

        if is_bad_description(description) or has_placeholder(description) or has_placeholder(body):
            skipped_placeholder += 1
            continue

        internal_link_count = len(list(dict.fromkeys(extract_internal_links(body))))
        if internal_link_count < 4:
            skipped_links += 1
            continue

        priority = int(queue_item.get("priority", queue_item.get("priority_score", 0)) or 0)
        candidates.append((priority, content_id, queue_item, review_item, internal_link_count))

    candidates.sort(key=lambda row: (row[0], row[1]))

    promoted: list[str] = []
    for _, content_id, queue_item, review_item, internal_link_count in candidates:
        if len(promoted) >= limit:
            break

        queue_item["status"] = "reviewed"
        update_frontmatter_status(DRAFTS / f"{content_id}.md", "reviewed")

        new_entry = queue_item_to_publish_entry(queue_item, review_item, internal_link_count)
        entry = publish_by_id.get(content_id)
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

    if not promoted:
        log("[FAIL] 没有可发布文章：没有 pass 且无 issues、无问号占位、内链达标的候选。")
        if skipped_placeholder:
            log(f"[INFO] 问号占位跳过：{skipped_placeholder} 篇。")
        if skipped_links:
            log(f"[INFO] 内链不足跳过：{skipped_links} 篇。")
        raise StepError("没有可发布文章。")

    log(f"[OK] 已放入发布池：{len(promoted)} 篇。")
    if skipped_placeholder:
        log(f"[INFO] 跳过问号占位稿：{skipped_placeholder} 篇。")
    if skipped_links:
        log(f"[INFO] 跳过内链不足稿：{skipped_links} 篇。")

    for content_id in promoted:
        log(f"  - {content_id}")

    return promoted


def promote_reviewed_candidates(limit: int, allow_warning: bool) -> list[str]:
    return promote_passed_drafts(limit, allow_warning)


def summarize_daily_publish_failure(report: dict, completed: subprocess.CompletedProcess) -> None:
    errors = [str(error) for error in report.get("errors") or [] if str(error).strip()]
    message = str(report.get("message") or "").strip()
    if message:
        log(f"[FAIL] 摘要：{message}")
    for error in errors[:5]:
        log(f"[FAIL] 原因：{error}")

    if not errors and not message:
        output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
        if output:
            for line in output.splitlines()[-10:]:
                log(line)


def publish_soft(limit: int, mode: str) -> None:
    title("[7/12] 发布文章")
    completed = run_cmd(
        [PYTHON, str(SCRIPTS / "daily_publish.py"), "--mode", mode, "--limit", str(limit)],
        "发布文章",
        check=False,
        show_success=False,
    )
    if completed.returncode == 0:
        report = load_json(ASSETS / "daily_publish_report.json", {})
        log(f"[OK] 发布完成：{int(report.get('published_count') or 0)} 篇。")
        return

    report = load_json(ASSETS / "daily_publish_report.json", {})
    if is_recoverable_daily_publish_failure(report):
        log("[WARN] 发布已完成，但全量审核门禁失败；失败稿会跳过，继续提交已通过文章。")
        return

    log("[FAIL] 发布文章")
    summarize_daily_publish_failure(report, completed)
    raise StepError("发布文章失败。")


def publish(limit: int, mode: str) -> None:
    publish_soft(limit, mode)


def summarize_placeholder_failure(output: str) -> None:
    failures = [line for line in output.splitlines() if "placeholder text found:" in line]
    if not failures:
        return

    log(f"[FAIL] 仍发现问号占位：{len(failures)} 处。")
    log("[INFO] 只显示前 15 处：")
    for line in failures[:15]:
        simplified = line.replace("[FAIL] placeholder text found: ", "")
        log("  - " + simplified[:220])
    if len(failures) > 15:
        log(f"  ... 还有 {len(failures) - 15} 处。")


def build_and_check_final() -> None:
    title("[8/12] 构建站点")
    run_cmd([PYTHON, str(SCRIPTS / "build_site.py")], "构建站点")

    title("[9/12] 检查站点")
    run_cmd([PYTHON, str(SCRIPTS / "check_sitemap_readiness.py")], "Sitemap 检查")

    completed = run_cmd(
        [PYTHON, str(SCRIPTS / "check_placeholder_text.py")],
        "问号占位检查",
        check=False,
        show_success=False,
    )
    if completed.returncode != 0:
        summarize_placeholder_failure((completed.stdout or "") + "\n" + (completed.stderr or ""))
        raise StepError("问号占位检查失败，需要继续重生或清理坏稿。")
    log("[OK] 问号占位检查")

    static_result = run_cmd([PYTHON, str(SCRIPTS / "check_static_site.py")], "静态站点检查", check=False)
    static_output = (static_result.stdout or "") + "\n" + (static_result.stderr or "")
    if static_result.returncode == 0:
        log("[OK] 静态站点检查")
        return
    if is_recoverable_static_site_failure(static_output):
        log("[WARN] 静态站点检查仅全量草稿审核门禁失败；已确认其他站点检查通过，继续。")
        return

    log("[FAIL] 静态站点检查")
    output = static_output.strip()
    if output:
        fail_lines = [line for line in output.splitlines() if "[FAIL]" in line]
        for line in (fail_lines or output.splitlines()[-20:])[:20]:
            log(line)
    raise StepError("静态站点检查失败。")


def build_and_check() -> None:
    build_and_check_final()


def git_commit_and_push(push: bool) -> None:
    title("[10/12] 提交站点变更")
    for item in TRACKED_OUTPUTS:
        run_cmd(["git", "add", item], f"加入提交：{item}", show_success=False)

    staged = run_cmd(["git", "diff", "--cached", "--name-only"], "读取待提交文件", check=False, show_success=False).stdout.splitlines()
    if not staged:
        log("[INFO] 没有需要提交的站点变更。")
        return

    log(f"[INFO] 待提交文件：{len(staged)} 个。")

    message = f"manual one-click publish content {datetime.now().date().isoformat()}"
    commit_result = run_cmd(["git", "commit", "-m", message], "Git 提交", check=False)
    if commit_result.returncode != 0:
        output = (commit_result.stdout + "\n" + commit_result.stderr).strip().lower()
        if "nothing to commit" in output or "no changes added" in output:
            log("[INFO] Git 没有新提交。")
            return
        raise StepError("git commit 失败")

    if push:
        title("[11/12] 推送到 GitHub")
        run_cmd(["git", "push", "origin", "main"], "推送到 GitHub")
    else:
        log("[INFO] 已提交到本地，但未 push。需要推送时执行：git push origin main")


def recover_previous_publish_if_needed() -> bool:
    report = detect_pending_recoverable_publish()
    if not report:
        return False

    title("[2/12] 恢复上次半成功发布")
    log("[WARN] 检测到上次已发布文章，但卡在全量草稿审核门禁。")
    log(f"[OK] 本次不再执行 daily_publish.py，避免重复发布下一批；直接构建、检查、提交。")
    log(f"[INFO] 上次已发布：{int(report.get('published_count') or 0)} 篇。")
    return True


def final_report() -> None:
    title("[12/12] 结果摘要")
    report = load_json(ASSETS / "daily_publish_report.json", {})

    status = report.get("status", "unknown")
    published_count = int(report.get("published_count") or 0)
    total_published = int(report.get("total_published") or 0)
    message = report.get("message", "")

    log(f"发布状态：{status}")
    log(f"本次发布：{published_count} 篇")
    log(f"累计发布：{total_published} 篇")
    if message:
        log(f"说明：{message}")

    items = report.get("published_items") or []
    if items:
        log("\n已发布 URL：")
        for item in items:
            log(f"  - {item.get('content_id')} {item.get('full_url') or item.get('target_url')}")

    status_lines = git_status_porcelain()
    runtime_leftovers = [line for line in status_lines if any(marker in line for marker in RUNTIME_DIR_MARKERS)]
    other_leftovers = [line for line in status_lines if line not in runtime_leftovers]

    if runtime_leftovers:
        log(f"\n[INFO] DeepSeek 临时/归档文件未提交：{len(runtime_leftovers)} 个，这是正常的。")

    if other_leftovers:
        log("\n[WARN] 还有非临时文件未提交：")
        for line in other_leftovers[:20]:
            log("  " + line)
        if len(other_leftovers) > 20:
            log(f"  ... 还有 {len(other_leftovers) - 20} 个。")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="9HWH 本地一键生成、审核、发布、构建、检查、提交。")
    parser.add_argument("--limit", type=int, default=7, help="每天生成/发布数量，默认 7。")
    parser.add_argument("--batch", default="batch-001", help="DeepSeek 任务包，默认 batch-001。")
    parser.add_argument(
        "--mode",
        choices=["conservative", "normal", "growth", "aggressive"],
        default="normal",
        help="发布节奏，默认 normal。",
    )
    parser.add_argument("--no-push", action="store_true", help="只本地提交，不 push。")
    parser.add_argument("--skip-pull", action="store_true", help="跳过 git pull。")
    parser.add_argument("--allow-warning", action="store_true", help="兼容旧参数；当前安全规则仍只发布 pass 且无 issues 的草稿。")
    parser.add_argument("--overwrite-generation", action="store_true", help="允许覆盖 DeepSeek inbox 里的同名生成输出。")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="DeepSeek 生成间隔秒数，默认 1。")
    parser.add_argument("--repair-limit", type=int, default=50, help="每次最多重生多少篇问号坏稿，默认 50。")
    parser.add_argument("--verbose", action="store_true", help="显示底层命令输出。默认不显示。")
    return parser.parse_args()


def main() -> int:
    global VERBOSE
    args = parse_args()
    VERBOSE = args.verbose
    os.chdir(ROOT)

    log("9HWH 一键发布")
    log(f"项目目录：{ROOT}")
    log(f"发布数量：{args.limit}")
    log(f"任务包：{args.batch}")
    log(f"发布模式：{args.mode}")
    log("输出模式：详细" if VERBOSE else "输出模式：简洁")

    maybe_git_pull(args.skip_pull)
    recovering = recover_previous_publish_if_needed()
    if not recovering:
        ensure_task_batch(args.batch)
        repair_placeholder_drafts(args.batch, args.repair_limit, args.sleep_seconds)
        generate_missing_drafts(args.batch, args.limit, args.overwrite_generation, args.sleep_seconds)
        import_and_review()
        promote_passed_drafts(args.limit, args.allow_warning)
        publish_soft(args.limit, args.mode)

    build_and_check_final()
    git_commit_and_push(push=not args.no_push)
    final_report()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StepError as exc:
        log("\n[FAIL] 一键发布中断")
        log(str(exc))
        log("\n下一步：把这段 [FAIL] 后面的输出贴给我。")
        raise SystemExit(1)
    except KeyboardInterrupt:
        log("\n[FAIL] 用户手动中断")
        raise SystemExit(130)
