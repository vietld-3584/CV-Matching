---
name: define-of-done
description: |
  完了の定義（define-of-done.md）の作成・クロージング判定。
  function-list.md・non-function-list.mdの機能・非機能要件と、overview.md
  （契約形態・役割分担）・stakeholders.md（承認フロー）を基にカテゴリ別の
  完了基準を定義する。プロジェクトクロージング時には既存基準の達成状況を判定し、
  未達成基準の対応（達成／スコープ除外／持出し）をクライアント承認フローに
  従って記録する。
allowed-tools:
  - Read
  - Edit
  - Bash
---

# define-of-done Skill

完了の定義（Definition of Done）を作成・クロージング判定するSkill。`jp-project-manager` エージェントの `DOD` メニューから呼ばれる。

## 目的

以下の **1ファイルのみ** を記入する：

- [`docs/01_management/define-of-done.md`](../../../docs/01_management/define-of-done.md) §1（完了の定義一覧）・§2（カテゴリの目安）・§4（クロージング総合判定）

**重要（スコープ境界）**：

- [`docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md)・[`docs/02_requirements/non-function-list.md`](../../../docs/02_requirements/non-function-list.md) には触れない。読み取り専用の参照情報として使う（機能・非機能要件の確定は `gather-requirements`/REQ の担当）。
- [`docs/01_management/stakeholders.md`](../../../docs/01_management/stakeholders.md) には触れない。§2（Sun*体制）・§3（意思決定・承認フロー）は読み取り専用参照として使う（体制の確定は `plan-project`/PLAN の担当）。
- [`docs/01_management/decision.md`](../../../docs/01_management/decision.md) には触れない。除外・持出し判断から重要な決定が生じた場合、記録をユーザーに促すのみで、`Edit` での追記は行わない。
- [`docs/01_management/risks-problems/problem-list.md`](../../../docs/01_management/risks-problems/problem-list.md) には触れない。一部達成の残課題について登録を促すのみで、`Edit` での追記は行わない（`track-risks-issues`/RISK 等の担当）。
- `define-of-done.md` §3（ステータス・判定基準の定義、未達成時の対応フロー4ステップ）自体は書き換えない。本Skillはこのフローを**実行する**側であり、定義の変更は対象外とする。
- §4は初期設定モードでは触れず、空欄のまま維持する（クロージング判定モードでのみ記入。詳細はメインフロー Step 6〜8）。

## 参照ドキュメント

実行時に必要に応じて読み込む：

- `references/hearing.md` — ヒアリングBlock A〜Dの問いかけ例・回答の解釈ルール
- `references/criteria-catalog.md` — カテゴリ別（6カテゴリ）に、ユーザーが基準を出せない場合にAIがどんな根拠から基準ドラフトを提案するかの一覧

## 入力の受け取り方

本Skillの主たる入力は、ユーザーが渡す外部ファイルではなく **リポジトリ内の既存ドキュメント** である。起動時に以下を `Read` で直接読み込む（ユーザーにパスを尋ねる必要はない）：

- [`docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md)・[`docs/02_requirements/non-function-list.md`](../../../docs/02_requirements/non-function-list.md)
- [`docs/01_management/overview.md`](../../../docs/01_management/overview.md)（§1契約形態・§4対応範囲）
- [`docs/01_management/stakeholders.md`](../../../docs/01_management/stakeholders.md)（§2体制・§3承認フロー、読み取り専用）
- [`docs/01_management/decision.md`](../../../docs/01_management/decision.md)・[`docs/01_management/risks-problems/problem-list.md`](../../../docs/01_management/risks-problems/problem-list.md)（読み取り専用。クロージング判定モードで参照）
- [`docs/01_management/define-of-done.md`](../../../docs/01_management/define-of-done.md)（自身）

これらが未記入・テンプレートのまま（`gather-requirements`/REQ 未実行等）の場合に限り、代替として外部の「要件定義書」を受け取ることもできる：

1. **実ファイルのパス** — `Read` で読む
2. **チャット内への直接貼り付け**（テキスト／Markdown）
3. **何も渡さない** — ヒアリングで埋める

**既知の制約**：`Read` は PDF はそのまま読めるが、`.docx`/`.xlsx`/`.doc`/`.xls` はバイナリ形式のためそのままでは読めない。これらのパスを渡された場合、またはReadが失敗した場合は、確認を挟まず次の順で対応してよい：

