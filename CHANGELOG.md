# Changelog

## 0.5.0 — 2026-06-18

实战回灌(周大生 Q3 客户方案)＋ 范文库 ＋ 个人禁忌层。

- 新增 **J 组江湖气 / 互联网黑话**(`patterns/banned-words.md`):军事 / 体育比喻 ＋ 阿里腔黑话 ＋ 替换速查表
- 新增 **个人禁忌层** `patterns/user-taste.md`:用户点名禁词 ＋ 手动改稿习惯成文,优先级最高
- 新增 **范文库** `patterns/exemplars.md`:蒸馏人味正面规则 ＋ ≤150 字短范文锚点(晚点 / 数英 / SocialBeta 等,第 24 条适当引用 ＋ 完整署名)＋ 个人锚点模板(机密不入库)
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
