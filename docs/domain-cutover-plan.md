# Domain Cutover Plan

## Current Strategy

- Keep the old site untouched for now.
- Treat the old source as read-only archive.
- Do not process old service pages in this stage.
- Validate Cloudflare preview first, then decide on formal domain cutover.

## Formal Domain Decision

- Immediate formal-domain binding: not recommended yet
- Reason: the rescue-v1 site has not been preview-verified in Cloudflare Pages in the current environment

## Old Site Handling

- Do not delete the old site now.
- Do not overwrite the old site without explicit authorization.
- Keep old URL and service-page migration for a later phase.

## 301 Strategy

- No broad 301 rollout in stage 17.
- Evaluate targeted redirects only after preview validation and old/new URL mapping are confirmed.

## Cutover Checklist

1. Cloudflare Pages preview deployment is reachable.
2. `verify_deployed_site.py` passes against the preview URL.
3. Rescue-v1 content scope is confirmed: 3 published URLs only.
4. `robots.txt` and `sitemap.xml` are correct online.
5. Stakeholder approval is given before changing formal DNS or production routing.

## Rollback Plan

1. Keep the old site serving until the new site is explicitly approved.
2. If the formal domain is switched and issues appear, point traffic back to the old site.
3. Re-run preview verification after fixes before another cutover attempt.
