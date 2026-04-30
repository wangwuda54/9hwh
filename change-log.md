# 9hwh 官网拯救项目变更记录

## 1. 使用原则

本文件记录 9hwh 官网拯救项目所有关键变化。

任何影响以下内容的重大变化都必须记录：官网定位、主结构、核心服务页、关键词池、旧 service 页面处理、索引策略、风险表达规则、内容发布规则、回滚点。

未记录的重大变更视为未批准。

低风险小修可以在阶段验收时汇总记录，不要求每次单独写入。

## 2. 变更记录格式

每次变更按以下格式记录：

```md
## YYYY-MM-DD - 变更标题

### 变更类型
- 类型：规范 / 内容 / 关键词 / 旧页面 / 索引 / 风险 / 结构 / 回滚

### 变更原因
- 为什么需要这次变更。

### 变更范围
- 涉及文件：
- 涉及页面：
- 是否影响旧 service 页面：
- 是否影响索引：

### 具体变更
- 变更 1。
- 变更 2。

### 风险判断
- 风险等级：低 / 中 / 高。
- 主要风险：
- 风险控制方式：

### 回滚点
- 修改前状态：
- 回滚方式：
- 回滚负责人：

### 验收结果
- 是否通过：
- 未通过原因：
- 下一步：
```

## 3. 每次改版必须记录什么

每次重大改版必须记录：改版日期、目的、涉及页面、涉及文件、修改前状态、修改后状态、回滚方式、是否影响 sitemap/robots/noindex/301/410/canonical、是否影响旧 service 页面、是否引入新关键词、是否清理高风险表达。

## 4. 关键词池变化记录

关键词池变化必须记录：批次名称、来源文件、生成日期、生成逻辑、覆盖国家、覆盖平台、覆盖行业、风险词数量、禁用词数量、可发布词数量、进入内容中心的词、不允许进入主结构的词、审核人。

记录格式：

```md
## YYYY-MM-DD - 关键词池变更：批次名称

- 来源文件：
- 生成逻辑：
- 总词量：
- 低风险：
- 中风险：
- 高风险：
- 禁用：
- 发布范围：
- 不进入主结构的原因：
- 后续动作：
```

## 5. 旧页面处理记录

旧 service 页面处理必须记录：批次编号、URL 数量、处理方式、处理原因、执行日期、执行前状态码、执行后状态码、是否有点击/展示/外链/转化、是否含高风险表达、回滚方式。

记录格式：

```md
## YYYY-MM-DD - 旧 service 页面处理：批次编号

- URL 数量：
- 分流类型：保留 / 重写 / 合并 / noindex / 410 / 301
- 数据依据：
- 风险依据：
- 执行范围：
- 回滚点：
- 观察指标：
- 观察结论：
```

## 6. 索引策略变化记录

索引策略变化必须记录：是否修改 sitemap、robots、noindex、301、410、canonical，涉及 URL 数量、预期效果、观察指标、异常处理方案。

记录格式：

```md
## YYYY-MM-DD - 索引策略变更：标题

- 策略类型：sitemap / robots / noindex / 301 / 410 / canonical
- 涉及范围：
- URL 数量：
- 变更原因：
- 执行前状态：
- 执行后状态：
- 观察周期：
- 异常处理：
- 回滚方案：
```

## 7. 回滚点记录

中高风险变更必须记录：修改前文件备份位置、修改前 URL 状态、修改前页面内容快照、修改前索引状态、修改前流量数据、回滚命令或人工步骤、回滚后验收标准。

## 8. 初始记录

## 2026-04-30 - 阶段 0：项目规范初始化

### 变更类型
- 类型：规范。

### 变更原因
- 当前官网存在链接池首页、批量 service 页面、模板化内容、高风险表达和索引治理混乱问题。
- 需要先建立规则，再进入盘点、设计和执行。

### 变更范围
- 新增 AGENTS.md。
- 新增根目录规范文件。
- 不修改首页代码。
- 不处理旧 service 页面。
- 不生成 sitemap、robots、noindex、301、410。

### 具体变更
- 建立项目总规则、关键词治理规则、官网定位规则。
- 建立旧 service 页面治理规则、索引治理规则、内容治理规则、变更记录规则。

### 风险判断
- 风险等级：低。
- 当前只新增规范，不影响公开站点。

### 回滚点
- 删除本次新增规范文件即可回滚。

### 验收结果
- 待确认。

