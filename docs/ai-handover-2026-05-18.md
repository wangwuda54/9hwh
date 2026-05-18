# 9hwh 官网项目 AI 交接单

更新时间：2026-05-18

本文件是当前 9hwh 官网项目给新 ChatGPT Team / Codex 接手时的权威交接说明。历史文档、旧任务包、旧报告里可能残留旧口径；如果与本文冲突，以本文为准。

## 1. 当前项目定位

9hwh 是海外广告代理 / 广告投放服务商。

不是：

- 内容发布矩阵项目
- 国内平台投放项目
- SEO 代运营团队
- KOL 资源合作机构
- 自然流量运营项目

核心服务围绕客户的海外广告投放获客，包括广告账户、投放测试、广告素材、落地页、表单线索、私信 / 咨询承接、转化追踪、初期预算测试和线索质量复盘。

## 2. 核心广告代理平台

当前内容和服务口径应围绕海外广告代理平台：

- Facebook Ads / Meta Ads
- Google Ads
- TikTok Ads / TK Ads
- X Ads

补充说明：

- Instagram 属于 Meta Ads 生态，可作为广告版位或素材场景提到，不要写成独立内容发布平台。
- YouTube 属于 Google Ads 视频广告生态，可作为广告场景提到，不要写成独立内容发布平台。
- 自建站是落地页、服务页和转化承接页面，不是“内容发布平台”。
- LinkedIn / Reddit / SEO / 自建站内容发布不要默认写成主服务平台，除非具体关键词明确要求。

## 3. 文章内容方向

文章应围绕客户如何通过海外广告平台开户、投放、测试和获客。

优先写：

- 客户搜索这个词时真正想解决什么获客问题
- 适合用哪个海外广告平台测试
- 广告账户怎么准备
- 广告素材怎么准备
- 落地页怎么承接
- 表单字段怎么设计
- 私信 / 表单 / 咨询线索怎么接
- 转化追踪怎么设置
- 初期预算怎么测试
- 怎么判断线索质量
- 后续怎么调整关键词、素材、人群和页面

不要写成：

- 国内平台投放建议
- 百度 / 360 / 头条 / 抖音 / 微信 / 小红书 / 快手 / 腾讯广告 / 巨量
- 内容发布平台推荐
- KOL 合作方案
- SEO 内容矩阵方案
- 自然流量运营方案
- LinkedIn / Reddit / YouTube / Instagram 内容发布矩阵
- 在 Facebook / YouTube / Reddit / LinkedIn 上发布内容作为主方案

## 4. 当前发布链路

当前发布链路应保持分离：

```text
DeepSeek API 生成正文
-> data/deepseek-inbox
-> scripts/import_deepseek_drafts.py
-> scripts/review_content_drafts.py
-> scripts/approve_reviewed_drafts.py
-> scripts/daily_publish.py
-> GitHub push
-> Cloudflare Pages 自动部署
```

要点：

- `.github/workflows/daily-publish.yml` 已恢复 `schedule`。
- `scripts/daily_publish.py` 负责从 `reviewed` 内容中发布。
- `scripts/approve_reviewed_drafts.py` 负责把审核通过草稿迁移为 `reviewed`。
- `scripts/generate_deepseek_drafts.py` 负责调用 DeepSeek API 生成正文。
- 发布链和内容生成链必须分离。
- `daily_publish.py` 不允许调用 DeepSeek API。

## 5. 当前内容库存模式

不要再每天临时补 1 篇。当前正确模式是库存池：

- 批量生成正文
- 批量导入
- 批量审核
- 批量 approve 成 `reviewed`
- 每天自动发布一部分
- 长期保持 `reviewed` 库存

目标：

- `reviewed` 库存至少保持 15 篇
- 理想库存 30 篇
- 自动发布默认每天 3 篇
- 不要一次性把库存全部发布完

## 6. 当前规则状态

当前规则是：

- 不设置禁词
- 不做词级审核
- 不强制写服务边界固定词
- 自建站 SEO 内容允许保留客户真实搜索词

不要恢复：

- `blocked_terms`
- `FORBIDDEN_TERMS`
- `HIGH_RISK_MARKERS`
- `SERVICE_BOUNDARY_MARKERS`
- `high-risk topic missing service boundary wording`
- `missing service boundary wording`

尤其不要再强制文章包含：

- 投放前评估
- 项目适配
- 投放地区
- 资质材料
- 审核风险

这些词可以自然出现，但不能作为审核硬要求。

## 7. 已知最近关键提交

以下提交是当前交接口径相关的关键节点：

- `4f0bbeeef5d9de4a52673f0ab0b407c4e8de47eb` Remove term-based content prohibitions
- `d47e6425aa81b64b9f71622016bc216e8e3d3cb8` Remove blocked content terms
- `7d329e07` Build DeepSeek content backlog and publish inventory

如果本地 `git log` 有更新，以最新 `main` 为准补充。

## 8. 当前仍需关注的问题

### 8.1 每天是否自动发布

如果某天没有发布，优先查 GitHub Actions run，不要先怀疑内容。

检查顺序：

1. 今天有没有 `daily publish reviewed content for YYYY-MM-DD` commit
2. `data/content-assets/daily_publish_report.json` 日期是否是今天
3. GitHub Actions 是否有 schedule run
4. run 是否失败
5. `content_status.json` 里 `reviewed` 是否足够

### 8.2 内容方向是否写偏

若 DeepSeek 文章写成国内平台、内容发布矩阵、自然流量、KOL 合作方向，应修正 `generate_deepseek_drafts.py` prompt 和未发布库存。

原则：

- 已发布文章先不要批量改
- 优先保证后续生成和未发布库存方向正确
- 不要因为方向修正恢复词级禁词

### 8.3 库存不足

如果 `reviewed` 低于 15，先补 DeepSeek 正文库存，不要反复运行发布命令。

## 9. 常用检查命令

```powershell
git status --short
git pull --ff-only origin main
type site_src\data\content\content_status.json
type data\content-assets\daily_publish_report.json
python scripts/daily_publish.py --dry-run --mode normal --limit 3
python scripts/build_site.py
python scripts/check_static_site.py
python scripts/check_sitemap_readiness.py
```

如需查 GitHub Actions：

```powershell
gh run list --repo wangwuda54/9hwh --workflow "Daily 9HWH publish" --limit 10
```

查看指定 run 日志：

```powershell
gh run view <RUN_ID> --repo wangwuda54/9hwh --log
```

## 10. 禁止事项

新 ChatGPT Team / Codex 接手时，默认不要做以下事项：

- 不要提交 `AGENTS.md`
- 不要改 workflow，除非明确发现 schedule 丢失
- 不要改 `daily_publish.py`，除非明确 bug
- 不要让 `daily_publish.py` 调用 DeepSeek API
- 不要直接操作 Cloudflare
- 不要处理旧 service 页面
- 不要扩大 `_redirects`
- 不要改 405、501、510、py6、py9
- 不要恢复禁词审核
- 不要恢复服务边界固定词审核
- 不要把广告代理业务写成内容发布平台
- 不要把海外广告代理写成国内平台投放

## 11. 新接手第一步

新 ChatGPT Team / Codex 接手后，第一步只做检查，不要立刻改代码：

```powershell
cd /d E:\sites\9hwh
git status --short
git pull --ff-only origin main
type site_src\data\content\content_status.json
type data\content-assets\daily_publish_report.json
git log --oneline -10
```

然后判断当前是：

- 发布链问题
- GitHub Actions 触发问题
- 内容库存问题
- DeepSeek 生成方向问题
- Cloudflare 部署问题

不要把这些问题混在一起处理。
