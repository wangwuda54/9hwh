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
