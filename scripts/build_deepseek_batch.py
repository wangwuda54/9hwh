from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "site_src" / "data" / "content" / "content_queue.json"
SOURCE_TASKS = ROOT / "data" / "deepseek-tasks"
BATCH_ROOT = ROOT / "data" / "deepseek-batches" / "batch-001"
BATCH_TASKS = BATCH_ROOT / "tasks"
DOCS = ROOT / "docs" / "content-batches"


PREFERRED_CLUSTERS = [
    "traffic-acquisition",
    "ad-campaign-support",
    "media-buying",
    "crypto-promotion",
    "dating-traffic",
    "game-promotion",
    "loan-leads",
    "insurance-leads",
    "immigration-leads",
    "online-work-leads",
    "fb-promotion",
    "google-promotion",
]
INTENT_HINTS = ["怎么做", "费用", "价格", "渠道", "哪家好", "靠谱吗", "怎么收费", "怎么投", "怎么找", "多少钱"]


def load_queue() -> list[dict]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))


def task_file_for(content_id: str) -> Path | None:
    matches = list(SOURCE_TASKS.glob(f"*-{content_id}.md"))
    return matches[0] if matches else None


def score(task: dict) -> tuple[int, int, int]:
    text = task["primary_keyword"] + task["title"]
    status_score = 100 if task["status"] == "prompt_ready" else 60
    intent_score = 0
    for index, hint in enumerate(INTENT_HINTS):
        if hint in text:
            intent_score = max(intent_score, 50 - index)
    cluster_score = 20 if task["cluster_id"] in PREFERRED_CLUSTERS else 0
    return (status_score + intent_score + cluster_score, -task["priority"], -len(text))


def select_batch(queue: list[dict], limit: int = 12) -> list[dict]:
    eligible = [
        task
        for task in queue
        if task["status"] in {"prompt_ready", "planned"}
        and not task.get("internal_only")
        and task_file_for(task["content_id"])
    ]
    by_cluster: dict[str, list[dict]] = {}
    for task in sorted(eligible, key=score, reverse=True):
        by_cluster.setdefault(task["cluster_id"], []).append(task)
    selected = []
    seen = set()
    for cluster in PREFERRED_CLUSTERS:
        tasks = by_cluster.get(cluster, [])
        if tasks and tasks[0]["content_id"] not in seen:
            selected.append(tasks[0])
            seen.add(tasks[0]["content_id"])
        if len(selected) >= limit:
            break
    if len(selected) < 10:
        for task in sorted(eligible, key=score, reverse=True):
            if task["content_id"] not in seen:
                selected.append(task)
                seen.add(task["content_id"])
            if len(selected) >= 10:
                break
    return selected[:limit]


def front_matter_hint(task: dict) -> str:
    secondary = ", ".join(task.get("secondary_keywords", []))
    return f"""---
content_id: {task['content_id']}
title: {task['title']}
description: 请填写 80-150 字页面描述
target_url: {task['target_url']}
primary_keyword: {task['primary_keyword']}
secondary_keywords: {secondary}
status: draft_received
---
"""


def batch_header(selected: list[dict]) -> str:
    return f"""# DeepSeek batch-001 写作任务包

## 本批次数量

{len(selected)} 篇。

## 总体要求

- 正文由 DeepSeek 生成。
- 请按每个 content_id 分开输出。
- 不要合并多篇文章。
- 不要省略 front matter。
- 不要写保证过审、保证效果、保证转化、保证收益。
- 不要写绕过平台政策、规避审核、抗风控。
- 不要写违法违规承诺。
- 不要编造案例、团队、办公室、联系方式。
- 内容适合长期官网，不要像灰色落地页。

## 每篇输出格式

```md
---
content_id:
title:
description:
target_url:
primary_keyword:
secondary_keywords:
status: draft_received
---

正文
```
"""


def build() -> None:
    queue = load_queue()
    selected = select_batch(queue, 12)
    if not 10 <= len(selected) <= 15:
        raise SystemExit(f"[FAIL] batch size must be 10-15, got {len(selected)}")
    if BATCH_ROOT.exists():
        shutil.rmtree(BATCH_ROOT)
    BATCH_TASKS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    index = []
    combined = [batch_header(selected)]
    for task in selected:
        src = task_file_for(task["content_id"])
        if not src:
            raise SystemExit(f"[FAIL] missing task file for {task['content_id']}")
        dst = BATCH_TASKS / src.name
        text = src.read_text(encoding="utf-8-sig")
        task_intro = f"\n\n## DeepSeek 输出 front matter 模板\n\n```md\n{front_matter_hint(task)}```\n"
        dst.write_text(text + task_intro, encoding="utf-8", newline="\n")
        combined.append(f"\n\n---\n\n# 任务：{task['content_id']}\n\n")
        combined.append(text)
        combined.append(task_intro)
        index.append({
            "batch_id": "batch-001",
            "content_id": task["content_id"],
            "target_url": task["target_url"],
            "title": task["title"],
            "h1": task["h1"],
            "primary_keyword": task["primary_keyword"],
            "secondary_keywords": task.get("secondary_keywords", []),
            "cluster_id": task["cluster_id"],
            "status": task["status"],
            "task_file": f"data/deepseek-batches/batch-001/tasks/{src.name}",
        })

    (BATCH_ROOT / "batch-001-index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (BATCH_ROOT / "batch-001-tasks.md").write_text("".join(combined), encoding="utf-8", newline="\n")
    clusters = Counter(item["cluster_id"] for item in selected)
    report = ["# batch-001 内容生产批次", "", f"- 任务数量：{len(selected)}", "", "## Cluster 分布", ""]
    for cluster, count in sorted(clusters.items()):
        report.append(f"- {cluster}: {count}")
    report.extend(["", "## 任务清单", "", "| content_id | title | cluster | target_url |", "| --- | --- | --- | --- |"])
    for task in selected:
        report.append(f"| {task['content_id']} | {task['title']} | {task['cluster_id']} | {task['target_url']} |")
    (DOCS / "batch-001-plan.md").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] generated batch-001 with {len(selected)} tasks")
    for cluster, count in sorted(clusters.items()):
        print(f"[OK] {cluster}: {count}")


if __name__ == "__main__":
    build()
