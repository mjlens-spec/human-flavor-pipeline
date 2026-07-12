#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
OUTPUT="$ROOT/skills/human-flavor-pipeline"

usage() {
  cat <<'EOF'
用法: bash scripts/build-skill-package.sh [--output <安装目录>]

默认输出到 skills/human-flavor-pipeline。
--output 指定完整的安装目录路径，适合在临时目录中构建和校验。
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      [ "$#" -ge 2 ] || {
        echo "--output 缺少目录参数" >&2
        usage >&2
        exit 2
      }
      OUTPUT="$2"
      shift 2
      ;;
    --output=*)
      OUTPUT="${1#--output=}"
      [ -n "$OUTPUT" ] || {
        echo "--output 目录不能为空" >&2
        exit 2
      }
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

output_parent="$(dirname "$OUTPUT")"
output_name="$(basename "$OUTPUT")"
case "$output_name" in
  ""|/|.|..)
    echo "拒绝使用不安全的输出目录: $OUTPUT" >&2
    exit 2
    ;;
esac

mkdir -p "$output_parent"
output_parent="$(cd "$output_parent" && pwd -P)"
OUTPUT="$output_parent/$output_name"

# 构建会替换已有输出，先拦住仓库本身、仓库祖先目录和仓库内非 skills 路径。
if [ "$OUTPUT" = "/" ] || [ "$OUTPUT" = "$ROOT" ] || [[ "$ROOT" == "$OUTPUT"/* ]]; then
  echo "拒绝覆盖仓库或仓库的祖先目录: $OUTPUT" >&2
  exit 2
fi
if [[ "$OUTPUT" == "$ROOT"/* ]] && [[ "$OUTPUT" != "$ROOT/skills/"* ]]; then
  echo "仓库内输出只允许放在 skills/ 下: $OUTPUT" >&2
  exit 2
fi

required=(SKILL.md patterns references corpus agents/openai.yaml scripts/check-fact-integrity.py tests/check-precision.py tests/check-fact-integrity.py tests/fixtures/18-precision-cases.jsonl tests/fixtures/19-recall-floor.jsonl tests/fixtures/20-fact-integrity-cases.jsonl tests/golden LICENSE)
for entry in "${required[@]}"; do
  [ -e "$ROOT/$entry" ] || {
    echo "缺少打包必需资源: $entry" >&2
    exit 1
  }
done

stage_root="$(mktemp -d "${TMPDIR:-/tmp}/human-flavor-pipeline-package.XXXXXX")"
trap 'rm -rf "$stage_root"' EXIT
package="$stage_root/human-flavor-pipeline"
mkdir -p "$package/agents" "$package/scripts" "$package/tests/fixtures" "$package/tests/golden"

cp "$ROOT/SKILL.md" "$package/SKILL.md"

for directory in patterns references corpus; do
  cp -R "$ROOT/$directory" "$package/$directory"
done

for directory in profiles packs; do
  if [ -e "$ROOT/$directory" ]; then
    cp -R "$ROOT/$directory" "$package/$directory"
  fi
done

cp "$ROOT/agents/openai.yaml" "$package/agents/openai.yaml"
cp "$ROOT/scripts/check-fact-integrity.py" "$package/scripts/check-fact-integrity.py"
cp "$ROOT/tests/check-precision.py" "$package/tests/check-precision.py"
cp "$ROOT/tests/check-fact-integrity.py" "$package/tests/check-fact-integrity.py"
cp "$ROOT/tests/fixtures/18-precision-cases.jsonl" "$package/tests/fixtures/18-precision-cases.jsonl"
cp "$ROOT/tests/fixtures/19-recall-floor.jsonl" "$package/tests/fixtures/19-recall-floor.jsonl"
cp "$ROOT/tests/fixtures/20-fact-integrity-cases.jsonl" "$package/tests/fixtures/20-fact-integrity-cases.jsonl"
for golden_file in README.md cases.jsonl cases.md run_eval.py test_run_eval.py; do
  cp "$ROOT/tests/golden/$golden_file" "$package/tests/golden/$golden_file"
done
cp "$ROOT/LICENSE" "$package/LICENSE"

rm -rf "$OUTPUT"
mv "$package" "$OUTPUT"

echo "skill package built: $OUTPUT"
