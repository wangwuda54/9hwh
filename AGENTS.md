# AGENTS.md - 9HWH 官网

本仓库只处理 9HWH 官网。

## 项目身份

- repo：`wangwuda54/9hwh`
- 本地目录：`E:/9HWH`
- 站点：`9hwh.com`

项目身份以当前仓库 remote 为准，不以 branch 名为准。

## 项目范围

- 静态站
- SEO
- GSC
- Cloudflare
- 内容系统
- 旧站治理

## 当前阶段

- 当前阶段、允许事项、禁止事项以 `project-status.md` 为准。
- 只有需要判断阶段边界时才读取 `project-status.md`。
- 简单任务不要做复杂全量检查。

## 禁止

- 不处理 py6。
- 不处理 405 / 510。
- 不处理 51JYF。
- 不运行发布系统脚本。
- 不读取或复制 py6 配置。
- 不读取或复制 py6 `.env`。
- 不把官网文件提交到 py6。
- 不把发布系统文件提交到 9HWH。
- 不 push，除非用户明确要求。
- 不部署，除非用户明确要求。

## 执行原则

- 只做用户明确要求的 9HWH 官网任务。
- 简单文档任务不运行 build。
- 代码或站点生成修改后，再按 `project-status.md` 运行必要检查。
- 不新增 `CODEX_START.md`。

## 长期内容治理

- 9hwh.com 要从链接池式站点治理为长期可信官网，优先降低风险，再追求增长。
- 主站结构应稳定、可审计、可回滚、可分批验证，不被阶段性关键词池污染。
- 关键词池只是阶段性输入，只能进入内容中心、专题页、FAQ 等可变内容层；进入公开页面前必须评估风险、意图、业务匹配和内容质量。
- 未审核关键词不得进入 sitemap；高风险关键词不得进入首页、导航和核心服务页。
- 主站表达保持克制可信，可使用“广告投放支持”“出海增长咨询”“账户协作流程”“合规材料准备”等中性表达。
- 不承诺审核结果、账号永久正常、规避系统、无限额度、包过审核、不封号等结果。
- 风险词只能用于风险说明、合规边界或不承接说明，不扩散到新内容、标题、描述、H1 或主 CTA。

## 旧 service 页面治理

- 旧 service 页面按阶段治理；冻结期只允许采集数据、打标签、建清单。
- 未完成盘点、分流、记录和回滚方案前，不批量重写、删除、重定向或屏蔽。
- 不得把旧 service 页面全部删除、全部 301 到首页，或用 `robots.txt` 屏蔽替代 `noindex`。
- 每个旧页面必须按规则分流：保留、重写、合并、`noindex`、`410`、`301`。
- 涉及 URL、索引、跳转、删除、旧 service 页面的修改，必须记录证据、原因、日期、影响范围和回滚路径，并分批执行。

## 优先参考文件

- `README.md`
- `project-status.md`
- `stage-gates.md`
- `project-rules.md`
- `keyword-policy.md`
- `site-positioning.md`
- `rebuild-roadmap.md`
- `old-service-policy.md`
- `inventory-schema.md`
- `indexing-policy.md`
- `content-policy.md`
- `change-log.md`