## 2026-04-30 - 阶段 4：生成系统增强与内容数据升级

### 变更类型
- 类型：工程 / 内容数据 / SEO / 自动质检。

### 变更原因
- 阶段 3 已完成 Python 静态生成系统基础版，但仍需要增强数据结构、模板组件、结构化数据、URL 清单和质量检查，降低后续维护成本。

### 变更范围
- 涉及文件：`site_src/`、`scripts/build_site.py`、`scripts/check_static_site.py`、`site/public/`、`docs/site-url-inventory.md`、`docs/stage-4-generator-upgrade.md`、`docs/build-and-maintenance.md`、`docs/stage-3-static-generator.md`、`project-status.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：仅更新新官网正式页面 sitemap，不包含旧 service 页面。

### 具体变更
- 完成阶段 4 生成系统增强。
- 新增 contact / FAQ / SEO / schema / content_blocks 数据。
- 升级 services / platforms / topics / markets 内容数据字段。
- 升级模板组件，新增面包屑、FAQ、CTA、服务边界和卡片网格 partial。
- 升级 `build_site.py`，自动生成 JSON-LD、sitemap lastmod、robots 和 URL inventory。
- 升级 `check_static_site.py`，增强 canonical、站内链接、sitemap、robots、服务边界和高风险词检查。
- 自动生成 `docs/site-url-inventory.md`。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。

### 风险判断
- 风险等级：中低
- 当前变更涉及生成系统和全站生成结果，但仍只在新官网目录内，不触碰旧 service 页面和部署配置。

### 回滚点
- 回退本次提交即可恢复阶段 3 生成系统。

### 验收结果
- `python scripts/build_site.py` 通过。
- `python scripts/check_static_site.py` 通过。

## 2026-04-30 - 阶段 5：关键词资产库与 URL 映射系统

### 变更类型
- 类型：关键词 / 结构 / SEO / 自动质检。

### 变更原因
- 9HWH 官网需要承接大量海外推广、引流获客、投放买量相关关键词，但不能把几万个关键词直接生成几万个公开页面。
- 需要建立关键词资产库、聚类规则、URL 映射和页面承接系统。

### 变更范围
- 涉及文件：`site_src/data/keywords/`、`scripts/build_keyword_assets.py`、`scripts/build_site.py`、`scripts/check_static_site.py`、`data/keyword-assets/`、`site/public/`、`docs/stage-5-keyword-asset-system.md`、`docs/keyword-to-url-map.md`、`docs/keyword-cluster-summary.md`、`project-status.md`、`docs/build-and-maintenance.md`、`docs/stage-4-generator-upgrade.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：只更新现有正式承接页 sitemap，不收录原始关键词列表。

### 具体变更
- 建立关键词资产库。
- 建立 keyword seed / rules / clusters / url_map。
- 新增 `scripts/build_keyword_assets.py`。
- 生成 keyword assets。
- 接入 `build_site.py`，在页面展示少量关键词承接方向。
- 升级 `check_static_site.py`，检查关键词资产、cluster target、首页敏感词和 blocked promise。
- 新增 keyword-to-url-map 和 cluster summary 文档。
- 未生成几万个公开页面。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。

### 风险判断
- 风险等级：中
- 主要风险：关键词资产中包含内部敏感类目，因此必须通过 rules、cluster 和 check 脚本控制，不允许进入首页、导航、sitemap 或公开页面。
- 风险控制方式：敏感类目标记为 `internal_only`，blocked promise 标记为 `blocked`，公开页面只展示少量代表性关键词承接方向。

### 回滚点
- 回退本次提交即可恢复阶段 4 生成系统。

### 验收结果
- `python scripts/build_keyword_assets.py` 通过。
- `python scripts/build_site.py` 通过。
- `python scripts/check_static_site.py` 通过。

## 2026-04-30 - 阶段 6：内容生产流水线与 DeepSeek 写作任务包

### 变更类型
- 类型：内容 / 生产流程 / 自动质检。

### 变更原因
- 需要把关键词资产转化为可控的内容生产任务，而不是直接生成大量低质量公开页面。
- 后续正文默认由 DeepSeek 负责，Codex 负责任务包、接入、构建和检查。

