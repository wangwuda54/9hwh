# DeepSeek 正文接入规范

本目录用于放置 DeepSeek 后续产出的正文草稿。

建议文件名：

```text
site_src/content_drafts/{content_id}.md
```

Markdown front matter：

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

正文内容
```

注意：

- draft 不等于发布。
- 只有 `content_queue.json` 中对应任务状态为 `ready_to_publish` 或 `published`，`build_site.py` 才能生成公开内容页。
- Codex 后续负责校验 front matter、内链、合规投放建议和构建结果。
- 不要把未审核正文直接发布到 sitemap。
- 不要放入 `service_` 页面或旧站页面内容。
