# Stage 15 GitHub Sync Preflight Report

## 1. Stage Goal

本阶段目标不是继续开发，而是对阶段 8 到阶段 14 的官网成果做最终本地审计，并安全同步到 GitHub 远程 `rescue-v1` 分支，同时继续保持不部署 Cloudflare Pages、不合并 `main`、不处理旧 service 页面。

## 2. Current Git Workspace

- 主工作区：`E:/9HWH`
- 当前分支：`rescue-v1`
- 当前 origin：`https://github.com/wangwuda54/9hwh.git`
- push 前 HEAD：`63a7266c394f7394b995e275609488fadb543cea`

## 3. Current Content State

- `draft_received`: `0`
- `reviewed`: `7`
- `published`: `3`

首批 `published` 内容为：

1. `c007-dating-traffic-dating-how-to-002063ad`
2. `c010-media-buying-part-time-how-to-5875d40e`
3. `c031-fb-promotion-fb-dating-traffic-5035e1c0`

## 4. Sitemap Readiness

- `check_sitemap_readiness.py` 通过
- sitemap 只包含必要公开基础页面和 3 篇已 `published` 内容
- `reviewed` 未发布内容未进入 sitemap
- `internal_only` 内容未进入 sitemap
- `robots.txt` 仍包含 sitemap 声明

## 5. GSC Status

- GSC 提交方案已准备
- 后续应提交 `https://www.9hwh.com/sitemap.xml`
- 未使用 Google Indexing API

## 6. Cloudflare Status

- 本阶段未部署 Cloudflare Pages
- 部署前仍需人工确认已发布页面、sitemap、robots 和业务复核状态

## 7. Old Service Pages

- 旧 service 页面未处理

## 8. Sensitive File Audit

- 未发现 `.env`、API key、DeepSeek 密钥、config 密钥文件进入 Git 提交面
- 未发现 `E:/py9`、`E:/py6`、`C:/py6` 文件被纳入 Git
- 本地存在 `scripts/__pycache__/` 运行缓存，但未被 Git 跟踪
- 未发现 `E:/9HWH_REPO` 或 `E:/9HWH_BACKUP_BEFORE_REPO_FIX` 被纳入 Git

## 9. Push Checks

- `review_content_drafts.py` 通过
- `pre_publish_audit.py --mode normal --limit 3 --dry-run` 通过
- `publish_from_queue.py --dry-run` 通过
- `check_sitemap_readiness.py` 通过
- `build_outreach_tasks.py` 通过
- `build_site.py` 通过
- `check_static_site.py` 通过

## 10. Push Target

- 仅 push 到：`origin rescue-v1`

## 11. Post-Push Verification

push 后应检查：

1. `git status --short` 应为空
2. `git log -1 --oneline` 应显示最新阶段 15 commit
3. `git ls-remote --heads origin rescue-v1` 应指向同一 commit
4. 远程应可看到：
   - `scripts/pre_publish_audit.py`
   - `scripts/plan_publish_queue.py`
   - `scripts/publish_from_queue.py`
   - `docs/stage-15-github-sync-preflight-report.md`
   - `site_src/data/content/content_status.json`

## 12. Next Recommendation

1. 远程同步完成后，由人工在 GitHub 上复核 `rescue-v1` 的关键文件。
2. 下一阶段如果要进入真实上线，应先做部署前人工复核，再单独执行 Cloudflare Pages 部署。
3. 在未做业务复核前，不继续增加 `published` 数量。
