# Stage 13 Content Publishing System V1 Report

## 1. Stage Goal

本阶段把官网从“内容生产和审核系统”推进到“可控发布系统”，重点不是公开上线，而是先把 `reviewed` 内容池、发布候选池、发布日历、sitemap readiness、外链任务池和排名监控种子全部接起来。

## 2. Main Workspace

- 唯一主工作区：`E:/9HWH`
- 当前分支：`rescue-v1`
- 当前 origin：`https://github.com/wangwuda54/9hwh.git`
- `E:/9HWH_REPO` 没有作为后续开发目录使用

## 3. Batch-001 Reviewed Promotion

- `batch-001` 正式任务数仍为 `10`
- `c045` 仍不在 `batch-001`
- `python scripts/update_content_status.py --batch batch-001 --from draft_received --to reviewed` 已执行
- 推进结果：`draft_received 10 -> 0`，`reviewed 0 -> 10`，`published` 仍为 `0`

## 4. Published Still Zero

- 本阶段没有任何内容进入 `published`
- `reviewed` 不等于 `published`
- `reviewed` 内容没有进入 sitemap，也没有进入公开站

## 5. Publish Queue Rules

- 只允许 `reviewed` 内容进入发布候选池
- 默认每日上限 `12`
- 硬上限 `20`
- 超过 `20` 必须显式 `--force`
- `internal_only`、`warning/fail`、重复 `target_url`、内链不足、含禁用表达、含 HTML、含一级标题的内容都不能进入发布候选

## 6. 30-Day Calendar Summary

- 已生成 `30` 天发布日历
- 当前 `batch-001` 的 `10` 篇 `reviewed` 内容全部进入候选池
- 为了分散风险，队列把 `crypto`、`loan`、`insurance`、`immigration` 等主题拆开安排，没有堆在同一天
- 当前计划从 `2026-05-01` 到 `2026-05-10` 每天排 `1` 篇，便于后续人工逐日放量

## 7. Internal-Link Release Standard

- 每篇文章至少 `4` 个站内内链
- 至少包含 `service/platform`、`topic`、`/services/ or /topics/` 总页、`/contact/`
- 这些检查已进入 `review_content_drafts.py`、`plan_publish_queue.py` 和 `publish_from_queue.py`
- 发布前只允许链接公开承接页，不允许把 `reviewed` 草稿文章互相当作公开页链接

## 8. Sitemap / Robots / GSC Readiness

- `check_sitemap_readiness.py` 已建立
- 当前 `sitemap.xml` 只包含公开静态页和允许公开的 URL
- `reviewed`、`draft_received`、`internal_only` 内容没有进入 sitemap
- `robots.txt` 已包含 `Sitemap: https://www.9hwh.com/sitemap.xml`

## 9. Why Not GIA

- 本阶段只做 GSC sitemap 提交准备，不做 Google Indexing API
- 官网目前仍处于“可控发布前”的阶段，先守住状态边界、sitemap 边界和质量检查，比追求强制收录更重要

## 10. Outreach Task Pool

- `build_outreach_tasks.py` 已建立
- 当前任务池总数 `60`
- `owned_profile 15`
- `external_article 15`
- `community_answer 15`
- `partner_link 10`
- `resource_page 5`
- 明确禁止垃圾外链、PBN、批量目录站、自动评论、隐藏链接和同内容多域名互链

## 11. Rank Tracking Seed

- `rank_tracking_seed.json` 已升级为按内容生成的种子结构
- 当前写入 `10` 条 `reviewed` 内容监控种子
- `published_date` 仍为空，等待后续真实发布
- 没有填写任何假曝光、点击或排名数据

## 12. Batch-002 Candidate Status

- `batch-002` candidates 已存在并保留 `15` 条
- 当前仍是候选池，不是正式任务包
- 没有调用 DeepSeek API
- 没有导入草稿，没有推进到 `reviewed`

## 13. C045 Block

- `c045` 仍在 `content_queue` 中保留为 `internal_only: true`
- 它没有进入 `batch-001`，也没有进入发布候选池

## 14. Push / Deploy / Publish Guardrail

- 本阶段没有 push
- 本阶段没有部署
- 本阶段没有自动发布任何内容

## 15. Next Manual Actions

1. 人工复核 `publish_queue.json` 的 10 条排期是否符合业务节奏。
2. 选定真正需要进入公开站的第一天内容，再单独执行发布前人工确认。
3. 若下一阶段启动 `batch-002`，先冻结候选清单，再生成正式任务包。
4. 真正开始公开发布后，再进入 GSC sitemap 提交和索引监控阶段。
