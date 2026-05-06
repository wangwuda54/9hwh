# Deployed Site Verification Report

- base_url:
- expected_published: 3
- status: pending

## Current Blocker

- No Cloudflare Pages preview URL is available in the current environment.
- `python scripts/verify_deployed_site.py --base-url <preview-url> --expected-published 3` has not been executed yet.

## Pending Checks

- homepage `200`
- `/services/` `200`
- `/topics/` `200`
- `/contact/` `200`
- `/robots.txt` `200`
- `/sitemap.xml` `200`
- `robots.txt` contains `Sitemap:`
- sitemap contains only the 3 published article URLs plus public site pages
- 7 reviewed unpublished URLs are absent from sitemap
- `c045` and other `internal_only` URLs are absent from sitemap

## Next Step

- Obtain the Cloudflare Pages preview URL and run the verification script.
