from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DATA = ROOT / "site_src" / "data" / "content"
OUTPUT = ROOT / "data" / "deepseek-tasks"
DOCS = ROOT / "docs"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def task_body(task: dict, rules: dict, site: dict, blocks: dict) -> str:
    sections = rules.get("article_required_sections", [])
    forbidden = rules.get("blocked_terms", [])
    prompt_rules = rules.get("deepseek_prompt_rules", [])
    links = [link for link in task.get("internal_links", []) if link]
    return f"""# DeepSeek 写作任务：{task['title']}

## 写作目标

正文由 DeepSeek 生成。请为 9HWH 官网撰写一篇长期可维护的内容草稿，用于后续 Codex 审核、接入和构建。

## 页面 URL

{task['target_url']}

## 主关键词

{task['primary_keyword']}

## 次关键词

{', '.join(task.get('secondary_keywords', [])) or '无'}

## 搜索意图

{task['intent']}

## 目标读者

正在评估海外推广、引流获客、广告投放支持、买量投流或相关项目获客路径的出海团队、个人团队和项目负责人。

## 推荐结构

{chr(10).join('- ' + item for item in sections)}

## 必须覆盖的问题

- 这个关键词背后的真实需求是什么？
- 适合什么项目类型？
- 推广前需要准备哪些资料？
- 可考虑哪些渠道？
- 哪些表达和承诺不能写？
- 如何联系 9HWH 做进一步沟通？

## 内链建议

{chr(10).join('- ' + link for link in links)}

## 禁止表达

{chr(10).join('- ' + item for item in forbidden)}

## 服务边界

{blocks['service_boundary']}

## 风格要求

{chr(10).join('- ' + item for item in prompt_rules)}

## 输出格式要求

- 输出 Markdown 正文。
- 不要输出 HTML。
- 不要编造联系方式。
- 不要写违法违规承诺。
- 不要像灰色落地页。
- 必须完整输出 front matter。front matter 后正文标题层级从 `##` 开始。Codex 后续会按 front matter 接入和检查，不要省略 front matter。
"""


def main() -> int:
    queue = load_json(CONTENT_DATA / "content_queue.json")
    rules = load_json(CONTENT_DATA / "content_rules.json")
    site = load_json(ROOT / "site_src" / "data" / "site.json")
    blocks = load_json(ROOT / "site_src" / "data" / "content_blocks.json")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    for old_file in OUTPUT.glob("*.md"):
        old_file.unlink()
    index_rows = ["# DeepSeek Task Index", "", "| content_id | title | target_url | primary_keyword | cluster_id | status | task_file |", "| --- | --- | --- | --- | --- | --- | --- |"]
    count = 0
    for task in queue:
        if task.get("internal_only") or task["status"] not in {"planned", "prompt_ready"}:
            continue
        filename = f"{task['priority']:03d}-{task['content_id']}.md"
        (OUTPUT / filename).write_text(task_body(task, rules, site, blocks), encoding="utf-8", newline="\n")
        index_rows.append(f"| {task['content_id']} | {task['title']} | {task['target_url']} | {task['primary_keyword']} | {task['cluster_id']} | {task['status']} | data/deepseek-tasks/{filename} |")
        count += 1
    (DOCS / "deepseek-task-index.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] generated {count} DeepSeek task packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