1. **Bash経由で使い捨てのPythonスクリプトを書いて解析する**：`.docx`/`.xlsx`はZIP+XML構造なので、`python-docx`/`openpyxl`が使えるならそれを使い、無ければ標準ライブラリの`zipfile`＋`xml.etree.ElementTree`で`word/document.xml`（docx）や`xl/sharedStrings.xml`・`xl/worksheets/sheetN.xml`（xlsx）を直接パースしてテキストを取り出す。抽出したテキストはその場で読み取って使い、スクリプトや中間ファイルはプロジェクト配下に残さない（一時ファイルが必要ならOSの一時ディレクトリを使う）。
2. `.doc`/`.xls`（旧バイナリ形式）で1の方法が使えない場合、`python3`が使えない場合、または抽出結果が文字化け・空など使い物にならない場合は、それ以上手段を変えて粘らず、次のように伝える：

> 「このファイルは自動では正しく読み取れませんでした。該当部分をテキストとして貼り付けていただくか、PDF/テキスト形式で書き出して再度パスを教えてください。」

この代替入力から抽出した情報は、`function-list.md`/`non-function-list.md` 自体には書き込まない（スコープ境界）。あくまでDoD基準の根拠としてのみ使う。

## 会話ガイドライン

- 番号選択ではなく **キーワードで例示** し、1ブロック内は1質問1ターン。
- モード判定（初期設定／クロージング判定）も含め、判断・数値・承認に関わる項目はユーザーの明示的な回答なしに確定しない。
- 基準ドラフトは必ず「ドラフト（要確認）」と明示し、ユーザーの採用・修正・削除を待つ。無断で確定値として書き込まない。
- クロージング判定時に「一部達成の残課題を `problem-list.md` に登録すべき」「重要な決定を `decision.md` に記録すべき」等の事務的リマインドは、ヒアリング中に都度割り込まず、Step 10の完了サマリでまとめて報告する。

## メインフロー

### Step 1: 入力とモードの確認

「入力の受け取り方」に記載のファイル群を `Read` する。`define-of-done.md` §1の各行のうち、カテゴリ／基準セルがHTMLコメント（`<!-- 例: ... -->`）ではない行（＝実データ行）の有無、および §4 の5つの「内容」セルがすべて空欄かどうかを確認する。

- 実データ行が0件（`D-001` のみプレースホルダー）→ **初期設定モード** と推定し、確認質問なしでそのまま進める。
- 実データ行があり §4が空欄 → 1問だけ確認する：「完了の定義一覧には既に基準が登録されています。今回は（基準の追加・見直し）と（クロージング判定：達成状況の確定・承認フロー）のどちらを行いますか？」
- 実データ行があり §4にも内容がある → 「前回のクロージング判定が記録されているようです。再判定（更新）を行いますか、それとも基準そのものの追加・見直しを行いますか？」

最終的なモードは常にユーザーの発言で確定する。**初期設定モード** はStep 2〜5・9・10、**クロージング判定モード** はStep 6〜10を実行する（Step 2〜5は既存基準の見直しが必要な場合のみ併用する）。

### Step 2: 既存ドキュメントの洗い出し（初期設定モード）

`function-list.md`（優先度別件数）・`non-function-list.md`（カテゴリ別件数・優先度）・`overview.md` §1/§4・`stakeholders.md` §2/§3 を整理する。`function-list.md`/`non-function-list.md` が未記入の場合、「先に `gather-requirements`（REQ）を実行すると、機能・非機能要件を踏まえた基準が作りやすくなりますが、このままヒアリングで進めることもできます」と1問だけ確認する。ブロックはしない。

### Step 3: カテゴリの目安の確認・調整（§2、hearing.md Block C）

現行6カテゴリ（機能要件／非機能要件（品質・性能）／ドキュメント・成果物／テスト・受入／運用移行・引き継ぎ／契約・請求）を提示し、`overview.md` §1契約形態・§4役割分担を踏まえて追加・削除・対象外注記の要否を確認する。変更があれば `Edit` で §2 に反映する。

### Step 4: 機能要件・非機能要件の基準の導出（§1、hearing.md Block A）

