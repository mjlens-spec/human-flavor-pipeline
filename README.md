# human-flavor-pipeline

一条**中文「去 AI 味」集大成流水线**,**Claude Code 与 Codex 双入口**。把任意草稿(AI 生成、AI 辅助或可疑文本)改成读起来像人认真写的终稿,同时守住事实、语体与一道人味。

- **Claude Code** 走 `SKILL.md`(技能格式,支持渐进式加载)
- **Codex** 走根目录 `AGENTS.md`(由 `SKILL.md` 同源生成,避免漂移)
- `patterns/` 与 `references/` 数据层两个工具共享

它吸收了 humanizer 类(voice profiles、质量评分矩阵、burstiness、保真闸)与 qu-ai-wei 类(门检、语体阶梯、毛边、AI 不敢写测试、整篇五问自检、空句检测、A–I 模式分组)两条线的精华。

它是 polish / transform 管线,不是生成器 —— 只改已有文本,不替你产生观察、采访与判断。

> 设计目标不是骗过 AI 检测器(那是脆弱的军备竞赛),而是让你自己的 AI 辅助稿子**确实读起来像人写的**。检测分下降是结果,不是目的。

---

## 管线一览

```
草稿 ＋ 渠道标记
      │  (场景门:快速/聊天 → 轻档直改;正式交付 → 先体检)
  0 · 门检 / 锁定 / 定调    判来源 ＋ 抽保护区 ＋ 定语体阶梯 ＋ 选渠道声口
      │                    (人写 → 仅清格式退出)
  1 · 诊断打分(只读)      AI 味 0–100 ＋ 人味 0–50 ＋ 热区(A–I 分组)
      │                    (低分 → 跳过 / 轻改)
  2 · 剥离                先结构 → 后词汇 → 六大润色动作 → 标点
      │                    (含空句检测)
  3 · 注入人味            长短句节奏 ＋ 声口/锚点 ＋ 留毛边
      │
  4 · 校验(事实优先两遍)  先查事实保真,再查 AI 残余 ＋ AI 不敢写测试 ＋ 五问
      │                    (高风险派独立子 agent;未达标 → 回改 ≤N 遍)
  5 · 报告交付            双评分 diff 报告 ＋ 渠道排版
```

全程一条**保护区**侧轨:数字、人名、引用、报价、代码在阶段 0 锁定,阶段 4 逐项核对,绝不漂移。

## 两种模式 ＋ 场景门

- **detect** —— 只跑阶段 0–1,出 `AI 味分 0–100`(越低越好)＋ `人味质量分 0–50`(越高越好)＋ 热区,**一个字都不改**。
- **full** —— 跑完整六段,出终稿 ＋ 打磨报告。
- **场景门** —— 快速 / 聊天场景默认轻档直改、报告压一行;正式交付(提案 / 特稿)默认先体检再改。

## 双评分

只压 AI 味分容易洗成无菌的另一种机器腔。两轴并看 —— AI 味查毛病(越低越好),人味质量查是否真像人(五维:直接性 / 节奏 / 信任读者 / 真实性 / 简洁,越高越好)。详见 [`references/scoring.md`](references/scoring.md)。

## 强度档位

| 档位 | AI 味分 | 改动幅度 |
|------|---------|----------|
| 轻 | 0–15 | 仅词汇替换 |
| 中 | 16–35 | bounded 删改,先列候选 |
| 深 | 36–100 | structural 重构 |

## 语体阶梯 ＋ 声口

九种语体按正式度排成阶梯,输出至多偏移一格,防止把特稿洗成公文或把公文洗成段子。声口(直白 / 温和 / 犀利 / 技术 / 叙事)与语体正交,是「句长 ＋ 用词 ＋ 结构」的捆绑,不是词汇皮肤。见 [`patterns/voice-profiles.md`](patterns/voice-profiles.md)。

## 渠道感知

同一套词典按交付渠道门控:飞书内部 / Notion 对外提案 / 公众号特稿 / 小红书 / 学术,各有不同的语体、标点、人味度。见 [`patterns/channel-presets.md`](patterns/channel-presets.md)。

