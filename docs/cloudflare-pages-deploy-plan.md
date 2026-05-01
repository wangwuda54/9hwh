# Cloudflare Pages Deploy Plan

## Recommended Project Settings

- GitHub repo: `wangwuda54/9hwh`
- Branch: `rescue-v1`
- Root directory: repository root
- Build command: `python scripts/build_site.py`
- Output directory: `site/public`
- Environment variables: none

## Build Dependencies

- No DeepSeek API key is required.
- No `E:/py9` config is required.
- No Node.js build is required for the current static site.

## Static Assets For Pages

- `site/public/_headers`
- `site/public/_redirects`
- `site/public/robots.txt`
- `site/public/sitemap.xml`

## Deployment Guardrails

- Do not deploy from `main` during this phase.
- Do not deploy unpublished reviewed content.
- Do not attach any local-only config, `.env`, or external system path.
- Only deploy after manual approval.
