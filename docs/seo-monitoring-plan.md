# SEO Monitoring Plan

## Goal

本阶段只建立排名监控种子结构，为后续接入 Search Console 或人工监控做准备，不填假数据，不接入任何外部 API。

## Seed Fields

- `content_id`
- `target_url`
- `primary_keyword`
- `secondary_keywords`
- `cluster`
- `content_type`
- `published_date`
- `index_status`
- `impressions`
- `clicks`
- `avg_position`
- `conversions`
- `checked_at`
- `notes`

## Monitoring Rhythm

- `reviewed` 内容先作为待发布监控候选，`published_date` 保持为空。
- 真正发布后再补 `published_date` 和首轮 `index_status`。
- 首周重点看是否被抓取、是否进入索引、是否开始出现 `impressions`。
- 后续按周补充 `clicks`、`avg_position`、`conversions`。

## Guardrails

- 本阶段不接入 Search Console API。
- 本阶段不接入 Google Indexing API。
- 没有真实数据前，`impressions`、`clicks`、`avg_position`、`conversions` 保持空值。
- 监控结构只服务于人工判断发布节奏和优先级，不驱动自动发布。
