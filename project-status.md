# 9hwh 官网拯救项目当前状态

## 1. 文件目的

本文件用于记录项目当前阶段、当前允许事项、当前禁止事项和进入下一阶段的条件。

AGENTS.md、project-rules.md、indexing-policy.md 不再写死临时阶段限制。当前阶段限制统一以本文件为准。

## 2. 当前阶段

- 当前阶段：阶段 5，关键词资产库与 URL 映射系统。
- 当前目标：建立关键词种子库、聚类规则、URL 映射和关键词资产生成脚本，让大量关键词先进入内部资产，再映射到少量高质量承接页。
- 当前推进状态：已建立 `site_src/data/keywords/`、`scripts/build_keyword_assets.py`、`data/keyword-assets/` 输出、关键词到 URL 映射文档和聚类统计文档。
- 当前性质：关键词不会直接等于公开页面；当前未进入 Cloudflare Pages 部署阶段，当前未处理旧 service 页面。

## 3. 当前允许事项

当前允许：

- 维护 `site_src/data/` 数据文件。
- 维护 `site_src/templates/` 模板文件。
- 维护 `site_src/assets/css/styles.css`。
- 运行 `python scripts/build_site.py` 生成 `site/public/`。
- 运行 `python scripts/check_static_site.py` 检查生成结果。
- 维护 `site_src/data/contact.json`、`faqs.json`、`seo.json`、`schema.json`、`content_blocks.json`。
- 维护 `site_src/data/keywords/` 关键词 seed、rules、clusters、url_map。
- 运行 `python scripts/build_keyword_assets.py` 生成内部关键词资产。
- 查看自动生成的 `docs/site-url-inventory.md`。
- 查看 `docs/keyword-to-url-map.md` 和 `docs/keyword-cluster-summary.md`。
- 更新构建和维护文档。

## 4. 当前禁止事项

当前禁止：

- 不进入 Cloudflare Pages 部署准备。
- 不新增 `_headers`。
- 不新增 `_redirects`。
- 不 push。
- 不修改 `site/legacy-source`。
- 不处理旧 service 页面。
- 不批量 301。
- 不批量 noindex。
- 不批量 410。
- 不创建 `docs/9hwh-rescue`。
- 不使用 Node / React / Next / Astro。
- 不写保证过审、保证不限号、保证效果、保证转化、保证收益等高风险承诺。
- 不把几万个关键词直接生成几万个公开页面。
- 不把敏感内部关键词放入首页、导航或 sitemap。

## 5. 当前输出范围

当前阶段允许输出：

- `site_src/` 源文件。
- Python 标准库构建脚本。
- Python 标准库检查脚本。
- `site/public/` 生成结果。
- `data/keyword-assets/` 内部关键词资产输出。
- 构建与维护文档。
- 项目状态和变更记录。

当前阶段不输出：

- Cloudflare Pages 部署配置。
- `_headers` 和 `_redirects`。
- 旧 service 页面处理结果。
- 批量跳转规则。
- noindex / 301 / 410 批量执行配置。
- legacy-source 归档内容的 Git 提交。
- 原始关键词列表公开页面。
- 大批低质量关键词页。

## 6. 阶段 5 完成条件

阶段 5 完成需要满足：

- 已建立关键词种子库。
- 已建立 public / internal / future blog / blocked 规则。
- 已建立关键词聚类定义。
- 已建立关键词到 URL 映射。
- 已生成关键词资产和统计。
- 已在页面中展示少量代表性关键词承接方向。
- 已升级检查脚本，检查关键词资产、cluster target、敏感词和 blocked promise。
- `python scripts/build_keyword_assets.py` 通过。
- `python scripts/build_site.py` 通过。
- `python scripts/check_static_site.py` 通过。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署阶段。

## 7. 当前阶段重点输入

当前阶段继续完善前，需要提供或确认：

- 正式联系方式。
- 是否继续扩充高质量 topics 页。
- 是否从 `future_blog` 队列挑选词交给 DeepSeek 写正文。
- 是否根据后续 GSC 反馈调整 URL 映射。
- 后续部署准备节奏。

## 8. 状态更新规则

当项目进入新阶段时，必须先更新本文件：

- 更新当前阶段。
- 更新当前目标。
- 更新允许事项。
- 更新禁止事项。
- 更新完成条件。
- 必要时同步更新 `stage-gates.md`。

阶段状态变化属于重大变更，必须写入 `change-log.md`。