### 变更范围
- 涉及文件：`site_src/data/content/`、`site_src/content_drafts/README.md`、`scripts/build_content_queue.py`、`scripts/generate_deepseek_tasks.py`、`scripts/build_site.py`、`scripts/check_static_site.py`、`data/content-assets/`、`data/deepseek-tasks/`、`docs/stage-6-content-pipeline.md`、`docs/content-production-workflow.md`、`docs/content-opportunity-report.md`、`docs/deepseek-task-index.md`、`docs/stage-5-keyword-asset-system.md`、`docs/build-and-maintenance.md`、`project-status.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：否；未完成内容不进入 sitemap。

### 具体变更
- 建立内容任务队列。
- 新增 content_queue / content_rules / content_status / content_slots。
- 新增 `scripts/build_content_queue.py`。
- 新增 `scripts/generate_deepseek_tasks.py`。
- 生成 DeepSeek 写作任务包。
- 新增 content_drafts 接入规范。
- 升级 `build_site.py` 内容接入逻辑，仅发布 `ready_to_publish` 或 `published` 内容。
- 升级 `check_static_site.py` 内容状态检查。
- 未直接批量写文章正文。
- 未生成几千个公开页面。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。

### 风险判断
- 风险等级：中
- 主要风险：内容任务数量增加后，如果缺少状态控制，容易误生成未审核页面。
- 风险控制方式：planned / prompt_ready 不进入 sitemap；只有 ready_to_publish / published 且有 draft 才可生成公开页面。

### 回滚点
- 回退本次提交即可恢复阶段 5 关键词资产系统。

### 验收结果
- `python scripts/build_content_queue.py` 通过。
- `python scripts/generate_deepseek_tasks.py` 通过。
- `python scripts/build_site.py` 通过。
- `python scripts/check_static_site.py` 通过。

## 2026-04-30 - 阶段 7：DeepSeek 第一批内容生产任务与回稿接入

### 变更类型
- 类型：内容生产 / 任务批次 / 审核流程。

### 变更原因
- 需要将阶段 6 的内容任务系统推进到可执行生产状态，生成第一批 DeepSeek 写作任务，并建立回稿导入、审核和状态管理工具。

### 变更范围
- 涉及文件：`data/deepseek-batches/`、`scripts/build_deepseek_batch.py`、`scripts/import_deepseek_drafts.py`、`scripts/review_content_drafts.py`、`scripts/update_content_status.py`、`scripts/build_site.py`、`scripts/check_static_site.py`、`site/public/`、`docs/stage-7-deepseek-batch-001.md`、`docs/deepseek-output-format.md`、`docs/content-review-rules.md`、`docs/content-production-workflow.md`、`project-status.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：否；未审核正文不进入 sitemap。

### 具体变更
- 生成 DeepSeek batch-001 写作任务包。
- 新增 `scripts/build_deepseek_batch.py`。
- 新增 `scripts/import_deepseek_drafts.py`。
- 新增 `scripts/review_content_drafts.py`。
- 新增 `scripts/update_content_status.py`。
- 新增 DeepSeek 输出格式文档。
- 新增内容审核规则。
- 更新内容生产工作流。
- 未直接写正文。
- 未生成未审核内容页。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。

### 风险判断
- 风险等级：中
- 主要风险：DeepSeek 回稿如果未审核直接发布，会造成风险表达、低质量内容或索引失控。
- 风险控制方式：回稿先进入 inbox，经导入和审核脚本检查，再手动更新状态，只有 ready_to_publish 或 published 才生成页面。

### 回滚点
- 回退本次提交即可恢复阶段 6 内容生产系统。

### 验收结果
- `python scripts/build_deepseek_batch.py` 通过。
- `python scripts/build_site.py` 通过。
- `python scripts/check_static_site.py` 通过。

## 2026-04-30 - 阶段 3：官网静态生成系统重建

### 变更类型
- 类型：结构 / 内容 / 工程化 / 索引。

### 变更原因
- 阶段 2B 已建立新官网页面结构，但继续手写 `site/public/*.html` 会造成导航、页脚、sitemap 和服务边界维护成本过高。
- 需要升级为 Python 标准库驱动的静态站生成系统，让后续维护优先修改数据和模板。

