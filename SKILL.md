---
name: human-flavor-pipeline
description: 简体中文已有稿件的「去 AI 味」体检、局部审校与保真改写。支持 detect 只读诊断、review 局部 Before/After、full 完整改写;守住数字、实体、引语、语体与作者笔调。用户说「去 AI 味」「改得说人话」「降 AI 味」「润色成人写的」「这段太 AI 了」或要求中文稿件 humanize 时使用。不要用于从零写作、英文正文、翻译或只改格式的任务。
license: MIT
metadata:
  version: 1.1.0
---

# human-flavor-pipeline · 中文保真编辑流水线

这是一条 transform 管线。它编辑输入中已经存在的内容,不替作者产生观察、经历、数据、来源或判断。目标是让稿件读起来像一个有真实理由写它的人,不是猜测作者身份,也不是迎合 AI 检测器。

## 三种模式

- **detect**:只读体检。输出必要性、双评分、证据、热区和风险,不改正文。
- **review**:在 detect 基础上给最值得改的 3–8 处局部 Before / After,不输出整篇替换稿。
- **full**:完整改写并交付事实核对与改动报告。

默认选择:

- 快速聊天、短句且用户明确说「直接改」:轻档 full,报告压缩。
- 正式文档、客户方案、长文:默认 review;用户确认或明确说「直接改好」才走 full。
- 用户明确说「只检查 / 先评分」:detect。

## 六条硬规则

1. **事实先于风格**:数字、金额、日期、版本号、实体、引语、代码和占位符不得丢失、变化或新增。
2. **不制造假人味**:不得编第一人称经历、人物动作、情绪、来源、产品能力或因果结论。
3. **必要性优先**:底子好的稿件允许不改;不为显示工作量重写。
4. **语体至多漂移一级**:跨级改写需要用户确认。
5. **通用层与个人层分开**:默认 `profiles/default.md`;不得自动启用 `profiles/lens.md` 或任何作者 Profile。
6. **有界迭代**:最多回改 2 遍;未解决项如实列出。

## 渐进加载

先读 `references/resource-router.md`,按任务加载最少必要资源。

所有任务至少读取:

- `patterns/banned-words.md`:A–H 表达模式、I 风险、J 风格偏好;
- `references/scoring.md`:评分与证据要求;
- `profiles/default.md` 或用户明确指定的 Profile。

条件加载:

- 载体 / 文体判断:`patterns/channel-presets.md`;
- 笔调 / 口播:`patterns/voice-profiles.md`;
- 规则拿不准:`patterns/catalog/README.md`,再进入对应深查文件;
- 营销代理任务:`packs/marketing-agency/router.md`,不得全量读取 corpus;
- full 模式:`references/editing-protocol.md`;
- 报告:`references/report-format.md`。

报告写明本次启用的 Profile、Domain Pack 和实际读取资源。

## 六阶段流程

### 0 · 门检、保护区、定调

1. 判断改写必要性低 / 中 / 高并给证据与置信度,不猜作者身份。
2. 锁定数字、百分比、金额、日期、实体、专名、直接引语、代码、日志和占位符。
3. 确定载体、受众、文体与笔调;只推断有充分证据的部分,其余声明假设。
4. 选择 Profile 与 Domain Pack。默认 Profile 不附加任何个人习惯。

### 1 · 只读诊断

按 A–H 诊断表达,把 I 风险、J 风格与个人偏好分开记录。命中必须给原文引用;同一根因合并为一个 cluster,不按裸字符串计数。

输出:

- AI 味分与低 / 中 / 高等级、置信度、证据 cluster;
- 人味质量分与最低维度;
- 热区段号;
- 事实 / 来源 / 格式风险;
- Profile / Pack 命中。

detect 到此交付。

### 2 · 模式分流

- review:只挑收益最高的 3–8 处,给真实 Before / After 和理由。
- full:按 `references/editing-protocol.md` 执行完整编辑。

信息不够时,报告「待补:具体场景 / 数据口径 / 来源」,不要自己补内容。

### 3 · 编辑与笔调校准

顺序是结构 → 词汇 → 句法 → 节奏 → 标点。只用输入已有信息把抽象落具体。

有明确 Profile 或用户真文时,只提取句长、连接、标点、用词、段落与人称倾向;不得搬运锚点事实。没有个人 Profile 时按文体与通用笔调处理,不模仿维护者。

口播允许有听觉功能的软垫、反问和自我修正。开场可以来自原文已有亲历、直接判断或有来源材料;不得为了「亲历起手」编现场。

### 4 · 事实硬闸

full 完成后必须比较 before / after:

```bash
python3 scripts/check-fact-integrity.py BEFORE AFTER
```

任何 missing / changed / added 默认失败并回退。`--allow-added` 只用于用户明确授权、已带来源的独立研究结果审计,普通改写不得使用。

确定性检查通过后,再独立复核脚本覆盖不到的实体 / 专名对应关系与语义新增:经历、归因、来源、产品能力、人物动机和因果关系。事实未过闸,不进入风格评分。

### 5 · 交付与写回

按 `references/report-format.md` 交付。正式文档写回前先给最终全文或 review diff,等用户确认;写回后回读验证预期范围和保护区。

涉及客户报价 / 未公开数据的稿件可以向被授权的协作对象定向流转、送审和交付;不得发给未授权对象,也不自动写入公开库。

## 研究与生成边界

本 Skill 不从零写方案。用户明确要求外部研究或补事实时,先由调研流程提供可追溯来源,再把核实材料并入输入。`corpus/` 和 Domain Pack 只帮助识别行业术语、合法结构与相邻方法,不得充当无来源事实库。

## 评测与回灌

- 规则护栏:`python3 tests/check-precision.py`;
- 事实硬闸:`python3 tests/check-fact-integrity.py --fixtures`;
- Golden schema:`python3 tests/golden/run_eval.py validate`;
- 新版本与 main 用盲化 A/B 评测,事实硬失败率优先于风格胜率;
- 用户手动修改按 `references/feedback-loop.md` 分层,不得一次修改就晋升通用规则。
