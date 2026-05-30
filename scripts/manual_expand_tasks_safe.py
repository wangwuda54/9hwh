from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONTENT_DIR = ROOT / "site_src" / "data" / "content"
CONTENT_STATUS_PATH = CONTENT_DIR / "content_status.json"
CONTENT_QUEUE_PATH = CONTENT_DIR / "content_queue.json"
PUBLISH_QUEUE_PATH = CONTENT_DIR / "publish_queue.json"
BLOG_INDEX_PATH = ROOT / "site" / "public" / "blog" / "index.html"
SITEMAP_PATH = ROOT / "site" / "public" / "sitemap.xml"
BACKUP_BASE = ROOT / "data" / "content-assets" / "manual-expand-backups"

BLOG_LOC_RE = re.compile(r"<loc>[^<]*/blog/[^<]*</loc>")
CONTENT_ID_RE = re.compile(r"^c(\d+)")
LINK_REPLACEMENTS = {
    "/services/lead-generation/": "/services/traffic-acquisition/",
    "/services/landing-page/": "/services/overseas-promotion/",
    "/topics/fb-promotion/": "/platforms/fb/",
    "/topics/finance-ads/": "/topics/finance-leads/",
    "/topics/google-ads/": "/platforms/google/",
    "/topics/ad-account/": "/services/ad-campaign-support/",
    "/topics/ad-budget/": "/services/ad-campaign-support/",
    "/topics/ad-review/": "/services/ad-campaign-support/",
    "/topics/creative-review/": "/services/ad-campaign-support/",
    "/topics/landing-page/": "/services/overseas-promotion/",
    "/topics/tiktok-ads/": "/platforms/tk/",
    "/topics/meta-ads/": "/platforms/fb/",
    "/platforms/tiktok/": "/platforms/tk/",
}
EXISTING_TOPIC_BY_CLUSTER = {
    "crypto-promotion": "/topics/crypto-promotion/",
    "dating-traffic": "/topics/dating-traffic/",
    "game-promotion": "/topics/game-promotion/",
    "immigration-leads": "/topics/immigration-leads/",
    "insurance-leads": "/topics/insurance-leads/",
    "loan-leads": "/topics/loan-leads/",
    "online-work-leads": "/topics/online-work-leads/",
}

BACKUP_FILES = [
    CONTENT_STATUS_PATH,
    CONTENT_QUEUE_PATH,
    PUBLISH_QUEUE_PATH,
    BLOG_INDEX_PATH,
    SITEMAP_PATH,
]

