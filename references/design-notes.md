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
- burstiness 显式注入(明确句长目标,而非泛泛「写自然点」)
- 回译式关键信息保真思路(humanize-text)→ 保护区 ＋ 事实保真闸
- 多模型 / 独立复核(StealthHumanizer)→ 高风险派独立子 agent
- 模块化两文件结构,数据与流程解耦

**来自 qu-ai-wei 类(中文)**
- 门检:先判人写还是 AI 写,人写只清格式
- 语体阶梯 ＋ 至多漂移一级
- 九种语体,规则按语体子集触发
- 六大主动润色动作(动词强化 / 节奏重塑 / 填充删除 / 抽象落具体 / 语序归位 / 语体匹配)
- 毛边机制 ＋ 「AI 不敢写」测试
- 整篇五问自检
- 空句检测
- A–I 模式分组
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
3. **双评分两轴并看** —— 只压 AI 味分会洗成无菌腔;人味分守住下限。
4. **事实优先的两遍校验** —— 第一遍只查事实,第二遍才查 AI 腔,顺序反了会误删信息。
5. **留毛边 ＋ AI 不敢写测试,但禁止伪造** —— 反过度净化与反幻觉的双重约束。
6. **有界迭代** —— 强度档位 ＋ 最多 N 遍回改,取代无限催降。
7. **渠道 ＋ 声口正交** —— 渠道定正式度,声口定句式锋芒。

## 0.3.0:深度无损合并 qu-ai-wei

0.3 版把本地另一个 humanizer 类 skill `qu-ai-wei`(MIT,@LifelongLazyLearner)深度并入,消除重复、只留一个。两者是互补关系而非纯重复:

- **human-flavor-pipeline 的强项**是架构 —— 六阶段管线、detect/full 模式、双评分、voice profiles、场景门。
- **qu-ai-wei 的强项**是数据 —— 961 行 51 条 verbatim 模式库、细粒度白名单 / 标点 / 句法、品牌声口判定、17 组测试 fixtures。

合并取「我的架构 ＋ 它的数据」:qu-ai-wei 的 references 并入 `patterns/catalog/` 作深查层(操作层 `banned-words.md` 拿不准时下钻),tests 并入 `tests/` 作回归集。署名与 MIT 许可保留(见 `CREDITS.md` 与 `patterns/catalog/LICENSE.qu-ai-wei`)。原 `qu-ai-wei` 已从活跃 skills 归档。

## 参考与致谢(同类项目)

直接并入:**qu-ai-wei**(MIT,见 `CREDITS.md`)。设计共识借鉴:humanizer-skill(Aboudjem)· shuorenhua(说人话)· Humanizer-zh(op7418)· humanize-text · StealthHumanizer · humanizer-de。本项目取其阶段化、分级、保真、留人味的共识,针对中文专业交付场景重构,非照搬。

## 不做什么

- 不以过 AI 检测器为目标
- 不从零生成内容
- 不处理英文正文与繁体中文
- 不替代人的观察、采访、判断
