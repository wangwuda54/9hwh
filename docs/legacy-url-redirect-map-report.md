# Legacy URL Redirect Map Report

## 扫描来源

- 本地旧站归档：`site/legacy-source`。读取了 `index.html`、`robots.txt`、`sitemap.xml` 和 `18000` 个 `service_*.html` 文件。
- 远程备份分支：`origin/backup-main-before-9hwh-rescue`。该分支根目录保留 `18000` 个 `service_*.html` 文件和旧 `sitemap.xml`。
- 当前仓库历史和现有审计文档：确认旧 sitemap 曾包含 `18000` 个旧服务 URL，首页曾直接链接其中 `100` 个旧服务入口。

## 映射结果

- 找到旧服务 URL：18000
- JSON 推荐 high confidence 301：14289
- JSON 推荐 medium confidence 301 / 需复核：2107
- JSON 低置信度 302：1604
- Cloudflare v1 精确 301 来源 URL：900
- Cloudflare v1 精确 301 规则：1800（同时覆盖无扩展名和 .html 两种旧路径）
- Cloudflare v1 302 兜底规则：2，目标为 `/services/legacy/`

| Target | URL count |
| --- | ---: |
| /platforms/tk/ | 3119 |
| /topics/finance-leads/ | 2870 |
| /topics/crypto-promotion/ | 2782 |
| /platforms/fb/ | 2292 |
| /topics/dating-traffic/ | 1926 |
| /topics/loan-leads/ | 1907 |
| /services/legacy/ | 1604 |
| /topics/game-promotion/ | 950 |
| /platforms/google/ | 550 |

## /service_15209

`/service_15209` 不是单独特殊处理页，它只是批量映射中的一条。旧标题和 H1 包含“虚拟币”，因此映射到 `/topics/crypto-promotion/`，状态建议为 301，confidence 为 high。

## 兜底策略

无法从旧标题、description、H1 或关键词中可靠识别主题的旧 `/service_*` URL，统一 302 到 `/services/legacy/`。这样用户不会再看到大量 404，也不会把不确定或低质旧意图永久传递给新页面。

## 为什么不能全部 301 到首页

旧页面意图分散，很多查询与首页不匹配。全部 301 到首页容易形成低相关跳转、软 404 或首页主题污染，也会让从 Google 进入的用户找不到原查询对应方向。

## 为什么不能全部恢复旧页面

旧服务页约 18000 个，多数是模板组合页，存在重复、低质和高风险表达。全部恢复会重新制造链接池和低质量索引信号，也会把旧风险内容重新公开。

## Sitemap 说明

本次没有把任何旧 `service_*` URL 放回 sitemap，也没有恢复旧页面正文。`/services/legacy/` 作为承接页生成，但设置 `noindex,follow` 且不进入 sitemap，用于用户承接和临时分流。

## 后续 GSC 补映射

1. 从 Google Search Console 导出近 3 到 6 个月包含 `/service_` 的页面、查询、点击、展示和外链优先级。
2. 对有点击或展示的旧 URL 优先人工复核旧标题、查询意图和新承接页。
3. 将确认相关的 URL 从待复核或兜底 302 提升为精确 301。
4. 对无数据且高风险、无承接价值的 URL 单独进入后续 noindex 或 410 决策，不在本批次混合处理。

## GSC ?????2026-05-08?

- GSC ???`9hwh.com-Performance-on-Search-2026-05-08.xlsx`
- ?? sheet?`??`
- ??? service URL?953?? 999 ???????46 ??????? `.html` ??????
- P0 ?? URL?64
- P1 ??? URL?27?????????? P0?
- P2 ??? URL?367?????????? P0/P1?
- ??????? > 0 ? 64??? >= 10 ? 29????? <= 5 ? 412
- GSC ?? URL ????? 301 ????303
- ? GSC ??????? `_redirects` ?? 301 ??? URL?282
- GSC ?? URL ???????155
- ?? GSC URL ????????259
- ???? legacy 302 ? GSC URL?114

### ?? URL ??

| URL | Priority | Clicks | Impressions | Best position | Target | Status | Confidence | Needs review |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| `/service_6521` | P0 | 3.0 | 3.0 | 1.0 | `/services/legacy/` | 302 | low | True |
| `/service_5172` | P0 | 3.0 | 3.0 | 1.33 | `/services/legacy/` | 302 | low | True |
| `/service_15900` | P0 | 2.0 | 41.0 | 4.0 | `/topics/finance-leads/` | 301 | high | False |
| `/service_17702` | P0 | 2.0 | 4.0 | 4.0 | `/topics/dating-traffic/` | 301 | high | False |
| `/service_8577` | P0 | 2.0 | 2.0 | 3.0 | `/services/legacy/` | 302 | low | True |
| `/service_10764` | P0 | 1.0 | 9.0 | 1.44 | `/topics/crypto-promotion/` | 301 | high | False |
| `/service_3853` | P1 | 0.0 | 34.0 | 1.0 | `/topics/loan-leads/` | 301 | high | False |
| `/service_15284` | P1 | 0.0 | 31.0 | 7.7 | `/topics/game-promotion/` | 301 | high | False |
| `/service_7019` | P1 | 0.0 | 19.0 | 1.26 | `/topics/loan-leads/` | 301 | high | False |
| `/service_13195` | P1 | 0.0 | 18.0 | 7.83 | `/topics/loan-leads/` | 301 | high | False |
| `/service_17145` | P1 | 0.0 | 17.0 | 6.18 | `/services/legacy/` | 302 | low | True |
| `/service_16546` | P1 | 0.0 | 17.0 | 6.76 | `/topics/loan-leads/` | 301 | high | False |
| `/service_10040` | P1 | 0.0 | 18.0 | 1.0 | `/topics/dating-traffic/` | 301 | high | False |

### ????

P0/P1/P2 ???????????????? topic/platform ?????? URL??????? 301 ????? Slots?????????????????????????????????????? URL?????? topic ?????? 302 ? `/services/legacy/` ??? `needs_review=true`?
