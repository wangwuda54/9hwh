# 阶段 7：DeepSeek 第一批内容生产任务

## 本阶段目标

阶段 7 将阶段 6 的内容生产系统推进到可执行生产状态：选择第一批内容任务，生成 DeepSeek batch-001，建立回稿 inbox、导入脚本、draft 审核脚本和状态更新工具。

## 为什么不让 Codex 直接写正文

当前规则是：后续 blog 正文、长文正文和内容页正文默认由 DeepSeek 写。Codex 负责选题、任务包、接入、审核、状态管理、构建与检查。这样可以避免 Codex 在工程推进中顺手生成大量未经审核的正文。

## 为什么不一次生成几千篇

关键词资产库是 SEO 资产，不是页面清单。一次生成几千篇会造成低质量页面、重复主题、索引失控和审核困难。本阶段只选 10-15 篇作为第一批实战任务。

## batch-001 选择规则

- 优先 `prompt_ready`。
- 覆盖不同 cluster。
- 优先搜索意图清晰的词，如怎么做、费用、价格、渠道、哪家好、靠谱吗、怎么收费。
- 不选择 internal_only。
- 不选择 blocked。
- 不选择成人粉、色粉、博彩、规避审核、抗风控等高风险方向。

## batch-001 任务清单

批次文件：

- `data/deepseek-batches/batch-001/batch-001-index.json`
- `data/deepseek-batches/batch-001/batch-001-tasks.md`
- `data/deepseek-batches/batch-001/tasks/*.md`

批次计划：

- `docs/content-batches/batch-001-plan.md`

## DeepSeek 输出格式

DeepSeek 必须按每个 `content_id` 单独输出 Markdown，不要合并多篇文章。每篇必须包含 front matter：

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

## 回稿放哪里

DeepSeek 回稿先放入：

```text
data/deepseek-inbox/
```

不要直接放入 `site_src/content_drafts/`。

## 如何导入

```powershell
python scripts/import_deepseek_drafts.py
```

导入脚本会检查 front matter、content_id、target_url、标题、描述、主关键词、正文长度和禁止表达。

## 如何审核

```powershell
python scripts/review_content_drafts.py
```

审核脚本会检查服务边界、内链、联系 CTA、禁止表达、旧 service 链接和关键词堆砌。

## 什么状态才能发布

只有审核通过后，才能用：

```powershell
python scripts/update_content_status.py --content-id xxx --status ready_to_publish
```

正式上线后才允许改为 `published`。

## 什么状态才能进入 sitemap

只有 `ready_to_publish` 或 `published` 且存在合格 draft 的内容才能生成页面并进入 sitemap。

以下状态不能进入 sitemap：

- `planned`
- `prompt_ready`
- `writing`
- `draft_received`
- `reviewed`
- `paused`

## 当前仍未处理事项

- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。
- 未直接写正文。
- 未发布任何 DeepSeek 正文。
