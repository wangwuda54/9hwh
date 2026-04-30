# batch-001 reviewed candidates

## 1. Batch summary

- 当前 batch-001 总篇数：10
- 成功生成篇数：10
- 成功导入篇数：10
- review pass 篇数：9
- review warning 篇数：1
- review fail 篇数：0

## 2. 可人工推进 reviewed 的 content_id 清单

- `c001-ad-campaign-support-how-to-17e66750`
- `c007-dating-traffic-dating-how-to-002063ad`
- `c010-media-buying-part-time-how-to-5875d40e`
- `c012-traffic-acquisition-dating-app-how-to-f56b0dad`
- `c031-fb-promotion-fb-dating-traffic-5035e1c0`
- `c043-game-promotion-fb-game-promotion-eec369fd`
- `c051-immigration-leads-fb-immigration-leads-b33be086`
- `c053-insurance-leads-fb-insurance-leads-b01d5372`
- `c055-loan-leads-fb-loan-leads-60d3dc0c`

## 3. 需要人工复核的 content_id 清单

- `c004-crypto-promotion-exchange-acquisition-how-to-efd74e87`
  - warning: less than 2 internal links

## 4. reviewed 候选说明

- reviewed 候选不等于正式 `reviewed` 状态。
- 本阶段没有自动执行 `update_content_status.py`。
- `data/deepseek-reviewed/` 只是导入后的归档副本目录，不代表内容已经进入 `reviewed`。
- 正式状态以 `site_src/data/content/content_status.json` 为准。

## 5. 不允许 published 的说明

- 本阶段只完成 DeepSeek 正文生成、导入和审核验证。
- 没有任何内容自动进入 `published`。
- 未经人工确认，不允许把 batch-001 候选直接推进到公开站。

## 6. 下一步人工确认命令建议

```powershell
python scripts/review_content_drafts.py
python scripts/update_content_status.py --content-id <content_id> --status reviewed
python scripts/build_site.py
python scripts/check_static_site.py
```
