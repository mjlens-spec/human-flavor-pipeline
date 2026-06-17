#!/usr/bin/env bash
# 从 SKILL.md 生成 AGENTS.md(Codex 入口)。
# SKILL.md 是唯一事实来源:去掉其顶部 YAML frontmatter(Claude Code 的路由元数据),
# 换上 Codex 头,正文与数据层引用原样保留。改规程改 SKILL.md 再重跑本脚本。
set -euo pipefail
cd "$(dirname "$0")/.."

{
  cat <<'HEADER'
# human-flavor-pipeline · Codex / AGENTS.md 入口

> 本文件由 `scripts/build-agents.sh` 从 `SKILL.md` 自动生成,请勿手改。
> 改操作规程请改 `SKILL.md`,然后重跑 `bash scripts/build-agents.sh`。
> 这是给 Codex(及任何读取 AGENTS.md 的 agent)的入口;Claude Code 走同源的 `SKILL.md`。
> 数据层 `patterns/` 与 `references/` 由两个工具共享,按需读取。
HEADER
  # 跳过第一段 YAML frontmatter(首行 --- 到下一个 --- 之间),其余原样输出(含正文里的 --- 分隔线)
  awk 'NR==1 && $0=="---"{infm=1; next} infm && $0=="---"{infm=0; next} !infm{print}' SKILL.md
} > AGENTS.md

echo "已生成 AGENTS.md (来源 SKILL.md)"
