# Credits 致谢与署名

本项目是中文去 AI 味实践的「集大成」综合,站在前人工作之上。以下内容含直接并入的第三方作品,按其许可保留署名。

## 直接并入(MIT)

### qu-ai-wei — by [@LifelongLazyLearner](https://github.com/LifelongLazyLearner/qu-ai-wei)

`patterns/catalog/` 与最初的 `tests/` 语料在 0.3.0 从 qu-ai-wei(MIT License,Copyright (c) 2026 @LifelongLazyLearner)并入。0.6.0 起这些文件已经针对本项目的多轴评分、中文误杀边界与事实保护做了本地修改,不应视为上游逐字镜像。包含:

- `patterns/catalog/patterns.md` —— 51 个上游主编号及本项目局部扩展(原文 / 改后对照、语体限定、跨规则 interlock)
- `patterns/catalog/platform-patterns.md` · `syntax.md` · `punctuation.md` · `whitelists.md` · `brand-voice.md` · `reference-models.md` · `sources.md` · `examples.md`
- `tests/` —— 17 组历史 fixtures、baseline / after 快照,以及本项目新增的 29 条 precision 契约与校验脚本

qu-ai-wei 的 MIT 许可全文保留在 `patterns/catalog/LICENSE.qu-ai-wei`。其规则与本项目自有的 `patterns/banned-words.md`(精炼操作层)互为表里 —— catalog 是深查层。

qu-ai-wei 本身受 [`humanizer`](https://github.com/blader/humanizer)(作者 Siqi Chen,MIT,2025)启发,并参考 [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)。这些上游致谢一并延续。两项上游的固定 commit、同步日期与本地改动摘要见 [`UPSTREAM.lock`](UPSTREAM.lock)。

## 设计共识(未直接并入代码,仅借鉴做法)

humanizer-skill(Aboudjem)· shuorenhua(说人话)· Humanizer-zh(op7418)· humanize-text · StealthHumanizer · humanizer-de。详见 `references/design-notes.md`。

## 范文锚点(原创脱敏,无第三方引用)

`patterns/exemplars.md` 的范文锚点均为**原创、脱敏的示范例**,只演示写作手法,**不含真实品牌 / 公司案例名,不引用第三方原文**,故无需第三方署名,也不附外部出处。

人味写作规则蒸馏自公开写作方法论:奥威尔《政治与英语》、阮一峰《中文技术文档写作规范》、叶圣陶 / 夏丏尊《文心》、sparanoid《中文文案排版指北》等(均为写作方法论,非品牌案例)。
