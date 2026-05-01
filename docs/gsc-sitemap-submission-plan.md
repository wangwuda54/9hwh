# GSC Sitemap Submission Plan

## Goal

本阶段只为 Google Search Console 的 sitemap 提交做本地准备，不调用 Google API，不做 Google Indexing API 提交。

## Scope

- 检查 `site/public/sitemap.xml` 是否只包含公开页面和已 `published` 的内容 URL。
- 检查 `reviewed`、`draft_received`、`internal_only` 内容是否未进入 sitemap。
- 检查 `site/public/robots.txt` 是否存在并包含 Sitemap 地址。
- 为后续手工提交到 GSC 留下可审计报告。

## Why Not GIA

- 官网当前还是“可控发布准备阶段”，并没有进入大规模公开发布。
- Google Indexing API 适用范围有限，不适合把普通官网内容当作默认收录方案。
- 先把 sitemap、robots、内容状态边界理顺，比抢提交通道更重要。

## Manual Steps For Next Stage

1. 确认某批内容已经人工发布，并且 `status = published`。
2. 重新构建站点与 sitemap。
3. 运行 `python scripts/check_sitemap_readiness.py`。
4. 人工在 GSC 提交 `https://www.9hwh.com/sitemap.xml`。
5. 后续通过 GSC 观察索引和曝光，而不是自动化强推。
