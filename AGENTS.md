# AGENTS.md - 9HWH 官网

本仓库只处理 9HWH 官网项目。

repo：
- wangwuda54/9hwh

当前推荐本地目录：
- E:/sites/9hwh

站点：
- 9hwh.com

项目范围：
- 静态站
- SEO
- GSC
- Cloudflare
- 内容系统
- 旧站治理
- DeepSeek 内容生产与接入

## 发布方式

9HWH 是 Python 静态站。

源码目录：
- site_src

生成输出：
- site/public

本地生成：
- python scripts/build_site.py

本地检查：
- python scripts/check_static_site.py

Cloudflare Pages 发布目录：
- site/public

发布方式：
- 本地生成并验证 site/public
- commit / push 到 GitHub
- push 后由 Cloudflare Pages 自动发布

不要走 py6 发布系统。
不要本地执行服务器发布。
不要再使用 E:/9HWH 作为 9HWH 工作目录，除非用户明确说明该路径已重新修复。

## 当前状态来源

当前阶段、允许事项、禁止事项以 project-status.md 为准。

只有需要判断阶段边界时才读取 project-status.md。
简单任务不要做复杂全量检查。

## 项目身份判断

项目身份以 git remote 为准，不以 branch 名为准。

如果当前目录 remote 不是 wangwuda54/9hwh，不要处理 9HWH 官网任务。

## 执行口径

我是个人团队，时间和效率优先。
不要按大公司流程执行。
不要写长计划、长设计文档、长风险说明。
不要为了最小 diff 保留明显错误结构。
直接按最优方案修改本任务相关文件。
先跑通官网主链路，有 bug 继续修，细节以后再完善。

## 禁止事项

- 不处理 py6
- 不处理 405 / 510
- 不处理 51JYF
- 不运行发布系统脚本
- 不读取或复制 py6 配置
- 不读取或复制 py6 .env
- 不把官网文件提交到 py6
- 不把发布系统文件提交到 9HWH
- 不提交 .env、密钥、token、账号配置
- 不提交日志、缓存、临时文件、运行态文件

## 验证、提交和部署

简单文档或内容规则修改只看 diff / status。
代码、构建、站点生成相关修改需要运行必要验证。
验证失败就继续修 bug，直到通过，或明确说明真实阻塞原因。
验证通过后可以直接 commit、push。
如果 push 会触发 Cloudflare Pages 自动部署，push 后说明已触发。
如果项目有明确部署命令且本次任务属于部署任务，可以直接部署。
