# 阶段 1：首页重做文件级计划

## 一、当前判断

- 旧源码已从 GitHub 恢复。
- 旧源码已归档到 `site/legacy-source`。
- 当前还未修改线上首页。
- 当前还未修改 sitemap / robots。
- 当前还未处理 service 页面。
- 阶段 1 可以进入首页重做规划。

## 二、首页重做目标

- 首页从 service 链接池改成正式官网首页。
- 首页建立品牌定位。
- 首页建立核心服务入口。
- 首页建立平台服务入口。
- 首页建立国家 / 地区入口。
- 首页建立行业入口。
- 首页建立联系入口。
- 首页移除旧 service 链接池。
- 首页保留合理的可抓取 HTML 内容。

## 三、建议首页结构

建议结构：

1. Hero 区
2. 核心服务区
3. 平台服务区
4. 国家 / 地区入口
5. 行业入口
6. 服务流程
7. 合规边界
8. 常见问题
9. 联系入口
10. 页脚导航

## 四、建议 URL 入口

首页第一阶段只链接这些正式入口：

- `/`
- `/google-ads-agency`
- `/google-ads-account`
- `/tiktok-ads-agency`
- `/tiktok-ads-account`
- `/facebook-ads-agency`
- `/facebook-business-manager`
- `/locations/`
- `/industries/`
- `/blog/`
- `/contact`

注意：

- 这些页面不一定本次全部创建。
- 首页可以先规划入口。
- 不要继续链接 `service_` 链接池。

## 五、阶段 1 文件级修改范围

- 应修改：
  - 旧首页文件：`E:\9HWH\site\legacy-source\index.html`
  - 导航文件：未发现独立导航文件，当前导航结构需在首页文件内重建
  - 页脚文件：未发现独立页脚文件，当前页脚位于 `E:\9HWH\site\legacy-source\index.html`
  - 首页样式文件：未发现独立样式文件，当前样式位于 `E:\9HWH\site\legacy-source\index.html`
  - 首页脚本文件：未发现独立首页脚本文件

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

## 七、阶段 1 执行顺序

建议：

1. 备份旧首页
2. 复制首页到新工作区
3. 重写首页结构
4. 保留基础样式
5. 移除 service 链接池
6. 增加正式服务入口
7. 本地预览
8. 检查链接
9. 再决定是否进入 sitemap / robots 阶段
