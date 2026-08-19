---
name: project-setup
description: |
  Sun* AI-Ready SDLC プロジェクトフォルダの立ち上げ。
  プロジェクト特性 (Q1〜Q4) を対話的にヒアリングし、
  takumi から必要な Agent / Command / Skill / Hook / Rule を取得して配置する。
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# project-setup Skill

立ち上げコマンドのオーケストレーション本体。会話と判断はこの Skill が担い、決定論的処理は `scripts/setup/*.sh` を呼び出して任せる。

## 目的

- プロジェクトに必要な takumi の要素 (Agent / Command / Skill / Hook / Rule / MCP) を絞り込み、`.claude/` に配置する
- ユーザーに自然言語でヒアリングし、機械的なフォーム入力体験を避ける
- 失敗時は `rollback.sh` で clean 状態に戻し、原因をユーザーに会話で報告する

## 参照ドキュメント

実行時に必要に応じて読み込む：

- `references/hearing.md` — Q1〜Q4 の問いかけ方・選択肢キー・自然言語パターン
- `references/catalog.md` — Agent / Command / MCP / Hook の名前と「何をしてくれるか」の説明
- `references/state-schema.md` — `.setup-state.json` のスキーマとライフサイクル

## 会話ガイドライン

- **1 質問 1 ターン**で進める。一度に全部投げない
- 選択肢は番号ではなく **キーワードで例示**（`references/hearing.md` の問いかけ例を参考）
- 自然言語の回答を許容する。曖昧な場合は確認質問を返す
- ヒアリング結果は順次 `.setup-state.json` に書き込む（スキーマは `references/state-schema.md`）
- 各スクリプト呼び出し後は終了コードを確認。非ゼロなら即 `bash scripts/setup/rollback.sh` を呼び、stdout/stderr を引用して原因報告

## メインフロー

### Step 1: 起動と既存検知

1. `.setup-state.json` が既に存在する場合は、ユーザーに「前回の続きから / やり直し / 中止」を会話で確認
2. `.claude/` 配下に Skill 自身以外のファイル（takumi 由来）がある、または `.mcp.json` が存在する場合は「これらを `tkm init` の出力で置き換えますが、続行してよいですか？」と確認

### Step 2: 前提チェック

```
bash scripts/setup/check-prereq.sh
```

stdout の JSON（`{"ok": bool, "missing": [...]}`）をパース。`ok=false` なら不足ツールごとに案内：

- `bash>=4` → `brew install bash`（macOS）
- `gh` → `brew install gh`
- `gh-auth` → `gh auth login`
- `jq` → `brew install jq`
- `node`/`npm` → 公式インストーラ案内
- `tkm` → `npm install -g @sunasteriskrnd/takumi`
- `tkm-auth` → `tkm auth login`

ユーザーが解決するまで中断。

### Step 3: ヒアリング (Q1 〜 Q3)

`references/hearing.md` を参照しながら、Q1 → Q2 → Q3-1 → Q3-2 の順に 1 質問 1 ターンで実施。
回答ごとに `.setup-state.json` を更新する（スキーマは `references/state-schema.md`）。

### Step 4: 取得対象の提示 + Q4

`references/catalog.md` と `scripts/setup/lib/mapping.json` を参照し、
現時点の `.setup-state.json` から **取得予定の Agent / Command / MCP / Hook をマークダウン表で提示**する。

**重要**：表は必ず「**名前** と **何をしてくれるか**」をセットにする。タイトル名だけの羅列は禁止。
ユーザーが何が取得されるか直感的に判断できる粒度にする。

提示フォーマット例：

```markdown
## 取得予定の Agents

| 名前 | 何をしてくれるか |
|------|----------------|
| `researcher` | 調査・情報収集を担当。find-skill 経由で必要な Skill を探す |
| `planner` | 要件定義 / 基本設計 / 詳細設計を踏まえた実装計画を作成 |
| `implementer` | TDD サイクル（RED → GREEN → REFACTOR）で実装を進める |
| ... |

## 取得予定の Commands

| コマンド | 何をしてくれるか |
|---------|----------------|
| `/tkm:find-skill` | 既存 Skill から要望に合うものを探す |
| `/tkm:create-plan` | planner を呼んで実装計画を作成 |
| ... |

## 追加 MCP

| 名前 | 何をしてくれるか |
|------|----------------|
| `playwright` | ブラウザ自動化。E2E テスト等 |

## 通知 Hook

| 媒体 | 何をしてくれるか |
|------|----------------|
| Slack | セッション完了通知を Slack に送信 |
```

その後 Q4 を尋ねる：

> 「以上を取得します。ここに記載がない作業で、AI にやらせたい作業はありますか？」

回答（空でも可）を `.setup-state.json` の `q4` に保存する。

### Step 5: 取得実行

順次実行。終了コード非ゼロなら `bash scripts/setup/rollback.sh` を呼んで会話で報告し中断。
**重要**：Q4 解決は prune より前に行う。これにより「Q4 で必要と判明した Agent / Command が prune で削除される」バグを避ける。

#### 5-1. takumi 展開

```
bash scripts/setup/bootstrap-takumi.sh
```

