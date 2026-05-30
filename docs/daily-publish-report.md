# Daily Publish Report

- status: failure
- run_date: 2026-05-30
- mode: normal
- daily_limit: 3
- hard_limit: 10
- dry_run: False
- selected_count: 3
- published_count: 3
- total_published: 72
- site_url: https://www.9hwh.com
- message: Post publish check failed: python scripts/check_static_site.py

## Published Items

| content_id | Title | URL |
| --- | --- | --- |
| c097-ad-account-stability-checklist | 广告账户稳定性怎么评估：主体、页面、素材和投放节奏 | https://www.9hwh.com/blog/ad-account-stability-checklist/ |
| c098-creative-localization-overseas | 海外广告素材本地化怎么做：语言、利益点和页面一致性 | https://www.9hwh.com/blog/creative-localization-overseas/ |
| c105-form-leads-follow-up | 表单线索怎么跟进：字段筛选、响应时效和咨询质量 | https://www.9hwh.com/blog/form-leads-follow-up/ |

## Errors

- post publish check failed: python scripts/check_static_site.py

## Post Publish Checks

| Command | Return code |
| --- | --- |
| `python scripts/build_site.py` | 0 |
| `python scripts/check_static_site.py` | 1 |
