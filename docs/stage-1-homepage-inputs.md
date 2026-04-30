# 阶段 1：首页重做输入清单

## 1. 阶段 1 目标

- 首页从旧 service 链接池改成正式官网首页。
- 明确 9hwh 的服务定位。
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
- 首页核心结构建议：
  - Hero 区
  - 核心服务区
  - 平台服务区
  - 国家 / 地区入口
  - 行业入口
  - 服务流程
  - 合规边界
  - FAQ
  - 联系入口

## 4. 阶段 1 禁止事项

- 不批量删除 service 页面。
- 不批量 301。
- 不批量 noindex。
- 不批量 410。
- 不一上来 robots 屏蔽 /service_。
- 不生成 service_18001+。
- 不买外链。
- 不做灰色收录玩法。

## 5. 阶段 1 输出物

- 新首页文件。
- 新导航结构。
- 新页脚结构。
- 首页文案。
- 首页内部链接清单。
- 阶段 1 自检结果。
