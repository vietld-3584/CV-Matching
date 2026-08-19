# セキュリティ設定チェックリスト

このドキュメントは、[社内 OSS リポジトリ セキュリティ設定ガイド](https://www.notion.so/sun-asterisk/OSS-3369530548f3804b8c83e0421f5f1d35)に基づき、`CV-Matching` リポジトリに適用すべきセキュリティ設定をまとめたものです。

ファイルとしてリポジトリにコミットできる設定（`.gitignore` / `dependabot.yml` / 各種ワークフロー / `SECURITY.md`）は本リポジトリに含まれています。GitHub UI 上でのみ設定できる項目はリポジトリ管理者が以下のチェックリストに従って適用してください。

> **本リポジトリの前提**: Python (FastAPI) のアプリケーションコードと依存マニフェスト (`pyproject.toml`)、および Dockerfile / Helm チャートを持つサービスリポジトリです。テンプレート由来の記述のうち、言語依存の項目は Python 向けに読み替えています。

## 凡例

- ✅ **ファイル済**: 本リポジトリにファイルとしてコミット済み
- ⚙️ **要 UI 設定**: GitHub の設定画面で管理者が適用する必要あり
- 📦 **利用先で適用**: テンプレートを利用する各プロジェクト側で適用する項目

---

## 1. ブランチ保護

| 項目 | 状態 | 補足 |
|------|------|------|
| `main` への直接 push 禁止（PR ベースのマージ強制） | ⚙️ 要 UI 設定 | Settings → Rules → Rulesets → New branch ruleset で `main` を対象に「Require a pull request before merging」 |
| PR レビュー承認を必須（最低 1 名） | ⚙️ 要 UI 設定 | 「Require approvals」を 1 以上に |
| 承認後の push で stale approval を解除 | ⚙️ 要 UI 設定 | 「Dismiss stale pull request approvals when new commits are pushed」 |
| ステータスチェック（CI）通過を必須 | ⚙️ 要 UI 設定 | 「Require status checks to pass」で `Test` / `Scorecard` / `OSV-Scanner` を指定。「Require branches to be up to date」も有効化 |
| force push 禁止 | ⚙️ 要 UI 設定 | 「Allow force pushes」が無効（デフォルト）であることを確認 |

## 2. シークレット・認証情報の管理

| 項目 | 状態 | 補足 |
|------|------|------|
| `.gitignore` で APIキー/秘密鍵を除外 | ✅ ファイル済 | [`.gitignore`](../.gitignore) |
| GitHub Secret Scanning を有効化 | ⚙️ 要 UI 設定 | Settings → Code security → Secret scanning |
| Push Protection を有効化 | ⚙️ 要 UI 設定 | Settings → Code security → Secret scanning → Push protection |
| CI/CD シークレットの集中管理 | ⚙️ 要 UI 設定 | Settings → Secrets and variables → Actions。Environment secrets の利用を推奨 |

## 3. Dependabot の運用

| 項目 | 状態 | 補足 |
|------|------|------|
| `dependabot.yml` の配置（interval / limit / groups / labels） | ✅ ファイル済 | [`.github/dependabot.yml`](../.github/dependabot.yml)。`weekly`（月曜）/ 上限 5 / グループ化 / ラベル設定済み |
| Dependabot alerts / security updates を有効化 | ⚙️ 要 UI 設定 | Settings → Code security → Dependabot |

> 本リポジトリでは `pip`（`pyproject.toml`）・`github-actions`・`docker`（ベースイメージ）の 3 エコシステムを対象にしています。

## 4. サプライチェーン攻撃への対策

| 項目 | 状態 | 補足 |
|------|------|------|
| ロックファイルをリポジトリに含める | ⚙️ 要対応 | `uv.lock` の commit を検討。現状 CI は `pyproject.toml` の範囲指定で解決している |
| deps.dev / Scorecard で依存リスクを評価 | ✅ ファイル済 | [`.github/workflows/scorecard.yml`](../.github/workflows/scorecard.yml) |
| CI で脆弱性スキャン（OSV-Scanner） | ✅ ファイル済 | [`.github/workflows/osv-scanner.yml`](../.github/workflows/osv-scanner.yml) |
| サードパーティ Actions をコミット SHA でピン留め | ✅ ファイル済 | 本リポジトリの全ワークフローで適用済み |
| ビルド定義をコードとして管理（手動ビルド排除） | ✅ ファイル済 | [`Dockerfile`](../Dockerfile) / [`docker-bake.hcl`](../docker-bake.hcl) / [`.github/workflows/build.yml`](../.github/workflows/build.yml) |
| 依存インストール時の任意コード実行を抑制 | ⚙️ 要検討 | `uv pip install` はビルドバックエンド経由の実行を伴うため、wheel 優先の解決を推奨 |

## 5. CI/CD のセキュリティ

| 項目 | 状態 | 補足 |
|------|------|------|
| ワークフロー権限のデフォルトを read-only に | ⚙️ 要 UI 設定 | Settings → Actions → General → Workflow permissions で「Read repository contents and packages permissions」 |
| 各ワークフローで必要権限のみ `permissions` で明示 | ✅ ファイル済 | 本リポジトリの全ワークフローで `permissions: read-all` をデフォルトとし、ジョブ単位で最小付与 |
| `pull_request_target` の取り扱い | ✅ 該当なし | 本リポジトリでは未使用。利用する場合は `types: [labeled]` 限定で運用 |

## 6. コード解析

| 項目 | 状態 | 補足 |
|------|------|------|
| Code Scanning（CodeQL）を有効化 | ⚙️ 要 UI 設定 | Python コードを持つため対象。Settings → Code security → Code scanning で `Default` セットアップを有効化 |
| サードパーティ SAST（Semgrep / trivy 等） | ⚙️ 要検討 | コンテナイメージの trivy スキャンを `build.yml` に追加する余地あり |

> CodeQL の設定例はガイドの「コード解析」セクションを参照してください。

## 7. アクセス制御

| 項目 | 状態 | 補足 |
|------|------|------|
| コラボレーター権限は最小限で付与 | ⚙️ 要 UI 設定 | 通常の開発者は Write、設定管理が必要なリードに Maintain/Admin |
| 2FA を全メンバーに必須化 | ⚙️ 要 UI 設定 | Organization Settings で必須化。セキュリティキー（FIDO2/WebAuthn）を推奨 |
| 不要なデプロイキー / PAT の定期棚卸し | ⚙️ 要 UI 設定 | 四半期ごとにレビュー。Fine-grained PAT の利用を推奨 |
| チーム単位で権限を管理 | ⚙️ 要 UI 設定 | [CODEOWNERS](../.github/CODEOWNERS) のオーナー指定をチームに移行することを推奨 |

## 8. セキュリティポリシーの公開

| 項目 | 状態 | 補足 |
|------|------|------|
| `SECURITY.md` を配置 | ✅ ファイル済 | [`SECURITY.md`](../SECURITY.md) |
| Private Vulnerability Reporting（参考） | ⚙️ 要 UI 設定 | Settings → Code security → Private vulnerability reporting。社内チャネルで完結する場合は無効でも可 |

---

## マージ後の管理者 TODO（要 UI 設定のまとめ）

- [ ] ブランチ保護 Ruleset を作成（PR 必須 / 承認 1 名 / stale approval 解除 / ステータスチェック / force push 禁止）
- [ ] Secret Scanning と Push Protection を有効化
- [ ] Dependabot alerts / security updates を有効化
- [ ] Workflow permissions のデフォルトを read-only に変更
- [ ] 2FA を Organization 全体で必須化
- [ ] コラボレーター/チーム権限を最小権限で見直し
- [ ] デプロイキー / PAT の棚卸しを定期タスク化
- [ ] （任意）Private Vulnerability Reporting の有効化を検討

---

_本チェックリストは社内 OSS リポジトリ セキュリティ設定ガイドに基づきます。最終更新: 2026-08-19_

- [ ] Code Scanning（CodeQL）を有効化（Python コードを持つため本リポジトリでは対象）
