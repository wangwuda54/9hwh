# Rank Tracking Weekly Routine

## Current State

- Formal domain launch: not completed
- Real deploy URL for tracking: not available in this environment
- Observation status: pending

## Observation Cadence

1. Day 7: check sitemap discovery and initial indexation signals
2. Day 14: check first impressions and early query footprint
3. Day 30: review trend direction and page-level exposure
4. Day 60: review stabilization and identify pages needing optimization

## Scope Rules

- Track only real deployed URLs.
- Focus on the 3 published pages first.
- Do not record made-up metrics.
- Keep the log empty or pending until there is a real host to observe.

## Weekly Workflow

1. Confirm whether the site is live on a preview or formal domain.
2. Check GSC coverage and performance if access exists.
3. Update `data/seo/rank_tracking_observations.json`.
4. Note only observed facts: index status, impressions, clicks, average position, and noteworthy queries.

## Decision Guide

- Not indexed: verify sitemap availability, robots, and internal discovery first.
- Indexed with no impressions: wait through the early window and improve discovery before rewriting.
- Impressions with no clicks: review titles, descriptions, and SERP intent fit later.
- Clicks with no inquiries: inspect CTA visibility and page-intent alignment.
