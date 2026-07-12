#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/human-flavor-pipeline-check.XXXXXX")"
trap 'rm -rf "$temp_root"' EXIT

package="$temp_root/output with spaces/human-flavor-pipeline"
bash "$ROOT/scripts/build-skill-package.sh" --output "$package"

required=(SKILL.md patterns references corpus agents/openai.yaml LICENSE)
for entry in "${required[@]}"; do
  [ -e "$package/$entry" ] || {
    echo "安装包缺少必需资源: $entry" >&2
    exit 1
  }
done

for directory in profiles packs; do
  if [ -e "$ROOT/$directory" ]; then
    [ -e "$package/$directory" ] || {
      echo "安装包漏掉可选资源目录: $directory" >&2
      exit 1
    }
  elif [ -e "$package/$directory" ]; then
    echo "安装包出现源仓库不存在的目录: $directory" >&2
    exit 1
  fi
done

expected_top_level=$'LICENSE\nSKILL.md\nagents\ncorpus\npatterns\nreferences'
for directory in packs profiles; do
  [ -e "$ROOT/$directory" ] && expected_top_level="${expected_top_level}"$'\n'"$directory"
done
actual_top_level="$(find "$package" -mindepth 1 -maxdepth 1 -exec basename {} \; | LC_ALL=C sort)"
expected_top_level="$(printf '%s\n' "$expected_top_level" | LC_ALL=C sort)"
if [ "$actual_top_level" != "$expected_top_level" ]; then
  echo "安装包顶层内容不符合预期" >&2
  diff -u <(printf '%s\n' "$expected_top_level") <(printf '%s\n' "$actual_top_level") >&2 || true
  exit 1
fi

for directory in patterns references corpus profiles packs; do
  if [ -e "$ROOT/$directory" ] && ! diff -qr "$ROOT/$directory" "$package/$directory"; then
    echo "安装包资源与源目录不一致: $directory" >&2
    exit 1
  fi
done
cmp "$ROOT/agents/openai.yaml" "$package/agents/openai.yaml"
cmp "$ROOT/LICENSE" "$package/LICENSE"

python3 - "$ROOT/SKILL.md" "$package/SKILL.md" <<'PY'
from pathlib import Path
import re
import sys

source_path = Path(sys.argv[1])
package_path = Path(sys.argv[2])
source = source_path.read_text(encoding="utf-8")
packaged = package_path.read_text(encoding="utf-8")

if packaged != source:
    raise SystemExit("安装包 SKILL.md 与源文件不一致")

frontmatter = packaged.split("---", 2)[1]
if re.search(r"(?m)^version:", frontmatter):
    raise SystemExit("安装包 SKILL.md 含官方校验不接受的顶层 version 字段")
if not re.search(r"(?m)^metadata:\s*\n(?:[ \t]+.*\n)*?[ \t]+version:\s*\S+", frontmatter):
    raise SystemExit("安装包 SKILL.md 缺少 metadata.version")

resource_pattern = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:patterns|references|corpus|profiles|packs)/[A-Za-z0-9_./*-]+)"
)
references = sorted(set(resource_pattern.findall(packaged)))
if not references:
    raise SystemExit("未从安装包 SKILL.md 识别到任何资源引用")

missing = []
for reference in references:
    target = package_path.parent / reference
    if "*" in reference:
        if not list(package_path.parent.glob(reference)):
            missing.append(reference)
    elif not target.exists():
        missing.append(reference)

if missing:
    raise SystemExit("SKILL.md 引用资源不存在: " + ", ".join(missing))

print(f"skill resource references ok: {len(references)} references")
PY

quick_validate="${QUICK_VALIDATE:-}"
if [ -n "$quick_validate" ]; then
  [ -f "$quick_validate" ] || {
    echo "QUICK_VALIDATE 指向的脚本不存在: $quick_validate" >&2
    exit 1
  }
else
  candidates=(
    "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
    "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
  )
  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate" ]; then
      quick_validate="$candidate"
      break
    fi
  done
fi

if [ -n "$quick_validate" ]; then
  echo "running official quick_validate: $quick_validate"
  python3 "$quick_validate" "$package"
else
  echo "提示: 未找到官方 quick_validate.py，已跳过官方校验。可设置 QUICK_VALIDATE=/path/to/quick_validate.py 后重跑。"
fi

echo "skill package check ok"
