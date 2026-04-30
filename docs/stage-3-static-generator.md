# 阶段 3：官网静态生成系统重建

## 1. 为什么从手写 HTML 转为 Python 静态生成

阶段 2B 已经建立了新官网页面、topics 关键词承接页和基础内链结构，但所有页面仍然是手写 HTML。继续手改 `site/public/*.html` 会导致导航、页脚、sitemap、服务边界和内链维护成本越来越高。

阶段 3 将站点升级为 Python 标准库驱动的静态生成系统：

- `site_src/` 保存数据、模板和样式源文件。
- `scripts/build_site.py` 负责生成站点。
- `site/public/` 作为生成结果。
- 后续维护优先修改 `site_src/`，不再长期直接手改 `site/public/`。

## 2. 新目录结构

- `site_src/data/`：站点数据。
- `site_src/templates/`：HTML 模板。
- `site_src/assets/css/`：CSS 源文件。
- `scripts/build_site.py`：静态站生成器。
- `scripts/check_static_site.py`：静态站检查脚本。
- `site/public/`：生成后的公开站点。

## 3. 数据文件说明

- `site.json`：站点名称、base URL、默认描述、联系方式占位、服务边界。
- `nav.json`：统一导航。
- `pages.json`：首页、总览页、市场页、内容中心、联系页、404 页面。
- `services.json`：4 个服务页。
- `platforms.json`：TK、FB、Google 平台页。
- `topics.json`：8 个关键词主题承接页。
- `markets.json`：市场列表和市场判断维度。

## 4. 模板说明

- `base.html`：全站基础模板，包含 HTML head、导航、main 插槽和页脚。
- `home.html`：首页模板。
- `page.html`：服务、平台、topics 详情页模板。
- `listing.html`：总览页模板。

模板只使用简单占位符，例如 `{{ title }}`、`{{ content }}`，不引入 Jinja2。

## 5. 构建命令

```powershell
cd E:\9HWH
python scripts/build_site.py
```

## 6. 检查命令

```powershell
cd E:\9HWH
python scripts/check_static_site.py
```

## 7. 输出目录

- 输出目录：`site/public/`
- CSS 输出：`site/public/assets/css/styles.css`
- sitemap 输出：`site/public/sitemap.xml`
- robots 输出：`site/public/robots.txt`

## 8. 后续如何新增页面

- 新增 service：优先修改 `site_src/data/services.json`。
- 新增 platform：优先修改 `site_src/data/platforms.json`。
- 新增 topic：优先修改 `site_src/data/topics.json`。
- 新增总览或独立页面：修改 `site_src/data/pages.json`，再调整 `scripts/build_site.py` 的生成逻辑。

## 9. 后续如何改导航

修改 `site_src/data/nav.json`，然后重新执行：

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

## 10. 后续如何改 sitemap

sitemap 由 `scripts/build_site.py` 自动生成。正式页面需要进入 sitemap 时，应进入生成器的页面生成列表，而不是手改 `site/public/sitemap.xml`。

## 11. 当前明确不做

- 不处理旧 service 页面。
- 不进入 Cloudflare Pages 部署阶段。
- 不新增 `_headers`。
- 不新增 `_redirects`。
- 不 push。
