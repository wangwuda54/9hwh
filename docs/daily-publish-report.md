# Daily Publish Report

- status: success
- run_date: 2026-05-17
- mode: normal
- daily_limit: 3
- hard_limit: 10
- dry_run: False
- selected_count: 3
- published_count: 3
- total_published: 26
- site_url: https://www.9hwh.com
- message: Published 3 reviewed item(s).

## Published Items

| content_id | Title | URL |
| --- | --- | --- |
| c019-ad-campaign-support-cost-cafc4fef | 理财费用：影响因素、预算准备和沟通要点 | https://www.9hwh.com/blog/cost-cafc4fef/ |
| c061-traffic-acquisition-leads-quality-test | 线索质量怎么测试：渠道判断、表单承接和跟进节奏 | https://www.9hwh.com/blog/leads-quality-test/ |
| c062-media-buying-small-budget-test | 小预算买量怎么测：素材、渠道和转化路径准备 | https://www.9hwh.com/blog/small-budget-media-buying-test/ |

## Post Publish Checks

| Command | Return code |
| --- | --- |
| `python scripts/build_site.py` | 0 |
| `python scripts/check_static_site.py` | 0 |
| `python scripts/check_sitemap_readiness.py` | 0 |