### 变更范围
- 涉及文件：`site_src/`、`scripts/build_site.py`、`scripts/check_static_site.py`、`site/public/`、`docs/stage-3-static-generator.md`、`docs/build-and-maintenance.md`、`project-status.md`、`docs/stage-2b-content-structure.md`、`docs/stage-2-site-build-plan.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：是，由生成器自动生成新官网 `sitemap.xml`

### 具体变更
- 建立 Python 静态生成器。
- 建立 `site_src` 数据和模板。
- 自动生成 `site/public`。
- 自动生成 `sitemap.xml` 和 `robots.txt`。
- 保留 `blog` 入口，不生成文章正文。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署阶段。
- 未 push。

### 风险判断
- 风险等级：中
- 主要风险：后续如果绕过生成器直接手改 `site/public`，会造成源文件和生成结果不一致。
- 风险控制方式：新增构建与维护文档，明确后续维护优先修改 `site_src/`。

### 回滚点
- 回退 `site_src/`、脚本、生成结果和本次文档修订即可恢复到阶段 2B 手写静态站状态。

### 验收结果
- 待确认。

## 2026-04-30 - 阶段 2B：站内内容与关键词承接体系建设

### 变更类型
- 类型：结构 / 内容 / 关键词 / 索引。

### 变更原因
- 当前处于官网重建期，重点应继续推进站内内容、页面结构、关键词承接和内链体系，而不是进入 Cloudflare Pages 部署配置。
- 需要为细分业务关键词建立克制、正式、可长期维护的 topics 承接页。

### 变更范围
- 涉及文件：`site/public/` 下现有页面、`site/public/topics/` 新增页面、`site/public/assets/css/styles.css`、`site/public/sitemap.xml`、`project-status.md`、`docs/stage-2-site-build-plan.md`、`docs/stage-2b-content-structure.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：是，仅更新新官网 `sitemap.xml`

### 具体变更
- 大范围重写新官网第一版内容。
- 新增 `/topics/` 关键词承接页面。
- 新增虚拟币推广、交友引流、游戏推广、金融咨询获客、贷款获客、保险获客、移民咨询获客、网赚与兼职获客主题页。
- 更新 sitemap，加入全部新官网正式页面。
- 强化全站导航、页脚、服务页、平台页、topics 页之间的内链。
- 未处理旧 service 页面。
- 未做 Cloudflare Pages 部署配置。
- 未新增 `_headers`。
- 未新增 `_redirects`。
- 未 push。

### 风险判断
- 风险等级：中
- 主要风险：topics 页面涉及更细分的业务关键词，需要持续保持克制表达，避免进入高风险承诺。
- 风险控制方式：所有主题页使用路径梳理、渠道建议、投放准备、执行协助、合作前确认政策和法规边界的表达。

### 回滚点
- 回退 `site/public/` 页面、`site/public/sitemap.xml`、阶段 2B 文档和本次 change-log 记录即可回到阶段 2 新站第一版。

### 验收结果
- 待确认。

## 2026-04-30 - 阶段 2：创建新官网静态站第一版

### 变更类型
- 类型：结构 / 内容 / 索引。

### 变更原因
- 阶段 1 首页草稿已完成，需要继续推进为可本地预览的新官网静态站第一版。
- 需要建立首页、服务页、平台页、市场页、内容中心、联系页和统一样式基线。

