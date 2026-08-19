#!/usr/bin/env bash
# anthropics/skills の tarball から skill-creator を取得し
# .claude/skills/skill-creator/ に配置する。LICENSE も同梱。
# 取得した SHA を最終行に stdout で報告する。

set -euo pipefail

dest=".claude/skills/skill-creator"
license_dest="$dest/LICENSE"

tmpdir="$(mktemp -d -t skill-creator-fetch.XXXXXX)"
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

tarball="$tmpdir/skills.tar.gz"
gh api repos/anthropics/skills/tarball/HEAD > "$tarball"
tar -xzf "$tarball" -C "$tmpdir"

# ルート抽出 (<owner>-<repo>-<sha>/)
root="$(find "$tmpdir" -mindepth 1 -maxdepth 1 -type d ! -name 'tmp*' | head -n 1)"
if [[ -z "$root" || ! -d "$root/skills/skill-creator" ]]; then
    echo "skill-creator not found in tarball" >&2
    exit 1
fi

rm -rf "$dest"
mkdir -p "$(dirname "$dest")"
cp -R "$root/skills/skill-creator" "$dest"

if [[ -f "$root/LICENSE" ]]; then
    cp "$root/LICENSE" "$license_dest"
fi

sha="$(basename "$root" | sed -E 's/^.+-([0-9a-f]+)$/\1/')"
echo "fetched: $dest"
echo "sha: $sha"
