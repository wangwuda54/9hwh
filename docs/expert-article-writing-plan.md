# Expert Article Writing Plan

## Purpose

Stage 20 adds a deep expert article track without adding unreviewed or automatically published content. DeepSeek API remains responsible for article body generation. Codex is responsible only for task planning, importing output, running review checks, and adding approved articles to the publish queue.

## Cadence

- Frequency: 2 expert articles per week
- Days: Tuesday and Friday
- Publish gate: reviewed only, then queued, then published by the daily publish system
- This stage does not call DeepSeek API and does not generate article bodies

## Initial Topic Plan

| ID | Topic | Planned day | Status |
| --- | --- | --- | --- |
| expert-001 | TK, FB, Google 三类海外获客渠道怎么选 | Tuesday | task_planned |
| expert-002 | 海外推广项目启动前需要准备什么 | Friday | task_planned |
| expert-003 | 为什么海外投放不能承诺保证效果 | Tuesday | task_planned |
| expert-004 | 出海项目落地页和素材准备清单 | Friday | task_planned |
| expert-005 | 高风险行业推广前的合规和平台边界判断 | Tuesday | task_planned |
| expert-006 | 海外广告投放前如何判断项目适合哪个渠道 | Friday | task_planned |
| expert-007 | 交友、游戏、金融、贷款、保险等项目推广前的风险边界 | Tuesday | task_planned |

## Workflow

1. Create a DeepSeek task package for the selected topic.
2. Generate the article body through the DeepSeek API outside this stage.
3. Import the output into the content draft workflow.
4. Run draft review and pre-publish audit.
5. Add only pass-reviewed content to `publish_queue.json`.
6. Publish through `scripts/daily_publish.py` under the configured daily limits.

## Guardrails

- No direct `published` status is created by the expert planning step.
- No article bypasses `content_queue.json`.
- No draft with warnings, failures, `internal_only`, or `draft_received` status can be published.
- `c045` remains blocked from publication.
- The hard daily publish limit is 10 unless there is explicit manual confirmation.