## 八条底线原则

1. 检测先于改写
2. 事实神圣(最高优先,保护区 ＋ 收尾核对)
3. 门检优先(人写只清格式)
4. 语体阶梯,至多漂移一级
5. 保留人味(留毛边 ＋ 过 AI 不敢写测试,但不伪造)
6. 分级 ＋ 语体门控
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
├── scripts/build-agents.sh     SKILL.md → AGENTS.md 同源生成脚本
├── CREDITS.md                  署名(含并入的 qu-ai-wei,MIT)
├── patterns/
│   ├── banned-words.md         操作层:A–J 模式分组(含 J 江湖气/黑话)＋ 三级强度 ＋ 白名单
│   ├── user-taste.md           个人禁忌层(点名禁词 ＋ 手动改稿习惯,优先级最高)
│   ├── exemplars.md            范文库:人味正面规则 ＋ 短范文锚点(署名引用)＋ 个人锚点
│   ├── catalog/                深查层:51 条 verbatim 模式库 ＋ 白名单/标点/句法/平台/品牌声口(并自 qu-ai-wei)
│   ├── channel-presets.md      渠道预设 ＋ 乙方腔好坏边界
│   ├── voice-profiles.md       五种声口(句长＋用词＋结构捆绑)
│   └── style-anchors.md        风格锚点(few-shot,贴你的真文)
├── references/
│   ├── scoring.md              双评分:AI 味 0–100 ＋ 人味质量 0–50
│   ├── self-audit.md           门检判定 ＋ AI 不敢写测试 ＋ 五问 ＋ 空句检测 ＋ 独立复核
│   ├── examples.md             实战样例(改前/改后 ＋ 打磨报告)
│   └── design-notes.md         集大成清单与同类项目致谢
└── tests/                      回归测试集:17 组 fixtures ＋ baseline/after 快照(并自 qu-ai-wei)
```

## 用之前建议做一件事

打开 [`patterns/style-anchors.md`](patterns/style-anchors.md),贴 1–2 段你自己最满意的真文。阶段 3 会用它做 few-shot,把终稿向你本人的声口对齐,而不是对齐一个通用「人类」。给范文比堆规则有效得多。

---

## English summary

A six-stage **Chinese-language "de-AI" (humanizer) pipeline**, shipped as a Claude Code skill, built as a best-of-both-worlds synthesis of humanizer-class tools (voice profiles, quality-scoring matrix, burstiness, fact-preservation) and qu-ai-wei-class skills (human-vs-AI gate, register ladder, "human edge", an "AI-wouldn't-dare-write-this" test, a five-question final audit, empty-sentence detection, A–I pattern groups).

It rewrites any existing draft into prose that reads like a careful human wrote it, preserving facts and one deliberate human edge. The goal is **not** to beat AI detectors but to make AI-assisted drafts genuinely read as human-written.

Stages: **0** gate / lock facts / set register & voice → **1** read-only diagnose (AI-tell 0–100 + human-quality 0–50) → **2** strip (structure → lexicon → six polish moves → punctuation) → **3** inject human texture → **4** verify (facts first, then AI residue + audits) → **5** dual-scored diff report. Two modes (`detect` / `full`), a scene gate, three intensity tiers, a nine-level register ladder (≤1-grade drift), five voice profiles, and channel-aware presets. Chinese (Simplified) only.

See [`references/design-notes.md`](references/design-notes.md) for the full synthesis list and credits.

## Credits

`patterns/catalog/` 与 `tests/` 直接并入 [qu-ai-wei](https://github.com/LifelongLazyLearner/qu-ai-wei)(MIT,@LifelongLazyLearner),许可与署名见 [CREDITS.md](CREDITS.md)。设计共识另借鉴 humanizer-skill、shuorenhua、Humanizer-zh 等。

## License

本项目 MIT — see [LICENSE](LICENSE)。并入的 qu-ai-wei 内容保留其原始 MIT 许可于 `patterns/catalog/LICENSE.qu-ai-wei`。
