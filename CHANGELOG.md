# Changelog

## 0.7.1 - 2026-06-23

口播 / 播客逐字稿声口补强,目标是防止 pipeline 把可说出来的稿子洗成书面稿。

- 新增 **口播(Spoken)** voice profile:承重句短准,连接组织允许第一人称、反问、口头转场、适量软垫和自我修正
- `SKILL.md` 阶段 3 新增口播校准:区分承重句与连接组织,同时明确不得编造亲历、数字、口头禅或固定收尾
- `patterns/banned-words.md` 与 `references/scoring.md` 增加口播软垫例外:有听觉功能的「其实 / 就是 / 我觉得」不按裸字符串扣分
- `patterns/style-anchors.md` 增加主播 / 口播锚点槽位,提醒私有节目素材留在本地,不要提交到公开 repo
- `tests/golden/cases.md` 增加口播逐字稿模型级评测用例,验证事实保真、软垫保留和防书面化
- 保持 29 条 precision 契约不变;本次是模型行为与声口规则更新

## 0.7.0 - 2026-06-20

对抗 0.6 精度偏置的反向加固:补召回护栏、否定先行松绑、单一真相源、模型级评测、外部锚。

- 新增**检测下限 floor**(`precision-rules.json` 4 条无例外规则:开场烘托 / 收尾套话 / 空强调 / PR 黑话)＋ **召回测试** `tests/fixtures/19-recall-floor.jsonl`;护栏从「只防误报」变「精度 + 召回」双向(check-precision.py 加载 18+19,36 用例:20 防误报 + 16 正样本)
- **否定先行硬禁 → 密度门控**:`不是X而是Y` 单次放行,同段 ≥2 次才罚(`negation_first_cluster`),`user-taste.md` 同步松绑
- **单一真相源**:散文层对模型 canonical,`precision-rules.json` 加 `canonical_source` ＋ `calibration` 字段;SKILL/banned-words 标明
- **护栏正名 ＋ 模型级评测**:`check-precision.py` 改述为 guardrail(绿≠skill 正确);新增 `tests/golden/`(before→after ＋ 五维 rubric)
- **外部权威锚**:Wikipedia「Signs of AI Writing」背书模式组;self-audit 终极一问借自 best-humanizer-handbook
- **声口必走**:有个人锚点时「写出自己的文风」从可选升为必走
- **词表校准**字段(应对模型迭代新味)＋ **`SKILL-lite.md`** 单文件变体(ChatGPT / Gemini 等)
- 调研:GitHub(best-humanizer-handbook 等)、小红书(头条去味工作流)

## 0.6.0 - 2026-06-18

精确率优先的规则校准,重点降低合法中文、专业文体与工作流残留的误报。

- 门检改为「改写必要性低 / 中 / 高」,不再猜测作者身份
- AI 味、人味、个人偏好、事实 / 来源风险、格式 / 载体风险拆轴;I/J 不重复计入 AI 味
- 载体、受众、文体、声口拆开判断,Notion / 飞书 / 公众号不再绑定固定文体
- 破折号改为功能与密度判断,删除无语料支持的「真人基线为 0」
- 技术英语服从团队约定、行业惯例与受众;泛称代词、准确业务术语不做裸字符串命中
- UTM、Markdown 与模板占位符改列工作流 / 格式风险,不再作为 AI 来源证据
- 新增假坦诚、格言公式、连续短句造戏剧感、标题后复述、变更叙事、助手尾巴等模式,并补相邻反例
- 删除无法核验的「Tim Cook 2026 年告别信」统计与示例
- 新增 `UPSTREAM.lock` 固定 qu-ai-wei 与 blader/humanizer commit
- 新增 `patterns/precision-rules.json` production 规则清单;29 条 precision 契约直接加载真实阈值、上下文与例外
- precision 新增相邻负样本,并修复学术样本「无强命中却强制判 AI」与版本同步检查

## 0.5.0 — 2026-06-18

实战回灌(一次真实客户方案)＋ 范文库 ＋ 个人禁忌层。

