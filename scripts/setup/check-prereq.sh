#!/usr/bin/env bash
# 前提ツールの存在確認。結果を JSON で stdout に出力する。
# 終了コード: 0 = 全て OK / 1 = 不足あり

set -uo pipefail

missing=()

check_cmd() {
    local name="$1"
    if ! command -v "$name" >/dev/null 2>&1; then
        missing+=("$name")
    fi
}

check_bash_version() {
    local major
    major="${BASH_VERSINFO[0]:-0}"
    if [[ "$major" -lt 4 ]]; then
        missing+=("bash>=4 (current: $BASH_VERSION)")
    fi
}

check_gh_auth() {
    if command -v gh >/dev/null 2>&1; then
        if ! gh auth status >/dev/null 2>&1; then
            missing+=("gh-auth (run: gh auth login)")
        fi
    fi
}

check_tkm_auth() {
    if command -v tkm >/dev/null 2>&1; then
        # tkm 0.8.1 は `auth status` を未ログインでも exit 0 で返し、
        # 標準出力に "Not logged in." を印字する。出力文字列で判定する。
        local out
        out="$(tkm auth status 2>&1 || true)"
        if printf '%s' "$out" | grep -qi "not logged in\|not signed in"; then
            missing+=("tkm-auth (run: tkm auth login)")
        fi
    fi
}

check_bash_version
check_cmd bash
check_cmd gh
check_cmd jq
check_cmd node
check_cmd npm
check_cmd tkm
check_gh_auth
check_tkm_auth

if [[ ${#missing[@]} -eq 0 ]]; then
    printf '{"ok":true,"missing":[]}\n'
    exit 0
else
    printf '{"ok":false,"missing":['
    for i in "${!missing[@]}"; do
        [[ $i -gt 0 ]] && printf ','
        printf '"%s"' "${missing[$i]//\"/\\\"}"
    done
    printf ']}\n'
    exit 1
fi
