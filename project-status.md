# 9hwh 官网拯救项目当前状态

## 1. 文件目的

本文件用于记录项目当前阶段、当前允许事项、当前禁止事项和进入下一阶段的条件。

AGENTS.md、project-rules.md、indexing-policy.md 不再写死临时阶段限制。当前阶段限制统一以本文件为准。

## 2. 当前阶段

- 当前阶段：阶段 3，官网静态生成系统重建。
- 当前目标：将手写静态页面升级为 Python 标准库驱动的静态站生成系统。
- 当前推进状态：已建立 `site_src/` 数据、模板和样式源文件；已建立 `scripts/build_site.py` 和 `scripts/check_static_site.py`；已自动生成 `site/public/`。
- 当前性质：继续推进官网工程化维护能力，当前未进入 Cloudflare Pages 部署阶段，当前未处理旧 service 页面。

## 3. 当前允许事项

当前允许：

- 维护 `site_src/data/` 数据文件。
- 维护 `site_src/templates/` 模板文件。
- 维护 `site_src/assets/css/styles.css`。
- 运行 `python scripts/build_site.py` 生成 `site/public/`。
- 运行 `python scripts/check_static_site.py` 检查生成结果。
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

## 5. 当前输出范围

当前阶段允许输出：

- `site_src/` 源文件。
- Python 标准库构建脚本。
- Python 标准库检查脚本。
- `site/public/` 生成结果。
- 构建与维护文档。
- 项目状态和变更记录。

当前阶段不输出：

- Cloudflare Pages 部署配置。
- `_headers` 和 `_redirects`。
- 旧 service 页面处理结果。
- 批量跳转规则。
- noindex / 301 / 410 批量执行配置。
- legacy-source 归档内容的 Git 提交。

## 6. 阶段 3 完成条件

阶段 3 完成需要满足：

- 已建立 Python 静态站生成器。
- 已建立 `site_src/data/` 数据文件。
- 已建立 `site_src/templates/` 模板文件。
- 已建立 `site_src/assets/css/styles.css`。
- 已可自动生成 `site/public/`。
- 已可自动生成 sitemap 和 robots。
- 检查脚本通过。
- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署阶段。

## 7. 当前阶段重点输入

当前阶段继续完善前，需要提供或确认：

- 正式联系方式。
- 是否继续扩充 services、platforms、topics 数据。
- 是否优化模板结构。
- 是否进入视觉强化。
- 后续博客正文生成与审核流程。

## 8. 状态更新规则

当项目进入新阶段时，必须先更新本文件：

- 更新当前阶段。
- 更新当前目标。
- 更新允许事项。
- 更新禁止事项。
- 更新完成条件。
- 必要时同步更新 `stage-gates.md`。

阶段状态变化属于重大变更，必须写入 `change-log.md`。
