# 阶段 1：首页重做文件级计划

## 一、当前判断

- 旧源码已从 GitHub 恢复。
- 旧源码已归档到 `site/legacy-source`。
- 当前还未修改旧站首页。
- 当前还未修改旧站 sitemap / robots。
- 当前还未处理旧 service 页面。
- 阶段 1 已完成首页重做规划与首页草稿输出。

## 二、首页重做目标

- 首页从旧 service 链接池改成正式官网首页。
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

首页第一阶段优先链接这些正式入口：

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

- 首页不再链接 `service_` 链接池。
- URL 结构不继续锁定为开户、BM 或单国家广告账户服务表达。

## 五、阶段 1 文件级修改范围

- 应修改：
  - 首页草稿文件：`E:\9HWH\site\public\index.html`
  - 参考旧首页文件：`E:\9HWH\site\legacy-source\index.html`
  - 导航结构：首页草稿内建立
  - 页脚结构：首页草稿内建立
  - 首页样式：作为第一版新站基线逐步抽离

- 不应修改：
  - 旧站 `sitemap.xml`
  - 旧站 `robots.txt`
  - `_headers`
  - `_redirects`
  - `service_*.html`
  - service 生成脚本

## 六、阶段 1 风险

- 构建风险：当前未发现构建配置，可能是纯静态直出。
- Cloudflare Pages 输出目录风险：未确认。
- 首页路径风险：当前新首页位于 `site/public/index.html`。
- service 链接池移除风险：旧站首页原本承担大量内链入口。
- 旧定位残留风险：首页若继续保留“开户/BM”表达，会与当前业务方向冲突。
- 高风险词暴露风险：历史词池只能留在审计材料，不能进入首页主文案。

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

## 八、阶段推进记录

- 首页已从草稿推进为新站第一版首页。
- 后续以 `site/public/index.html` 为正式首页基线。
