# 阶段 6：内容生产流水线与 DeepSeek 写作任务包

## 为什么不直接生成几千个关键词页面

阶段 5 已经建立关键词资产库，但关键词资产不是公开页面清单。阶段 6 继续坚持同一原则：不能把几千个关键词直接变成几千个低质量页面，也不能回到旧 `service_` 批量页面模式。

本阶段只建立内容生产流水线，不由 Codex 批量写正文。

## content_queue 的作用

`site_src/data/content/content_queue.json` 是内容生产队列，用于记录未来可能写作的内容任务。每条任务包含关键词、cluster、目标 URL、状态、内链建议、风险等级和 DeepSeek 是否需要写作。

`content_queue` 不等于公开页面。只有状态进入 `ready_to_publish` 或 `published`，并且存在合格正文草稿时，生成器才允许生成正式内容页。

## DeepSeek 任务包的作用

`data/deepseek-tasks/` 保存写作任务包。任务包用于交给 DeepSeek 生成正文，包含：

- 写作目标
- 页面 URL
- 主关键词和次关键词
- 搜索意图
- 推荐结构
- 必须覆盖的问题
- 内链建议
- 禁止表达
- 服务边界
- 输出格式要求

## Codex 的职责

- 从关键词资产中生成内容任务队列。
- 生成 DeepSeek 写作任务包。
- 建立 draft 接入格式。
- 校验 DeepSeek 正文格式、内链、服务边界和风险表达。
- 在状态满足条件时接入正文并构建页面。

## DeepSeek 的职责

- 根据任务包生成正文。
- 不写违法违规承诺。
- 不写保证过审、保证效果、保证收益、绕过平台政策、规避审核等表达。
- 输出适合长期官网维护的 Markdown 正文。

## 内容状态流程

状态流转：

1. `planned`
2. `prompt_ready`
3. `writing`
4. `draft_received`
5. `reviewed`
6. `ready_to_publish`
7. `published`

`paused` 用于暂停不适合继续生产的内容。

## 哪些内容能进入 sitemap

只有满足以下条件的内容才能进入 sitemap：

- `content_queue` 状态是 `ready_to_publish` 或 `published`。
- `site_src/content_drafts/{content_id}.md` 存在。
- draft front matter 与任务一致。
- 通过 `scripts/check_static_site.py` 检查。

## 哪些内容不能进入 sitemap

- `planned`
- `prompt_ready`
- `writing`
- `draft_received`
- `reviewed`
- `paused`
- internal_only 关键词
- blocked 关键词
- 未审核正文
- 旧 service 页面

## 如何避免重新变成 service_ 批量页

- 不用一个关键词生成一个页面。
- 不生成 `service_*.html`。
- 不把 content_queue 直接变成公开页面。
- 不把未完成正文放入 sitemap。
- 每批内容限制数量，先任务化，再写作，再审核，再发布。

## 后续如何批量但可控地写文章

1. 先运行 `build_content_queue.py` 生成有限数量任务。
2. 从 `prompt_ready` 中挑选一小批给 DeepSeek。
3. DeepSeek 输出正文到 `site_src/content_drafts/`。
4. Codex 校验和接入。
5. 状态改成 `ready_to_publish`。
6. 构建并检查。
7. 通过后再进入发布流程。

## 当前仍未处理事项

- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。
- 未批量生成正文。
- 未生成几千个公开页面。
