# Online Verification Checklist

## Before Running Verification

1. Confirm the deployed base URL.
2. Confirm the branch is `rescue-v1`.
3. Confirm the expected published count is still `3`.

## Run

```powershell
python scripts/verify_deployed_site.py --base-url https://your-preview-domain.pages.dev --expected-published 3
```

## Required Checks

- Homepage returns `200`
- `/services/` returns `200`
- `/topics/` returns `200`
- `/contact/` returns `200`
- `/robots.txt` returns `200`
- `/sitemap.xml` returns `200`
- `robots.txt` contains the sitemap URL
- Sitemap contains only the 3 published article URLs plus base public pages
- 7 reviewed unpublished URLs are not in the sitemap
- `c045` and other internal-only URLs are not in the sitemap
- Published pages contain a contact or consultation entry
- No obvious path error such as `/blog//topics/`

## Output

- `data/content-assets/deployed_site_verification_report.json`
- `docs/deployed-site-verification-report.md`
