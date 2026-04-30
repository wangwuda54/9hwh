# 旧 service 页面盘点字段规范

## 1. 文件目的

本文件定义旧 service 页面盘点、风险判断、分流决策、批次执行和回滚记录的字段规范。

`old-service-policy.md` 只定义治理原则，具体字段以本文件为准。

## 2. 表一：old-service-inventory

用于记录每个旧 service URL 的基础状态。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| url | 是 | 旧 service 页面完整 URL 或路径。 |
| path | 是 | URL 路径，例如 `/service_123`。 |
| service_id | 是 | service 编号，例如 `123`。 |
| status_code | 是 | 当前 HTTP 状态码。 |
| index_status | 否 | GSC 或搜索引擎索引状态。 |
| last_crawled | 否 | 最近抓取时间。 |
| title | 否 | 页面 title。 |
| h1 | 否 | 页面 H1。 |
| meta_description | 否 | 页面描述。 |
| canonical | 否 | 页面 canonical。 |
| word_count | 否 | 正文大致字数。 |
| template_group | 否 | 所属模板组。 |
| primary_topic | 否 | 初步主题，例如 Google Ads、TikTok Ads、Facebook BM。 |
| country | 否 | 国家或地区。 |
| platform | 否 | 平台。 |
| industry | 否 | 行业。 |
| source_file | 否 | 仓库内源文件路径。 |
| generated_by | 否 | 生成脚本或生成来源。 |
| notes | 否 | 备注。 |

## 3. 表二：old-service-metrics

用于记录页面价值数据。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| url | 是 | 对应旧 service URL。 |
| clicks_3m | 否 | 最近 3 个月自然搜索点击。 |
| impressions_3m | 否 | 最近 3 个月自然搜索展示。 |
| ctr_3m | 否 | 最近 3 个月 CTR。 |
| avg_position_3m | 否 | 最近 3 个月平均排名。 |
| clicks_12m | 否 | 最近 12 个月自然搜索点击。 |
| impressions_12m | 否 | 最近 12 个月自然搜索展示。 |
| external_links | 否 | 外链数量或重要外链说明。 |
| internal_links | 否 | 站内链接数量或来源说明。 |
| conversions | 否 | 有效咨询、表单、WhatsApp、邮件等转化记录。 |
| revenue_signal | 否 | 是否存在业务价值信号。 |
| data_source | 是 | GSC、日志、爬虫、人工检查等。 |
| data_date | 是 | 数据导出日期。 |

## 4. 表三：old-service-risk

用于记录风险和质量判断。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| url | 是 | 对应旧 service URL。 |
| risk_level | 是 | low / medium / high / banned。 |
| risky_terms | 否 | 命中的高风险词。 |
| risky_claims | 否 | 是否存在包过审、不封号、抗风控等承诺。 |
| policy_issue | 否 | 平台政策、法律合规或业务边界问题。 |
| duplicate_level | 否 | low / medium / high。 |
| content_quality | 是 | good / rewrite_needed / thin / duplicate / unsafe。 |
| user_intent_match | 否 | 页面是否满足搜索意图。 |
| can_rewrite | 是 | yes / no / unknown。 |
| can_merge | 是 | yes / no / unknown。 |
| risk_notes | 否 | 风险说明。 |

## 5. 表四：old-service-decision

用于记录分流决策。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| url | 是 | 对应旧 service URL。 |
| decision | 是 | keep / rewrite / merge / noindex / 301 / 410 / observe。 |
| target_url | 条件必填 | 301 或合并时的承接 URL。 |
| decision_reason | 是 | 决策原因。 |
| evidence | 是 | 数据或人工证据。 |
| approved_by | 否 | 审核人。 |
| approved_at | 否 | 审核时间。 |
| batch_id | 否 | 所属执行批次。 |
| rollback_plan_id | 否 | 对应回滚方案编号。 |
| status | 是 | proposed / approved / executed / rolled_back / paused。 |

## 6. 表五：old-service-batch-log

用于记录批量执行情况。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| batch_id | 是 | 批次编号。 |
| batch_type | 是 | noindex / 301 / 410 / rewrite / merge / mixed。 |
| url_count | 是 | URL 数量。 |
| execution_date | 是 | 执行日期。 |
| executor | 否 | 执行人或脚本。 |
| affected_files | 是 | 涉及文件，例如 `_redirects`、页面模板、headers 配置。 |
| pre_check_result | 是 | 执行前检查结果。 |
| post_check_result | 是 | 执行后检查结果。 |
| gsc_observation_start | 否 | GSC 观察开始日期。 |
| gsc_observation_end | 否 | GSC 观察结束日期。 |
| anomaly | 否 | 异常情况。 |
| next_action | 否 | 下一步动作。 |

## 7. 表六：old-service-rollback

用于记录回滚方案。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| rollback_plan_id | 是 | 回滚方案编号。 |
| batch_id | 是 | 对应批次编号。 |
| rollback_trigger | 是 | 触发回滚的条件。 |
| original_status | 是 | 执行前状态。 |
| original_files_backup | 条件必填 | 执行前文件备份位置或提交号。 |
| rollback_steps | 是 | 回滚步骤。 |
| validation_steps | 是 | 回滚后验证步骤。 |
| owner | 否 | 回滚负责人。 |
| rollback_status | 是 | ready / not_ready / executed / not_needed。 |

## 8. 决策枚举说明

### decision

- keep：暂时保留。
- rewrite：人工重写。
- merge：合并到相关新页面或专题页。
- noindex：允许抓取但退出索引。
- 301：跳转到高度相关承接页。
- 410：永久废弃。
- observe：暂缓观察。

### risk_level

- low：低风险。
- medium：中风险，需要编辑或限制发布范围。
- high：高风险，不进入主结构。
- banned：禁止公开使用或必须删除 / 隔离。

### content_quality

- good：可保留或轻量优化。
- rewrite_needed：需要人工重写。
- thin：内容薄弱。
- duplicate：重复或近似重复。
- unsafe：存在高风险表达或不适合公开。

## 9. 最低执行要求

阶段 5 后，如需批量处理旧 service 页面，至少必须具备：

- old-service-inventory。
- old-service-risk。
- old-service-decision。
- old-service-batch-log。
- old-service-rollback。

缺少 inventory、decision 或 rollback 任一项，不得批量执行 noindex、301、410 或删除。
