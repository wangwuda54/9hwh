# Daily Publish Report

- status: failure
- run_date: 2026-05-28
- mode: normal
- daily_limit: 7
- hard_limit: 10
- dry_run: False
- selected_count: 0
- published_count: 0
- total_published: 0
- site_url: https://www.9hwh.com
- message: Post publish check failed: python scripts/check_static_site.py

## Published Items

| content_id | Title | URL |
| --- | --- | --- |

## Errors

- post publish check failed: python scripts/check_static_site.py

## Post Publish Checks

| Command | Return code |
| --- | --- |
| `python scripts/build_site.py` | 0 |
| `python scripts/check_static_site.py` | 1 |
