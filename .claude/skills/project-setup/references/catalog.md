# 取得物カタログ

Step 4「取得対象の提示」で表示する Agent / Command / MCP / Hook の名称と説明。
Skill はここを参照して、`.setup-state.json` の選択結果に対応するエントリを抜き出し、
**「名前 / 何をしてくれるか」をセットにしたマークダウン表**として提示する。

## Agents

| 名前 | 何をしてくれるか |
|------|----------------|
| `researcher` | 調査・情報収集を担当。`find-skill` 経由で必要な Skill を探す |
| `git-manager` | git 操作（branch / commit / PR 作成等）を担当 |
| `mcp-manager` | MCP サーバーの管理（追加・削除・接続確認）を担当 |
| `project-manager` | PM 役割の支援。スケジュール管理・チーム調整・振り返り運営 |
| `brainstormer` | アイデア発散・初期検討。企画段階の壁打ち相手 |
| `planner` | 要件定義 / 基本設計 / 詳細設計を踏まえた実装計画を作成 |
| `implementer` | TDD サイクル（RED → GREEN → REFACTOR）で実装を進める |
| `code-simplifier` | 実装後のコードを簡素化・整理 |
| `tester` | 結合テスト・E2E 検証を担当 |
| `reviewer` | コードレビューを担当 |
| `debugger` | バグ調査と修正を担当 |
| `deployer` | デプロイ・リリース作業を担当 |
| `doc-writer` | 成果物ドキュメント（API ドキュメント等）を作成 |
| `journal-writer` | 開発記録・レトロスペクティブ用ジャーナルを作成 |
| `designer` | UI/UX デザインを担当 |
| `ui-ux-designer` | UI/UX デザインの詳細支援（画面遷移・コンポーネント設計） |

## Commands (`/tkm:...`)

| コマンド | 何をしてくれるか |
|---------|----------------|
| `/tkm:find-skill` | 既存 Skill から要望に合うものを探す |
| `/tkm:takumi` | takumi トップレベルのエントリーポイント |
| `/tkm:research` | researcher を呼んで調査を依頼 |
| `/tkm:git` | git-manager を呼んで git 操作を依頼 |
| `/tkm:run-retro` | project-manager を呼んで振り返りを実施 |
| `/tkm:brainstorm` | brainstormer を呼んで壁打ち |
| `/tkm:create-plan` | planner を呼んで実装計画を作成 |
| `/tkm:clean-code` | code-simplifier を呼んでコード簡素化 |
| `/tkm:ship` | implementer を呼んで実装〜PR 作成までを一気通貫 |
| `/tkm:run-tests` | tester を呼んでテスト実行 |
| `/tkm:review-code` | reviewer を呼んでコードレビュー |
| `/tkm:fix-bug` | debugger を呼んでバグ修正 |
| `/tkm:deploy-app` | deployer を呼んでデプロイ |
| `/tkm:manage-docs` | doc-writer を呼んでドキュメント整備 |
| `/tkm:write-journal` | journal-writer を呼んで開発記録を作成 |

## MCP サーバー

| 名前 | 何をしてくれるか |
|------|----------------|
| `playwright` | ブラウザ自動化。E2E テスト・スクリーンショット取得などに利用 |
| `context7` | ライブラリ / フレームワークの最新ドキュメントを取得 |
| `momorph` | フロントエンド設計・コンポーネント生成支援（momorph プラットフォーム連携） |

## Hooks（通知）

| 名前 | 何をしてくれるか |
|------|----------------|
| `notifications/notify.cjs` (Slack) | セッション完了などのタイミングで Slack に通知 |
| `notifications/notify.cjs` (Discord) | 同上 Discord 向け |
| `notifications/notify.cjs` (Telegram) | 同上 Telegram 向け |

> Hook の登録先は `.claude/settings.local.json` の `hooks.SessionStop` と `hooks.Stop`。
> 詳細は takumi の `hooks/notifications/README.md`（取得後に確認可能）。

## 常時取得される要素

ヒアリング結果に関わらず以下は必ず取得される（メモランダム §5-2 参照）：

- 設定ファイル群：`.claude/settings.json`, `.claude/metadata.json`, `.claude/statusline.cjs` ほか
- コア Rule 5 ファイル：`primary-workflow.md` / `orchestration-protocol.md` / `development-rules.md` / `team-coordination-rules.md` / `documentation-management.md`
- 共通 Skill：`_shared/`, `common/`, `find-skill/`
- Anthropic 公式 `skill-creator`（不足 Skill を新規作成するため）
- 常時 Agent：`researcher`, `git-manager`, `mcp-manager`
- 常時 Command：`/tkm:find-skill`, `/tkm:takumi`, `/tkm:research`, `/tkm:git`
- 全 hook（`.claude/settings.json` に登録されている分）
