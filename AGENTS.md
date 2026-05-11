# AGENTS.md

本仓库只处理 9HWH 官网。

repo 必须是 `wangwuda54/9hwh`。  
本地目录必须是 `E:/9HWH`。

本文件是 AI / Agent / Codex 在本地执行任务前必须阅读的工作规则。若本文件与历史规则冲突，以用户当前明确指令和本文件为准。

---

## 0. 硬门禁

执行任何修改前必须确认：

```bash
git rev-parse --show-toplevel
git branch --show-current
git remote -v
git status --short
```

必须满足：

- `show-toplevel = E:/9HWH`
- remote 包含 `wangwuda54/9hwh.git`

如果 `show-toplevel` 是 `E:/py9`、`E:/py6`、`C:/py6`，必须立即停止。  
如果 remote 包含 `wangwuda54/py6.git` 或 `wangwuda54/51jyf.git`，必须立即停止。

不得根据 branch 名判断项目身份。项目身份只由 top-level、remote、当前任务名称 / 用户指定项目共同判断。

---

## 1. 本仓库范围

9HWH 只处理：

- 9hwh.com 官网
- 静态站
- SEO
- GSC
- Cloudflare
- 内容系统
- 旧 service 页面治理
- DeepSeek 正文生产分工

`project-status.md` 是当前阶段依据；涉及阶段、优先级、发布口径时，先读该文件。

---

## 2. 跨项目禁止

本仓库禁止：

- 修改 `E:/py9`
- 修改 `E:/py6`
- 修改 `C:/py6`
- 修改 `E:/51JYF`
- 运行 405 / 510 发布脚本
- 读取或复制 py6 config
- 读取或复制 py6 `.env`
- 把官网文件提交到 py6
- 把发布系统文件提交到 9HWH
- 读取、复制、提交其他项目密钥、token、API key

如果任务属于 py6 发布系统，必须停止并切到 py6 工作区，目标 remote 必须是 `wangwuda54/py6.git`。  
如果任务属于 51JYF，必须停止并切到 `E:/51JYF`，目标 remote 必须是 `wangwuda54/51jyf.git`。

---

## 3. 提交与运行边界

未经用户明确要求：

- 不 push
- 不部署
- 不运行 build
- 不运行 smoke
- 不改 Cloudflare 部署配置
- 不改 GitHub Actions
- 不改 sitemap / robots
- 不读取或复制 `.env`

规则文档任务只允许修改用户明确允许的规则文件，不得顺手修改 `site_src/`、`scripts/`、`data/`、`reports/`、`logs/`、`public/`、`site/`。
