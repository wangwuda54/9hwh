# 当前官网源码审计

## 一、源码来源

- GitHub 仓库：https://github.com/wangwuda54/9hwh
- 本地恢复目录：`E:\9HWH-source`
- 新官网归档目录：`E:\9HWH\site\legacy-source`
- 是否已成功 clone：是
- 是否已归档到 legacy-source：是
- 是否触碰 `E:\py9` / `E:\py6` / `C:\py6`：否

## 二、源码结构

- 首页文件：
  - `E:\9HWH-source\index.html`
- 构建配置：
  - 未发现 `package.json`
  - 未发现 `vite.config.*`
  - 未发现 `astro.config.*`
  - 未发现 `next.config.*`
  - 未发现 `nuxt.config.*`
  - 未发现 `wrangler.toml`
- 静态资源目录：
  - 未发现独立 `public/`、`src/`、`assets/` 目录
  - 当前结构为根目录静态文件
- sitemap.xml：
  - `E:\9HWH-source\sitemap.xml`
- robots.txt：
  - `E:\9HWH-source\robots.txt`
- _headers：
  - 未发现
- _redirects：
  - 未发现
- service 页面样例：
  - `E:\9HWH-source\service_0.html`
  - `E:\9HWH-source\service_7904.html`
  - `E:\9HWH-source\service_17996.html`
  - 根目录共识别 `18000` 个 `service_*.html`
- service 生成脚本：
  - 未确认
  - 旧源码仓库内未发现 `.py`、`scripts/*.py`、`tools/*.py`
- 其他关键文件：
  - `E:\9HWH-source\robots.txt`
  - `E:\9HWH-source\sitemap.xml`

## 三、当前首页判断

- 首页文件是否存在：存在，路径为 `E:\9HWH-source\index.html`
- 首页是否像 service 链接池：是
- 首页是否包含大量 `/service_` 链接：是
  - 当前首页内直接写有 `100` 个 `service_*.html` 链接
- 首页是否具备正式品牌定位：否
  - 当前以 “Global Ad Agency 官方服务中心” 和资源承诺式文案为主
- 首页是否具备核心服务入口：否
- 首页是否具备地区入口：否
- 首页是否具备行业入口：否
- 首页是否具备联系入口：有
  - 但当前主要是 Telegram 客服跳转，不是正式官网联系结构

## 四、service 链接池来源判断

- 判断来源：写死在 HTML
- 判断依据：
  - `E:\9HWH-source\index.html` 第 38 行直接内嵌整段 `<li><a href="service_xxxx.html">...`
  - 使用正则统计，首页中共有 `100` 个 `href="service_*.html"` 链接
  - 当前未发现 JS 动态生成逻辑
  - 当前未发现 Python 生成脚本
  - `sitemap.xml` 另外包含 `18000` 个 `service_*.html` URL，但首页链接池本身不是从 sitemap 运行时注入的

## 五、Cloudflare Pages 相关判断

- 是否存在 package.json：否
- 是否存在构建命令线索：未确认
- 是否存在输出目录线索：未确认
- 是否存在 _headers：否
- 是否存在 _redirects：否
- 是否存在 sitemap.xml：是，路径为 `E:\9HWH-source\sitemap.xml`
- 是否存在 robots.txt：是，路径为 `E:\9HWH-source\robots.txt`

## 六、阶段 1 首页重做建议

- 阶段 1 应优先修改的文件：
  - `E:\9HWH\site\legacy-source\index.html`
  - 后续建议基于该文件备份后再迁入新工作区重做
- 阶段 1 应避免修改的文件：
  - `E:\9HWH\site\legacy-source\sitemap.xml`
  - `E:\9HWH\site\legacy-source\robots.txt`
  - 全部 `service_*.html`
- 是否建议先复制首页到新工作区再重做：是
- 是否建议保留旧首页备份：是
- 是否需要先建立预览分支：建议需要
- 是否能进入首页重做：能
  - 当前首页文件已确认
  - 旧源码已成功恢复并归档
  - 但 Cloudflare Pages 构建命令和输出目录仍未确认，进入编码前仍需补充这两项
