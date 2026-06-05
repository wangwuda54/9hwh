# 9HWH 发布后台说明

## 已新增的能力

- `/admin/`：发布后台页面。
- `/api/admin/*`：Cloudflare Pages Functions 后台接口。
- `data/published-posts.json`：发布内容数据源。
- `/blog/`：公开发布列表页。
- `/posts/<slug>.html`：每次发布时自动生成或更新的公开内容页。

## 使用前必须配置的 Cloudflare Pages 环境变量

在 Cloudflare Dashboard 中进入当前 Pages 项目：

`Settings` -> `Environment variables`

新增以下变量，Production 和 Preview 建议都配置：

| 变量名 | 必填 | 说明 |
| --- | --- | --- |
| `ADMIN_PASSWORD` | 是 | 登录 `/admin/` 的后台密码。 |
| `SESSION_SECRET` | 是 | 后台登录 Cookie 签名密钥，建议使用 32 位以上随机字符串。 |
| `GITHUB_TOKEN` | 是 | GitHub fine-grained token，需要对 `wangwuda54/9hwh` 有 Contents 读写权限。 |
| `GITHUB_REPO` | 否 | 默认 `wangwuda54/9hwh`。 |
| `GITHUB_BRANCH` | 否 | 默认 `main`。 |

## GitHub Token 权限建议

使用 Fine-grained personal access token：

- Repository access：只选择 `wangwuda54/9hwh`
- Permissions：
  - Contents：Read and write
  - Metadata：Read

不要把 token 写入仓库文件。只能放在 Cloudflare Pages 环境变量中。

## 发布流程

1. 打开 `/admin/`。
2. 输入 `ADMIN_PASSWORD` 登录。
3. 填写：
   - URL Slug
   - 标题
   - 摘要
   - 标签
   - 正文
4. 点击 `保存草稿`：只更新 `data/published-posts.json`。
5. 点击 `发布 / 更新发布`：
   - 更新 `data/published-posts.json`
   - 生成或覆盖 `/posts/<slug>.html`
   - 重新生成 `/blog/index.html`
   - 写入 GitHub commit
   - 由 Cloudflare Pages 的 Git 集成触发重新部署

## 注意事项

- 正文按纯文本处理，不执行 HTML，降低后台误填脚本的风险。
- 当前版本不做删除和撤回；个人团队场景下建议先保留发布记录，避免误删线上页面。
- 每次发布会产生一个 GitHub commit。
- 如果后台提示 `缺少 GITHUB_TOKEN`、`缺少 ADMIN_PASSWORD` 等错误，先检查 Cloudflare Pages 环境变量。
- 如果 GitHub API 返回 401/403，重点检查 token 是否过期、是否只授权到正确仓库、Contents 权限是否为 Read and write。
