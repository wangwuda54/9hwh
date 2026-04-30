# 阶段 5：关键词资产库与 URL 映射系统

## 为什么不能几万个关键词直接生成几万个页面

9HWH 官网需要承接大量海外推广、引流获客、投放买量相关关键词，但关键词数量不等于公开页面数量。几万个关键词直接生成几万个公开页面，会带来低质量页面、重复页面、索引失控、维护困难和品牌表达风险。

正确路径是：

- 关键词先进入内部资产库。
- 关键词按平台、类目、动作、国家、搜索意图分组。
- 搜索意图相近的一组关键词映射到一个高质量承接页。
- sitemap 只收录正式承接页。
- 后续根据 GSC 反馈再判断是否扩展新页面。

## 当前关键词来源

当前阶段不读取、不修改、不提交 `E:\py9`、`E:\py6`、`C:\py6` 的发布系统文件。关键词口径基于已确认的业务维度，在 `E:\9HWH` 内独立建立数据文件：

- `site_src/data/keywords/seed.json`
- `site_src/data/keywords/rules.json`
- `site_src/data/keywords/clusters.json`
- `site_src/data/keywords/url_map.json`

## 关键词维度

- 国家 / 市场：美国、英国、加拿大、澳大利亚、欧洲、日本、韩国、台湾、新加坡、马来西亚、泰国、越南、印度、俄罗斯、巴西、中东。
- 平台：TK、FB、谷歌。
- 类目：虚拟币、币圈引流、交易所拉新、交友引流、游戏、贷款、保险、移民、网赚、兼职等。
- 动作词：推广、引流、获客、拉新、投放、广告代投、投流、买量、代运营等。
- 长尾后缀：怎么做、怎么投、多少钱、费用、渠道、平台、哪家好、靠谱吗等。

## 聚类规则

关键词先按搜索意图进入 cluster：

- `overseas-promotion`
- `traffic-acquisition`
- `ad-campaign-support`
- `media-buying`
- `tk-promotion`
- `fb-promotion`
- `google-promotion`
- `crypto-promotion`
- `dating-traffic`
- `game-promotion`
- `finance-leads`
- `loan-leads`
- `insurance-leads`
- `immigration-leads`
- `online-work-leads`
- `markets`

每个 cluster 只对应一个正式承接 URL，避免重复页面互相竞争。

## URL 映射规则

主要映射由 `site_src/data/keywords/url_map.json` 管理。例如：

- 海外推广、海外流量推广、出海项目推广：映射到首页。
- 引流获客：映射到 `/services/traffic-acquisition/`。
- 广告投放、广告代投：映射到 `/services/ad-campaign-support/`。
- 投流、买量：映射到 `/services/media-buying/`。
- TK 推广、FB 推广、谷歌推广：映射到平台页。
- 虚拟币推广、币圈引流、交易所拉新：映射到 `/topics/crypto-promotion/`。
- 交友引流、交友 App 注册：映射到 `/topics/dating-traffic/`。

完整映射见 `docs/keyword-to-url-map.md`。

## public_status 含义

- `public_primary`：核心公开承接词，页面可自然展示。
- `public_secondary`：次级公开承接词，可进入页面少量代表性展示。
- `internal_only`：只作为内部资产和后续判断，不公开展示，不进入 sitemap。
- `future_blog`：适合未来问答或文章承接，当前不批量生成正文。
- `blocked`：禁止公开使用或需要明确排除的承诺词、违规词和风险词。

## 各层页面承接边界

- 首页：只承接海外推广、海外流量推广、出海项目推广、引流获客、广告投放支持、拉新买量等主词。
- services：承接服务词，如引流获客、广告投放、广告代投、投流、买量、推广代运营。
- platforms：承接平台词，如 TK 推广、FB 推广、谷歌推广。
- topics：承接细分类目词，如虚拟币推广、币圈引流、交友引流、游戏推广、贷款获客、保险获客、移民获客、网赚推广、兼职获客。
- blog：未来承接长尾问答词，正文后续由 DeepSeek 按质量标准编写。

## 当前只做内部资产的词

敏感内部类目当前只进入 `internal_only`，不生成公开页面，不进入首页，不进入导航，不进入 sitemap。

包括：

- 色粉
- 精准色粉
- 成人粉
- 成人兴趣粉
- 充值色粉
- Slot
- 维权
- 债务
- 索赔

## sitemap 控制规则

- sitemap 只收录正式承接页。
- sitemap 不收录原始关键词列表。
- sitemap 不收录 `internal_only` 或 `blocked` 关键词页面。
- 当前不新增几万个公开关键词页。

## 后续如何根据 GSC 扩展页面

后续上线并积累 GSC 数据后，可以按以下顺序扩展：

1. 查看已有承接页的展示、点击、查询词。
2. 找到高曝光、高相关、低风险的词组。
3. 判断是否已有页面能承接。
4. 如果现有页面不足，再新增高质量 topic 或 blog 页面。
5. 新页面必须先进入 URL 映射，再进入 sitemap。

## 当前仍未处理事项

- 未处理旧 service 页面。
- 未进入 Cloudflare Pages 部署。
- 未 push。
- 未批量生成博客正文。
- 未生成大量关键词页面。
