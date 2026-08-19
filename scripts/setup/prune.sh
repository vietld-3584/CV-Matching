#!/usr/bin/env bash
# .setup-state.json と mapping.json を元に Agent/Command/Skill をホワイトリスト方式で削除し、
# Q3-1/Q3-2 の選択に応じて hooks/notifications・momorph 関連を除外する。
#
# 使い方: prune.sh --state <path-to-setup-state.json> [--dry-run]
#   --dry-run: 削除せず、削除予定のパスを "would-remove: <path>" 形式で stdout に出力する。
# 削除したパスは 1 行 1 件で stdout に出力する。

set -euo pipefail

state_path=""
dry_run=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --state) state_path="${2:-}"; shift 2 ;;
        --dry-run) dry_run=1; shift ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "$state_path" || ! -f "$state_path" ]]; then
    echo "state file not found: ${state_path:-<empty>}" >&2
    exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mapping_path="$script_dir/lib/mapping.json"

if [[ ! -f "$mapping_path" ]]; then
    echo "mapping file not found: $mapping_path" >&2
    exit 2
fi

remove_path() {
    local p="$1"
    [[ -e "$p" ]] || return 0
    if [[ -n "$dry_run" ]]; then
        echo "would-remove: $p"
    else
        rm -rf "$p"
        echo "$p"
    fi
}

# Agent / Command / Skill ホワイトリスト構築
# Q4 で要求された追加分 (state.q4_additions.{agents,commands,skills}) も含める。
# これにより「Q4 で必要と判明したのに prune で削除される」バグを防ぐ。
build_whitelist() {
    local kind="$1"  # "agents" | "commands" | "skills"

    # always_get
    jq -r ".always_get.${kind} // [] | .[]" "$mapping_path"

    # role_to_*
    while IFS= read -r role; do
        [[ -z "$role" ]] && continue
        jq -r --arg r "$role" ".role_to_${kind}[\$r] // [] | .[]" "$mapping_path"
    done < <(jq -r '.roles // [] | .[]' "$state_path")

    # process_to_*
    while IFS= read -r proc; do
        [[ -z "$proc" ]] && continue
        jq -r --arg p "$proc" ".process_to_${kind}[\$p] // [] | .[]" "$mapping_path"
    done < <(jq -r '.processes // [] | .[]' "$state_path")

    # q4_additions: Step 5 で Skill が Q4 を解決して書き込んだ追加分
    jq -r ".q4_additions.${kind} // [] | .[]" "$state_path"
}

agent_whitelist="$(build_whitelist agents | sort -u)"
command_whitelist="$(build_whitelist commands | sort -u)"
skill_whitelist_initial="$(build_whitelist skills | sort -u)"

in_list() {
    local needle="$1" list="$2"
    printf '%s\n' "$list" | grep -Fxq "$needle"
}

prune_dir() {
    local dir="$1" whitelist="$2"
    [[ -d "$dir" ]] || return 0
    if [[ -z "$whitelist" ]]; then
        echo "prune.sh: whitelist for $dir is empty; skipping to avoid wiping the directory." >&2
        return 0
    fi
    local file basename name
    for file in "$dir"/*.md; do
        [[ -e "$file" ]] || continue
        basename="${file##*/}"
        name="${basename%.md}"
        if ! in_list "$name" "$whitelist"; then
            remove_path "$file"
        fi
    done
}

