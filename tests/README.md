# tests/

回归样本与可执行检查。当前包含 17 组改写快照、29 条精确率契约样本、召回 floor、20 条事实硬闸样本、10 条结构化 Golden 用例和安装包检查。

## 样本

- `fixtures/01-03`:通用概述、公众号伪深度、小红书模板。
- `fixtures/04`:抽象否定对举,要求回落到原文已有事实。
- `fixtures/05`:低改写必要性的口语叙事,门检应停手。
- `fixtures/06`:品牌文案,保护短句、排比与英文专名。
- `fixtures/07`:学术 / 科技白名单。技术中英混排、`进行`、`然而`均有功能,应判低必要性,不得出现「无强命中但强制判 AI」的矛盾。
- `fixtures/08-12`:咨询黑话、小红书疗愈、B 站解说、否定堆叠、表格滥用。
- `fixtures/13-17`:小红书探店、穿搭、办公、护肤、家居。#47b 占位符只算工作流风险,不得证明作者身份;技术名与护肤成分受保护。
- `fixtures/18-precision-cases.jsonl`:18 个反误杀样本 + 11 个正向控制。6 类新增 slop 均有相邻负样本;其余覆盖合法破折号、技术中英混排、公开信泛称、人工模板占位符、Markdown 载体 / 链接差异、正式枚举与准确业务术语。
- `fixtures/20-fact-integrity-cases.jsonl`:数字、金额、日期、版本、引语、代码、占位符 missing / changed / added 硬闸及相邻反例。
- `golden/`:结构化模型行为评测,覆盖客户方案、公众号、低必要性稿、口播、达人脚本、新增事实和结构误杀;支持盲化 A/B 数据准备与结果汇总。

`baseline/` 是合并前的历史快照;`after/` 是当前行为快照。历史正文可能提到旧版规则,但每份当前快照的 `【门检】` 行必须使用「改写必要性低 / 中 / 高」,不得断言「AI 生成文本 / 真人文本」。

## 自动检查

```bash
bash tests/check-version-sync.sh
bash tests/check-snapshot-smoke.sh
python3 tests/check-precision.py
python3 tests/check-fact-integrity.py --fixtures
python3 tests/golden/run_eval.py validate
python3 -m unittest tests/golden/test_run_eval.py
bash tests/check-skill-package.sh
```

- `check-version-sync.sh`:从 `SKILL.md` frontmatter 读取版本,检查 README、CHANGELOG 与生成后的 AGENTS.md。不存在的可选入口不参与检查。
- `check-snapshot-smoke.sh`:检查快照结构、门检语义、事实保护和各 fixture 的关键边界。
- `check-precision.py`:从 `patterns/precision-rules.json` 加载 production 阈值、上下文与例外,并校验操作层 / 深查层文档锚点。它不是作者身份检测器。
- `check-fact-integrity.py`:运行时事实硬闸的测试入口;普通 transform 中 missing / changed / added 任一出现即失败。
- `golden/run_eval.py`:校验用例、生成随机盲化 A/B judge packets、汇总 win / tie / loss 与事实硬失败率。
- `check-skill-package.sh`:在临时目录构建完整安装包,检查资源引用并运行官方 quick validate。

## 判据

1. 门检只判断改写必要性,不猜作者身份。
2. A-H 表达模式、I 风险、J 风格偏好分轴记录。
3. 终稿保留原文数字、实体、引语、技术名和占位符;未给出的事实不得补写,标「待核实」也不能放行。
4. 合法结构按文体保护:品牌排比、技术英语、正式枚举、业务术语、功能性破折号均不误杀。
5. 新增规则必须同时提供正向控制与至少一个相邻负样本。
