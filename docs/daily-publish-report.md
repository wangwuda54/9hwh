# Daily Publish Report

- status: success
- run_date: 2026-05-18
- mode: normal
- daily_limit: 3
- hard_limit: 10
- dry_run: False
- selected_count: 3
- published_count: 3
- total_published: 29
- site_url: https://www.9hwh.com
- message: Published 3 reviewed item(s).

## Published Items

| content_id | Title | URL |
| --- | --- | --- |
| c064-ad-campaign-support-material-test | 广告素材怎么测试：角度、预算和反馈复盘方法 | https://www.9hwh.com/blog/ad-material-test/ |
| c075-youtube-promotion-leads | YouTube推广获客怎么做：内容渠道、落地页和再营销准备 | https://www.9hwh.com/blog/youtube-promotion-leads/ |
| c006-crypto-promotion-crypto-promotion-how-to-1b5b5379 | 虚拟币推广怎么做：推广路径、渠道判断和准备清单 | https://www.9hwh.com/blog/crypto-promotion-how-to-1b5b5379/ |

## Post Publish Checks

| Command | Return code |
| --- | --- |
| `python scripts/build_site.py` | 0 |
| `python scripts/check_static_site.py` | 0 |
| `python scripts/check_sitemap_readiness.py` | 0 |
