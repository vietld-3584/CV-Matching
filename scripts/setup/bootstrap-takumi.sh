#!/usr/bin/env bash
# Skill 自身を退避してから `tkm init` を実行し、終了後に退避ファイルを復元する。
# tkm の非対話フラグは help を覗いて判定。無ければ `yes |` でフォールバック。
# 終了コード: tkm init の戻り値（成功時は 0）

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
SKILL_PATH=".claude/skills/project-setup"
COMMAND_PATH=".claude/commands/setup-project.md"

cd "$PROJECT_ROOT"

stage_dir=""
restore_on_exit() {
    if [[ -n "$stage_dir" && -d "$stage_dir" ]]; then
        if [[ -d "$stage_dir/skill" ]]; then
            mkdir -p "$(dirname "$SKILL_PATH")"
            rm -rf "$SKILL_PATH"
            mv "$stage_dir/skill" "$SKILL_PATH"
        fi
        if [[ -f "$stage_dir/command.md" ]]; then
            mkdir -p "$(dirname "$COMMAND_PATH")"
            mv "$stage_dir/command.md" "$COMMAND_PATH"
        fi
        rmdir "$stage_dir" 2>/dev/null || true
    fi
}
trap restore_on_exit EXIT

stage_dir="$(mktemp -d -t setup-project-staging.XXXXXX)"
if [[ -d "$SKILL_PATH" ]]; then
    mv "$SKILL_PATH" "$stage_dir/skill"
fi
if [[ -f "$COMMAND_PATH" ]]; then
    mv "$COMMAND_PATH" "$stage_dir/command.md"
fi

# takumi は非対話モード時に `--yes` と `--kit` の両方が必須（tkm 0.8.1 以降）。
# `--yes` で「最新リリース使用」に暗黙同意、`--kit core` で core kit を明示指定。
tkm init --yes --kit core