`function-list.md` を優先度別に、`non-function-list.md` をカテゴリ別に集約し、既存の**プレースホルダーでない行を上書きせず**、新しい `D-xxx` IDで追記する形で基準ドラフトを提示する。ユーザー確認後、`Edit` で §1 に反映する（「関連ID」列に対応する `F-xxx`/`NFR-xxx` を記載）。個別に基準を分けたい機能・NFRがあれば別行として追加する。

### Step 5: その他4カテゴリの基準ヒアリング・AIドラフト（§1、hearing.md Block B、criteria-catalog.md）

ドキュメント・成果物／テスト・受入／運用移行・引き継ぎ／契約・請求の順に、まずユーザーに基準があるか聞き、なければ `references/criteria-catalog.md` の該当カテゴリの着眼点からドラフトを提示する。確定した基準を都度 `Edit` する。Step 3で対象外としたカテゴリは省略してよい。

### Step 6: 判定方法・エビデンスの確認とステータス確定（クロージング判定モードのみ、hearing.md Block D）

§1の各実データ行について、「判定方法・エビデンス」列の結果をユーザーに確認し、ステータス（達成／一部達成／未達成）を確定する。AIが推測して判定しない。一部達成の場合は残課題の `problem-list.md` 登録状況を確認する（登録はしない）。

### Step 7: 未達成・一部達成への対応フロー（クロージング判定モードのみ）

テンプレート §3「未達成時の対応フロー」の4ステップをそのまま実行する：

1. 対応方針（対応して達成／スコープ除外(waive)／次フェーズへ持出し）と理由を「ドラフト（要確認）」として提案する。
2. `stakeholders.md` §3の該当承認者へのレビュー・承認状況をユーザーに確認する（承認者・承認日）。
3. 承認済みの行のみ、ステータス／未達成時の対応／除外・持出しの理由／承認者／承認日／更新日を `Edit` で確定する。未承認の行は「承認待ち」として保留する。
4. 重要な決定が生じた場合、`decision.md` への記録をユーザーに促す（Editはしない）。

### Step 8: §4 クロージング総合判定の記入（クロージング判定モードのみ）

全行の判定が済んでいることを確認する（未解決行があれば暫定値である旨の確認を取る）。総合達成率は「達成」件数を分子、全件数を分母として算出し、除外（waive）件数・次フェーズへの持出し件数は別項目として集計する（この算出方法自体もユーザーに確認する）。最終承認者・承認日・総合コメント（ドラフト→確認）を `Edit` する。

### Step 9: 改訂履歴の追記

実質的な変更があった場合、`define-of-done.md` §5「改訂履歴」に日付・更新者（`define-of-done skill` または対話中のペルソナ名）・内容を1行追加する。

### Step 10: 完了サマリ

記入した基準・カテゴリ調整・（クロージング判定モード時）達成率を要約する。未確定のまま残った基準、承認待ちの対応方針、`problem-list.md`/`decision.md` への未登録の記録依頼を、プロジェクトクロージングの前提として明示する。

## エラー時の対応

- 読めないファイル形式 → 上記「入力の受け取り方」のフォールバック文言で案内する
- `function-list.md`/`non-function-list.md` が未記入 → REQ実行を1問だけ推奨する。ブロックはしない
- 既存の実データ行を上書きしそうな場面 → 必ず確認を取ってから実行する
- クライアント承認が得られていない対応方針 → 確定せず「承認待ち」として完了サマリで報告する
- ステータス・エビデンスが最後まで確定しない基準 → 空欄のまま残し、無理に達成／未達成を推測しない
- 一部達成の残課題が `problem-list.md` に未登録 → 登録を促すが、自ら書き込まない

## 関連ファイル

- `references/hearing.md` — ヒアリングBlock A〜Dの詳細
- `references/criteria-catalog.md` — 完了基準のAIドラフト提案カタログ
- [`../../../docs/01_management/define-of-done.md`](../../../docs/01_management/define-of-done.md)
- [`../../../docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md)
- [`../../../docs/02_requirements/non-function-list.md`](../../../docs/02_requirements/non-function-list.md)
- [`../../../docs/01_management/overview.md`](../../../docs/01_management/overview.md)
- [`../../../docs/01_management/stakeholders.md`](../../../docs/01_management/stakeholders.md)
- [`../../../docs/01_management/decision.md`](../../../docs/01_management/decision.md)
- [`../../../docs/01_management/risks-problems/problem-list.md`](../../../docs/01_management/risks-problems/problem-list.md)
