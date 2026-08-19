# GUIDE

> `docs/` フォルダの構成ガイドです。番号はSDLCフェーズの順序です。

```
docs/
├── 01_management/                  # プロジェクト管理
│   ├── overview.md                 # 全体サマリー（契約・体制・進め方）※最初に読む
│   ├── stakeholders.md             # 関係者一覧・意思決定権限
│   ├── schedule.md                 # マイルストーン/WBS ベースライン計画
│   ├── progress.md                 # 進捗実績（schedule.mdとの対計画差異）
│   ├── task-list.md                # タスク一覧（GitHub Issueへのポインタ）
│   ├── decision.md                 # 意思決定ログ
│   ├── define-of-done.md           # 完了(Done)の基準
│   ├── feedbacks/
│   │   ├── feedback-list.md        # 日常的なフィードバック
│   │   └── change-request.md       # スコープ/予算に影響する正式な変更依頼
│   ├── risks-problems/
│   │   ├── risk-list.md            # 未発生リスク一覧
│   │   └── problem-list.md         # 発生済み課題一覧
│   ├── mtg-logs/                    # 会議ログ（yyyy-mm-dd-log-N.mdを複製）
│   └── reports/                     # 週次報告（yyyy-mm-dd-weekly-report.mdを複製）
│
├── 02_requirements/                 # 要件定義
│   ├── project-overview.md         # サービスの背景・課題・提供価値
│   ├── role-list.md                # 利用者ロールと権限
│   ├── function-list.md            # 機能一覧（スコープの集約ビュー）
│   ├── functions/                   # 機能詳細（function-N-名前.mdを複製）
│   ├── non-function-list.md        # 非機能要件（性能・可用性・セキュリティ等）
│   ├── business-flow.md            # 主要業務フロー
│   └── glossary.md                  # 業務用語集
│
├── 03_system-design/                # システム設計
│   ├── architecture.md             # アーキテクチャ全体像
│   ├── database.md                  # DB設計
│   └── api-design/
│       ├── api-list.md              # API一覧
│       └── api-N-名前.md            # API詳細（複製して作成）
│
├── 04_screen-design/                 # 画面設計
│   ├── screen-list.md               # 画面一覧
│   ├── bussiness-specs/             # 画面業務仕様（screen-N-名前.mdを複製）
│   └── technical-specs/             # 画面技術仕様（同上）
│
├── 05_releases/                      # リリースノート（yyyy-mm-dd-release-note-N.mdを複製）
│
├── 06_test/                          # テスト
│   ├── test-plan.md                # テスト計画（レベル・体制・合否基準）
│   ├── test-schedule.md            # テストマイルストーン/WBS
│   └── testcase/
│       ├── testcase-list.md        # テストケース一覧
│       └── testcase-N-名前.md      # テストケース詳細（複製して作成）
│
└── 99_draft_wip/                     # 下書き・検討中メモの一時置き場、定期的にクリアする
```

## 運用メモ

- 「(サンプル)」付きファイルはテンプレート。複製して命名規則通りに作成する。
- 予定は `schedule.md`、実績は `progress.md` と役割を分け、内容を重複させない。
- `TODO: 内容を記入してください` のファイルは未着手。
