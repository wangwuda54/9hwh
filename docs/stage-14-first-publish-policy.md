# Stage 14 First Publish Policy

## Why Not Publish 10 Or 18000 Pages At Once

一次性放量会让官网失去“可控发布”的能力。我们现在更需要观察首批页面是否被正常构建、是否正确进入 sitemap、是否只暴露 `published` 页面、以及站内承接是否稳定，而不是追求短期数量。

## First Batch Recommendation

- 首批建议数量：`3` 篇
- `daily normal limit`：`3`
- `daily scaling limit`：`12`
- `hard limit`：`20`

## Risk Dispersion Rule

- 首批不要同时发布多个 `crypto / loan / insurance / immigration` 主题。
- 首批优先混排：
  - 1 篇普通长尾问题页
  - 1 篇服务或平台承接清晰的页面
  - 1 篇社交流量或游戏主题页

## Reviewed vs Published

- `reviewed` 代表内容通过质量审核，但还不是公开页面。
- `published` 才允许进入公开站、进入 sitemap、被后续 GSC 提交覆盖。
- 任何 `reviewed` 内容在正式放行前都必须保持不公开。

## Pre-Publish Checklist

- 状态必须是 `reviewed`
- 审核必须 `pass`
- `warning = 0`
- `fail = 0`
- 目标 URL 唯一
- 至少 4 个站内内链
- 不含禁用表达
- 不含 HTML
- 不含一级标题 `#`
- 不链接 `internal_only`
- 不链接未公开文章页

## Rollback Strategy

- 如果 staged publish 后构建或 sitemap 检查失败，立即把该批内容从 `published` 回退到 `reviewed`
- 重新构建站点并复跑静态检查
- 在确认问题修复前，不继续扩大发布数量
