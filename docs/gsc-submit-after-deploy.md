# GSC Sitemap Submit After Deploy

## Current Stage Status

- Stage 17 status: pending real deployment URL
- GSC submission status: pending
- Allowed submission scope: sitemap only
- Not allowed: GIA, Google Indexing API, bulk single-URL submission

## Preconditions

1. Cloudflare Pages preview or live URL is reachable.
2. `/sitemap.xml` returns `200`.
3. `/robots.txt` returns `200` and contains the sitemap declaration.
4. The sitemap still contains only the 3 published article URLs plus public site pages.
5. The site being submitted is the rescue-v1 deployment, not the old site.

## Manual Submission Steps

1. Open Google Search Console for the correct property.
2. Confirm the property matches the final deploy target.
3. Submit only the sitemap URL.
4. Record the result in `data/seo/gsc_submission_log.json`.

## Preferred Sitemap Targets

- Preview validation only: do not submit yet unless the preview host is also the chosen GSC property.
- Formal launch target: `https://www.9hwh.com/sitemap.xml`

## What To Record

- `submitted_at`
- `sitemap_url`
- `property`
- `status`
- `submitted_by`
- `notes`

## Pending Decision

- If there is only a Cloudflare preview URL, keep the GSC log at `pending`.
- Submit only after the user confirms the correct property and the sitemap is live on the intended host.
