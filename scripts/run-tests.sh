#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"

if [[ -f "$validator" ]]; then
    for skill_dir in "$repo_root"/skills/*; do
        [[ -d "$skill_dir" ]] || continue
        python3 "$validator" "$skill_dir"
    done
else
    echo "warning: skill validator not found: $validator" >&2
fi

python3 -m unittest discover -s "$repo_root/tests"
