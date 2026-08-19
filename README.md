# Sun* AI Ready Software Development Life Cycle

## 概要

Sun* AI Ready SDLCは、AI（特にClaude）を活用した効率的なソフトウェア開発を実現するためのテンプレート集です。このリポジトリは、モダンなWeb・モバイルアプリケーション開発において、AIとの協働を前提とした開発プロセス、Issue管理、ワークフロー自動化のベストプラクティスを提供します。

## 主な特徴

- **`/setup-project` 立ち上げコマンド**: プロジェクト特性（チーム役割・AI 活用工程・通知・MCP）を対話的にヒアリングし、[takumi](https://takumi.sun-asterisk.ai/ja/docs/) から必要な Agent / Command / Skill / Hook / Rule を自動取得
- **GitHub Issue テンプレート**: Feature Epic、Frontend/Backend 実装、バグレポートなど、開発フェーズごとに最適化されたテンプレート
- **GitHub Workflow テンプレート**: Claude Code 統合、コードレビュー自動化、セキュリティチェックなど

## 必要ツール

| ツール | 用途 | インストール |
|--------|------|------------|
| `claude` CLI | スラッシュコマンドと Skill の実行環境 | [Claude Code 公式](https://docs.claude.com/) |
| `bash` 4.x+ | セットアップスクリプト実行（macOS デフォルトは 3.x） | `brew install bash` |
| `gh` CLI（認証済み） | takumi/anthropics のリポジトリ取得 | `brew install gh` → `gh auth login` |
| `jq` | JSON 生成・パース | `brew install jq` |
| `node` & `npm` | takumi の前提 | [Node.js 公式](https://nodejs.org/) |
| `tkm` CLI | takumi 取得 | `npm install -g @sunasteriskrnd/takumi` |

## セットアップ方法

このテンプレートを使ってプロジェクトを立ち上げる手順です。

### 1. リポジトリをクローン

```bash
gh repo create <your-org>/<your-project> --template sun-asterisk-internal/sun-ai-ready-sdlc --private --clone
cd <your-project>
```

### 2. Claude Code を起動して `/setup-project` を実行

```bash
claude
```

Claude Code の対話画面で：

```
/setup-project
```

`project-setup` Skill が起動し、以下を対話形式でヒアリングします：

- **Q1: チーム役割** — PM / TechLead / Engineer / QA / Designer / DevOps（複数選択可）
- **Q2: AI 活用工程** — 企画ブレスト / 要件定義 / 基本設計 / 詳細設計 / 実装 / 結合テスト / レビュー / デバッグ / デプロイ / ドキュメント作成 / 振り返り / UI/UX デザイン（複数選択可）
- **Q3-1: 通知媒体** — 不要 / Slack / Discord / Telegram
- **Q3-2: 外部 MCP** — momorph / playwright / context7 ほか（自由記述可）
- **Q4: 追加要望** — 「既存コードのスキャン」など、上記で拾えない作業

ヒアリング結果に応じて Skill が以下を自動実行します：

1. `tkm init` で takumi を展開
2. 選択した役割・工程に対応する Agent / Command のみを残してプルーニング
3. Anthropic 公式 `skill-creator` を取得
4. `.mcp.json` と `.claude/settings.local.json` を生成
5. Q4 で必要な Skill が既存に無ければ `skill-creator` で新規作成

### 3. セットアップ後の手動タスク

- **`.mcp.json` の認証情報を編集**：選んだ MCP に応じて token / API key を埋める（GitHub MCP なら `GITHUB_PERSONAL_ACCESS_TOKEN` 等）
- **通知の Webhook URL を設定**：Slack/Discord/Telegram を選んだ場合、`.claude/hooks/notifications/` の README に従って `.env` 等を配置
- **`CLAUDE.md` をプロジェクトに合わせて編集**

> ⚠ `/tkm:init-claude` は **実行しない** でください。これは `tkm init` を再走させるコマンドで、`/setup-project` の prune で削除した takumi 標準ファイルが全て元に戻ります（カスタムファイルしか保護されない）。本コマンドは takumi 自体のアップグレード時に使うものです。

### 4. 立ち上げのやり直し

何か間違えてやり直したい場合：

```bash
bash scripts/setup/rollback.sh   # .claude/ の takumi 由来分と .mcp.json を巻き戻す
```

その後 `/setup-project` を再実行できます。

## 内部構成（開発者向け）

立ち上げコマンドは「スラッシュコマンド + Skill + 裏方スクリプト」のハイブリッド：

```
.claude/commands/setup-project.md     ← スラッシュコマンド入口
.claude/skills/project-setup/
├ SKILL.md                            ← オーケストレーション本体
└ references/
    ├ catalog.md                      ← Agent/Command/MCP/Hook の説明
    ├ hearing.md                      ← Q1〜Q4 の問いかけ方
    └ state-schema.md                 ← .setup-state.json のスキーマ
scripts/setup/
├ check-prereq.sh                     ← 前提検査
├ bootstrap-takumi.sh                 ← tkm init + Skill 退避/復元
├ prune.sh                            ← ホワイトリスト削除
├ fetch-skill-creator.sh              ← anthropics/skills 取得
├ write-configs.sh                    ← .mcp.json / settings.local.json 生成
├ rollback.sh                         ← 失敗時クリーンアップ
└ lib/
    ├ mapping.json                    ← Q→取得物の対応表
    └ mcp-templates.json              ← MCP サーバー定義雛形
```

Skill が会話と判断、scripts が決定論的処理を担当します。
