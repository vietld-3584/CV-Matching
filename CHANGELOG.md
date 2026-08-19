# Changelog

このプロジェクトのすべての注目すべき変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/lang/ja/) に従います。

## [Unreleased]

### Added
- OSS運用のための基盤ファイル追加（CODEOWNERS, MAINTAINERS.md, CHANGELOG.md）
- CONTRIBUTING.md の拡充
- 社内OSSセキュリティ設定ガイド準拠のセキュリティ基盤
  - `SECURITY.md`（脆弱性の報告手順・対応フロー）
  - `.github/dependabot.yml`（GitHub Actions の更新管理）
  - `.github/workflows/scorecard.yml`（OpenSSF Scorecard）
  - `.github/workflows/osv-scanner.yml`（OSV-Scanner による脆弱性スキャン）
  - `docs/security-settings.md`（ガイド全8カテゴリのセキュリティ設定チェックリスト）

### Changed
- `.gitignore` にシークレット・認証情報の除外パターンを追加
- CONTRIBUTING.md にセキュリティ報告・コントリビューション時のセキュリティ配慮セクションを追加

### Deprecated

### Removed

### Fixed

### Security
- サードパーティ GitHub Actions をコミット SHA でピン留め
- ワークフロー権限をデフォルト read-only とし、ジョブ単位で最小権限を付与

---

## [0.1.0] - 2024-12-05

### Added
- 初期リリース
- GitHub Issue テンプレート（proposal, task）
- GitHub PR テンプレート
- Claude Code カスタムコマンド（create-issue, commit, create-pr）
- Web Development テンプレート
  - Serena memories（プロジェクト概要、アーキテクチャ、API、データモデル等）
  - Claude commands（task-executor, generate-imple, generate-epic等）
- ドキュメント
  - ライフサイクル説明
  - Issue管理ガイド
  - プロジェクト計画ガイド

---

<!-- リンク定義 -->
[Unreleased]: https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/releases/tag/v0.1.0