TOPIC_POOL = [
    {
        "slug": "google-ads-overseas-lead-generation",
        "title": "Google Ads海外获客怎么做：搜索词、落地页和转化追踪准备",
        "primary_keyword": "Google Ads海外获客怎么做",
        "secondary_keywords": ["Google Ads海外获客", "搜索广告", "转化追踪"],
        "cluster_id": "google-ads",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/google-ads/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "meta-lead-forms-overseas",
        "title": "Meta Lead Forms海外线索表单怎么搭：字段、筛选和跟进路径",
        "primary_keyword": "Meta Lead Forms海外线索表单",
        "secondary_keywords": ["Meta广告", "线索表单", "海外获客"],
        "cluster_id": "meta-ads",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/topics/fb-promotion/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "tiktok-ads-overseas-testing",
        "title": "TikTok Ads海外投放测试怎么做：素材节奏、预算和落地页承接",
        "primary_keyword": "TikTok Ads海外投放测试",
        "secondary_keywords": ["TikTok Ads", "海外投放", "素材测试"],
        "cluster_id": "tiktok-ads",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/platforms/tiktok/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "overseas-loan-leads-preparation",
        "title": "海外贷款获客投放前怎么评估：地区、表单和落地页准备",
        "primary_keyword": "海外贷款获客投放前评估",
        "secondary_keywords": ["海外贷款获客", "表单线索", "落地页准备"],
        "cluster_id": "loan-leads",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/loan-leads/",
        "risk_level": "medium",
        "intent": "lead_generation_question",
    },
    {
        "slug": "insurance-leads-overseas-ad-checklist",
        "title": "海外保险获客广告怎么准备：受众、资质和咨询转化路径",
        "primary_keyword": "海外保险获客广告准备",
        "secondary_keywords": ["保险获客", "海外广告", "咨询转化"],
        "cluster_id": "insurance-leads",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/insurance-leads/",
        "risk_level": "medium",
        "intent": "lead_generation_question",
    },
    {
        "slug": "immigration-leads-landing-page-review",
        "title": "海外移民获客落地页怎么审：承诺边界、表单和咨询链路",
        "primary_keyword": "海外移民获客落地页审核",
        "secondary_keywords": ["移民获客", "落地页审核", "表单线索"],
        "cluster_id": "immigration-leads",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/immigration-leads/",
        "risk_level": "medium",
        "intent": "landing_page_question",
    },
    {
        "slug": "dating-app-overseas-promotion",
        "title": "海外交友App推广怎么准备：渠道、素材审核和用户转化路径",
        "primary_keyword": "海外交友App推广",
        "secondary_keywords": ["交友App推广", "海外推广", "素材审核"],
        "cluster_id": "dating-traffic",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/topics/dating-traffic/",
        "risk_level": "medium",
        "intent": "channel_question",
    },
    {
        "slug": "mobile-game-user-acquisition-overseas",
        "title": "海外手游买量怎么做：素材测试、商店页和回传配置",
        "primary_keyword": "海外手游买量怎么做",
        "secondary_keywords": ["手游买量", "海外获客", "回传配置"],
        "cluster_id": "game-promotion",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/game-promotion/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "finance-ads-landing-page",
        "title": "金融广告落地页怎么改：承诺表达、表单和审核反馈处理",
        "primary_keyword": "金融广告落地页怎么改",
        "secondary_keywords": ["金融广告", "落地页", "审核反馈"],
        "cluster_id": "finance-ads",
        "target_service": "/services/landing-page/",
        "target_topic": "/topics/",
        "risk_level": "medium",
        "intent": "landing_page_question",
    },
    {
        "slug": "crypto-ads-compliance-boundary",
        "title": "虚拟币广告投放前怎么评估：地区限制、页面表达和风险边界",
        "primary_keyword": "虚拟币广告投放前评估",
        "secondary_keywords": ["虚拟币广告", "地区限制", "风险边界"],
        "cluster_id": "crypto-promotion",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/crypto-promotion/",
        "risk_level": "medium",
        "intent": "risk_assessment",
    },
    {
        "slug": "high-risk-project-creative-review",
        "title": "高风险项目广告素材怎么审：卖点、承诺和页面一致性",
        "primary_keyword": "高风险项目广告素材审核",
        "secondary_keywords": ["广告素材审核", "页面一致性", "投放风险"],
        "cluster_id": "creative-review",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "medium",
        "intent": "creative_review",
    },
    {
        "slug": "ad-account-setup-overseas",
        "title": "海外广告账户开户前准备：主体、地区、落地页和预算判断",
        "primary_keyword": "海外广告账户开户前准备",
        "secondary_keywords": ["广告账户", "海外开户", "预算判断"],
        "cluster_id": "ad-account",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "account_question",
    },
    {
        "slug": "ad-creative-review-checklist",
        "title": "广告素材审核清单：文案、图片、落地页和转化路径怎么对齐",
        "primary_keyword": "广告素材审核清单",
        "secondary_keywords": ["广告素材", "审核清单", "落地页"],
        "cluster_id": "creative-review",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "creative_review",
    },
    {
        "slug": "landing-page-review-before-ads",
        "title": "广告投放前落地页怎么检查：首屏、表单、信任信息和速度",
        "primary_keyword": "广告投放前落地页检查",
        "secondary_keywords": ["落地页检查", "广告投放", "表单转化"],
        "cluster_id": "landing-page",
        "target_service": "/services/landing-page/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "landing_page_question",
    },
    {
        "slug": "pixel-gtm-utm-conversion-tracking",
        "title": "Pixel、GTM和UTM怎么配：海外投放转化追踪基础检查",
        "primary_keyword": "海外投放转化追踪配置",
        "secondary_keywords": ["Pixel", "GTM", "UTM"],
        "cluster_id": "tracking",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "tracking_question",
    },
    {
        "slug": "multilingual-landing-pages-overseas",
        "title": "多语言落地页怎么准备：地区话术、表单字段和咨询入口",
        "primary_keyword": "多语言落地页准备",
        "secondary_keywords": ["多语言落地页", "海外推广", "咨询入口"],
        "cluster_id": "landing-page",
        "target_service": "/services/landing-page/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "landing_page_question",
    },
    {
        "slug": "google-search-ads-paths",
        "title": "Google搜索广告路径怎么规划：关键词、否词和落地页匹配",
        "primary_keyword": "Google搜索广告路径规划",
        "secondary_keywords": ["Google搜索广告", "关键词", "否词"],
        "cluster_id": "google-ads",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/google-ads/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "facebook-lead-ads-fields",
        "title": "Facebook Lead Ads字段怎么设计：线索质量和跟进效率的平衡",
        "primary_keyword": "Facebook Lead Ads字段设计",
        "secondary_keywords": ["Facebook Lead Ads", "线索质量", "表单字段"],
        "cluster_id": "fb-promotion",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/fb-promotion/",
        "risk_level": "low",
        "intent": "lead_generation_question",
    },
    {
        "slug": "tiktok-spark-ads-testing",
        "title": "TikTok Spark Ads怎么测试：达人内容、素材节奏和落地页承接",
        "primary_keyword": "TikTok Spark Ads测试",
        "secondary_keywords": ["Spark Ads", "TikTok投放", "素材测试"],
        "cluster_id": "tiktok-ads",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/platforms/tiktok/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "ad-budget-testing-overseas",
        "title": "海外广告预算测试怎么排：冷启动、素材组和转化观察周期",
        "primary_keyword": "海外广告预算测试",
        "secondary_keywords": ["广告预算", "冷启动", "转化观察"],
        "cluster_id": "ad-budget",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "budget_question",
    },
    {
        "slug": "ad-rejection-diagnosis",
        "title": "广告被拒怎么诊断：素材、落地页、账户和地区限制排查",
        "primary_keyword": "广告被拒诊断",
        "secondary_keywords": ["广告被拒", "素材审核", "落地页排查"],
        "cluster_id": "ad-review",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "medium",
        "intent": "review_question",
    },
    {
        "slug": "ad-account-stability-checklist",
        "title": "广告账户稳定性怎么评估：主体、页面、素材和投放节奏",
        "primary_keyword": "广告账户稳定性评估",
        "secondary_keywords": ["广告账户", "稳定性", "投放节奏"],
        "cluster_id": "ad-account",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "account_question",
    },
    {
        "slug": "creative-localization-overseas",
        "title": "海外广告素材本地化怎么做：语言、利益点和页面一致性",
        "primary_keyword": "海外广告素材本地化",
        "secondary_keywords": ["素材本地化", "海外广告", "页面一致性"],
        "cluster_id": "creative-review",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "creative_review",
    },
    {
        "slug": "cross-border-lead-quality",
        "title": "跨境线索质量怎么判断：来源、表单、预算和销售跟进",
        "primary_keyword": "跨境线索质量判断",
        "secondary_keywords": ["跨境获客", "线索质量", "销售跟进"],
        "cluster_id": "lead-generation",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "lead_generation_question",
    },
    {
        "slug": "consultation-conversion-path",
        "title": "咨询转化路径怎么设计：广告、落地页、表单和人工跟进",
        "primary_keyword": "咨询转化路径设计",
        "secondary_keywords": ["咨询转化", "落地页表单", "人工跟进"],
        "cluster_id": "conversion-path",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "conversion_question",
    },
    {
        "slug": "overseas-landing-page-speed",
        "title": "海外落地页速度怎么查：首屏加载、表单提交和广告质量",
        "primary_keyword": "海外落地页速度检查",
        "secondary_keywords": ["落地页速度", "广告质量", "首屏加载"],
        "cluster_id": "landing-page",
        "target_service": "/services/landing-page/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "landing_page_question",
    },
    {
        "slug": "google-ads-keyword-match",
        "title": "Google Ads关键词匹配怎么选：广泛、词组、完全和否词策略",
        "primary_keyword": "Google Ads关键词匹配",
        "secondary_keywords": ["关键词匹配", "Google Ads", "否词策略"],
        "cluster_id": "google-ads",
        "target_service": "/services/ad-campaign-support/",
        "target_topic": "/topics/google-ads/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "meta-audience-testing-overseas",
        "title": "Meta海外受众测试怎么做：兴趣、类受众和再营销分层",
        "primary_keyword": "Meta海外受众测试",
        "secondary_keywords": ["Meta广告", "受众测试", "再营销"],
        "cluster_id": "meta-ads",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/topics/fb-promotion/",
        "risk_level": "low",
        "intent": "channel_question",
    },
    {
        "slug": "tiktok-creative-fatigue",
        "title": "TikTok素材衰退怎么判断：点击率、转化率和换素材节奏",
        "primary_keyword": "TikTok素材衰退判断",
        "secondary_keywords": ["TikTok素材", "点击率", "换素材"],
        "cluster_id": "tiktok-ads",
        "target_service": "/services/overseas-promotion/",
        "target_topic": "/platforms/tiktok/",
        "risk_level": "low",
        "intent": "creative_review",
    },
    {
        "slug": "form-leads-follow-up",
        "title": "表单线索怎么跟进：字段筛选、响应时效和咨询质量",
        "primary_keyword": "表单线索跟进",
        "secondary_keywords": ["表单线索", "咨询质量", "响应时效"],
        "cluster_id": "lead-generation",
        "target_service": "/services/lead-generation/",
        "target_topic": "/topics/",
        "risk_level": "low",
        "intent": "lead_generation_question",
    },
    {
        "slug": "overseas-ad-consultation-prep",
        "title": "海外广告咨询前要准备什么：地区、产品、页面、素材和预算",
        "primary_keyword": "海外广告咨询准备",
        "secondary_keywords": ["广告咨询", "投放准备", "预算评估"],
        "cluster_id": "consultation",
        "target_service": "/contact/",
        "target_topic": "/services/",
        "risk_level": "low",
        "intent": "consultation_question",
    },
]


