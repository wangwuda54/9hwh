# SEO Monitoring Plan

## Goal

先建立排名监控种子结构，为后续接入 Search Console 或其他真实数据源做准备。

## Tracking Fields

- `content_id`
- `target_url`
- `primary_keyword`
- `secondary_keywords`
- `cluster`
- `published_date`
- `index_status`
- `impressions`
- `clicks`
- `avg_position`
- `conversions`
- `checked_at`
- `notes`

## Monitoring Rhythm

- 发布后先记录 `published_date` 和初始 `index_status`。
- 首周关注是否被抓取、是否进入索引、是否开始出现 impressions。
- 后续按周更新 impressions、clicks、avg_position 和 conversions。

## Suggested Workflow

- 发布前写入种子记录。
- 发布后用人工检查更新 `index_status`。
- 等后续阶段接入真实数据后，再自动回填曝光、点击和平均排名。

## Guardrails

- 没有 Search Console API 之前，不伪造任何真实排名数据。
- `avg_position` 在没有真实数据时保持 `null`。
- 监控数据只服务于判断内容节奏和优先级，不驱动自动发布。
