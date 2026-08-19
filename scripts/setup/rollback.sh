#!/usr/bin/env bash
# setup プロセス失敗時のロールバック。
# .claude/ と中間ファイルを削除し、.bak が残っていれば復元する。
# Skill から呼ばれることを想定（人手実行も可）。

set -uo pipefail

removed=()
restored=()

remove_if_exists() {
    local path="$1"
    if [[ -e "$path" ]]; then
        rm -rf "$path"
        removed+=("$path")
    fi
}

restore_if_bak() {
    local file="$1"
    if [[ -f "${file}.bak" ]]; then
        mv "${file}.bak" "$file"
        restored+=("$file")
    fi
}

# .claude/ と中間ファイル削除（ただし Skill 自身は保護されているため bootstrap 側で復元済み想定）
remove_if_exists ".claude/agents"
remove_if_exists ".claude/hooks"
remove_if_exists ".claude/rules"
remove_if_exists ".claude/schemas"
remove_if_exists ".claude/session-state"
remove_if_exists ".claude/templates"
remove_if_exists ".claude/output-styles"
remove_if_exists ".claude/commands/tkm"
remove_if_exists ".claude/metadata.json"
remove_if_exists ".claude/settings.json"
remove_if_exists ".claude/statusline.cjs"
remove_if_exists ".claude/.sk.json"
remove_if_exists ".claude/.takumi.json"
remove_if_exists ".repomixignore"
remove_if_exists "release-manifest.json"
remove_if_exists ".setup-state.json"

# skills/ は project-setup 以外を削除
if [[ -d ".claude/skills" ]]; then
    for d in .claude/skills/*; do
        [[ -e "$d" ]] || continue
        if [[ "$(basename "$d")" != "project-setup" ]]; then
            rm -rf "$d"
            removed+=("$d")
        fi
    done
fi

# .bak からの復元
restore_if_bak ".mcp.json"
restore_if_bak ".claude/settings.local.json"

echo "removed:"
printf '  %s\n' "${removed[@]:-(none)}"
echo "restored:"
printf '  %s\n' "${restored[@]:-(none)}"
