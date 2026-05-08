# GSC Sitemap Submit After Deploy

## Current Stage Status

- Stage 20 status: formal site is live and `main` is the recommended production branch
- GSC submission status: sitemap submitted and read successfully
- Discovered pages: about 26
- Allowed submission scope: sitemap only
- Not allowed: GIA, Google Indexing API, or bulk single-URL submission

## Current Sitemap Target

- Formal launch target: `https://www.9hwh.com/sitemap.xml`
- Follow-up windows: 7 days, 14 days, and 30 days

## Operating Rules

1. Do not repeatedly submit the sitemap after each daily publish.
2. Do not use GIA.
3. Do not bulk-submit single URLs.
4. After daily publishing, rely on the updated sitemap and normal Google crawling.
5. Keep `data/seo/gsc_submission_log.json` as the source of record for sitemap submission and read status.

## What To Record For Future Changes

- `recorded_at`
- `sitemap_url`
- `property`
- `status`
- `discovered_pages_approx`
- `notes`
