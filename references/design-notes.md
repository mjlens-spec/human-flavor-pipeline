# 设计说明

这条管线综合了 GitHub 上口碑较好的一批去 AI 味 / humanizer 项目的共识做法,再结合中文专业写作(营销策划、客户方案、长报道特稿、飞书 / Notion / 公众号交付)的真实工作流重构而成。0.2 版起明确定位为「集大成者」:把 humanizer 类与 qu-ai-wei 类两条线的精华都吸收进来。

---

## 为什么是六阶段,而不是一个大 prompt

调研到的多数低质工具是「一个大 prompt 边读边改」,问题是检测和改写混在一起,改坏了事实也发现不了,且无法对单一环节调参。口碑较好的项目(humanizer-skill 的 4-pass、shuorenhua 的双遍审读、humanizer-de 的 5-pass)都把流程拆成可独立调参的阶段。本管线据此拆成六段,关键是检测与改写分离、收尾独立校验。

## 吸收的精华(集大成清单)

**来自 humanizer 类(英文 / 通用)**
- 0–100 AI-tell score 作首尾两道闸(humanizer-skill)
- voice profiles 作「句长 ＋ 用词 ＋ 结构」捆绑,而非词汇皮肤(humanizer-skill)
- 质量评分矩阵,五维各打分(Humanizer-zh)→ 本管线的人味质量分 0–50
- 节奏校准(检查机械等长与连续短句,不设固定句长目标)
- 回译式关键信息保真思路(humanize-text)→ 保护区 ＋ 事实保真闸
- 多模型 / 独立复核(StealthHumanizer)→ 高风险派独立子 agent
- 模块化两文件结构,数据与流程解耦

**来自 qu-ai-wei 类(中文)**
- 门检:判断改写必要性,不猜作者身份
- 语体阶梯 ＋ 至多漂移一级
- 九种语体,规则按语体子集触发
- 六大主动润色动作(动词强化 / 节奏重塑 / 填充删除 / 抽象落具体 / 语序归位 / 语体匹配)
- 毛边机制(只保留原文已有内容,不设强制测试)
- 整篇五问自检
- 空句检测
- A–H 表达模式 ＋ I 风险 ＋ J 风格偏好
- 白名单豁免
- 打磨报告带真实原文 / 改后引用

**来自中文 humanizer 调研(shuorenhua 等)**
- 三级禁用词典(Tier 1/2/3)
- 场景门(快速 / 聊天 vs 正式交付,默认强度不同)
- 校验事实优先、AI 腔在后的两遍读
- 强度分档,不无限催降
- 平台 register 区分

## 关键设计决策

1. **先检测后改写(阶段 1 只读)** —— 让「改前 → 改后」的双评分落差成为可量化交付。
2. **先结构后词汇(阶段 2 顺序)** —— 结构信号比词汇强,只换词不动结构的稿子骗得过检测器也骗不过人。
3. **多轴分开记录** —— AI 味与人味负责表达质量;个人偏好、事实 / 来源、格式 / 载体风险另列。
4. **事实优先的两遍校验** —— 第一遍只查事实,第二遍才查 AI 腔,顺序反了会误删信息。
5. **保留原有毛边,但禁止伪造** —— 原文没有具体态度或经历时如实报告,不强造。
6. **有界迭代** —— 强度档位 ＋ 最多 N 遍回改,取代无限催降。
7. **载体 / 受众 / 文体 / 声口拆分** —— 载体只管格式,其余三项共同决定语言与节奏。

## 0.7.0:召回护栏与外部锚(对抗 0.6 的精度偏置)

0.6 精确率优先做得到位,但暴露一个结构性偏置:测试只惩罚误报、不奖励召回,长期会把 skill 调成「什么都不敢改」;且把「否定先行」一刀切硬禁,是好洞察的过度泛化。0.7 做反向加固:

