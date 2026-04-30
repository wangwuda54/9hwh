# Stage 8 Content Production System v1 Report

## 1. Stage Goal

Stage 8 builds the first maintainable content production and intake system for the 9HWH official website. The goal is not to publish new content immediately, but to make DeepSeek draft intake, Codex review, candidate planning, and public-site build gates auditable and safe.

## 2. Completed Changes

- Tightened the public build gate so content drafts are only rendered when the content queue status is `published`.
- Kept `draft_received` and `reviewed` out of public HTML, sitemap, and URL inventory.
- Added `internal_only` blocking for content tasks and candidate generation.
- Marked `c045-google-promotion-tk-immigration-ads-bcb960fd` as `internal_only` in the content queue while keeping the source record.
- Synced content queue c001 with the corrected batch-001 wording: `加密货币推广怎么做`.
- Rebuilt DeepSeek draft import as a stricter batch-aware importer.
- Rebuilt draft review as a content quality gate with pass / fail / warning output per article.
- Added candidate-only batch generation for batch-002.
- Generated batch-002 candidate files without creating a formal DeepSeek task package.

## 3. Content Status Flow

The final content flow is:

1. `planned` or `prompt_ready`: content opportunity exists, but no DeepSeek draft has been accepted.
2. `draft_received`: DeepSeek draft has been imported. Import scripts may only set this status.
3. `reviewed`: human/Codex review has accepted the draft quality. Review scripts report issues but do not auto-promote.
4. `published`: a separate manual confirmation action after review.

Rules:

- DeepSeek import must keep `status: draft_received`.
- Review does not auto-publish content.
- No script may automatically change content to `published`.
- `published` requires an explicit status update after `reviewed`.
- `build_site.py` renders content drafts only when queue status is `published`.
- `internal_only` content must not enter public pages, sitemap, URL inventory, formal DeepSeek tasks, or batch candidates.

## 4. DeepSeek Draft Intake Flow

1. Put returned Markdown files into `data/deepseek-inbox/`.
2. Run `python scripts/import_deepseek_drafts.py`.
3. The importer splits files by front matter and supports multiple articles per file.
4. Each article is checked against DeepSeek batch indexes or the content queue.
5. Locked fields must match the task package: `title`, `target_url`, `primary_keyword`, `secondary_keywords`.
6. Imported files are written to `site_src/content_drafts/` with `status: draft_received`.
7. Existing `reviewed` or `published` content is protected unless an explicit overwrite flag is used; `published` remains protected from import overwrite.
8. Import reports are written to `data/content-assets/import_report.json` and `docs/content-import-report.md`.

## 5. Review Rule Checklist

`scripts/review_content_drafts.py` now checks:

- Required front matter fields: `content_id`, `title`, `description`, `target_url`, `primary_keyword`, `secondary_keywords`, `status`.
- Legal draft statuses: `draft_received`, `reviewed`, `published`.
- Import-stage draft status remains `draft_received`.
- Empty, short, or long descriptions.
- Empty title.
- Empty or malformed `target_url`.
- Duplicate `content_id`.
- Duplicate `target_url`.
- Primary keyword presence in title, description, or opening body.
- Forbidden expressions such as `保证过审`, `保证不限号`, `保证效果`, `保证转化`, `保证收益`, `绕过平台政策`, `规避审核`, `抗风控`, `Cloak`, `仿牌`, `博彩`, `黑五类`, `三不限`, `违规业务也能做`, `任何平台都能过`, `任何行业都能投`.
- High-risk topics require service boundary wording.
- Fabricated office, team size, case, or contact claims.
- Body headings must not start with `#`.
- HTML body is not allowed.
- Empty or too-short body fails.
- Each article receives pass / fail / warning status in the report.

## 6. Batch-001 Current State

- `c045-google-promotion-tk-immigration-ads-bcb960fd` was removed from batch-001.
- `c001-ad-campaign-support-how-to-17e66750` was corrected to `加密货币推广怎么做`.
- batch-001 contains 10 tasks.
- batch-001 requires complete front matter output.
- batch-001 is still not published and not deployed.

## 7. Batch-002 Candidate State

- Candidate-only generation is available through `scripts/generate_deepseek_batch_candidates.py`.
- Current candidate files:
  - `data/deepseek-batches/batch-002/batch-002-candidates.md`
  - `data/deepseek-batches/batch-002/batch-002-candidates.json`
- Current candidate count: 15.
- The files are candidate-only and are not a formal DeepSeek task package.
- `internal_only` records and batch-001 used content IDs / target URLs are excluded.

## 8. Still Forbidden

- Do not push.
- Do not deploy to Cloudflare Pages.
- Do not process old service pages.
- Do not read, modify, or reference `E:/py9`, `E:/py6`, or `C:/py6`.
- Do not send batch-002 to DeepSeek from candidate files.
- Do not auto-promote reviewed content to published.
- Do not let `internal_only` content enter public pages, sitemap, or URL inventory.

## 9. Next Manual Actions

- Review the batch-002 candidate list and remove any topic that is strategically risky or mismatched.
- When DeepSeek returns batch-001 drafts, import them with `python scripts/import_deepseek_drafts.py`.
- Run `python scripts/review_content_drafts.py` and fix every fail before status promotion.
- Manually promote accepted drafts to `reviewed`.
- Only after final human confirmation, manually promote selected reviewed drafts to `published`.
- Re-run `python scripts/build_site.py` and `python scripts/check_static_site.py` before any later deployment decision.
