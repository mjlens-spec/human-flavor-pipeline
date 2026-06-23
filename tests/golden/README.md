# Golden 模型级评测

`tests/check-precision.py` 测的是**确定性护栏层**(正则 / 词频提示调得准不准:少误报、floor 仍照抓)。它**绿不等于 skill 改得对** —— skill 的执行者是 LLM,按散文层做模糊判断,正则只是提示。

这个目录补的是另一半:**模型级评测**。给定 `before`,让模型按 skill 走一遍 detect + full,再对照 `cases.md` 的 rubric 打分。**不做字符串精确断言**(模型输出逐次会变),而是由人或 LLM-judge 按五维评:

1. **事实保真** —— 数字 / 实体 / 引用 / 报价是否原样(硬条件,违反即不及格)
2. **召回** —— 该去的 AI 味 / 江湖气 / floor slop 去了没
3. **精度** —— 该留的(合法术语、乙方 deck 结构、正常对比)留住没,有没有过度净化
4. **声口** —— 有个人锚点时是否对齐了作者文风;口播稿是否可被自然说出来,而不是被洗成书面稿
5. **诚实** —— 没有为「显得有人味」而制造假坦诚 / 伪洞察 / 戏剧短句

## 怎么跑

人工:把 `cases.md` 每条 `before` 贴给装好本 skill 的 Claude Code / Codex,要 detect 再要 full,拿输出对 rubric。
半自动:用一个 LLM-judge agent,输入(before, after, rubric),输出五维评分 + 是否及格。

每次大改 skill 后至少过一遍 golden;护栏测试(precision)在 CI / commit 前跑,golden 评测在版本发布前跑。
