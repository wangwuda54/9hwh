# Stage 14 First Publish Preflight Report

## 1. Stage Goal

本阶段把官网从“reviewed 内容池 + 发布队列”推进到“首批 published 可安全放行”的状态，并为后续 GSC / Cloudflare 前置操作准备本地审计结果。

## 2. First Publish Strategy

- 首批只放行 `3` 篇
- 采用 `normal` 模式
- 组合为：
  - `1` 篇普通长尾问题页
  - `1` 篇服务承接页
  - `1` 篇社交流量主题页
- 避免首批堆积 `crypto / loan / insurance / immigration`

## 3. Pre-Publish Audit Result

- `pre_publish_audit.py --mode normal --limit 3 --dry-run` 通过
- 审计建议首批候选为：
  - `c007-dating-traffic-dating-how-to-002063ad`
  - `c010-media-buying-part-time-how-to-5875d40e`
  - `c031-fb-promotion-fb-dating-traffic-5035e1c0`

## 4. Actual Published Status

- 本阶段已执行 staged publish
- 实际 `published` 的内容为：
  - `c007-dating-traffic-dating-how-to-002063ad` / `交友私聊怎么做：推广路径、渠道判断和准备清单` / `/blog/dating-how-to-002063ad/`
  - `c010-media-buying-part-time-how-to-5875d40e` / `兼职怎么做：推广路径、渠道判断和准备清单` / `/blog/part-time-how-to-5875d40e/`
  - `c031-fb-promotion-fb-dating-traffic-5035e1c0` / `FB交友引流：海外推广与获客准备指南` / `/blog/topics/fb-dating-traffic-5035e1c0/`

## 5. Status Summary

- `draft_received`: `0`
- `reviewed`: `7`
- `published`: `3`

## 6. Sitemap Readiness

- `check_sitemap_readiness.py` 通过
- sitemap 只包含必要基础公开页和 `3` 篇已 `published` 页面
- `reviewed` 未发布内容没有进入 sitemap
- `internal_only` 内容没有进入 sitemap

## 7. Build And Static Checks

- `build_site.py` 通过
- `check_static_site.py` 通过
- 本阶段修复了 published 文章 breadcrumb 的 `/blog/topics/` 错链
- 本阶段修复了静态检查脚本对 published 文章 URL 的 sitemap 识别问题

## 8. C045 Block

- `c045` 仍保持 `internal_only: true`
- `c045` 没有进入 publish queue
- `c045` 没有进入公开站

## 9. GSC And Cloudflare Status

- 已生成 GSC / Cloudflare 前置检查报告
- GSC 方案为提交 sitemap，不使用 GIA
- 当前仍不部署
- 当前仍不 push

## 10. Boundary Confirmation

- 未处理旧 service 页面
- 未使用 `E:/9HWH_REPO` 作为开发目录
- 未 push
- 未部署

## 11. Next Recommendation

1. 对这 `3` 篇已 published 页面做人工业务复核。
2. 若准备进入真实上线阶段，再安排手工 push 与部署。
3. 观察首批页面的抓取、索引和承接表现后，再决定是否按队列继续放量。
