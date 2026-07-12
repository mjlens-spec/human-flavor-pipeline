#!/usr/bin/env bash
# 生成仓库级薄 AGENTS.md。Codex 与 Claude Code 的运行时 Skill 都消费
# 同一个 SKILL.md;AGENTS.md 只约束本仓库的维护流程,不复制完整 Skill 正文。
set -euo pipefail
cd "$(dirname "$0")/.."

render() {
  cat <<'EOF'
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
  - `python3 tests/check-fact-integrity.py --self-test`
  - `bash tests/check-skill-package.sh`
EOF
}

if [[ "${1:-}" == "--check" ]]; then
  expected="$(mktemp)"
  trap 'rm -f "$expected"' EXIT
  render > "$expected"
  cmp -s "$expected" AGENTS.md || {
    echo "AGENTS.md 未由当前 scripts/build-agents.sh 生成" >&2
    exit 1
  }
  echo "AGENTS.md sync ok"
else
  render > AGENTS.md
  echo "已生成薄 AGENTS.md (仓库维护入口)"
fi
