# human-flavor-pipeline

![version](https://img.shields.io/badge/version-0.9.1-blue.svg)

当前版本:v0.9.1

一条**中文「去 AI 味」集大成流水线**,**Claude Code 与 Codex 双入口**。它只判断文本是否需要改,不根据文风猜作者身份;改写时守住事实、语体与作者原有笔调。

- **Claude Code** 走 `SKILL.md`(技能格式,支持渐进式加载)
- **Codex** 走根目录 `AGENTS.md`(由 `SKILL.md` 同源生成,避免漂移)
- **只吃单 system prompt 的工具**(ChatGPT / Gemini 等)走 `SKILL-lite.md`
- `patterns/` 与 `references/` 数据层两个工具共享

它吸收了 humanizer 类(voice profiles、质量评分矩阵、节奏校准、保真闸)与 qu-ai-wei 类(改写必要性门检、语体阶梯、毛边、整篇五问、空句检测、模式分组)两条线的精华。上游版本记录见 [`UPSTREAM.lock`](UPSTREAM.lock)。

它是 polish / transform 管线,不是生成器。只改已有文本,不替你产生观察、采访与判断。

---

## 版本沿革(最新在前)

- **v0.9.1**:术语去生硬化。「声口」改叫「笔调」,「场景门」改叫「适用场景匹配」,「四维门控」改叫「四项维度权衡」,更贴近母语表达。这份版本记录本身也从一段挤在一起的引用块拆成了现在的列表。
- **v0.9.0**:新增 `corpus/` 项目语料库。首次系统性提炼头条易公司知识库,涵盖公司通案、跨行业方法论、华东项目案例(81 条)与措辞词汇表。脱敏经多路 agent 通读复核,最后由用户本人逐字终审公开,详见 [`corpus/README.md`](corpus/README.md)。
- **v0.8.5**:白名单补达人业务黑话,如筛选漏斗、金字塔分层、人群资产分级。新增两条判据:表格自证套路、多层结构叠加。口播补两条反面模式:材料引入式冷开场、系列回扣不硬编期号。达人脚本落成六段式可执行骨架。
- **v0.8.0**:从真实写作语料提炼笔调画像填进锚点,脱敏进 repo,真稿留本地。补营销 / 媒介圈内词白名单。否定先行个人层松绑为策略分野例外。新增【新增信息】标记,改写补进原文没有的数字或事实一律先标待核实,不静默植入。达人 / 博主脚本笔调成型,翻译腔诊断规则上提到操作层。
- **v0.7.1**:补入口播 / 播客逐字稿笔调。可朗读的软垫词、反问、口头转场与自我修正,从无信息填充里单独区分出来,不再一刀切当废话删。事实闸同步收紧:不为了显得像口播就编造亲历、数字、口头禅或固定收尾。
- **v0.7.0**:精度与召回双向护栏定型。检测下限 floor 防止「什么都不敢改」,配套召回测试守住底线。否定先行从一刀切硬禁改成密度门控。定下单一真相源(散文 canonical),补齐模型级评测 `tests/golden/`,外部锚定 Wikipedia 的「Signs of AI Writing」。有个人笔调锚点时,笔调对齐从可选升级为必走项。

完整变更历史见 [`CHANGELOG.md`](CHANGELOG.md)。

> 设计目标不是骗过 AI 检测器(那是脆弱的军备竞赛),而是让你自己的 AI 辅助稿子**确实读起来像人写的**。检测分下降是结果,不是目的。

---

## 管线一览

```
草稿 ＋ 载体 / 受众 / 文体 / 笔调
      │  (适用场景匹配:快速/聊天 → 轻档直改;正式交付 → 先体检)
  0 · 门检 / 锁定 / 定调    判改写必要性 ＋ 抽保护区 ＋ 拆四个维度
      │                    (必要性低 → 停手或只做指定修复)
  1 · 诊断打分(只读)      AI 味 ＋ 人味 ＋ 个人偏好 ＋ 事实/格式风险
  2 · 剥离                先结构 → 后词汇 → 六大润色动作 → 标点
      │                    (含空句检测)
  3 · 注入人味            按内容调节节奏 ＋ 笔调/锚点 ＋ 保留原有毛边
      │
  4 · 校验(事实优先两遍)  先查事实保真,再查表达残余 ＋ 原有人味 ＋ 五问
      │                    (高风险派独立子 agent;未达标 → 回改 ≤N 遍)
  5 · 报告交付            双评分 diff 报告 ＋ 渠道排版
```

全程一条**保护区**侧轨:数字、人名、引用、报价、代码在阶段 0 锁定,阶段 4 逐项核对,绝不漂移。

## 两种模式 ＋ 适用场景匹配

- **detect**:只跑阶段 0–1,出改写必要性、`AI 味分 0–100`、`人味质量分 0–50`、个人偏好与风险项,**一个字都不改**。
- **full**:跑完整六段,出终稿 ＋ 打磨报告。
- **适用场景匹配**:快速 / 聊天场景默认轻档直改、报告压一行;正式交付(提案 / 特稿)默认先体检再改。

## 多轴诊断

AI 味与人味双评分负责表达质量;个人偏好、事实 / 来源风险、改写新增信息、格式 / 载体风险另列,不混入 AI 味。AI 味是编辑启发式,不回答「谁写的」。详见 [`references/scoring.md`](references/scoring.md)。

## 强度档位

| 档位 | 改写必要性 | 改动幅度 |
|------|---------|----------|
| 轻 | 低,或只有偏好 / 格式问题 | 定点修改 |
| 中 | 多个独立模式成簇出现 | bounded 删改 |
| 深 | 明确结构问题跨组共现 | structural 重构,仍受事实保护 |

## 语体阶梯 ＋ 笔调

九种语体按正式度排成阶梯,输出至多偏移一格,防止把特稿洗成公文或把公文洗成段子。笔调(直白 / 温和 / 犀利 / 技术 / 叙事 / 口播)与语体正交,是「节奏 ＋ 用词 ＋ 结构」的捆绑,不是词汇皮肤。见 [`patterns/voice-profiles.md`](patterns/voice-profiles.md)。

## 四项维度权衡

载体、受众、文体、笔调分开判断。Notion / 飞书 / 公众号只决定格式能力,不自动绑定客户方案、内部文档或特稿。见 [`patterns/channel-presets.md`](patterns/channel-presets.md)。

## 八条底线原则

1. 检测先于改写
2. 事实神圣(最高优先,保护区 ＋ 收尾核对)
3. 门检优先(必要性低就退场,不猜作者身份)
4. 语体阶梯,至多漂移一级
5. 保留原有人味(没有就报告,不强造)
6. 分级 ＋ 四项维度权衡
7. 全程透明(双评分 diff 报告)
8. 有界迭代(强度档位,不无限催降)

---

## 安装与使用

### Claude Code

```bash
git clone https://github.com/mjlens-spec/human-flavor-pipeline.git ~/.claude/skills/human-flavor-pipeline
```

新开会话后,说「帮我去 AI 味」「这段太 AI 了改一下」「降 AI 味」,或粘贴文本要求改写,skill 会按 `SKILL.md` 的 `description` 自动触发;也可 `/human-flavor-pipeline` 显式调。

### Codex

Codex 读取 `AGENTS.md`。两种用法:

```bash
# A. 作为项目级指令:在仓库目录内启动 Codex,根目录 AGENTS.md 自动加载
git clone https://github.com/mjlens-spec/human-flavor-pipeline.git
cd human-flavor-pipeline && codex

# B. 作为全局指令:把内容并入(或软链)到 ~/.codex/AGENTS.md
git clone https://github.com/mjlens-spec/human-flavor-pipeline.git ~/.humanizer
ln -s ~/.humanizer/AGENTS.md ~/.codex/AGENTS.md   # 或按需 include
```

然后在 Codex 里贴稿说「去 AI 味」即按同一套六阶段执行。

> `AGENTS.md` 由 `SKILL.md` 经 `scripts/build-agents.sh` 生成。改规程只改 `SKILL.md`,再跑 `bash scripts/build-agents.sh` 重新生成,**不要手改 AGENTS.md**,以免与 Claude Code 入口漂移。

## 目录结构

```
human-flavor-pipeline/
├── SKILL.md                    Claude Code 入口 ＋ 唯一事实来源(六阶段主流程)
├── AGENTS.md                   Codex 入口(由 SKILL.md 经 scripts/build-agents.sh 生成)
├── SKILL-lite.md               单文件变体(ChatGPT / Gemini 等只吃 system prompt 的工具)
├── scripts/build-agents.sh     SKILL.md → AGENTS.md 同源生成脚本
├── CREDITS.md                  署名(含并入的 qu-ai-wei,MIT)
├── patterns/
│   ├── banned-words.md         操作层:A–H 表达模式 ＋ I 风险 ＋ J 风格偏好
│   ├── user-taste.md           个人禁忌层(点名禁词 ＋ 手动改稿习惯,优先级最高)
│   ├── exemplars.md            范文库:人味正面规则 ＋ 原创脱敏短锚点 ＋ 个人锚点(含脱敏笔调示范)
│   ├── precision-rules.json    production 阈值 / 上下文 / 例外(供 precision 契约加载)
│   ├── catalog/                深查层:51 个主编号 ＋ 本地扩展/白名单(含营销圈内词)/标点/句法/平台/品牌笔调
│   ├── channel-presets.md      载体/受众/文体/笔调拆分 ＋ 乙方腔边界
│   ├── voice-profiles.md       六种笔调(节奏＋用词＋结构捆绑,含口播下的达人/博主脚本亚型)
│   └── style-anchors.md        风格锚点(few-shot,贴你的真文;含已提炼笔调参数表作 fallback)
├── references/
│   ├── scoring.md              多轴诊断:双评分 ＋ 偏好 ＋ 风险
│   ├── self-audit.md           改写必要性门检 ＋ 原有人味 ＋ 五问 ＋ 独立复核
│   ├── examples.md             实战样例(改前/改后 ＋ 打磨报告)
│   └── design-notes.md         集大成清单与同类项目致谢
├── corpus/                     项目语料库(选读):公司通案 / 跨行业方法论 / 华东项目案例 / 措辞词汇表,已脱敏并经人工终审公开,见 corpus/README.md
└── tests/                      快照 ＋ 29 条 precision 契约 ＋ 召回 floor(19)＋ golden 模型级评测(含口播 / 达人脚本 / 新增信息标记)＋ 自动检查
```

## 用之前建议做一件事

打开 [`patterns/style-anchors.md`](patterns/style-anchors.md),贴 1–2 段你自己最满意的真文。阶段 3 会用它做 few-shot,把终稿向你本人的笔调对齐,而不是对齐一个通用「人类」。给范文比堆规则有效得多。

---

## English summary

A six-stage pipeline for Chinese text, built to edit AI-flavored drafts until they read like something a person actually wrote. It judges whether a rewrite is needed before touching anything, rather than guessing who wrote it. Expression scores stay separate from preference and workflow risk, so a personal quirk or a formatting mismatch never gets mistaken for AI residue. Facts, register, and the author's existing voice don't move.

It edits what's already on the page. It won't invent a personal detail or an opinion just to pass a style check, and beating AI detectors was never the goal.

Stages: **0** gate / lock facts / separate carrier, audience, register, and voice → **1** read-only multi-axis diagnosis → **2** edit structure and wording → **3** calibrate rhythm without fixed sentence lengths → **4** verify facts first → **5** diff report. Chinese (Simplified) only.

See [`references/design-notes.md`](references/design-notes.md) for the full synthesis list and credits.

## Credits

`patterns/catalog/` 与 `tests/` 直接并入 [qu-ai-wei](https://github.com/LifelongLazyLearner/qu-ai-wei)(MIT,@LifelongLazyLearner),许可与署名见 [CREDITS.md](CREDITS.md)。设计共识另借鉴 humanizer-skill、shuorenhua、Humanizer-zh 等。

## License

本项目采用 MIT 许可,见 [LICENSE](LICENSE)。并入的 qu-ai-wei 内容保留其原始 MIT 许可于 `patterns/catalog/LICENSE.qu-ai-wei`。
