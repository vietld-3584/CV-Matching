#!/usr/bin/env bash
# .setup-state.json と mcp-templates.json を元に
# .mcp.json と .claude/settings.local.json を生成する。
# 既存ファイルがあれば <file>.bak に退避する。
#
# 使い方: write-configs.sh --state <path-to-setup-state.json>

set -euo pipefail

state_path=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --state) state_path="${2:-}"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$state_path" || ! -f "$state_path" ]]; then
    echo "state file not found: ${state_path:-<empty>}" >&2
    exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mcp_templates="$script_dir/lib/mcp-templates.json"

backup_if_exists() {
    local file="$1"
    # 既存 .bak は上書きしない（初回の状態を保持して再実行安全に）
    if [[ -f "$file" && ! -f "${file}.bak" ]]; then
        cp "$file" "${file}.bak"
    fi
}

# ----- .mcp.json -----
generate_mcp_json() {
    local out=".mcp.json"
    backup_if_exists "$out"

    # predefined: name の配列。templates から定義を引く。
    # custom: {name, command, args, env, type} の配列。
    jq -n \
        --slurpfile state "$state_path" \
        --slurpfile tpl "$mcp_templates" \
        '
        ($state[0].mcp.predefined // []) as $pre
        | ($state[0].mcp.custom // []) as $cus
        | ($tpl[0].servers // {}) as $servers
        | reduce $pre[] as $name ({}; .[$name] = ($servers[$name] // {"command": "", "args": [], "note": "template not found, please fill in manually"}))
        | reduce $cus[] as $c (.; .[$c.name] = ($c | del(.name)))
        | {"mcpServers": .}
        ' > "$out"
    echo "wrote: $out"
}

# ----- .claude/settings.local.json -----
generate_settings_local() {
    local notify
    notify="$(jq -r '.notify // "none"' "$state_path")"

    if [[ "$notify" == "none" ]]; then
        return 0
    fi

    local out=".claude/settings.local.json"
    mkdir -p "$(dirname "$out")"
    backup_if_exists "$out"

    # 既存があれば読み込んで hooks をマージ。無ければ新規。
    local existing="{}"
    if [[ -f "${out}.bak" ]]; then
        existing="$(cat "${out}.bak")"
    fi

    printf '%s' "$existing" | jq \
        --arg channel "$notify" \
        '
        .hooks //= {}
        | .hooks.SessionStop = [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/notifications/notify.cjs"}]}]
        | .hooks.Stop = [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/notifications/notify.cjs"}]}]
        | .notifications = {"channel": $channel}
        ' > "$out"
    echo "wrote: $out"
}

generate_mcp_json
generate_settings_local
