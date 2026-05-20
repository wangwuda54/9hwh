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

Dry-run prints the processing plan and writes nothing. It checks `topics-json` and `videos-json`, but it does not require FFmpeg, SCP, SSH, center videos, or `sucai` videos.

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

`--start-index` is 1-based. `--start-index 1 --limit 3` processes:

```text
ai-video-service-001
ai-video-service-002
ai-video-service-003
```

`--start-index 40` starts from the 40th item in `video_topics.json`.

## Only Missing

Use `--only-missing` to avoid regenerating a local video/thumbnail that already exists:

```powershell
python video_pipeline.py run ... --target both --limit 40 --only-missing
```

This does not drop the topic from later steps. Existing site videos can still be uploaded, reused remotely, and written to `videos.json` when the upload/reuse path calls for it. Existing platform videos are still written into `platform_publish.csv` with `status=existing`.

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

This creates `platform_publish.csv` with title, description, tags, video path, thumbnail path, `site_url`, and `status`. Platform-only runs skip build/check by default unless `--force-build` is passed.

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

Use `--reuse-remote` when the RN video and thumbnail already exist and should be reused:

```powershell
python video_pipeline.py run ... --target site --reuse-remote --only-missing
```

With `--reuse-remote`, if both remote files exist, the script skips SCP, marks `remote_reused=true`, updates `videos.json`, and can still run build/check. If only one remote file exists, the script stops that item with an incomplete remote resource error. If `--overwrite` is passed together with `--reuse-remote`, overwrite wins and the script uploads.

## Update videos.json

After a successful site upload or remote reuse, the script updates `site_src/data/videos.json` by `slug`:

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

`duration_seconds` is probed from the actual output MP4. If probing fails, the script falls back to `--duration` and writes a warning.

Existing `draft` or `rejected` records keep their status unless `--force-published` is passed. `video_topics.json` is never changed.

## Build and Check

For `--target site` and `--target both`, unless `--skip-build` is passed, the pipeline runs:

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

For `--target platform`, build/check is skipped by default. Pass `--force-build` if a platform-only run should also build and check the site.

## Commit and Push

The pipeline does not commit or push by default.

Pass `--commit` to stage and commit only the video landing page data/build outputs. Pass `--push` to run:

```powershell
git -c http.proxy= -c https.proxy= push origin main
```

Do not commit generated MP4/JPG assets.

The commit path runs `git status --short`, stages only explicit site data/build paths, refuses media/output files in the cached diff, and never uses `git add .`.

## Common Errors

`missing dependency: ffmpeg` means FFmpeg is not on `PATH`.

`input/sucai must contain at least 2 usable video files` means the material folder is missing or empty.

`local output exists; use --overwrite or --only-missing` means the script protected an existing local MP4.

`remote file exists; use --overwrite to replace` means the RN server already has that file.

`remote resources incomplete` means `--reuse-remote` found only the video or only the thumbnail on RN.

`forbidden visual term` means the title, tags, or Telegram text would put blocked wording into the video frame.

`topic validation failed` means `video_topics.json` has a missing required field, too few tags, or forbidden wording.

## External Publishing

For Dailymotion / Rumble / Odysee, use:

```text
E:/ceshhi/output/platform/platform_publish.csv
```

The CSV includes local video path, thumbnail path, platform title, description, tags, status, and the `/v/<slug>/` site URL for the platform description field. The site URL is not written into the video image.

Rows use:

```text
ok        newly generated platform video
existing  local platform video and thumbnail already existed
error     generation failed for this topic
```

## Recommended Test Flow

Run syntax check first:

```powershell
python -m py_compile video_pipeline.py
```

Preview the first three topics without media dependencies:

```powershell
python video_pipeline.py run ... --target both --limit 3 --dry-run
```

Verify existing platform assets still enter the CSV:

```powershell
python video_pipeline.py run ... --target platform --limit 3 --only-missing --skip-build
```

Verify site local reuse without upload:

```powershell
python video_pipeline.py run ... --target site --limit 1 --only-missing --skip-upload --skip-build
```

For real RN replacement, use `--overwrite`. For real RN reuse, use `--reuse-remote`.
