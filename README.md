# human-flavor-pipeline

一条**中文「去 AI 味」六阶段流水线**,以 Claude Code skill 形式提供。把任意草稿(AI 生成、AI 辅助或可疑文本)改成读起来像人认真写的终稿,同时守住事实与一道人味。

它是 polish / transform 管线,不是生成器 —— 只改已有文本,不替你产生观察、采访与判断。

> 设计目标不是骗过 AI 检测器(那是脆弱的军备竞赛),而是让你自己的 AI 辅助稿子**确实读起来像人写的**。检测分下降是结果,不是目的。

---

## 管线一览

```
草稿 ＋ 渠道标记
      │
  0 · 门检 / 锁定      判来源 ＋ 抽取保护区 ＋ 定语体
      │               (人写 → 仅清格式退出)
  1 · 诊断打分(只读)  AI 味 0–100 ＋ 热区 ＋ 选档
      │               (低分 → 跳过 / 轻改)
  2 · 剥离            先结构后词汇 ＋ 标点规整
      │
  3 · 注入人味        长短句节奏 ＋ 风格锚点 ＋ 留毛边
      │
  4 · 校验            事实保真核对 ＋ 复打分(高风险派独立子 agent)
      │               (未达标且档位允许 → 回改 ≤N 遍)
  5 · 报告交付        评分 diff 报告 ＋ 渠道排版
```

全程有一条**保护区**侧轨:数字、人名、引用、报价、代码在阶段 0 锁定,阶段 4 逐项核对,绝不漂移。

## 两种模式

- **detect** —— 只跑阶段 0–1,出 `AI 味分 0–100` ＋ 热区,**一个字都不改**。适合特稿这种「先要体检」的场景。
- **full** —— 跑完整六段,出终稿 ＋ 打磨报告。

用户没指定时,默认先 detect 体检,再问要不要 full。

## 强度档位

| 档位 | AI 味分 | 改动幅度 |
|------|---------|----------|
| 轻 | 0–15 | 仅词汇替换 |
| 中 | 16–35 | bounded 删改,先列候选 |
| 深 | 36–100 | structural 重构 |

## 渠道感知

同一套词典按交付渠道门控:飞书内部 / Notion 对外提案 / 公众号特稿 / 小红书 / 学术,各有不同的语体、标点、人味度。详见 [`patterns/channel-presets.md`](patterns/channel-presets.md)。

## 七条底线原则

1. 检测先于改写
2. 分级 ＋ 语体门控
3. 事实神圣(保护区 ＋ 收尾核对)
4. 保留人味(留毛边,但不伪造)
5. 全程透明(带评分的 diff 报告)
6. 有界迭代(强度档位,不无限催降)
7. 渠道感知

---

## 安装(Claude Code)

把本仓库放进 Claude Code 的 skills 目录即可:

```bash
git clone https://github.com/mjlens-spec/human-flavor-pipeline.git ~/.claude/skills/human-flavor-pipeline
```

然后在对话里说「帮我去 AI 味」「这段太 AI 了改一下」「降 AI 味」,或粘贴文本要求改写,skill 会自动触发;也可显式调用。

## 目录结构

```
human-flavor-pipeline/
├── SKILL.md                    六阶段主流程
├── patterns/
│   ├── banned-words.md         三级禁用词典 ＋ 结构反模式
│   ├── channel-presets.md      渠道预设
│   └── style-anchors.md        风格锚点(few-shot,贴你的真文)
└── references/
    ├── scoring.md              AI 味分 0–100 评分细则
    └── design-notes.md         设计说明与同类项目致谢
```

## 用之前建议做一件事

打开 [`patterns/style-anchors.md`](patterns/style-anchors.md),贴 1–2 段你自己最满意的真文。阶段 3 会用它做 few-shot,把终稿向你本人的声口对齐,而不是对齐一个通用「人类」。给范文比堆规则有效得多。

---

## English summary

A six-stage **Chinese-language "de-AI" (humanizer) pipeline**, shipped as a Claude Code skill. It rewrites any existing draft (AI-generated, AI-assisted, or AI-sounding) into prose that reads like a careful human wrote it, while preserving facts and one deliberate "human edge."

It is a polish/transform pipeline, not a generator. The goal is **not** to beat AI detectors (a fragile arms race) but to make your own AI-assisted drafts genuinely read as human-written.

Stages: **0** gate & lock facts → **1** read-only diagnose & score (0–100) → **2** strip (structure first, then lexicon) → **3** inject human texture → **4** verify (fact-preservation + rescore) → **5** scored diff report & channel formatting. A protected-spans rail (numbers, names, quotes, prices, code) is locked at stage 0 and verified at stage 4.

Two modes: `detect` (read-only checkup) and `full` (rewrite + report). Three intensity tiers scale edits to the score. Channel-aware presets adapt register/punctuation per delivery target (Feishu / Notion / WeChat / Xiaohongshu / academic). Chinese (Simplified) only.

Design synthesizes consensus patterns from well-regarded open-source humanizers (humanizer-skill, shuorenhua, Humanizer-zh, humanize-text, StealthHumanizer, humanizer-de); see [`references/design-notes.md`](references/design-notes.md).

## License

MIT — see [LICENSE](LICENSE).
