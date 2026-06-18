#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: install-skills-codex.sh [--dry-run] [--codex-skills-dir DIR]

Installs the Asterinas debugger skills into Codex.
EOF
}

dry_run=false
codex_skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"

while (($#)); do
    case "$1" in
        --dry-run)
            dry_run=true
            shift
            ;;
        --codex-skills-dir)
            codex_skills_dir="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$repo_root/skills"

install_skill() {
    local skill_dir="$1"
    local skill_name
    skill_name="$(basename "$skill_dir")"
    local target_dir="$codex_skills_dir/$skill_name"

    echo "install $skill_name -> $target_dir"
    if [[ "$dry_run" == true ]]; then
        return
    fi

    rm -rf "$target_dir"
    mkdir -p "$target_dir"
    cp -a "$skill_dir/." "$target_dir/"
}

if [[ ! -d "$source_dir" ]]; then
    echo "missing skills directory: $source_dir" >&2
    exit 1
fi

if [[ "$dry_run" == false ]]; then
    mkdir -p "$codex_skills_dir"
fi

for skill_dir in "$source_dir"/*; do
    [[ -d "$skill_dir" ]] || continue
    install_skill "$skill_dir"
done
