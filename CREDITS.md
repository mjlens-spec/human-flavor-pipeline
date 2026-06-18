# Credits 致谢与署名

本项目是中文去 AI 味实践的「集大成」综合,站在前人工作之上。以下内容含直接并入的第三方作品,按其许可保留署名。

## 直接并入(MIT)

### qu-ai-wei — by [@LifelongLazyLearner](https://github.com/LifelongLazyLearner/qu-ai-wei)

`patterns/catalog/` 与 `tests/` 下的内容**直接来自** qu-ai-wei(MIT License,Copyright (c) 2026 @LifelongLazyLearner),在本项目 0.3.0「深度无损合并」时并入,作为细粒度深查层与回归测试集。包含:

- `patterns/catalog/patterns.md` —— 51 条 A–I 模式核心参考(原文 / 改后对照、语体限定、跨规则 interlock)
- `patterns/catalog/platform-patterns.md` · `syntax.md` · `punctuation.md` · `whitelists.md` · `brand-voice.md` · `reference-models.md` · `sources.md` · `examples.md`
- `tests/` —— 17 组 fixtures、baseline / after 快照、校验脚本

qu-ai-wei 的 MIT 许可全文保留在 `patterns/catalog/LICENSE.qu-ai-wei`。其规则与本项目自有的 `patterns/banned-words.md`(精炼操作层)互为表里 —— catalog 是深查层。

qu-ai-wei 本身受 [`humanizer`](https://github.com/blader/humanizer)(作者 Siqi Chen,MIT,2025)启发,并参考 [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)。这些上游致谢一并延续。

## 设计共识(未直接并入代码,仅借鉴做法)

humanizer-skill(Aboudjem)· shuorenhua(说人话)· Humanizer-zh(op7418)· humanize-text · StealthHumanizer · humanizer-de。详见 `references/design-notes.md`。

## 范文短引用(著作权法第 24 条适当引用)

`patterns/exemplars.md` 含若干 ≤150 字的短摘录,**为说明写作风格、供学习借鉴**,依《中华人民共和国著作权法》第 24 条第(二)项「为介绍、评论某一作品或者说明某一问题,在作品中适当引用他人已经发表的作品」适当引用,均标注作者 / 出处 / URL,非转载、不构成对原作的市场替代。来源含:晚点 LatePost、数英 Digitaling、SocialBeta、品牌星球 BrandStar 等公开发表文章。如相关权利人不希望被引用,提 issue 即移除。

人味写作规则蒸馏自:奥威尔《政治与英语》、阮一峰《中文技术文档写作规范》、叶圣陶 / 夏丏尊《文心》、sparanoid《中文文案排版指北》、晚点 LatePost 记者手记等(均注明出处)。
