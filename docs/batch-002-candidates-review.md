# Batch-002 Candidates Review

## Scope

- 检查 `data/deepseek-batches/batch-002/` 下的候选池是否仍然适合作为下一批内容生产准备。
- 本阶段只保留 `candidate_only` 状态，不转正式任务包，不调用 DeepSeek API，不导入草稿。

## Validation Result

- `batch-002` candidates 当前数量为 `15`。
- 与 `batch-001` 正式任务包相比，没有重复 `content_id`。
- 与 `batch-001` 正式任务包相比，没有重复 `target_url`。
- 候选池中不包含 `c045`。
- 候选池保留了 `candidate_only: true`，没有越界进入正式生产流。

## Notes

- 现有候选混合了平台专题、长尾问句和高风险主题专题，结构上适合下一阶段继续做人审筛选。
- 高风险主题仍需要继续分散，不建议在下一批中让 `loan`、`insurance`、`immigration`、`crypto` 同时占据过高比例。
- 下一阶段若要转为正式任务包，应再次冻结 URL、标题、关键词和承接页映射。
