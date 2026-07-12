# human-flavor-pipeline

![version](https://img.shields.io/badge/version-1.0.0-blue.svg)

当前版本:v1.0.0

一条**中文「去 AI 味」集大成流水线**。Claude Code 与 Codex 共用同一个 `SKILL.md`;它只判断文本是否需要改,不根据文风猜作者身份,改写时守住事实、语体与作者原有笔调。

- **Claude Code / Codex** 都走可安装目录里的 `SKILL.md`
- 根目录 `AGENTS.md` 只约束仓库维护,不再复制完整 Skill 正文
- **只吃单 system prompt 的工具**(ChatGPT / Gemini 等)走 `SKILL-lite.md`
- `patterns/` 与 `references/` 数据层两个工具共享

它吸收了 humanizer 类(voice profiles、质量评分矩阵、节奏校准、保真闸)与 qu-ai-wei 类(改写必要性门检、语体阶梯、毛边、整篇五问、空句检测、模式分组)两条线的精华。上游版本记录见 [`UPSTREAM.lock`](UPSTREAM.lock)。

它是 polish / transform 管线,不是生成器。只改已有文本,不替你产生观察、采访与判断。

---

## 版本沿革(最新在前)

- **v1.0.0**:从规则集升级为可信编辑系统。新增 review 局部审校、确定性事实硬闸、可运行 Golden 盲化 A/B、Default / Lens Profile 隔离、Marketing Agency Domain Pack 与 corpus 路由。普通改写不得新增事实,即使标「待核实」也先判失败。
- **v0.9.2**:修复分发外壳。新增完整可安装 Skill 目录、安装后资源检查、标准 frontmatter、OpenAI UI 元数据与 CI;Claude Code / Codex 统一消费 `SKILL.md`,根目录 `AGENTS.md` 收缩为仓库维护说明。机密 / 高风险稿按授权对象定向流转,不再笼统禁止外发。
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
  1 · 诊断打分(只读)      AI 味 ＋ 人味 ＋ Profile/Pack ＋ 事实/格式风险
      │  模式分流          detect 停止 / review 局部对照 / full 完整改写
  2 · 编辑                先结构 → 后词汇 → 句法 → 节奏 → 标点
      │                    (含空句检测)
  3 · 注入人味            按内容调节节奏 ＋ 笔调/锚点 ＋ 保留原有毛边
      │
  4 · 事实硬闸            missing / changed / added 任一出现即失败
      │                    (高风险派独立子 agent;未达标 → 回改 ≤N 遍)
  5 · 报告交付            双评分 diff 报告 ＋ 渠道排版
```

全程一条**保护区**侧轨:数字、人名、引用、报价、代码在阶段 0 锁定,阶段 4 逐项核对,绝不漂移。

## 三种模式 ＋ 适用场景匹配

- **detect**:只跑阶段 0–1,出改写必要性、`AI 味分 0–100`、`人味质量分 0–50`、个人偏好与风险项,**一个字都不改**。
- **review**:在 detect 基础上给最值得改的 3–8 处局部 Before / After,不输出整篇替换稿。正式文档默认先走这一档。
- **full**:跑完整六段,出终稿 ＋ 打磨报告。
- **适用场景匹配**:快速 / 聊天场景默认轻档直改、报告压一行;正式交付(提案 / 特稿)默认先体检再改。

## 多轴诊断

AI 味与人味双评分负责表达质量;Profile、Domain Pack、事实 / 来源风险与格式 / 载体风险另列。普通改写出现原文没有的事实直接失败,不再用「待核实」放行。AI 味是编辑启发式,不回答「谁写的」。详见 [`references/scoring.md`](references/scoring.md)。

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

## 六条底线原则

1. 事实先于风格,不得丢失、改变或新增
2. 不制造假人味,不编经历、来源、情绪或因果
3. 门检优先,必要性低允许不改
4. 语体阶梯至多漂移一级
5. 通用 Core、个人 Profile、领域 Pack 分开
6. 有界迭代,最多回改 2 遍

---

## 安装与使用

### Claude Code / Codex

```bash
npx skills add mjlens-spec/human-flavor-pipeline -g -y -s human-flavor-pipeline
```

安装器应选择 `skills/human-flavor-pipeline/` 下的完整运行包,而不是只复制仓库根目录的单个 `SKILL.md`。新开会话后说「帮我去 AI 味」「这段太 AI 了改一下」「降 AI 味」即可触发。

## 目录结构

```
human-flavor-pipeline/
├── SKILL.md                    Claude Code 入口 ＋ 唯一事实来源(六阶段主流程)
├── AGENTS.md                   仓库维护说明(薄入口,不复制 Skill 正文)
├── SKILL-lite.md               单文件变体(ChatGPT / Gemini 等只吃 system prompt 的工具)
├── scripts/build-agents.sh     SKILL.md → AGENTS.md 同源生成脚本
├── CREDITS.md                  署名(含并入的 qu-ai-wei,MIT)
├── patterns/
│   ├── banned-words.md         操作层:A–H 表达模式 ＋ I 风险 ＋ J 风格偏好
│   ├── user-taste.md           0.x 个人层兼容文件(1.0 不默认加载)
│   ├── exemplars.md            范文库:人味正面规则 ＋ 原创脱敏短锚点 ＋ 个人锚点(含脱敏笔调示范)
│   ├── precision-rules.json    production 阈值 / 上下文 / 例外(供 precision 契约加载)
│   ├── catalog/                深查层:51 个主编号 ＋ 本地扩展/白名单(含营销圈内词)/标点/句法/平台/品牌笔调
│   ├── channel-presets.md      载体/受众/文体/笔调拆分 ＋ 乙方腔边界
│   ├── voice-profiles.md       六种笔调(节奏＋用词＋结构捆绑,含口播下的达人/博主脚本亚型)
│   └── style-anchors.md        锚点提取方法与兼容模板
├── profiles/                   可选个人 / 团队笔调;默认 default,lens 需明确启用
├── packs/marketing-agency/     营销代理领域包与 corpus 检索路由
├── references/
│   ├── scoring.md              多轴诊断:双评分 ＋ 偏好 ＋ 风险
│   ├── self-audit.md           改写必要性门检 ＋ 原有人味 ＋ 五问 ＋ 独立复核
│   ├── examples.md             实战样例(改前/改后 ＋ 打磨报告)
│   └── design-notes.md         集大成清单与同类项目致谢
├── corpus/                     项目语料库(只经 Domain Pack 定向读取)
├── skills/human-flavor-pipeline/  生成的完整可安装包
└── tests/                      快照、29 条 precision 契约、recall floor、事实硬闸、Golden 盲测与安装检查
```

## 个性化建议

公开安装默认使用 [`profiles/default.md`](profiles/default.md),不会模仿维护者。需要个人笔调时,显式启用 [`profiles/lens.md`](profiles/lens.md) 或提供安装目录外的本地 Profile 与 1–2 段真文。给范文比堆规则有效,但锚点里的事实不会被搬进稿件。

---

## English summary

A six-stage pipeline for Chinese text, built to edit AI-flavored drafts until they read like something a person actually wrote. It judges whether a rewrite is needed before touching anything, rather than guessing who wrote it. Expression scores stay separate from preference and workflow risk, so a personal quirk or a formatting mismatch never gets mistaken for AI residue. Facts, register, and the author's existing voice don't move.

It edits what's already on the page. It won't invent a personal detail or an opinion just to pass a style check, and beating AI detectors was never the goal.

Modes: **detect** for read-only diagnosis, **review** for targeted Before/After suggestions, and **full** for a complete rewrite. Every full rewrite passes a deterministic fact gate before style scoring. Chinese (Simplified) only.

See [`references/design-notes.md`](references/design-notes.md) for the full synthesis list and credits.

## Credits

`patterns/catalog/` 与 `tests/` 直接并入 [qu-ai-wei](https://github.com/LifelongLazyLearner/qu-ai-wei)(MIT,@LifelongLazyLearner),许可与署名见 [CREDITS.md](CREDITS.md)。设计共识另借鉴 humanizer-skill、shuorenhua、Humanizer-zh 等。

## License

本项目采用 MIT 许可,见 [LICENSE](LICENSE)。并入的 qu-ai-wei 内容保留其原始 MIT 许可于 `patterns/catalog/LICENSE.qu-ai-wei`。