# Skills は「ディレクトリ単位」で判定する。
# always_keep_paths のうち .claude/skills/ 直下のエントリを whitelist に追加し、
# 参照スキャン (BFS) で生き残る skills / agents / rules から名指しされている skill も保護する。
# 動的活性化 (L4) は静的に拾えないが、名指し参照 (L3) はここで救う。
prune_skills_dir() {
    local dir=".claude/skills"
    [[ -d "$dir" ]] || return 0
    if [[ -z "$skill_whitelist_initial" ]]; then
        echo "prune.sh: whitelist for $dir is empty; skipping to avoid wiping the directory." >&2
        return 0
    fi

    # 1) always_keep_paths のうち $dir/ 直下配下のエントリを追加
    local keep_from_always
    keep_from_always="$(
        jq -r '.always_keep_paths // [] | .[]' "$mapping_path" \
            | awk -v d="$dir/" 'index($0, d)==1 { rest=substr($0, length(d)+1); sub(/\/.*/,"",rest); print rest }'
    )"
    local combined
    combined="$(printf '%s\n%s\n_shared\ncommon\n' "$skill_whitelist_initial" "$keep_from_always" | sort -u | sed '/^$/d')"

    # 2) 候補スキル (実在ディレクトリ) を列挙
    local all_candidates=()
    local sub name
    for sub in "$dir"/*/; do
        [[ -d "$sub" ]] || continue
        name="${sub%/}"; name="${name##*/}"
        all_candidates+=("$name")
    done

    # 3) 単発参照スキャン: rules と生き残る agents から名指しされる skill を保護する。
    #    原設計メモの依存レベル分類に沿い、
    #    - L2 (Rules / Agent 本文の Agent/Skill 名指し) は静的シグナルとして採用
    #    - L4 (skill 内での skill 参照) は動的活性化の記述であり、拾うと誤爆源になる (help/bootstrap/takumi
    #      など複数の skill が SKILL.md 内でカタログ的に他 skill を列挙するため) → スキャン対象から除外
    #    このため BFS 不動点収束ではなく単発スキャンで十分。
    local search_files=()
    if [[ -d ".claude/rules" ]]; then
        while IFS= read -r f; do search_files+=("$f"); done < <(find .claude/rules -type f -name '*.md' 2>/dev/null)
    fi
    while IFS= read -r a; do
        [[ -z "$a" ]] && continue
        [[ -f ".claude/agents/$a.md" ]] && search_files+=(".claude/agents/$a.md")
    done <<< "$agent_whitelist"

    if [[ ${#search_files[@]} -gt 0 ]]; then
        local added=""
        local cand
        for cand in "${all_candidates[@]}"; do
            if in_list "$cand" "$combined"; then continue; fi
            if grep -qwF "$cand" "${search_files[@]}" 2>/dev/null; then
                added+="$cand"$'\n'
            fi
        done
        if [[ -n "$added" ]]; then
            combined="$(printf '%s\n%s' "$combined" "$added" | sort -u | sed '/^$/d')"
        fi
    fi

    # 4) whitelist 外を削除
    for sub in "$dir"/*/; do
        [[ -d "$sub" ]] || continue
        name="${sub%/}"; name="${name##*/}"
        if ! in_list "$name" "$combined"; then
            remove_path "$sub"
        fi
    done
}

# Agent / Command / Skill プルーニング
prune_dir ".claude/agents" "$agent_whitelist"
prune_dir ".claude/commands/tkm" "$command_whitelist"
prune_skills_dir

# 常時除外
while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    remove_path "$path"
done < <(jq -r '.always_remove_paths // [] | .[]' "$mapping_path")

# Q3-1: 通知なしなら notifications を削除
notify="$(jq -r '.notify // "none"' "$state_path")"
if [[ "$notify" == "none" ]]; then
    while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        remove_path "$path"
    done < <(jq -r '.remove_when_unselected.notifications_none // [] | .[]' "$mapping_path")
fi

# Q3-2: momorph 未選択なら momorph 関連を削除
has_momorph="$(jq -r '(.mcp.predefined // []) | index("momorph") | if . == null then "no" else "yes" end' "$state_path")"
if [[ "$has_momorph" == "no" ]]; then
    while IFS= read -r path; do
        [[ -z "$path" ]] && continue
        remove_path "$path"
    done < <(jq -r '.remove_when_unselected.momorph // [] | .[]' "$mapping_path")
fi