class ExpandError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="9HWH safe task pool expander.")
    parser.add_argument("--target-new", type=int, default=30)
    parser.add_argument("--batch", default="latest")
    parser.add_argument("--max-batch-size", type=int, default=15)
    parser.add_argument("--rebalance-batches", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
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


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def count_published() -> int:
    return int((load_json(CONTENT_STATUS_PATH, {}) or {}).get("published", 0) or 0)


def count_blog_cards() -> int:
    if not BLOG_INDEX_PATH.exists():
        return 0
    return BLOG_INDEX_PATH.read_text(encoding="utf-8-sig").count("<article")


def count_sitemap_blog_urls() -> int:
    if not SITEMAP_PATH.exists():
        return 0
    return len(BLOG_LOC_RE.findall(SITEMAP_PATH.read_text(encoding="utf-8-sig")))


def batch_paths(batch_id: str) -> tuple[Path, Path, Path]:
    batch_dir = ROOT / "data" / "deepseek-batches" / batch_id
    return batch_dir, batch_dir / f"{batch_id}-index.json", batch_dir / f"{batch_id}-tasks.md"


def batch_number(batch_id: str) -> int:
    match = re.match(r"batch-(\d+)$", batch_id)
    return int(match.group(1)) if match else 0


def existing_batch_ids() -> list[str]:
    root = ROOT / "data" / "deepseek-batches"
    ids = [path.name for path in root.glob("batch-*") if path.is_dir()]
    return sorted(ids, key=batch_number)


def next_batch_id(batch_id: str) -> str:
    return f"batch-{batch_number(batch_id) + 1:03d}"


def load_batch_index(batch_id: str) -> list[dict]:
    _batch_dir, index_path, _tasks_path = batch_paths(batch_id)
    return load_json(index_path, [])


def resolve_append_batch(max_batch_size: int) -> str:
    ids = existing_batch_ids() or ["batch-001"]
    for batch_id in ids:
        if batch_id == "batch-001":
            continue
        if len(load_batch_index(batch_id)) < max_batch_size:
            return batch_id
    return next_batch_id(ids[-1])


def render_batch_tasks(batch_id: str, items: list[dict]) -> None:
    _batch_dir, _index_path, tasks_path = batch_paths(batch_id)
    sections = []
    for item in items:
        task_file = item.get("task_file")
        if not task_file:
            continue
        path = ROOT / str(task_file)
        if path.exists():
            sections.append(path.read_text(encoding="utf-8-sig").rstrip())
    header = "# DeepSeek batch writing tasks\n\n不要省略 front matter\n不要合并多篇文章\n\n"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text(header + "\n\n---\n\n".join(sections).rstrip() + "\n", encoding="utf-8", newline="\n")


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


def backup_tree(source: Path, backup_dir: Path) -> None:
    target = backup_dir / rel(source)
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    elif source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def create_rebalance_backup(batch_ids: list[str]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = BACKUP_BASE / stamp
    for batch_id in batch_ids:
        batch_dir, _index_path, _tasks_path = batch_paths(batch_id)
        backup_tree(batch_dir, backup_dir)
    for source in [CONTENT_STATUS_PATH, CONTENT_QUEUE_PATH, PUBLISH_QUEUE_PATH]:
        backup_tree(source, backup_dir)
    return backup_dir


def write_batch_index(batch_id: str, items: list[dict]) -> None:
    _batch_dir, index_path, _tasks_path = batch_paths(batch_id)
    for item in items:
        item["batch_id"] = batch_id
        number_match = CONTENT_ID_RE.match(str(item.get("content_id", "")))
        number = int(number_match.group(1)) if number_match else len(items)
        item["task_file"] = f"data/deepseek-batches/{batch_id}/tasks/{number:03d}-{item['content_id']}.md"
    write_json(index_path, items)


def rebalance_batches(max_batch_size: int, dry_run: bool) -> int:
    before = (count_published(), count_blog_cards(), count_sitemap_blog_urls())
    source = load_batch_index("batch-001")
    if len(source) <= max_batch_size:
        ok(f"batch-001 task count already <= {max_batch_size}")
        return 0
    chunks = [source[index : index + max_batch_size] for index in range(0, len(source), max_batch_size)]
    batch_ids = [f"batch-{index + 1:03d}" for index in range(len(chunks))]
    print(f"batch-001 will be split into: {', '.join(batch_ids)}")
    if dry_run:
        for batch_id, chunk in zip(batch_ids, chunks):
            print(f"- {batch_id}: {len(chunk)} tasks")
        final_check(before, None)
        return 0

    backup_dir = create_rebalance_backup(batch_ids)
    ok(f"backup created at {rel(backup_dir)}")

    for batch_id, chunk in zip(batch_ids, chunks):
        batch_dir, _index_path, _tasks_path = batch_paths(batch_id)
        tasks_dir = batch_dir / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        new_items = []
        for item in chunk:
            item = dict(item)
            old_path = ROOT / str(item.get("task_file", ""))
            number_match = CONTENT_ID_RE.match(str(item.get("content_id", "")))
            number = int(number_match.group(1)) if number_match else len(new_items) + 1
            new_task = tasks_dir / f"{number:03d}-{item['content_id']}.md"
            if old_path.exists() and old_path.resolve() != new_task.resolve():
                shutil.copy2(old_path, new_task)
            elif new_task.exists():
                pass
            else:
                new_task.write_text(task_markdown(item), encoding="utf-8", newline="\n")
            item["batch_id"] = batch_id
            item["task_file"] = rel(new_task)
            new_items.append(item)
        write_json(batch_paths(batch_id)[1], new_items)
        render_batch_tasks(batch_id, new_items)
        keep = {Path(str(item["task_file"])).name for item in new_items}
        for path in tasks_dir.glob("*.md"):
            if path.name not in keep:
                path.unlink()

    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    batch_by_id = {
        item.get("content_id"): batch_id
        for batch_id in batch_ids
        for item in load_batch_index(batch_id)
    }
    for item in publish_queue:
        content_id = item.get("content_id")
        if content_id in batch_by_id:
            item["batch"] = batch_by_id[content_id]
    write_json(PUBLISH_QUEUE_PATH, publish_queue)
    final_check(before, backup_dir)
    completed = subprocess.run(["E:/python/python.exe", "scripts/check_static_site.py"], cwd=ROOT, text=True)
    if completed.returncode != 0:
        raise ExpandError("check_static_site.py failed after batch rebalance")
    return 0


def max_content_number(items: list[dict]) -> int:
    highest = 0
    for item in items:
        match = CONTENT_ID_RE.match(str(item.get("content_id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return highest


def existing_ids_and_urls(*collections: list[dict]) -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    urls: set[str] = set()
    for collection in collections:
        for item in collection:
            if item.get("content_id"):
                ids.add(str(item["content_id"]))
            if item.get("target_url"):
                urls.add(str(item["target_url"]))
    return ids, urls


def make_description(topic: dict) -> str:
    return (
        f"{topic['title']}，围绕投放前评估、账户和素材准备、落地页承接、"
        "转化追踪与咨询判断，帮助项目方先把可执行条件梳理清楚。"
    )


def normalize_site_link(link: str) -> str:
    return LINK_REPLACEMENTS.get(str(link or "").strip(), str(link or "").strip())


def content_queue_item(content_id: str, number: int, topic: dict) -> dict:
    target_service = normalize_site_link(topic["target_service"])
    target_topic = normalize_site_link(topic["target_topic"])
    if not target_topic or target_topic == "/topics/" or target_topic.startswith("/platforms/"):
        target_topic = EXISTING_TOPIC_BY_CLUSTER.get(str(topic.get("cluster_id", "")), "/topics/finance-leads/")
    return {
        "content_id": content_id,
        "target_url": f"/blog/{topic['slug']}/",
        "title": topic["title"],
        "h1": topic["title"],
        "description": make_description(topic),
        "intent": topic["intent"],
        "cluster_id": topic["cluster_id"],
        "primary_keyword": topic["primary_keyword"],
        "secondary_keywords": topic["secondary_keywords"],
        "source_keywords": [topic["primary_keyword"]],
        "page_type": "blog_article",
        "status": "prompt_ready",
        "priority": number,
        "word_count_target": 1800,
        "deepseek_required": True,
        "target_service": target_service,
        "target_topic": target_topic,
        "internal_links": [
            target_service,
            target_topic,
            "/services/",
            "/topics/",
            "/contact/",
        ],
        "risk_level": topic["risk_level"],
        "notes": "安全扩展任务池追加任务；未生成、未审核、未发布。",
    }


def publish_queue_item(content_id: str, topic: dict) -> dict:
    return {
        "content_id": content_id,
        "title": topic["title"],
        "target_url": f"/blog/{topic['slug']}/",
        "primary_keyword": topic["primary_keyword"],
        "content_type": "topic_expansion",
        "priority_score": 40,
        "risk_level": topic["risk_level"],
        "publish_status": "pending",
        "planned_publish_date": "",
        "batch": "",
        "review_status": "",
        "internal_link_count": 0,
        "notes": "safe_expand pending generation and review",
    }


def batch_index_item(batch_id: str, content_id: str, number: int, topic: dict) -> dict:
    task_file = f"data/deepseek-batches/{batch_id}/tasks/{number:03d}-{content_id}.md"
    return {
        "batch_id": batch_id,
        "content_id": content_id,
        "target_url": f"/blog/{topic['slug']}/",
        "title": topic["title"],
        "h1": topic["title"],
        "primary_keyword": topic["primary_keyword"],
        "secondary_keywords": topic["secondary_keywords"],
        "cluster_id": topic["cluster_id"],
        "status": "planned",
        "task_file": task_file,
    }


def task_markdown(item: dict) -> str:
    if "intent" not in item:
        secondary_value = item.get("secondary_keywords", [])
        secondary = ", ".join(secondary_value) if isinstance(secondary_value, list) else str(secondary_value)
        return f"""# task: {item.get('content_id', '')}

# DeepSeek writing task: {item.get('title', '')}

## Page URL

{item.get('target_url', '')}

## Primary keyword

{item.get('primary_keyword', '')}

## Secondary keywords

{secondary}

## DeepSeek output front matter template

```md
---
content_id: {item.get('content_id', '')}
title: {item.get('title', '')}
description: please write an 80-150 character page description
target_url: {item.get('target_url', '')}
primary_keyword: {item.get('primary_keyword', '')}
secondary_keywords: {secondary}
status: draft_received
---
```
"""
    links = [
        link
        for link in [
            item.get("target_service"),
            item.get("target_topic"),
            "/services/",
            "/topics/",
            "/contact/",
        ]
        if link
    ]
    secondary = ", ".join(item["secondary_keywords"])
    return f"""# 任务：{item['content_id']}

# DeepSeek 写作任务：{item['title']}

## 写作目标

正文由 DeepSeek 生成。请为 9HWH 官网撰写一篇长期可维护的内容草稿，用于后续 Codex 审核、接入和构建。

## 页面 URL

{item['target_url']}

## 主关键词

{item['primary_keyword']}

## 次关键词

{secondary}

## 搜索意图

{item['intent']}

## 目标读者

正在评估海外推广、引流获客、广告投放支持、买量投流或相关项目获客路径的出海团队、个人团队和项目负责人。

## 推荐结构

- 搜索意图判断
- 适合什么项目
- 推广前准备
- 账户、素材、落地页和转化路径的关系
- 常见问题
- 投放前评估
- 咨询准备建议

## 必须覆盖的问题

- 这个关键词背后的真实需求是什么？
- 适合什么项目类型？
- 推广前需要准备哪些资料？
- 可考虑哪些渠道？
- 哪些表达需要先做风险评估？
- 如何整理地区、产品、页面、素材和预算后再咨询 9HWH？

## 内链建议

{chr(10).join(f"- {link}" for link in links)}

## 禁止表达

- 保证过审
- 保证不限号
- 保证效果
- 保证转化
- 保证收益
- 绕过平台政策
- 规避审核
- 抗风控
- Cloak
- 仿牌
- 黑五类
- 三不限
- 违规业务也能做
- 任何平台都能过
- 任何行业都能投

## 风格要求

- 内容要适合长期官网，不要像灰色落地页。
- 表达要克制、正式、可维护。
- 必须包含投放前评估和咨询准备建议。
- 风险用实操判断表达，例如素材太激进、页面承诺太满、账户和落地页不匹配会带来审核风险。

## 输出格式要求

- 输出 Markdown 正文。
- 不要输出 HTML。
- 不要编造联系方式。
- 不要写违法违规承诺。
- 必须完整输出 front matter。front matter 后正文标题层级从 `##` 开始。

## DeepSeek 输出 front matter 模板

```md
---
content_id: {item['content_id']}
title: {item['title']}
description: 请填写 80-150 字页面描述
target_url: {item['target_url']}
primary_keyword: {item['primary_keyword']}
secondary_keywords: {secondary}
status: draft_received
---
```
"""


def plan_new_tasks(target_new: int, batch_id: str) -> tuple[list[dict], list[dict], list[dict]]:
    content_queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    _batch_dir, batch_index_path, _batch_tasks_path = batch_paths(batch_id)
    batch_index = load_json(batch_index_path, [])
    existing_ids, existing_urls = existing_ids_and_urls(content_queue, publish_queue, batch_index)
    highest = max(max_content_number(content_queue), max_content_number(publish_queue), max_content_number(batch_index))

    new_content: list[dict] = []
    new_publish: list[dict] = []
    new_batch: list[dict] = []
    next_number = highest + 1
    for topic in TOPIC_POOL:
        content_id = f"c{next_number:03d}-{topic['slug']}"
        target_url = f"/blog/{topic['slug']}/"
        if content_id in existing_ids or target_url in existing_urls:
            continue
        content_item = content_queue_item(content_id, next_number, topic)
        publish_item = publish_queue_item(content_id, topic)
        publish_item["batch"] = batch_id
        new_content.append(content_item)
        new_publish.append(publish_item)
        new_batch.append(batch_index_item(batch_id, content_id, next_number, topic))
        next_number += 1
        if len(new_content) >= target_new:
            break
    return new_content, new_publish, new_batch


def update_status(content_queue: list[dict], before_published: int) -> dict:
    status = load_json(CONTENT_STATUS_PATH, {})
    counts = {
        "prompt_ready": 0,
        "writing": 0,
        "draft_received": 0,
        "reviewed": 0,
        "published": before_published,
        "paused": 0,
    }
    for item in content_queue:
        state = str(item.get("status", ""))
        if state in counts and state != "published":
            counts[state] += 1
    status.update(counts)
    status["total_planned"] = len(content_queue)
    status["published"] = before_published
    return status


def write_expansion(batch_id: str, new_content: list[dict], new_publish: list[dict], new_batch: list[dict], before_published: int) -> None:
    batch_dir, batch_index_path, batch_tasks_path = batch_paths(batch_id)
    tasks_dir = batch_dir / "tasks"
    content_queue = load_json(CONTENT_QUEUE_PATH, [])
    publish_queue = load_json(PUBLISH_QUEUE_PATH, [])
    batch_index = load_json(batch_index_path, [])

    content_queue.extend(new_content)
    publish_queue.extend(new_publish)
    batch_index.extend(new_batch)

    write_json(CONTENT_QUEUE_PATH, content_queue)
    write_json(PUBLISH_QUEUE_PATH, publish_queue)
    write_json(batch_index_path, batch_index)
    write_json(CONTENT_STATUS_PATH, update_status(content_queue, before_published))

    tasks_dir.mkdir(parents=True, exist_ok=True)
    appended_sections = []
    for content_item, batch_item in zip(new_content, new_batch):
        text = task_markdown(content_item).rstrip() + "\n"
        task_path = ROOT / batch_item["task_file"]
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(text, encoding="utf-8", newline="\n")
        appended_sections.append(text)

    old_text = batch_tasks_path.read_text(encoding="utf-8-sig") if batch_tasks_path.exists() else ""
    separator = "\n\n---\n\n" if old_text.strip() else ""
    batch_tasks_path.write_text(old_text.rstrip() + separator + "\n\n---\n\n".join(appended_sections) + "\n", encoding="utf-8", newline="\n")


def remove_task_files(items: list[dict]) -> None:
    for item in items:
        task_file = item.get("task_file")
        if not task_file:
            continue
        path = ROOT / str(task_file)
        if path.exists():
            path.unlink()


def final_check(
    before: tuple[int, int, int],
    backup_dir: Path | None,
    new_batch: list[dict] | None = None,
    restore_files: list[Path] | None = None,
) -> tuple[int, int, int]:
    after = (count_published(), count_blog_cards(), count_sitemap_blog_urls())
    labels = ("published", "/blog/ 卡片", "sitemap blog URL")
    for label, before_value, after_value in zip(labels, before, after):
        if after_value < before_value:
            if backup_dir:
                restore_backup(backup_dir, restore_files or BACKUP_FILES)
            if new_batch:
                remove_task_files(new_batch)
            raise ExpandError(f"{label} 数量下降：{before_value} -> {after_value}，已恢复备份，禁止继续。")
    ok(f"published 未下降：{before[0]} -> {after[0]}")
    ok(f"/blog/ 卡片未下降：{before[1]} -> {after[1]}")
    ok(f"sitemap blog URL 未下降：{before[2]} -> {after[2]}")
    return after


def main() -> int:
    args = parse_args()
    if args.target_new < 0:
        fail("target-new must be non-negative")
        return 1
    if args.max_batch_size < 10:
        fail("max-batch-size must be at least 10")
        return 1

    print("9HWH safe task pool expander")
    before = (count_published(), count_blog_cards(), count_sitemap_blog_urls())
    print(f"current published: {before[0]}")
    print(f"current /blog/ cards: {before[1]}")
    print(f"current sitemap blog URLs: {before[2]}")
    print()

    try:
        if args.rebalance_batches:
            return rebalance_batches(args.max_batch_size, args.dry_run)

        if before[0] <= 0:
            raise ExpandError("published <= 0; stopped")
        batch_id = resolve_append_batch(args.max_batch_size) if args.batch == "latest" else args.batch
        if batch_id == "batch-001" and len(load_batch_index("batch-001")) >= args.max_batch_size:
            batch_id = "batch-002"
        new_content, new_publish, new_batch = plan_new_tasks(args.target_new, batch_id)
        print("[1/3] find appendable tasks")
        info(f"current expansion batch: {batch_id}")
        ok(f"planned new tasks: {len(new_content)}")
        for item in new_content:
            print(f"- {item['content_id']} | {item['title']} | {item['target_url']}")
        print()

        if args.dry_run:
            print("[2/3] dry-run")
            ok("no files written")
            print()
            print("[3/3] protection check")
            final_check(before, None)
            return 0

        print("[2/3] backup and write")
        _batch_dir, batch_index_path, batch_tasks_path = batch_paths(batch_id)
        backup_files = [*BACKUP_FILES, batch_index_path, batch_tasks_path]
        backup_dir = create_backup(backup_files)
        ok(f"backup created at {rel(backup_dir)}")
        if new_content:
            write_expansion(batch_id, new_content, new_publish, new_batch, before[0])
        ok("task pool expansion complete")
        print()

        print("[3/3] protection check")
        final_check(before, backup_dir, new_batch, backup_files)
        return 0
    except ExpandError as exc:
        fail(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
