# /v/ 视频页模块说明

## 用途

`/v/` 用于在 9HWH 主站下生成批量视频落地页，URL 形如：

```text
https://www.9hwh.com/v/<slug>/
```

这些页面用于 Google 搜索收录、视频案例展示、服务说明和客户联系承接。它不是独立站，也不依赖数据库、复杂 CMS、会员、评论或登录系统。

## videos.json 字段

视频数据放在：

```text
site_src/data/videos.json
```

每条数据字段：

- `id`：内部编号。
- `status`：只生成 `published`。`draft`、`noindex`、`rejected` 不生成可索引页面，也不进入 sitemap。
- `slug`：视频页 URL 标识，必须唯一。
- `title`：页面 title 和 VideoObject name，必填。
- `h1`：页面主标题，必填。
- `description`：meta description、页面说明和 VideoObject description，必填。
- `summary`：视频说明正文。
- `video_file`：视频文件路径，必须以 `/videos/` 开头。
- `thumbnail`：封面图路径，必须以 `/thumbnails/` 开头。
- `duration_seconds`：视频秒数，必须是正整数。
- `upload_date`：上传日期，格式 `YYYY-MM-DD`。
- `tags`：页面展示用标签。
- `contact_note`：联系承接说明，不写排名、审核、转化承诺。
- `related_links`：站内相关链接，只允许 `/` 开头的站内路径。

## 构建命令

```bash
python scripts/build_site.py
```

构建后会生成：

- `site/public/v/<slug>/index.html`
- `site/public/sitemap.xml`
- `site/public/video-sitemap.xml`
- `site/public/robots.txt`
- `docs/site-url-inventory.md`

## 检查命令

```bash
python scripts/check_static_site.py
```

检查内容包括视频页是否生成、是否进入普通 sitemap 和 video sitemap、页面是否有唯一 h1、canonical、meta description、`video` 标签和 `VideoObject`，以及视频数据里的 slug、路径和时长是否合法。

## video-sitemap.xml

`video-sitemap.xml` 只包含 `status == "published"` 的视频页，并输出 Google 视频 sitemap 需要的 `thumbnail_loc`、`title`、`description`、`content_loc`、`duration` 和 `publication_date`。

`robots.txt` 会同时声明：

```text
Sitemap: https://www.9hwh.com/sitemap.xml
Sitemap: https://www.9hwh.com/video-sitemap.xml
```

## 视频文件位置

后续真实视频和封面图同步到生成目录：

```text
site/public/videos/
site/public/thumbnails/
```

第一阶段允许先生成页面结构，检查脚本对缺失的 mp4 / jpg 只给 WARN，不会 FAIL。

## 添加新视频

不要直接长期手改 `site/public/v/`。

新增视频时修改 `site_src/data/videos.json`，确保 `slug` 唯一、状态为 `published`，再重新运行构建和检查命令。
