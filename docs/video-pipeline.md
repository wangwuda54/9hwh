# 9HWH video pipeline

`video_pipeline.py` is the new keyword-driven batch video workflow for the 9HWH `/v/` section and later Dailymotion / Rumble / Odysee publishing. It does not depend on the old `视频生成.py`.

## Input directory

Default local material root:

```text
E:/ceshhi/input/
├─ centers/
│  ├─ center1.mp4
│  └─ center2.mp4
├─ center.mp4
├─ sucai/
│  ├─ material1.mp4
│  └─ material2.mp4
├─ bgm/
│  └─ bgm1.mp3
└─ fonts/
   └─ optional Chinese fonts
```

The script prefers `input/centers/*.mp4`. If that folder is missing or empty, it falls back to `input/center.mp4`. `input/sucai/` must contain at least two usable videos. BGM is optional; when no BGM is found, the script writes a silent AAC track so the MP4 is not audio-less.

## Site and Platform Versions

`--target site` creates files for the 9HWH `/v/` pages:

```text
E:/ceshhi/output/site/videos/<slug>.mp4
E:/ceshhi/output/site/thumbnails/<slug>.jpg
```

`--target platform` creates files for external publishing:

```text
E:/ceshhi/output/platform/videos/<slug>-platform.mp4
E:/ceshhi/output/platform/thumbnails/<slug>.jpg
E:/ceshhi/output/platform/platform_publish.csv
```

`--target both` creates both sets. Only the site version uploads to the RN video server.

## Visual Rules

The video is a keyword support asset, not a 9HWH brand ad. The picture must focus on the keyword title, scene material, and one Telegram consultation entry. The script blocks visible text containing `9HWH`, `9hwh.com`, `查看完整页面`, `不承诺`, `不保证`, and similar forbidden phrases.

The video image does not show a URL. URLs are allowed in `platform_publish.csv` descriptions because those are publishing metadata, not video frames.

## Dry Run

Dry-run prints the processing plan and writes nothing:

```powershell
python video_pipeline.py run `
  --topics-json E:/sites/9hwh/site_src/data/video_topics.json `
  --videos-json E:/sites/9hwh/site_src/data/videos.json `
  --site-root E:/sites/9hwh `
  --input-dir E:/ceshhi/input `
  --output-dir E:/ceshhi/output `
  --asset-base-url https://video.9hwh.com `
  --server root@107.174.53.241 `
  --remote-root /var/www/video-assets `
  --target both `
  --limit 3 `
  --dry-run
```

## Only Missing

Use `--only-missing` to skip a slug when the local output video already exists:

```powershell
python video_pipeline.py run ... --target both --limit 40 --only-missing
```

Use `--overwrite` only when local output videos or remote RN files are intentionally being replaced.

## Generate Site Version

```powershell
python video_pipeline.py run `
  --topics-json E:/sites/9hwh/site_src/data/video_topics.json `
  --videos-json E:/sites/9hwh/site_src/data/videos.json `
  --site-root E:/sites/9hwh `
  --input-dir E:/ceshhi/input `
  --output-dir E:/ceshhi/output `
  --asset-base-url https://video.9hwh.com `
  --server root@107.174.53.241 `
  --remote-root /var/www/video-assets `
  --target site
```

## Generate Platform Version

```powershell
python video_pipeline.py run ... --target platform --skip-upload
```

This creates `platform_publish.csv` with title, description, tags, video path, thumbnail path, and `site_url`.

## Generate Both

```powershell
python video_pipeline.py run ... --target both
```

When upload is enabled, only the site MP4 and site JPG are uploaded.

## Upload RN

Site files upload through `scp`:

```text
/var/www/video-assets/videos/<slug>.mp4
/var/www/video-assets/thumbnails/<slug>.jpg
```

After upload, the script runs ownership and permission fixes:

```text
chown -R www-data:www-data /var/www/video-assets
chmod -R 755 /var/www/video-assets
```

It does not delete remote files. It does not overwrite remote files unless `--overwrite` is passed.

## Update videos.json

After a successful site upload, the script updates `site_src/data/videos.json` by `slug`:

```json
{
  "id": "auto-<slug>",
  "status": "published",
  "slug": "<slug>",
  "video_file": "https://video.9hwh.com/videos/<slug>.mp4",
  "thumbnail": "https://video.9hwh.com/thumbnails/<slug>.jpg",
  "duration_seconds": 45,
  "upload_date": "YYYY-MM-DD",
  "source_filename": "<slug>.mp4"
}
```

Existing `draft` or `rejected` records keep their status unless `--force-published` is passed. `video_topics.json` is never changed.

## Build and Check

Unless `--skip-build` is passed, the pipeline runs:

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

These commands only build and check the 9HWH static site.

## Commit and Push

The pipeline does not commit or push by default.

Pass `--commit` to stage and commit only the video landing page data/build outputs. Pass `--push` to run:

```powershell
git -c http.proxy= -c https.proxy= push origin main
```

Do not commit generated MP4/JPG assets.

## Common Errors

`missing dependency: ffmpeg` means FFmpeg is not on `PATH`.

`input/sucai must contain at least 2 usable video files` means the material folder is missing or empty.

`local output exists; use --overwrite or --only-missing` means the script protected an existing local MP4.

`remote file exists; use --overwrite to replace` means the RN server already has that file.

`forbidden visual term` means the title, tags, or Telegram text would put blocked wording into the video frame.

## External Publishing

For Dailymotion / Rumble / Odysee, use:

```text
E:/ceshhi/output/platform/platform_publish.csv
```

The CSV includes local video path, thumbnail path, platform title, description, tags, and the `/v/<slug>/` site URL for the platform description field. The site URL is not written into the video image.