### 变更范围
- 涉及文件：`site/public/index.html`、`site/public/services/index.html`、`site/public/services/overseas-promotion/index.html`、`site/public/services/traffic-acquisition/index.html`、`site/public/services/ad-campaign-support/index.html`、`site/public/services/media-buying/index.html`、`site/public/platforms/index.html`、`site/public/platforms/tk/index.html`、`site/public/platforms/fb/index.html`、`site/public/platforms/google/index.html`、`site/public/markets/index.html`、`site/public/blog/index.html`、`site/public/contact/index.html`、`site/public/404.html`、`site/public/assets/css/styles.css`、`site/public/sitemap.xml`、`site/public/robots.txt`、`project-status.md`、`docs/stage-1-homepage-plan.md`、`docs/stage-2-site-build-plan.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：是，仅新增新官网版本的 `sitemap.xml` 与 `robots.txt`

### 具体变更
- 创建新官网静态站第一版。
- 创建首页、服务页、平台页、市场页、内容中心、联系页和 404 页面。
- 创建统一样式文件 `site/public/assets/css/styles.css`。
- 创建 `sitemap.xml` 和 `robots.txt`。
- `sitemap.xml` 只包含新官网正式页面。
- `robots.txt` 未屏蔽 `/service_`。
- 未处理旧 service 页面。
- 未提交 `site/legacy-source`。
- 未 push。

### 风险判断
- 风险等级：中
- 主要风险：当前联系方式仍为占位内容，Cloudflare Pages 构建与部署目录尚未确认。
- 风险控制方式：先以本地静态预览为基线，不对旧 service 页面和 legacy-source 做任何处理。

### 回滚点
- 回退 `site/public/` 相关文件和阶段 2 文档即可恢复到首页草稿阶段。

### 验收结果
- 待确认。

## 2026-04-30 - 阶段 0 收尾：独立重建工作区初始化

### 变更类型
- 类型：规范 / 结构。

### 变更原因
- 需要将 `E:\9HWH` 从其他项目目录隔离，建立独立官网重建仓库和阶段 1 输入准备环境。

### 变更范围
- 涉及文件：AGENTS.md、README.md、project-rules.md、project-status.md、stage-gates.md、old-service-policy.md、indexing-policy.md、change-log.md、.gitignore、docs/stage-1-homepage-inputs.md、docs/local-project-layout.md。
- 涉及目录：site/、scripts/、tools/、backups/、docs/、docs/archive/。
- 是否影响旧 service 页面：否。
- 是否影响索引：否。

### 具体变更
- 初始化 `E:\9HWH` 为独立官网重建目录并建立独立 Git 仓库。
- 修正根目录规范引用，确认规范文件不再引用旧规范目录路径。
- 建立重建期基础目录和空目录占位文件。
- 补齐 `.gitignore`。
- 生成阶段 1 首页重做输入清单和本地项目目录说明。
- 未改首页、sitemap、robots、service 页面。

### 风险判断
- 风险等级：低。
- 当前变更仅涉及规范文件、文档和目录初始化，不影响公开站点。

### 回滚点
- 删除本次新增的目录占位文件、文档和 Git 初始化结果即可回滚。

### 验收结果
- 待确认。

## 2026-04-30 - 阶段 1 准备：恢复并审计旧官网源码

### 变更类型
- 类型：规范 / 结构 / 回滚。

### 变更原因
- 需要从 GitHub 恢复旧官网源码，建立 `legacy-source` 归档，并为首页重做生成可执行的文件级计划。

### 变更范围
- 旧源码仓库：https://github.com/wangwuda54/9hwh
- 旧源码恢复目录：`E:\9HWH-source`
- 旧源码归档目录：`E:\9HWH\site\legacy-source`
- 涉及文件：`docs/current-source-audit.md`、`docs/stage-1-homepage-plan.md`、`docs/stage-1-homepage-inputs.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：否

### 具体变更
- 从 GitHub 恢复旧官网源码到 `E:\9HWH-source`
- 将旧源码完整归档到 `site/legacy-source`
- 新增 `current-source-audit.md`
- 新增 `stage-1-homepage-plan.md`
- 更新 `stage-1-homepage-inputs.md`
- 未改首页
- 未改 sitemap
- 未改 robots
- 未处理 service 页面
- 未 push

### 风险判断
- 风险等级：低
- 当前变更仅涉及源码恢复、归档和文档审计，不触碰线上文件

### 回滚点
- 删除 `E:\9HWH\site\legacy-source` 归档目录和本次新增文档即可回滚

### 验收结果
- 待确认。

## 2026-04-30 - 阶段 1：首页定位修正与首页草稿

### 变更类型
- 类型：规范 / 内容 / 结构。

### 变更原因
- 当前业务定位已从“广告账户开户/BM 服务商”修正为“海外流量推广与获客支持”。
- 需要把首页结构、首页文案方向和 URL 规划同步修正为更宽、更稳、更可调整的表达。

### 变更范围
- 涉及文件：`site/public/index.html`、`project-status.md`、`docs/stage-1-homepage-plan.md`、`docs/stage-1-homepage-inputs.md`、`change-log.md`
- 是否影响旧 service 页面：否
- 是否影响索引：否

### 具体变更
- 将首页方向修正为海外流量推广、引流获客、广告投放支持、拉新买量和代投代运营协助。
- 将首页 URL 规划修正为 `/services/`、`/platforms/`、`/markets/`、`/blog/`、`/contact` 方向。
- 新增首页草稿文件 `site/public/index.html`。
- 明确首页服务边界，不承诺绕过平台审核，不保证审核或投放结果。
- 未改 sitemap
- 未改 robots
- 未改 `_headers`
- 未改 `_redirects`
- 未处理 service 页面
- 未 push

### 风险判断
- 风险等级：低
- 当前变更仅涉及首页草稿和阶段文档，不触碰旧站线上文件

### 回滚点
- 删除或回退 `site/public/index.html` 及本次文档修订即可回滚

### 验收结果
- 待确认。
