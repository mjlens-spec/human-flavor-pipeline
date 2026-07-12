# Golden 模型级评测

`tests/check-precision.py` 测的是**确定性护栏层**(正则 / 词频提示调得准不准:少误报、floor 仍照抓)。它**绿不等于 skill 改得对** —— skill 的执行者是 LLM,按散文层做模糊判断,正则只是提示。

这个目录补的是另一半:**模型级评测**。`cases.jsonl` 是结构化用例真相源;给定 `before`,让当前 main 与候选版本分别执行目标模式,先过事实硬闸,再做随机盲化 A/B。**不做字符串精确断言**,由人或独立 LLM judge 比较:

1. **事实保真** —— 数字 / 实体 / 引用 / 报价是否原样(硬条件,违反即不及格)
2. **召回** —— 该去的 AI 味 / 江湖气 / floor slop 去了没
3. **精度** —— 该留的(合法术语、乙方 deck 结构、正常对比)留住没,有没有过度净化
4. **笔调** —— 有个人锚点时是否对齐了作者文风;口播稿是否可被自然说出来,而不是被洗成书面稿
5. **诚实** —— 没有为「显得有人味」而制造假坦诚 / 伪洞察 / 戏剧短句

## 怎么跑

```bash
# 校验结构化用例
python3 tests/golden/run_eval.py validate

# 查看 prepare / report 参数
python3 tests/golden/run_eval.py prepare --help
python3 tests/golden/run_eval.py report --help

# runner 自测
python3 -m unittest tests/golden/test_run_eval.py
```

先分别保存 main 和 candidate 对同一 case 的输出,再用 `prepare` 随机化 A/B 并单独保存答案密钥。judge 不得看到版本标签;`report` 汇总 candidate win / baseline win / tie、硬失败率和不可接受结果。

每次大改 Skill 后至少过一遍 Golden。事实硬失败率优先于风格胜率;事实失败的输出不得因「更自然」而获胜。`cases.md` 仅保留人类可读说明,`cases.jsonl` 才供 runner 使用。
