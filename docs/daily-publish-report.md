# Daily Publish Report

- status: failure
- run_date: 2026-05-30
- mode: aggressive
- daily_limit: 7
- hard_limit: 10
- dry_run: False
- selected_count: 7
- published_count: 7
- total_published: 69
- site_url: https://www.9hwh.com
- message: Post publish check failed: python scripts/check_static_site.py

## Published Items

| content_id | Title | URL |
| --- | --- | --- |
| c091-multilingual-landing-pages-overseas | 多语言落地页怎么准备：地区话术、表单字段和咨询入口 | https://www.9hwh.com/blog/multilingual-landing-pages-overseas/ |
| c086-high-risk-project-creative-review | 高风险项目广告素材怎么审：卖点、承诺和页面一致性 | https://www.9hwh.com/blog/high-risk-project-creative-review/ |
| c079-overseas-loan-leads-preparation | 海外贷款获客投放前怎么评估：地区、表单和落地页准备 | https://www.9hwh.com/blog/overseas-loan-leads-preparation/ |
| c080-insurance-leads-overseas-ad-checklist | 海外保险获客广告怎么准备：受众、资质和咨询转化路径 | https://www.9hwh.com/blog/insurance-leads-overseas-ad-checklist/ |
| c081-immigration-leads-landing-page-review | 海外移民获客落地页怎么审：承诺边界、表单和咨询链路 | https://www.9hwh.com/blog/immigration-leads-landing-page-review/ |
| c084-finance-ads-landing-page | 金融广告落地页怎么改：承诺表达、表单和审核反馈处理 | https://www.9hwh.com/blog/finance-ads-landing-page/ |
| c085-crypto-ads-compliance-boundary | 虚拟币广告投放前怎么评估：地区限制、页面表达和风险边界 | https://www.9hwh.com/blog/crypto-ads-compliance-boundary/ |

## Errors

- post publish check failed: python scripts/check_static_site.py

## Post Publish Checks

| Command | Return code |
| --- | --- |
| `python scripts/build_site.py` | 0 |
| `python scripts/check_static_site.py` | 1 |
