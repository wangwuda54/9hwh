# GSC And Cloudflare Preflight Report

## Current Publish Status

- 当前已 `published`：`3` 篇
- 当前 `reviewed` 未发布：`7` 篇
- 当前 `draft_received`：`0` 篇

## Sitemap Status

- `sitemap.xml` 已准备好
- 当前 sitemap 只包含必要公开基础页面和 `3` 篇已 `published` 内容
- `reviewed` 未发布内容未进入 sitemap
- `internal_only` 内容未进入 sitemap

## Robots

- `robots.txt` 存在
- `robots.txt` 已包含 `Sitemap: https://www.9hwh.com/sitemap.xml`

## GSC Note

- 后续应提交 sitemap 到 GSC
- 本项目不使用 Google Indexing API
- 本阶段不调用任何外部 Google API

## Cloudflare Pages Preflight

部署前仍需人工确认：

1. 当前 sitemap 与公开站是否只暴露允许公开的页面
2. 首批 3 篇 published 的页面内容、URL、内链和承接页是否已经过业务复核
3. 是否准备好对应的 GSC sitemap 提交流程
4. 是否确认当前仓库内容不包含敏感配置、缓存和无关文件

## Current Release Guardrail

- 当前是否允许部署：不部署
- 当前是否允许 push：不 push

## Rollback

- 若部署前或部署后发现问题，可将这 3 篇从 `published` 回退为 `reviewed`
- 重新 build、重跑 sitemap/static checks
- 在问题修复前，不继续放量
