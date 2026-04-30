# 构建与维护说明

## 1. 常用命令

```powershell
cd E:\9HWH
python scripts/build_site.py
python scripts/check_static_site.py
```

## 2. 如何构建

构建命令：

```powershell
python scripts/build_site.py
```

构建器会读取 `site_src/data/` 和 `site_src/templates/`，然后生成 `site/public/`。

## 3. 如何检查

检查命令：

```powershell
python scripts/check_static_site.py
```

检查内容包括：

- 关键页面是否存在。
- HTML 是否包含 title、description、viewport、canonical。
- 每页是否只有一个 h1。
- 是否出现 `service_`。
- 是否出现禁止高风险承诺。
- sitemap 是否包含旧页面或归档路径。
- robots 是否保持允许抓取并指向 sitemap。

## 4. 如何本地预览

```powershell
cd E:\9HWH\site\public
python -m http.server 8080
```

浏览器访问：

```text
http://127.0.0.1:8080/
```

## 5. 如何新增 service

修改：

```text
site_src/data/services.json
```

新增服务后运行：

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

## 6. 如何新增 topic

修改：

```text
site_src/data/topics.json
```

新增 topic 时必须保持克制表达，不写高风险承诺，不创建成人 / 色粉专题页。

## 7. 如何改 contact

优先修改：

```text
site_src/data/contact.json
```

联系方式占位、咨询准备清单、响应说明和联系页服务边界都在 `contact.json` 中。不要编造邮箱、电话、微信或 Telegram。

## 8. 如何修改 FAQ

优先修改：

```text
site_src/data/faqs.json
```

FAQ 分为 `global`、`services`、`platforms`、`topics`、`markets`、`contact`。新增 FAQ 时不要写高风险承诺，不要写“保证过审、保证效果、保证收益”等表达。

## 9. 如何修改服务边界

优先修改：

```text
site_src/data/content_blocks.json
site_src/data/site.json
site_src/data/contact.json
```

服务边界必须保持克制、清楚，强调平台政策、地区法规、行业限制和项目表达边界。

## 10. 如何查看 URL inventory

构建后查看：

```text
docs/site-url-inventory.md
```

该文件由 `scripts/build_site.py` 自动生成，不建议手工长期维护。

## 11. 如何处理构建失败

先运行：

```powershell
python scripts/build_site.py
python scripts/check_static_site.py
```

如果构建失败，优先检查 JSON 格式、URL 重复、模板占位符和必填字段。如果检查失败，优先看 `[FAIL]` 行，修复 canonical、站内链接、sitemap、robots 或高风险词问题。

## 12. 如何避免直接手改 site/public

`site/public/` 是生成结果。长期维护时应优先修改：

- `site_src/data/`
- `site_src/templates/`
- `site_src/assets/css/styles.css`
- `scripts/build_site.py`

然后重新构建。

## 13. 什么时候才进入 Cloudflare Pages

只有当站内内容结构、联系方式、视觉基线、sitemap 和旧 service 页面盘点策略都稳定后，才进入 Cloudflare Pages 部署准备。

当前阶段不做：

- `_headers`
- `_redirects`
- Cloudflare Pages 配置
- push
- 旧 service 页面处理

## 14. 如何更新关键词 seed

修改：

```text
site_src/data/keywords/seed.json
```

`seed.json` 只保存关键词维度，包括国家、平台、类目、动作词和长尾后缀。不要把几万个原始词直接写进公开页面。

## 15. 如何更新 cluster

修改：

```text
site_src/data/keywords/clusters.json
```

每个 cluster 必须有 `cluster_id`、`target_url`、`intent`、`public_page` 和 `sitemap`。搜索意图相近的一组关键词应映射到一个高质量承接页。

## 16. 如何重新生成 keyword assets

执行：

```powershell
python scripts/build_keyword_assets.py
python scripts/build_site.py
python scripts/check_static_site.py
```

生成结果位于：

```text
data/keyword-assets/
docs/keyword-to-url-map.md
docs/keyword-cluster-summary.md
```

## 17. 如何检查关键词映射

优先查看：

```text
docs/keyword-to-url-map.md
docs/keyword-cluster-summary.md
data/keyword-assets/keyword_summary.json
```

如果检查脚本报 cluster target 缺失，说明某个 cluster 映射到了不存在的页面。

## 18. 为什么不要直接新增几万个页面

关键词库是资产，不是页面清单。几万个关键词直接生成公开页面会造成重复、低质量、维护失控和索引风险。当前规则是先聚类、再映射 URL、再用高质量页面承接。

## 19. 如何决定关键词是否进入公开页面

判断顺序：

- 是否属于 `blocked`：如果是，不公开。
- 是否属于 `internal_only`：如果是，只保留内部资产。
- 是否属于 `future_blog`：如果是，后续按内容质量和 GSC 反馈规划文章。
- 是否已有对应承接页：如果有，映射到现有 URL。
- 是否需要新页面：只有搜索意图明显独立、低风险、可写出高质量内容时才新增。

## 20. 如何生成内容任务队列

执行：

```powershell
python scripts/build_content_queue.py
```

内容任务来自 keyword assets，但任务不等于公开页面。默认每批最多生成有限数量任务，避免批量低质页面。

## 21. 如何生成 DeepSeek 任务包

执行：

```powershell
python scripts/generate_deepseek_tasks.py
```

任务包输出到：

```text
data/deepseek-tasks/
```

正文由 DeepSeek 生成，Codex 不直接批量写文章正文。

## 22. 如何接入 DeepSeek 正文

将 DeepSeek 产出的 Markdown 放入：

```text
site_src/content_drafts/{content_id}.md
```

格式说明见：

```text
site_src/content_drafts/README.md
```

## 23. 如何判断内容是否进入 sitemap

只有同时满足以下条件才进入 sitemap：

- `content_queue.json` 中状态为 `ready_to_publish` 或 `published`。
- `site_src/content_drafts/{content_id}.md` 存在。
- 构建和检查通过。

`planned`、`prompt_ready`、`writing`、`draft_received`、`reviewed`、`paused` 都不能进入 sitemap。

## 24. 如何避免批量低质页面

- 不把关键词池直接转成页面。
- 不把 content_queue 直接转成公开页面。
- 每批先生成任务包，再人工或模型写正文，再审核。
- 没有正文、没有审核、没有服务边界的内容不能发布。
