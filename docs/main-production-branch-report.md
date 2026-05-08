# Main Production Branch Report

## Summary

Stage 20 promotes `main` to the long-term production branch for the 9HWH company site. The redesigned site work already lives on `rescue-v1`, and the formal site has replaced the old site, so production should now use the standard `main` branch instead of keeping `rescue-v1` as the live branch.

## Branch Decisions

- `main` now tracks the redesigned 9HWH website result from `rescue-v1`.
- `rescue-v1` is retained as the redesign phase backup and must not be deleted.
- `backup-main-before-9hwh-rescue` preserves the old `main` state before promotion.
- Cloudflare Pages should use `main` as the production branch going forward.
- `rescue-v1` should not remain the long-term production branch after this stage.

## Rollback

If the promoted `main` needs to be rolled back, use the remote backup branch:

```bash
git fetch origin
git checkout main
git reset --hard origin/backup-main-before-9hwh-rescue
git push origin main --force-with-lease
```

Use rollback only after confirming the production issue and preserving any new commits that need to be retained.

## Content Status

- Published content: 3 articles
- Reviewed but unpublished content: 7 articles
- Publication gate: only `reviewed` content with a pass review can move to `published`
- Blocked from publishing: `draft_received`, `internal_only`, review warning/fail items, and `c045`

## GSC And Sitemap

- Sitemap URL: `https://www.9hwh.com/sitemap.xml`
- GSC status: sitemap submitted and read successfully
- Discovered pages: about 26
- Follow-up window: observe 7, 14, and 30 day indexing behavior
- Do not use GIA
- Do not bulk-submit individual URLs
- Do not repeatedly resubmit the sitemap after each daily publish; rely on sitemap updates and normal crawling