- **检测下限(floor)＋ 召回测试** —— `precision-rules.json` 新增 4 条无例外 floor 规则(开场烘托 / 收尾套话 / 空强调 / PR 黑话),`tests/fixtures/19-recall-floor.jsonl` 用 `pos_*` 用例守住「真 slop 必被抓」。护栏测试从「只测不误报」变成「精度 + 召回」双向。
- **否定先行:硬禁 → 密度门控** —— `不是 X 而是 Y` 单次放行(合法对比),同段 ≥2 次才判套路(`negation_first_cluster`),套用 0.6 自己给 fake_candor 的克制思路。
- **单一真相源** —— 明确散文层(`banned-words.md` ＋ `user-taste.md`)对模型 canonical,`precision-rules.json` 是派生护栏契约;新增 `canonical_source` 字段。
- **护栏 ≠ 正确,补模型级评测** —— `check-precision.py` 正名为 guardrail;新增 `tests/golden/`(before→after ＋ 五维 rubric,人 / LLM-judge 评),专测模型行为。
- **外部权威锚** —— A–H 模式组与 floor 以 Wikipedia「Signs of AI Writing」背书;self-audit 终极一问「像不像有人有真实理由要写它」借自 best-humanizer-handbook。
- **声口必走** —— 有个人锚点时「写出自己的文风」从可选升为必走(小红书头条工作流的差异点)。
- **词表校准 ＋ Lite 变体** —— 词表标「最后校准模型 / 日期」应对模型迭代的新味;新增 `SKILL-lite.md` 给只吃单 system prompt 的工具(ChatGPT / Gemini)。

调研来源:GitHub(best-humanizer-handbook、anti-slop-writing、peakoss/anti-slop)、小红书(头条工作流「先看出 AI 味 → 改成人话 → 写出自己的文风」)。

## 0.6.0:精确率与证据边界

本版把表达模式、个人偏好、事实风险与格式风险拆开,并用可执行 precision 契约防止裸关键词误杀。契约直接加载 `patterns/precision-rules.json` 的 production 阈值、上下文与例外,同时校验操作层与深查层文档锚点。上游版本与本地差异见 `UPSTREAM.lock`。

## 0.3.0:深度无损合并 qu-ai-wei

0.3 版把本地另一个 humanizer 类 skill `qu-ai-wei`(MIT,@LifelongLazyLearner)深度并入,消除重复、只留一个。两者是互补关系而非纯重复:

- **human-flavor-pipeline 的强项**是架构 —— 六阶段管线、detect/full 模式、双评分、voice profiles、场景门。
- **qu-ai-wei 的强项**是数据 —— 51 个主编号的模式参考、细粒度白名单 / 标点 / 句法、品牌声口与 17 组测试 fixtures。

合并取「我的架构 ＋ 它的数据」:qu-ai-wei 的 references 并入 `patterns/catalog/` 作深查层(操作层 `banned-words.md` 拿不准时下钻),tests 并入 `tests/` 作回归集。署名与 MIT 许可保留(见 `CREDITS.md` 与 `patterns/catalog/LICENSE.qu-ai-wei`)。原 `qu-ai-wei` 已从活跃 skills 归档。

## 0.5.0:实战回灌 ＋ 范文库 ＋ 个人禁忌层

一次真实客户方案实战后,把经验回灌进 skill:

- **J 组江湖气 / 互联网黑话**升为独立模式组 —— 实战证明底子好的稿子真正要清的是挑大梁 / 主战场 / 卡 / 打通 / 赋能 / 闭环这类比喻腔,而非典型 AI 腔。
- **个人禁忌层 `user-taste.md`** —— 用户的语言洁癖(点名禁词 ＋ 手动改稿习惯)成文,优先级高于通用词典。仲裁:事实 > 个人禁忌 > 渠道语体 > 通用。
- **乙方腔 ≠ AI 味** —— 客户方案语体下,战略角色 / KFS / 节点日历是合规 deck 结构,不扣分;只去空话型乙方腔。
- **范文库 `exemplars.md`** —— 不只禁,还给正面写作规则与原创脱敏短锚点(不含真实品牌案例,不引第三方原文)。
- **写回前过目 checkpoint** ＋ **扫描防跨词假阳性** ＋ **机密内容不入公开库**(从实战拦截与客户机密保护中得到的硬规则)。

## 参考与致谢(同类项目)

直接并入:**qu-ai-wei**(MIT,见 `CREDITS.md`)。设计共识借鉴:humanizer-skill(Aboudjem)· shuorenhua(说人话)· Humanizer-zh(op7418)· humanize-text · StealthHumanizer · humanizer-de。本项目取其阶段化、分级、保真、留人味的共识,针对中文专业交付场景重构,非照搬。

## 不做什么

- 不以过 AI 检测器为目标
- 不从零生成内容
- 不处理英文正文与繁体中文
- 不替代人的观察、采访、判断
