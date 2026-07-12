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
check_contains "version: ${version}" SKILL.md "SKILL.md metadata.version 未同步到 ${version}"
check_contains "版本:${version}" SKILL-lite.md "SKILL-lite.md 版本号未同步到 ${version}"

precision_count="$(awk 'NF { count++ } END { print count+0 }' tests/fixtures/18-precision-cases.jsonl)"
check_contains "${precision_count} 条 precision 契约" README.md "README precision 契约数未同步到 ${precision_count}"
check_contains "${precision_count} 条 precision 契约" CHANGELOG.md "CHANGELOG precision 契约数未同步到 ${precision_count}"
check_contains "${precision_count} 条精确率契约样本" tests/README.md "tests/README precision 契约数未同步到 ${precision_count}"
check_contains "51 个主编号" README.md "README 规则计数口径未同步"

bash scripts/build-agents.sh --check

echo "version sync ok: ${version}"
