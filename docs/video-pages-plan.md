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

## 批量导入视频资产

外部视频生成流程完成后，使用导入脚本把视频文件接入 `/v/` 落地页系统：

```bash
python scripts/import_video_assets.py \
  --input-dir E:/ceshhi/output \
  --title-prefix "AI数字人视频生成服务" \
  --base-slug ai-video-service \
  --status published
```

输入目录可以包含：

```text
E:/ceshhi/output/
  1.MP4
  2.MP4
  3.MP4
```

脚本会扫描 `.mp4`、`.mov`、`.mkv`、`.webm` 视频文件，为每个新视频生成唯一 slug，例如：

```text
ai-video-service-001
ai-video-service-002
ai-video-service-003
```

导入后会写入：

```text
site_src/data/videos.json
site/public/videos/<slug>.mp4
site/public/thumbnails/<slug>.jpg
```

封面优先使用输入目录里的同名封面文件（`.jpg`、`.jpeg`、`.png`、`.webp`）；没有同名封面时，脚本会用 `ffmpeg` 从视频第 2 秒截取一帧，如果视频过短或截取失败，会退到第 0.5 秒。视频时长通过 `ffprobe` 获取，并写入 `duration_seconds`。

参数说明：

- `--input-dir`：必填，外部生成视频所在目录。
- `--title-prefix`：必填，标题前缀；脚本会生成 `<title-prefix> 001` 这类标题。
- `--base-slug`：必填，URL slug 前缀，只允许小写字母、数字和连字符。
- `--status`：默认 `published`。
- `--limit`：可选，只导入前 N 个尚未导入的视频。
- `--dry-run`：可选，只打印导入计划，不写文件。
- `--overwrite-assets`：可选，允许覆盖已存在的 mp4/jpg 资产。
- `--start-index`：可选，默认从现有 `videos.json` 中同前缀 slug 自动推断。

脚本会给每条新记录写入：

```json
"source_filename": "1.MP4"
```

这个字段用于避免同一个输入文件重复导入。再次运行脚本时，已经出现在 `source_filename` 里的文件会被跳过。

导入完成后运行：

```bash
python scripts/build_site.py
python scripts/check_static_site.py
```

不要手动修改 `site/public/v/` 下的生成页。`site/public/v/` 是构建产物，下一次运行 `scripts/build_site.py` 会重新生成；长期数据源只应维护 `site_src/data/videos.json` 和 `site/public/videos/`、`site/public/thumbnails/` 里的资产。
