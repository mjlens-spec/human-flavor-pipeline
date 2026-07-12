# human-flavor-pipeline · 仓库维护说明

本仓库开发同名中文编辑 Skill。Claude Code 与 Codex 的运行时入口均为 `SKILL.md`;根目录 `AGENTS.md` 只负责仓库维护,不再复制完整改写规程。

## 工作规则

- 修改运行规程时改根目录 `SKILL.md` 及其直接引用的 `patterns/`、`references/`、`profiles/`、`packs/`。
- `skills/human-flavor-pipeline/` 是生成的可安装目录,不要手改;运行 `bash scripts/build-skill-package.sh` 重建。
- 只有在处理中文稿件去味任务时才读取完整 `SKILL.md`;版本维护、测试和仓库审计不预加载整套写作规则。
- 保留用户已有改动和未跟踪文件,不要覆盖无关内容。
- 提交前运行:
  - `bash tests/check-version-sync.sh`
  - `bash tests/check-snapshot-smoke.sh`
  - `python3 tests/check-precision.py`
  - `python3 tests/check-fact-integrity.py --fixtures`
  - `python3 tests/golden/run_eval.py validate`
  - `python3 -m unittest tests/golden/test_run_eval.py`
  - `bash tests/check-skill-package.sh`
