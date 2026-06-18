#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

version="$(
  awk '
    BEGIN { in_fm=0 }
    /^---$/ {
      if (in_fm==0) { in_fm=1; next }
      if (in_fm==1) { exit }
    }
    in_fm==1 && $1=="version:" { print $2; exit }
  ' SKILL.md
)"

[ -n "$version" ] || {
  echo "未能从 SKILL.md frontmatter 读取版本号" >&2
  exit 1
}

check_contains() {
  local pattern="$1"
  local file="$2"
  local message="$3"

  if ! rg -q --fixed-strings -- "$pattern" "$file"; then
    echo "$message" >&2
    exit 1
  fi
}

check_contains "version-${version}-blue.svg" README.md "README badge 版本号未同步到 ${version}"
check_contains "当前版本:v${version}" README.md "README 当前版本未同步到 v${version}"
check_contains "## ${version} -" CHANGELOG.md "CHANGELOG.md 缺少 ${version} 版本节"
check_contains "version: ${version}" SKILL.md "SKILL.md 版本号未同步到 ${version}"

precision_count="$(awk 'NF { count++ } END { print count+0 }' tests/fixtures/18-precision-cases.jsonl)"
check_contains "${precision_count} 条 precision 契约" README.md "README precision 契约数未同步到 ${precision_count}"
check_contains "${precision_count} 条 precision 契约" CHANGELOG.md "CHANGELOG precision 契约数未同步到 ${precision_count}"
check_contains "${precision_count} 条精确率契约样本" tests/README.md "tests/README precision 契约数未同步到 ${precision_count}"
check_contains "51 个主编号" README.md "README 规则计数口径未同步"

expected="$(mktemp)"
trap 'rm -f "$expected"' EXIT
{
  cat <<'HEADER'
# human-flavor-pipeline · Codex / AGENTS.md 入口

> 本文件由 `scripts/build-agents.sh` 从 `SKILL.md` 自动生成,请勿手改。
> 改操作规程请改 `SKILL.md`,然后重跑 `bash scripts/build-agents.sh`。
> 这是给 Codex(及任何读取 AGENTS.md 的 agent)的入口;Claude Code 走同源的 `SKILL.md`。
> 数据层 `patterns/` 与 `references/` 由两个工具共享,按需读取。
HEADER
  awk 'NR==1 && $0=="---"{infm=1; next} infm && $0=="---"{infm=0; next} !infm{print}' SKILL.md
} > "$expected"

if ! cmp -s "$expected" AGENTS.md; then
  echo "AGENTS.md 未由当前 SKILL.md 生成" >&2
  exit 1
fi

echo "version sync ok: ${version}"
