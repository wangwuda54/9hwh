# 阶段 4：生成系统增强与内容数据升级

## 本次目标

阶段 4 的目标是把阶段 3 的“可生成页面”升级为“可长期维护的官网生成系统”。本次重点不进入 Cloudflare Pages 部署，不处理旧 service 页面，而是增强数据、模板、SEO、结构化数据和自动质检。

## 新增数据文件

- `site_src/data/contact.json`：集中管理联系页说明、联系方式占位、咨询准备清单和服务边界。
- `site_src/data/faqs.json`：集中管理 global、services、platforms、topics、markets、contact FAQ。
- `site_src/data/seo.json`：集中管理默认 SEO 字段、canonical base、noindex 路径和 sitemap 开关。
- `site_src/data/schema.json`：控制 Organization、WebSite、BreadcrumbList、FAQPage、Service JSON-LD 开关。
- `site_src/data/content_blocks.json`：集中管理服务边界、流程、适合项目、平台摘要、市场摘要和不承诺事项。

## 新增模板组件

- `site_src/templates/partials/footer.html`
- `site_src/templates/partials/breadcrumb.html`
- `site_src/templates/partials/cta.html`
- `site_src/templates/partials/faq.html`
- `site_src/templates/partials/boundary.html`
- `site_src/templates/partials/card_grid.html`
- `site_src/templates/partials/nav.html`

这些组件用于统一导航、页脚、面包屑、CTA、FAQ、服务边界、卡片网格和相关链接模块。

## 生成器升级点

- 读取全部 data JSON。
- 支持 partial 模板。
- 自动生成导航、页脚、面包屑和 canonical。
- 自动生成 FAQ HTML。
- 自动生成 Organization、WebSite、BreadcrumbList、FAQPage、Service JSON-LD。
- 自动生成带 `lastmod` 的 sitemap。
- 自动生成 robots.txt。
- 自动复制 CSS。
- 自动生成 `docs/site-url-inventory.md`。
- 自动检查重复 URL、canonical 一致性和 sitemap 收录状态。

## 检查脚本升级点

- 检查 sitemap URL 是否存在本地文件。
- 检查本地可索引 HTML 是否进入 sitemap。
- 检查 title、description、viewport、canonical、h1、导航、页脚和内部链接。
- 检查服务页和 topics 页是否包含服务边界。
- 检查联系页是否包含咨询准备清单。
- 检查 forbidden terms、`service_`、`legacy-source`。
- 检查 robots 是否包含 sitemap 且未屏蔽 service。

## JSON-LD 结构化数据

当前生成：

- Organization
- WebSite
- BreadcrumbList
- FAQPage
- Service

联系方式尚未提供，因此不编造电话、邮箱、地址或社交账号。

## URL inventory 自动生成

`docs/site-url-inventory.md` 由 `scripts/build_site.py` 自动生成，包含：

| URL | Source | Output File | Type | Sitemap | Indexable | Title | Description |

该文件只包含正式页面，不包含 404、legacy-source 或旧 service 页面。

## 当前仍未处理事项

- 未处理旧 service 页面。
- 未生成 `_headers`。
- 未生成 `_redirects`。
- 未进入 Cloudflare Pages 部署。
- 未 push。

## 下一步建议

- 补正式联系方式。
- 继续加深 topics 内容。
- 继续强化视觉和内容层级。
- 最后再进入 GitHub remote / Cloudflare Pages 部署准备。
