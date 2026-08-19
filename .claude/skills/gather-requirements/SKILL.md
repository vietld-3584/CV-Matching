---
name: gather-requirements
description: |
  要件定義（role-list.md / function-list.md / non-function-list.md / business-flow.md / glossary.md）の作成。
  提案書・プロジェクト概要（クライアントブリーフ）を読み込み、不足情報は
  自然言語で対話的にヒアリングして5ファイルを記入する。非機能要件はユーザーが
  提示できない場合、プロジェクト特性からAIがドラフトを提案する。
allowed-tools:
  - Read
  - Edit
  - Bash
---

# gather-requirements Skill

要件定義フェーズのドキュメントを作成するSkill。`jp-project-manager` エージェントの `REQ` メニューから呼ばれる。

## 目的

以下の **5ファイルのみ** を記入する：

- [`docs/02_requirements/role-list.md`](../../../docs/02_requirements/role-list.md) — 利用者ロール一覧・権限マトリクス
- [`docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md) — 機能一覧（スコープ）
- [`docs/02_requirements/business-flow.md`](../../../docs/02_requirements/business-flow.md) — 業務フロー概要（mermaid）
- [`docs/02_requirements/non-function-list.md`](../../../docs/02_requirements/non-function-list.md) — 非機能要件一覧
- [`docs/02_requirements/glossary.md`](../../../docs/02_requirements/glossary.md) — 用語集

**重要（スコープ境界）**：

- [`docs/02_requirements/project-overview.md`](../../../docs/02_requirements/project-overview.md) には触れない。サービス概要・背景課題・目的は `plan-project`（PLAN）が担当済みの前提とし、本Skillは**読み取り専用の背景情報**として使う。
- [`docs/02_requirements/functions/`](../../../docs/02_requirements/functions/) 配下の機能詳細ファイル（ユースケース・入出力・業務ルールの深掘り）は作成しない。function-list.md の「詳細ドキュメント」列は空欄／`TBD`のままにし、後続の別Skill（機能詳細作成）に委ねる。
- [`docs/01_management/define-of-done.md`](../../../docs/01_management/define-of-done.md) には触れない。完了判定は要件確定後の別Skill（`define-of-done`/DOD）の担当。

business-flow.md は**プロジェクト全体を貫く主要フローの概要図**（必須機能を軸にした大枠のmermaid）のみを扱う。個々の機能内の代替・例外フローは対象外（＝機能詳細ファイル側の責務）。

## 参照ドキュメント

実行時に必要に応じて読み込む：

- `references/hearing.md` — ヒアリングBlock A〜Eの問いかけ例・回答の解釈ルール・記入順序の依存関係
- `references/nfr-catalog.md` — 非機能要件8カテゴリごとに、プロジェクト特性から何を根拠にドラフトを提案するかの一覧（ユーザーが自分で出せない場合に使う）

## 入力の受け取り方

ユーザーは 提案書／プロジェクト概要（クライアント提供のブリーフ） を、以下いずれの形でも渡せる：

1. **実ファイルのパス** — `Read` で読む
2. **チャット内への直接貼り付け**（テキスト／Markdown）
3. **何も渡さない** — 全項目をヒアリング対象とする

**既知の制約**：`Read` は PDF はそのまま読めるが、`.docx`/`.xlsx`/`.doc`/`.xls` はバイナリ形式のためそのままでは読めない。これらのパスを渡された場合、またはReadが失敗した場合は、確認を挟まず次の順で対応してよい：

1. **Bash経由で使い捨てのPythonスクリプトを書いて解析する**：`.docx`/`.xlsx`はZIP+XML構造なので、`python-docx`/`openpyxl`が使えるならそれを使い、無ければ標準ライブラリの`zipfile`＋`xml.etree.ElementTree`で`word/document.xml`（docx）や`xl/sharedStrings.xml`・`xl/worksheets/sheetN.xml`（xlsx）を直接パースしてテキストを取り出す。抽出したテキストはその場で読み取って使い、スクリプトや中間ファイルはプロジェクト配下に残さない（一時ファイルが必要ならOSの一時ディレクトリを使う）。
2. `.doc`/`.xls`（旧バイナリ形式）で1の方法が使えない場合、`python3`が使えない場合、または抽出結果が文字化け・空など使い物にならない場合は、それ以上手段を変えて粘らず、次のように伝える：

> 「このファイルは自動では正しく読み取れませんでした。該当部分をテキストとして貼り付けていただくか、PDF/テキスト形式で書き出して再度パスを教えてください。」

## 会話ガイドライン

- **常に「文書からの推測」を先に試し、ヒアリングは不足分のみ**に絞る。推測できた項目も「〇〇と理解しましたが合っていますか？」と確認してから確定する。
- ヒアリングは `references/hearing.md` のBlock A〜Eの単位で進め、**1ブロック内は1質問1ターン**。番号選択ではなくキーワードで例示し、自然言語の回答を許容する。曖昧なら確認質問を返す。
- **非機能要件（Block D）はユーザーへの丸投げにしない**。ユーザーが数値目標を出せない場合、`references/nfr-catalog.md` を参照してAIが「ドラフト（要確認）」として提案し、ユーザーに採用・修正・削除を選んでもらう。無断で確定値として書き込まない。
- **用語集（Block E）は後追い収集**。Block A〜Dのヒアリング中に出てきた業務用語・略語・クライアント固有語をその場でメモしておき、Block Eで一覧化してユーザーに定義を確認する。ゼロから「用語を教えてください」とは聞かない。

## メインフロー

### Step 1: 入力とコンテキストの確認

- 提案書／プロジェクト概要（クライアントブリーフ）を確認する。ファイルパスなら `Read`、貼付けならそのまま内容として扱う。
- [`docs/02_requirements/project-overview.md`](../../../docs/02_requirements/project-overview.md) と [`docs/01_management/overview.md`](../../../docs/01_management/overview.md) を `Read` し、サービス概要・背景課題・対象プラットフォーム・契約制約など、既に確定済みの背景情報を把握する（**書き込みはしない**）。
- `project-overview.md` が未記入・テンプレートのままの場合：ブロックはしないが、「project-overview.mdがまだ未記入のようです。先に`plan-project`（PLAN）を実行すると背景情報を活かしてヒアリングを進めやすくなりますが、このまま要件のヒアリングを始めることもできます。どちらにしますか？」と1問だけ確認する。

### Step 2: 既存5ファイルの確認

対象5ファイルを `Read` し、各セクション・行を次のいずれかに分類する：

- **未記入**（HTMLコメントのガイド・テンプレート例のみ）→ 自由に記入してよい
- **記入済み**（実データが入っている）→ 無断で上書きしない。既存値を提示し、更新するか確認する

5ファイルとも既に完全に記入済みの場合は、その旨を伝えて「更新・追加したい項目はありますか？」と聞き、該当項目のみピンポイント対応に切り替える。

### Step 3: ロール一覧のヒアリング（role-list.md §1）

`references/hearing.md` Block A に従い、利用者ロール（エンドユーザー種別・管理者・運用担当等）をヒアリングする。確定するたびに `Edit` で `role-list.md` §1 の行を追加・更新する（既存の `ROLE-001`/`ROLE-002` はテンプレート例として扱い、実データで上書きする）。

### Step 4: 機能一覧のヒアリング（function-list.md）

`references/hearing.md` Block B に従い、機能をヒアリングする。各機能について 機能名・概要・優先度（必須/推奨/任意/対象外）・対象ロール（Step 3のROLE-ID） を確定し、`function-list.md` に追記する。「詳細ドキュメント」列は空欄のままにする（後続Skillの担当）。

### Step 5: 権限マトリクスの作成（role-list.md §2）

Step 3・4の結果から、機能×ロールの権限（作成・閲覧・更新・削除等）をAIがドラフトし、ユーザーに一括確認する。「〇〇機能はROLE-002のみ、〇〇機能は全ロール閲覧可、で合っていますか？」のように提示し、差分のみ修正してもらう。確定後 `Edit` で反映する。

### Step 6: 業務フロー概要の作成（business-flow.md）

Step 4で優先度「必須」とした機能を中心に、主要な業務フロー（利用者起点→主要機能→完了）をAIがmermaidでドラフトし、ユーザーに確認する。フローが複数系統ある場合（例：利用者フローと管理者フローが分かれる）は見出しを分けて追加する。個々の機能内の代替・例外分岐までは描かない（機能詳細ファイルの責務）。

### Step 7: 非機能要件のヒアリング・AI提案（non-function-list.md）

`references/hearing.md` Block D と `references/nfr-catalog.md` に従う：

1. まずユーザーに数値目標・基準があるか聞く。
2. 出てこない場合、`references/nfr-catalog.md` の該当カテゴリの根拠（対象プラットフォーム・データの機密性・想定規模等、Step 1で読んだ背景情報）からAIがドラフト値を提案し、「ドラフト（要確認）」と明示したうえで提示する。
3. ユーザーが採用・修正・削除を選んだ結果のみを確定値として `non-function-list.md` に書き込む。全8カテゴリを機械的に埋めようとしない（該当しないカテゴリは対象外でよい）。

### Step 8: 用語集の整理（glossary.md）

Step 3〜7のヒアリング中に出てきた業務用語・略語・クライアント固有語を一覧にして提示し、定義をユーザーに確認する。「ヒアリング中に出てきた用語として〇〇・△△がありますが、定義を教えてください。他に追加したい用語はありますか？」の形でまとめて聞いてよい。確定した用語のみ `glossary.md` に反映する。

### Step 9: ファイルへの反映・改訂履歴

各ファイルへの書き込みは確定した時点で都度 `Edit` する（ブロック完了を待たず反映してよい）。実質的な変更を行ったファイルには、そのファイル自身の「改訂履歴」表に日付・更新者（`gather-requirements skill` または対話中のペルソナ名）・内容を1行追加する。

### Step 10: 完了サマリ

5ファイルそれぞれについて、記入した内容の要約と、未確定のまま残っている項目（ユーザーが回答を保留した等）を明示する。特に function-list.md の「詳細ドキュメント」が未着手であること、business-flow.md が概要レベルに留まることを、後続Skill（機能詳細作成、`define-of-done`/DOD等）が着手する前の前提として伝える。

## エラー時の対応

- 読めないファイル形式 → 上記「入力の受け取り方」のフォールバック文言で案内する
- 複数の入力文書間で内容が矛盾する → 両方の記載を提示し、ユーザーに確定してもらう。どちらかを勝手に採用しない
- 既存ファイルの実データを上書きしそうな場面 → 必ず確認を取ってから実行する
- 非機能要件でユーザーが数値を決められない → 空欄のまま残し、Step 10の完了サマリで未確定事項として報告する（無理に数値化しない）

## 関連ファイル

- `references/hearing.md` — ヒアリングBlock A〜Eの詳細
- `references/nfr-catalog.md` — 非機能要件のAIドラフト提案カタログ
- [`../../../docs/02_requirements/role-list.md`](../../../docs/02_requirements/role-list.md)
- [`../../../docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md)
- [`../../../docs/02_requirements/business-flow.md`](../../../docs/02_requirements/business-flow.md)
- [`../../../docs/02_requirements/non-function-list.md`](../../../docs/02_requirements/non-function-list.md)
- [`../../../docs/02_requirements/glossary.md`](../../../docs/02_requirements/glossary.md)