#### 5-2. Q4 事前解決（prune の前）

`.setup-state.json` の `q4` が空でなければ：

1. `.claude/commands/tkm/find-skill.md` の指示に従って、`q4` に対応する既存 Skill / Command / Agent を特定
2. 該当する **名前**（拡張子・パス無しの basename）を `.setup-state.json` の `q4_additions` に書き込む：
   - 例：q4="既存コードのスキャン" → `q4_additions: { "agents": [], "commands": ["scan-codebase"], "skills": ["scan-codebase"] }`
3. find-skill で見つからなかった場合は `q4_additions` を空のまま残し、Step 6 で `skill-creator` で新規作成する

`q4_additions.agents` / `q4_additions.commands` / `q4_additions.skills` は Step 5-3 / 5-4 の prune.sh が読み取り、ホワイトリストに加える。

#### 5-3. プルーニング dry-run と確認

```
bash scripts/setup/prune.sh --state .setup-state.json --dry-run
```

`would-remove:` で始まる行を集めて **削除予定リストをマークダウン表で提示**する。とくに `.claude/skills/` 配下の削除は takumi の実装知識 (SKILL.md) が消える意味合いなので、次のように会話でユーザーに確認する：

> 「以下を削除します。この中に残しておきたいものはありますか？」

- **残したい** ものがあれば、その名前を `.setup-state.json` の `q4_additions.skills` (skill の場合) / `q4_additions.agents` / `q4_additions.commands` に追記してから 5-4 に進む
- **すべて OK** なら 5-4 に進む
- 迷ったら **残す方向** に倒す（false negative < false positive の原則）

#### 5-4. プルーニング本番実行

```
bash scripts/setup/prune.sh --state .setup-state.json
```

`q4_additions` の Agent / Command / Skill も保護される。Skill 側は追加で「生き残る agents / rules が名指ししている skill」も自動保護される（rules と agents の名指し = L2 レベルの静的宣言のみを safety net として採用。skill 内での skill 参照は L4 動的活性化の記述であり誤爆源になるため対象外）。

#### 5-5. skill-creator 取得

```
bash scripts/setup/fetch-skill-creator.sh
```

#### 5-6. 設定ファイル生成

```
bash scripts/setup/write-configs.sh --state .setup-state.json
```

### Step 6: Q4 残作業

`.setup-state.json` の `q4` が非空 **かつ Step 5-2 で `q4_additions` が空**（= find-skill で見つからなかった）の場合のみ：

1. `.claude/skills/skill-creator/SKILL.md` の指示に従って新規 Skill を作成（ユーザーと対話しながら）
2. 作成した Skill 名を `q4_additions.skills` に追記

最後に `.setup-state.json` の `q4_handled` を `true` に更新する。

### Step 7: 完了サマリ

自然言語で要約する：

- 取得した Agent / Command / MCP / Hook の最終一覧（Step 4 と同じ「名前 + 説明」形式）
- セットアップ後の手動タスク：
  - `.mcp.json` の認証情報（PAT / API key 等）を埋める
  - 通知を選んだ場合は webhook URL を `.env` 等に設定（`.claude/hooks/notifications/` の README 参照）
  - プロジェクト固有の `CLAUDE.md` 編集（**[#83](https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/issues/83)** のカスタマイズ Skill 完成後はそちらで対応予定）
- 関連 issue の案内：
  - **[#83](https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/issues/83)**：CLAUDE.md カスタマイズ Skill 作成中
  - **[#84](https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/issues/84)**：`docs/` 雛形拡充予定
  - **[#85](https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/issues/85)**：`.github/` 初期内容拡充予定

**注意**：`/tkm:init-claude` は **絶対に勧めない**。これは `tkm init` を再実行するスラッシュコマンドで、prune で削除した takumi 標準ファイルを全て元に戻してしまう（カスタムファイルしか保護されない）。本コマンドの本来の用途は「takumi 新バージョン公開時のアップグレード」であり、立ち上げ完了直後の案内には不適切。

## エラー時の対応

- スクリプトが exit != 0 を返したら即 `bash scripts/setup/rollback.sh`
- stdout / stderr を会話で引用し、原因を分かりやすく説明
- 修正案を提示（例：`tkm init` 失敗 → 「ネット接続と `tkm` のバージョンを確認の上、再実行してください」）
- 自己判断で setup を「強行」しない。失敗の根本原因を取り除いてから再実行

## 関連ファイル

- `scripts/setup/check-prereq.sh` — 前提検査
- `scripts/setup/bootstrap-takumi.sh` — `tkm init` 実行（Skill 自身は退避→復元）
- `scripts/setup/prune.sh` — Agent/Command のホワイトリスト削除と opt-out 除外
- `scripts/setup/fetch-skill-creator.sh` — anthropics/skills から skill-creator 取得
- `scripts/setup/write-configs.sh` — `.mcp.json` / `.claude/settings.local.json` 生成
- `scripts/setup/rollback.sh` — 失敗時のクリーンアップ
- `scripts/setup/lib/mapping.json` — Q→取得物の対応表
- `scripts/setup/lib/mcp-templates.json` — MCP サーバー定義雛形
