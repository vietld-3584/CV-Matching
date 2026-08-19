# Contributing to AI Ready SDLC

このプロジェクトへのコントリビューションに興味を持っていただきありがとうございます！🎉

このドキュメントでは、コントリビューションの方法とガイドラインを説明します。

## 目次

- [行動規範](#行動規範)
- [コントリビューションの種類](#コントリビューションの種類)
- [はじめる前に](#はじめる前に)
- [Issue の作成](#issue-の作成)
- [Pull Request の作成](#pull-request-の作成)
- [レビュープロセス](#レビュープロセス)
- [セキュリティ](#セキュリティ)
- [開発ツール](#開発ツール)

## 行動規範

このプロジェクトでは、オープンで友好的なコミュニティを維持することを大切にしています。
すべてのコントリビューターは、お互いを尊重し、建設的なコミュニケーションを心がけてください。

## コントリビューションの種類

以下のような形でコントリビューションできます：

- 🐛 **バグ報告**: テンプレートの不具合や誤りを報告
- 💡 **機能提案**: 新しいテンプレートや改善案の提案
- 📝 **ドキュメント改善**: READMEやガイドの改善
- 🔧 **テンプレート追加/改善**: 新しいテンプレートの追加や既存テンプレートの改善
- 👀 **レビュー**: 他のPRのレビュー
- 💬 **ディスカッション**: GitHub Discussions での議論参加

## はじめる前に

### 必要なツール

- Git
- GitHub CLI (`gh`)
- Claude Code（推奨）

### リポジトリのセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc.git
cd sun-ai-ready-sdlc

# 作業ブランチを作成
git checkout -b feat/your-feature-name
```

## Issue の作成

### Issue を作成する前に

1. [既存の Issue](https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/issues) を検索して、重複がないか確認
2. [Discussions](https://github.com/sun-asterisk-internal/sun-ai-ready-sdlc/discussions) で類似の議論がないか確認

### Issue テンプレート

- **Proposal**: 改善提案や新機能のアイデア
- **Task**: 具体的なタスク
- **Feature Request**: テンプレートへの機能追加要望
- **Bug Report**: 不具合報告
- **RFC**: 大きな変更の Request for Comments

### 良い Issue の書き方

- タイトルは具体的に
- 背景・目的を明確に説明
- 可能であれば解決案も提示
- スクリーンショットや例があれば添付

## Pull Request の作成

### ブランチ命名規則

```
feat/機能名        # 新機能
fix/修正内容       # バグ修正
docs/ドキュメント名  # ドキュメント更新
refactor/対象     # リファクタリング
```

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 形式に従ってください：

```
[#{issue番号}]prefix(scope): メッセージ

例:
[#123]feat(web-template): Add new Claude command for testing
[#45]docs(readme): Update quickstart guide
fix(mobile-template): Fix typo in Serena memory
```

**Prefix 一覧:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `refactor`: リファクタリング
- `style`: コードの意味に影響しない変更（フォーマット等）
- `test`: テストの追加・修正
- `ci`: CI設定の変更
- `build`: ビルドシステムや外部依存の変更

### PR チェックリスト

PR を作成する前に確認してください：

- [ ] 関連する Issue がリンクされている
- [ ] コミットメッセージが規約に従っている
- [ ] ドキュメントが必要に応じて更新されている
- [ ] 既存のテンプレートを壊していない

### PR の作成方法

```bash
# 変更をコミット
git add .
git commit -m "[#123]feat(scope): Your message"

# リモートにプッシュ
git push origin feat/your-feature-name

# PR を作成（GitHub CLI使用）
gh pr create --title "feat: Your feature" --body "Closes #123"
```

## レビュープロセス

1. **自動チェック**: CI が通っていることを確認
2. **コードオーナーレビュー**: CODEOWNERS に定義されたメンテナーがレビュー
3. **フィードバック対応**: レビューコメントに対応
4. **承認 & マージ**: 承認を得たらメンテナーがマージ

### レビュー観点

- テンプレートとしての汎用性
- ドキュメントの明確さ
- 既存構成との整合性
- AI（Claude）との親和性

## セキュリティ

### 脆弱性を発見したら

セキュリティ上の問題（脆弱性、シークレット漏洩、テンプレートに含まれる危険な設定など）を発見した場合は、**公開 Issue を作成せず**、[SECURITY.md](./SECURITY.md) に記載の非公開チャネルで報告してください。

### コントリビューション時のセキュリティ配慮

- **シークレットをコミットしない**: APIキー・秘密鍵・認証情報を含むファイルは [`.gitignore`](./.gitignore) で除外されています。テスト用のダミー値であっても実在しそうな形式は避けてください。
- **GitHub Actions はコミット SHA でピン留め**: ワークフローを追加・変更する際は、サードパーティ Action をタグではなくコミット SHA で固定し、コメントでバージョンを併記してください（例: `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`）。
- **最小権限**: ワークフローには必要な `permissions` のみを明示的に付与してください。

リポジトリ全体のセキュリティ設定方針は [docs/security-settings.md](./docs/security-settings.md) を参照してください。

## 開発ツール

### Claude Custom Command

このプロジェクトでは、開発作業を効率化するための Claude Code カスタムコマンドが `.claude/commands/` ディレクトリに定義されています。

**Create Issue**

リポジトリに Issue を作成するコマンドです。

```bash
/create-issue <テンプレート名>
```

テンプレート名:
- `proposal`: 改善などの提案 Issue で利用
- `task`: Todo タスクの Issue で利用

**Commit**

現在のブランチで実装された内容を基に、適切な粒度でコミットを作成するコマンドです。
Conventional Commits 形式に従ったコミットメッセージを自動生成します。

```bash
/commit
```

主な機能：
- 変更内容を分析し、適切なコミットメッセージを生成
- プレフィックス（feat, fix, refactor 等）を自動選択
- main ブランチの場合は自動的に適切なブランチ名で分岐

**Create Pull Request**

現在のブランチから Pull Request を作成するコマンドです。

```bash
/create-pr
```

## 質問・相談

- **Slack**: #ai-ready-sdlc（TBD）
- **GitHub Discussions**: 技術的な質問やアイデアの相談

---

コントリビューションお待ちしています！ 🚀
