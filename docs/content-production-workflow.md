# 内容生产工作流

## 1. 生成内容任务队列

```powershell
cd E:\9HWH
python scripts/build_content_queue.py
```

输出：

- `site_src/data/content/content_queue.json`
- `site_src/data/content/content_status.json`
- `data/content-assets/content_queue_summary.json`
- `docs/content-opportunity-report.md`

## 2. 生成 DeepSeek 写作任务包

```powershell
python scripts/generate_deepseek_tasks.py
```

输出：

- `data/deepseek-tasks/*.md`
- `docs/deepseek-task-index.md`

## 3. DeepSeek 正文放入 drafts

正文文件放入：

```text
site_src/content_drafts/{content_id}.md
```

必须使用 front matter：

```md
---
content_id:
title:
description:
target_url:
status:
primary_keyword:
secondary_keywords:
---
```

## 4. 审核正文

审核重点：

- 是否符合任务包。
- 是否包含服务边界。
- 是否有合理内链。
- 是否存在 blocked 或 internal_only 词。
- 是否有保证过审、保证效果、保证收益等承诺。
- 是否像长期官网文章，而不是灰色落地页。

## 5. 改状态为 ready_to_publish

只有审核通过后，才能把 `content_queue.json` 中对应任务状态改为：

```text
ready_to_publish
```

正式上线后再改为：

```text
published
```

## 6. 构建站点

```powershell
python scripts/build_site.py
```

未完成状态的内容不会生成页面，也不会进入 sitemap。

## 7. 检查站点

```powershell
python scripts/check_static_site.py
```

检查通过后才能考虑提交。

## 8. 如何发布

当前阶段不进入 Cloudflare Pages 部署。后续发布前仍需确认：

- sitemap 是否只包含正式页面。
- robots 是否未屏蔽旧 service。
- 是否没有 `_headers`、`_redirects` 的误改。
- 是否没有旧 service 页面处理。

## 9. 哪些内容不能发布

- 未完成正文。
- 未审核正文。
- 状态不是 `ready_to_publish` 或 `published` 的内容。
- internal_only 关键词内容。
- blocked 关键词内容。
- 缺少服务边界的内容。
- 有违规承诺或夸张结果承诺的内容。

## 10. 生成 batch-001 任务包

```powershell
python scripts/build_deepseek_batch.py
```

输出：

- `data/deepseek-batches/batch-001/batch-001-index.json`
- `data/deepseek-batches/batch-001/batch-001-tasks.md`
- `data/deepseek-batches/batch-001/tasks/*.md`

## 11. DeepSeek 回稿导入

将 DeepSeek 回稿放入：

```text
data/deepseek-inbox/
```

然后执行：

```powershell
python scripts/import_deepseek_drafts.py
```

导入通过后会写入 `site_src/content_drafts/{content_id}.md`，并生成导入报告。

## 12. draft 审核

```powershell
python scripts/review_content_drafts.py
```

审核报告：

- `data/content-assets/draft_review_report.json`
- `docs/content-draft-review-report.md`

## 13. 状态更新

```powershell
python scripts/update_content_status.py --content-id xxx --status reviewed
python scripts/update_content_status.py --content-id xxx --status ready_to_publish
```

不允许从 `planned` 直接跳到 `published`。

## 14. 发布前检查

发布前必须执行：

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

只有 `ready_to_publish` 或 `published` 且存在 draft 的内容才会生成页面并进入 sitemap。
