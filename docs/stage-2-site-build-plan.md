# 阶段 2：新官网基础页面建设记录

## 1. 本次创建的页面清单

- `site/public/index.html`
- `site/public/services/index.html`
- `site/public/services/overseas-promotion/index.html`
- `site/public/services/traffic-acquisition/index.html`
- `site/public/services/ad-campaign-support/index.html`
- `site/public/services/media-buying/index.html`
- `site/public/platforms/index.html`
- `site/public/platforms/tk/index.html`
- `site/public/platforms/fb/index.html`
- `site/public/platforms/google/index.html`
- `site/public/markets/index.html`
- `site/public/blog/index.html`
- `site/public/contact/index.html`
- `site/public/404.html`
- `site/public/assets/css/styles.css`
- `site/public/sitemap.xml`
- `site/public/robots.txt`

## 2. 新 URL 结构

- `/`
- `/services/`
- `/services/overseas-promotion/`
- `/services/traffic-acquisition/`
- `/services/ad-campaign-support/`
- `/services/media-buying/`
- `/platforms/`
- `/platforms/tk/`
- `/platforms/fb/`
- `/platforms/google/`
- `/markets/`
- `/blog/`
- `/contact/`
- `/404.html`

## 3. 页面定位

- 首页：面向出海项目的海外流量推广与获客支持。
- 服务页：围绕海外推广、引流获客、广告投放支持和买量投流建立正式入口。
- 平台页：围绕 TK、FB、Google 建立平台方向说明。
- 市场页：说明重点关注的海外市场方向，不夸大为固定本地团队。
- 内容中心：作为后续内容建设入口，不批量生成文章正文。
- 联系页：承接咨询信息和合作前准备清单。

## 4. 未处理事项

- 未处理旧 service 页面。
- 未做 301 / noindex / 410。
- 未建立 `_headers` 与 `_redirects`。
- 未确认 Cloudflare Pages 构建命令与输出目录。
- 未填入正式联系方式。
- 未进行视觉强化和品牌资产补充。

## 5. 下一步建议

- 优先完善视觉层和页面信息层级。
- 确认 `site/public/` 是否作为最终部署目录。
- 补充正式联系方式和品牌介绍。
- 准备 Cloudflare Pages 构建与部署配置。
- 在进入旧 service 页面阶段前，先完成盘点与风险批次设计。

## 6. 旧 service 页面说明

- 本阶段明确未处理旧 service 页面。
- 本阶段未提交 `site/legacy-source`。
- 本阶段没有把旧 service 页面加入新站 `sitemap.xml`。

## 7. 阶段 2B 页面清单

- 已重写首页 `/`。
- 已重写服务页 `/services/`、`/services/overseas-promotion/`、`/services/traffic-acquisition/`、`/services/ad-campaign-support/`、`/services/media-buying/`。
- 已重写平台页 `/platforms/`、`/platforms/tk/`、`/platforms/fb/`、`/platforms/google/`。
- 已新增 topics 页面 `/topics/`、`/topics/crypto-promotion/`、`/topics/dating-traffic/`、`/topics/game-promotion/`、`/topics/finance-leads/`、`/topics/loan-leads/`、`/topics/insurance-leads/`、`/topics/immigration-leads/`、`/topics/online-work-leads/`。
- 已重写市场页 `/markets/`、内容中心 `/blog/`、联系页 `/contact/` 和 `404.html`。

## 8. 全站内链结构

- 首页链接到服务、平台、topics、市场、联系页。
- 服务页链接到对应服务详情、平台页和 topics 页。
- 平台页链接到对应服务页和相关 topics 页。
- topics 页链接到推荐服务入口和联系页。
- 市场页链接到服务与 topics。
- 内容中心暂不生成文章正文，只承接未来内容分类。

## 9. sitemap 更新

- `site/public/sitemap.xml` 已加入全部新官网正式页面。
- sitemap 未包含旧 service 页面。
- sitemap 未包含 `legacy-source`。
- sitemap 未包含 `404.html`。

## 10. 本阶段未做事项

- 未做 Cloudflare Pages 部署配置。
- 未新增 `_headers`。
- 未新增 `_redirects`。
- 未处理旧 service 页面。
- 未做 301 / noindex / 410。

## 11. 阶段 3 生成系统记录

- 已建立 Python 静态生成器 `scripts/build_site.py`。
- 已建立检查脚本 `scripts/check_static_site.py`。
- 已建立 `site_src/data/` 和 `site_src/templates/`。
- 已由生成器自动生成 `site/public/`。
- 已自动生成 `sitemap.xml` 和 `robots.txt`。
- 保留 `blog/` 入口，不生成文章正文。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署阶段。
