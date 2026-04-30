# Stage 9 DeepSeek API Generation Report

## 1. Stage Goal

Stage 9 adds a direct DeepSeek API draft generation loop inside `E:/9HWH`, so batch writing can move from task packages to API-driven draft output without leaving the official website repository.

## 2. DeepSeek API Config Source

The script reads DeepSeek config from `E:/py9` in read-only mode and currently supports the existing Python config structure in `E:/py9/config.py`.

Recognized fields:

- `AI_PROVIDER`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`
- `DEEPSEEK_THINKING_ENABLED`

## 3. Secret Handling

- The API key is never written into `E:/9HWH`.
- The API key is never written into reports or logs.
- Reports only record the config source path and recognized field names.
- The script uses the key only in-memory for the outbound API request.

## 4. Script Usage

```powershell
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --dry-run
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --limit 1
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --resume
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --only c001-ad-campaign-support-how-to-17e66750
python scripts/generate_deepseek_drafts_api.py --batch batch-001 --run-import-review
```

## 5. Resume Rules

- Existing per-article inbox files are preserved by default.
- `--overwrite` allows replacing existing per-article outputs.
- `--resume` keeps existing files and continues missing items in the same batch directory.

## 6. Output Paths

- `data/deepseek-inbox/<batch-id>/`
- `data/deepseek-inbox/<batch-id>/<content_id>.md`
- `data/deepseek-inbox/<batch-id>/failed/<content_id>.md`
- `data/deepseek-inbox/<batch-id>-deepseek-output.md`
- `data/content-assets/deepseek_api_generation_report.json`
- `docs/deepseek-api-generation-report.md`

## 7. Import And Review Flow

After generation succeeds, the next manual steps are:

```powershell
python scripts/import_deepseek_drafts.py
python scripts/review_content_drafts.py
```

`--run-import-review` is available for convenience, but default behavior does not auto-run import or review.

## 8. Hard Boundaries

- The script must not auto-publish content.
- The script must not push.
- The script must not deploy.
- The script must not process old service pages.
- Validation failures stay out of the normal inbox import flow.

## 9. Next Manual Checks

- Inspect any files under `failed/`.
- Run import and review for accepted inbox outputs.
- Manually decide whether a reviewed draft should stay reviewed or later move to published.

