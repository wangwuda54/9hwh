# 阶段 1：首页重做输入清单

## 1. 阶段 1 目标

- 首页从旧 service 链接池改成正式官网首页。
- 明确 9HWH 的服务定位为海外流量推广与获客支持服务站。
- 建立核心服务入口。
- 建立地区入口。
- 建立行业入口。
- 建立联系入口。
- 不处理旧 service 页面。
- 不改 sitemap / robots。

## 2. 进入阶段 1 前必须提供的信息

- 当前官网源码所在目录：`E:\9HWH-source`
- 旧源码恢复目录：`E:\9HWH-source`
- legacy 归档目录：`E:\9HWH\site\legacy-source`
- 当前首页文件路径：`E:\9HWH-source\index.html`
- 当前是否纯静态 HTML：是
- 是否使用框架：未发现，当前判断为否
- Cloudflare Pages 构建命令：未确认
- Cloudflare Pages 输出目录：未确认
- 当前 sitemap.xml 内容：根目录存在 `E:\9HWH-source\sitemap.xml`，内容为 `18000` 个 `service_*.html` URL 列表
- sitemap.xml 路径：`E:\9HWH-source\sitemap.xml`
- 当前 robots.txt 内容：根目录存在 `E:\9HWH-source\robots.txt`，内容为 `Googlebot Allow /`、`User-agent: * Disallow: /`，并声明 `Sitemap: https://www.9hwh.com/sitemap.xml`
- robots.txt 路径：`E:\9HWH-source\robots.txt`
- 当前 `_headers` 内容：未确认，旧源码目录内未发现 `_headers`
- `_headers` 路径：未确认
- 当前 `_redirects` 内容：未确认，旧源码目录内未发现 `_redirects`
- `_redirects` 路径：未确认
- 构建配置路径：未确认，旧源码目录内未发现 `package.json`、`wrangler.toml` 或前端框架配置
- 当前 service 页面生成脚本位置：未确认
- service 页面样例：`E:\9HWH-source\service_0.html`、`E:\9HWH-source\service_7904.html`、`E:\9HWH-source\service_17996.html`
- 当前首页是否自动插入 service 链接池：否，当前判断为直接写死在 `index.html`
- service 链接池来源判断：写死在 HTML；依据是 `index.html` 中直接存在 `100` 个 `href="service_*.html"` 链接，未发现 JS 动态生成或 Python 脚本
- 当前导航和页脚文件位置：未发现独立文件；当前页脚位于 `E:\9HWH-source\index.html`，导航未确认

## 3. 首页重做方向

- 首页不再作为 service 链接池。
- 首页定位：
  - 9HWH 是面向出海项目的海外流量推广与获客支持服务站，围绕 TK、FB、Google 等主流渠道，提供推广咨询、广告投放、引流获客、拉新买量和代运营协助。
- 首页允许写：
  - 海外流量推广
  - 引流获客
  - 广告投放支持
  - 拉新买量
  - 代投代运营
  - TK 推广支持
  - FB 推广支持
  - Google 推广支持
  - 海外市场推广咨询
- 首页禁止写成：
  - Google Ads 开户服务商
  - TikTok Ads 开户服务商
  - Facebook BM 开户服务商
  - 某国家广告开户注册服务
- 高风险细分类目只允许保留在内部审计文档，不进入首页主文案：
  - 色粉、成人粉、仿牌、博彩、黑五类、规避审核、抗风控、绕过平台政策、保证过审、保证不限号
- 首页核心结构建议：
  - 顶部导航
  - Hero 区
  - 核心服务区
  - 平台方向
  - 市场方向
  - 适合项目类型
  - 服务流程
  - 服务边界
  - FAQ
  - 联系入口
- 首页 URL 规划方向：
  - `/services/`
  - `/services/overseas-promotion`
  - `/services/traffic-acquisition`
  - `/services/ad-campaign-support`
  - `/services/media-buying`
  - `/platforms/`
  - `/platforms/tk`
  - `/platforms/fb`
  - `/platforms/google`
  - `/markets/`
  - `/blog/`
  - `/contact`

## 4. 阶段 1 禁止事项

- 不批量删除 service 页面。
- 不批量 301。
- 不批量 noindex。
- 不批量 410。
- 不一上来 robots 屏蔽 /service_。
- 不生成 service_18001+。
- 不买外链。
- 不做灰色收录玩法。
- 不把高风险历史关键词写进首页主文案。

## 5. 阶段 1 输出物

- 新首页文件。
- 新导航结构。
- 新页脚结构。
- 首页文案。
- 首页内部链接清单。
- 阶段 1 自检结果。
