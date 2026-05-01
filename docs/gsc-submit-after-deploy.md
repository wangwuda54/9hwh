# GSC Submit After Deploy

## Submission Rule

- Only submit the sitemap.
- Do not use Google Indexing API.
- Do not bulk-submit individual URLs.

## Preconditions

1. `https://your-domain/sitemap.xml` returns `200`
2. Sitemap is not empty
3. Sitemap contains only published URLs
4. `robots.txt` contains the sitemap declaration

## What To Record

- `submitted_at`
- `sitemap_url`
- `property`
- `status`
- `submitted_by`
- `notes`

## After Submission

- Watch `index_status`
- Watch `impressions`
- Watch `clicks`
- Watch `avg_position`
- Do not promise indexing or ranking
