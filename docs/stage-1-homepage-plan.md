# 阶段 1：首页重做文件级计划

## 一、当前判断

- 旧源码已从 GitHub 恢复。
- 旧源码已归档到 `site/legacy-source`。
- 当前还未修改线上首页。
- 当前还未修改 sitemap / robots。
- 当前还未处理 service 页面。
- 阶段 1 可以进入首页重做规划与首页草稿产出。

## 二、首页重做目标

- 首页从 service 链接池改成正式官网首页。
- 首页建立“海外流量推广与获客支持”品牌定位。
- 首页建立核心服务入口。
- 首页建立平台服务入口。
- 首页建立国家 / 地区入口。
- 首页建立行业入口。
- 首页建立联系入口。
- 首页移除旧 service 链接池。
- 首页保留合理的可抓取 HTML 内容。
- 首页避免写成 Google Ads / TikTok Ads / Facebook Ads 开户服务商。
- 首页保留更宽、更稳、更可调整的表达，便于后期业务变化。

## 三、建议首页结构

建议结构：

1. 顶部导航
2. Hero 区
3. 核心服务区
4. 平台方向
5. 市场方向
6. 适合项目类型
7. 服务流程
8. 服务边界
9. FAQ
10. 联系入口
11. 页脚导航

## 四、建议 URL 入口

首页第一阶段只规划并优先链接这些正式入口：

- `/`
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

注意：

- 这些页面不一定本次全部创建。
- 首页可以先规划入口。
- 不要继续链接 `service_` 链接池。
- 不要把 URL 结构继续锁死为开户/BM/单国家广告账户服务。

## 五、阶段 1 文件级修改范围

- 应修改：
  - 首页草稿文件：`E:\9HWH\site\public\index.html`
  - 参考旧首页文件：`E:\9HWH\site\legacy-source\index.html`
  - 导航结构：先在首页草稿内建立
  - 页脚结构：先在首页草稿内建立
  - 首页样式：先以内联样式完成第一版草稿
  - 首页脚本文件：第一版不依赖额外脚本文件

- 不应修改：
  - `sitemap.xml`
  - `robots.txt`
  - `_headers`
  - `_redirects`
  - `service_*.html`
  - service 生成脚本

## 六、阶段 1 风险

- 构建风险：当前未发现构建配置，可能是纯静态直出，也可能存在仓库外部署步骤
- Cloudflare Pages 输出目录风险：未确认
- 首页路径风险：当前首页直接位于根目录 `index.html`
- service 链接池移除风险：旧首页当前包含 `100` 个 `service_` 链接，移除后内链结构会显著变化
- 旧页面内链骤降风险：首页不再导流旧 `service_` 后，旧页会失去一部分站内入口
- 新页面未建立导致入口 404 的风险：首页若先挂正式入口但目标页未建，会产生新 404
- 业务定位漂移风险：如果首页继续使用“开户/BM/单国家广告服务”表达，会与当前流量推广定位冲突
- 风险词暴露风险：虚拟币、贷款、成人、网赚等历史关键词只能留在审计文档，不能进入首页主文案

## 七、阶段 1 执行顺序

建议：

1. 备份旧首页
2. 在 `site/public/index.html` 建立首页草稿
3. 用“海外流量推广与获客支持”重写首页结构
4. 移除 service 链接池
5. 增加正式服务、平台、市场和联系入口
6. 写清服务边界
7. 本地预览
8. 检查链接
9. 再决定是否进入 sitemap / robots 阶段