- 新增 **J 组江湖气 / 互联网黑话**(`patterns/banned-words.md`):军事 / 体育比喻 ＋ 阿里腔黑话 ＋ 替换速查表
- 新增 **个人禁忌层** `patterns/user-taste.md`:用户点名禁词 ＋ 手动改稿习惯成文,优先级最高
- 新增 **范文库** `patterns/exemplars.md`:蒸馏人味正面规则 ＋ 原创脱敏短范文锚点(不含真实品牌案例、不引第三方原文)＋ 个人锚点模板(机密不入库)
- `channel-presets.md` 增**乙方腔好坏边界**:deck 结构不扣分,只去空话型乙方腔
- `scoring.md` 增 J 组 / 个人禁忌计分、**防跨词假阳性**、乙方腔不计入
- `SKILL.md` 增门检分流(底子好→定点清理)、**写回前过目 checkpoint**、机密保护
- `CREDITS.md` 增范文短引用的著作权法第 24 条声明与署名
- 重新生成 `AGENTS.md`

## 0.4.0 — 2026-06-17

跨工具兼容:Claude Code ＋ Codex 双入口。

- 新增 `AGENTS.md`(Codex 入口),由 `SKILL.md` 经 `scripts/build-agents.sh` 同源生成,剥离 Claude 专有 frontmatter、保留正文与数据层引用 —— 单一事实来源,不漂移
- `SKILL.md` / `references/self-audit.md` 的子 agent 复核改为工具无关措辞(Claude Code 用 Task 工具 / Codex 用其子 agent 机制)
- README 增「安装与使用」双工具说明(Claude Code skill ＋ Codex AGENTS.md)
- `patterns/` 与 `references/` 数据层保持工具无关,两端共享

## 0.3.0 — 2026-06-17

深度无损合并本地 `qu-ai-wei`(MIT,@LifelongLazyLearner),消重只留一个 humanizer skill。

- 并入 `patterns/catalog/` —— qu-ai-wei 的 961 行 51 条 verbatim 模式库、白名单、标点 / 句法、平台模式、品牌声口、参考模型(作深查层,`banned-words.md` 拿不准时下钻)
- 并入 `tests/` —— 17 组 fixtures ＋ baseline / after 快照(作回归测试集)
- 新增 `CREDITS.md` 与 `patterns/catalog/LICENSE.qu-ai-wei`,保留 MIT 署名
- `banned-words.md` / `SKILL.md` 接线深查层;`design-notes.md` 记录合并
- 原 `qu-ai-wei` 从活跃 skills 归档至 `~/.claude/skills-archive/`

## 0.2.0 — 2026-06-17

集大成升级 —— 吸收 humanizer 类与 qu-ai-wei 类两条线的精华。

新增:
- **场景门**:快速 / 聊天 vs 正式交付,默认强度与报告粒度不同
- **语体阶梯 ＋ 九种语体**:输出至多偏移一格,防跨级洗坏
- **声口(voice profiles)**:直白 / 温和 / 犀利 / 技术 / 叙事,「句长＋用词＋结构」捆绑(`patterns/voice-profiles.md`)
- **六大主动润色动作**:动词强化 / 节奏重塑 / 填充删除 / 抽象落具体 / 语序归位 / 语体匹配
- **AI 不敢写测试 ＋ 整篇五问自检 ＋ 空句检测 ＋ 门检判定**(`references/self-audit.md`)
- **人味质量分 0–50** 五维矩阵,与 AI 味分双轴并看(`references/scoring.md`)
- **实战样例**:改前 / 改后对照,含特稿「不该过度改」反例(`references/examples.md`)
- 词典重组为 **A–I 模式分组** ＋ 三级强度(`patterns/banned-words.md`)
- 校验改为**事实优先的两遍读**(先保真,后查 AI 腔)
- 底线原则 7 → 8 条

## 0.1.0 — 2026-06-17

首版。中文去 AI 味六阶段流水线:门检 → 诊断打分 → 剥离 → 注入人味 → 校验 → 报告交付。两种模式、三级词典、渠道预设、风格锚点、AI 味分、保护区、有界迭代。
