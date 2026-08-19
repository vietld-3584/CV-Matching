---
name: plan-schedule
description: |
  スケジュールベースライン（schedule.md：前提条件・マイルストーン・WBS）の作成。
  ユーザーからヒアリングしたマイルストーンと、既存の function-list.md・overview.md §4
  （対応範囲・役割分担）・stakeholders.md §2（Sun*体制・アサイン工数）を基に、
  Epic/StoryレベルのWBSと開始日・終了日（予定）を算出する。
allowed-tools:
  - Read
  - Edit
  - Bash
---

# plan-schedule Skill

スケジュールベースラインを作成するSkill。`jp-project-manager` エージェントの `SCH` メニューから呼ばれる。

## 目的

**主目的**は以下1ファイルの記入：

- [`docs/01_management/schedule.md`](../../../docs/01_management/schedule.md) — 前提条件・マイルストーン・WBS（Epic/Story）

WBS算出に必要な前提データが欠けている場合に限り、以下3ファイルにも **副次的に** 書き込む（無断上書きはしない。詳細はStep 2・4・5・7）：

- [`docs/01_management/overview.md`](../../../docs/01_management/overview.md) §4（対応範囲・役割分担）— 実施者が未確定の行のみ
- [`docs/01_management/stakeholders.md`](../../../docs/01_management/stakeholders.md) §2（Sun*体制）— 「アサイン工数（稼働）」列が空のメンバーのみ
- [`docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md) — 「関連WBS ID」列のみ

**重要（スコープ境界）**：

- [`docs/01_management/define-of-done.md`](../../../docs/01_management/define-of-done.md) には触れない（別Skill `define-of-done`/DOD の担当）。
- [`docs/01_management/progress.md`](../../../docs/01_management/progress.md) には触れない。本Skillは **ベースライン計画（予定）** のみを扱い、実績・ステータスの追跡は別Skill（`report-project`/REP）の担当。
- `stakeholders.md` の §1（クライアント体制）・§3〜§6には触れない（`plan-project`/PLAN の担当）。§2も「アサイン工数」列以外は上書きしない。

## 参照ドキュメント

実行時に必要に応じて読み込む：

- `references/hearing.md` — ヒアリングBlock A〜Dの問いかけ例・回答の解釈ルール
- `references/wbs-breakdown.md` — overview.md §4の各行→Epic化条件、function-list.mdの機能数によるStory粒度の自動判定基準、工程間のデフォルト依存関係ルール、稼働キャパシティからの日程算出の考え方

## 入力の受け取り方

ユーザーは 見積書(工数) を、以下いずれの形でも渡せる：

1. **実ファイルのパス** — `Read` で読む
2. **チャット内への直接貼り付け**（テキスト／Markdown）
3. **何も渡さない** — ヒアリング（Block B）で工数を確定する

マイルストーンは基本的に **ヒアリングで直接聴取する**（文書からの抽出を試みない。プロジェクト計画書等に記載があれば参考にしてよいが、必ずユーザーに確定してもらう）。

**既知の制約**：`Read` は PDF はそのまま読めるが、`.docx`/`.xlsx`/`.doc`/`.xls` はバイナリ形式のためそのままでは読めない。これらのパスを渡された場合、またはReadが失敗した場合は、確認を挟まず次の順で対応してよい：

1. **Bash経由で使い捨てのPythonスクリプトを書いて解析する**：`.docx`/`.xlsx`はZIP+XML構造なので、`python-docx`/`openpyxl`が使えるならそれを使い、無ければ標準ライブラリの`zipfile`＋`xml.etree.ElementTree`で`word/document.xml`（docx）や`xl/sharedStrings.xml`・`xl/worksheets/sheetN.xml`（xlsx）を直接パースしてテキストを取り出す。抽出したテキストはその場で読み取って使い、スクリプトや中間ファイルはプロジェクト配下に残さない（一時ファイルが必要ならOSの一時ディレクトリを使う）。
2. `.doc`/`.xls`（旧バイナリ形式）で1の方法が使えない場合、`python3`が使えない場合、または抽出結果が文字化け・空など使い物にならない場合は、それ以上手段を変えて粘らず、次のように伝える：

> 「このファイルは自動では正しく読み取れませんでした。該当部分をテキストとして貼り付けていただくか、PDF/テキスト形式で書き出して再度パスを教えてください。」

## 会話ガイドライン

- マイルストーンの確定は常にユーザー主導。AIが勝手に日付を仮置きしない。
- `overview.md` §4 の実施者が未確定の行を埋める際は、`plan-project` の Block D と同じ観点（契約形態とのすり合わせ、UAT・本番インフラ構築はクライアント側になりやすい点）に注意する。
- 稼働キャパシティのヒアリング（Block C）は、`overview.md` §1「契約形態」を先に確認し、ラボ型/SESなら「人日/月」、請負なら「プロジェクト全体の総アサイン人日」で聞く。契約形態自体が未確定の場合は先にそれを確認する。
- 工数・キャパシティ・依存関係など数値・判断が必要な項目は、ユーザーの明示的な回答なしに確定しない。
- Story分解の粒度（1機能=1Story か グルーピングか）は `references/wbs-breakdown.md` の基準で自動判定してよいが、グルーピングした場合はグループ内容をユーザーに一言確認する。

## メインフロー

### Step 1: 入力の確認

見積書(工数) をユーザーから確認する。ファイルパスなら `Read`、貼付けならそのまま内容として扱う。読めない形式は上記のフォールバック文言で案内する。未提供の場合はStep 6のヒアリングで埋める前提で進める。

### Step 2: 既存ファイルの確認

`schedule.md` / `overview.md` / `stakeholders.md` / `function-list.md` を `Read` し、以下を洗い出す：

- `schedule.md` の各セクションが未記入（テンプレート例のみ）か記入済みか。記入済みの場合は無断で上書きせず、既存値を提示して更新するか確認する
- `overview.md` §4 の作業項目のうち、実施者列が空の行
- `overview.md` §1「契約形態」（Block C・キャパシティ単位の判定に必須。未確定なら先に確認する）
- `stakeholders.md` §2 の「アサイン工数（稼働）」列が空のメンバー
- `function-list.md` の機能一覧（件数・優先度・対象ロール）

`overview.md` §4 が大半未確定、かつ `function-list.md` も空の場合は、「先に `plan-project`（PLAN）・`gather-requirements`（REQ）を実行すると、対応範囲やスコープを踏まえたスケジュールが作りやすくなりますが、このままヒアリングで進めることもできます」と1問だけ確認する。ブロックはしない。

### Step 3: マイルストーンのヒアリング（Block A）

`references/hearing.md` Block A に従い、マイルストーン名・予定日・完了条件（Deliverable）を聴取する。確定するたびに `Edit` で `schedule.md` §2 に追記する（既存の `M-01` はテンプレート例として実データで上書きする）。

### Step 4: スコープ確定（`overview.md` §4 の突き合わせ）

`references/wbs-breakdown.md` の対応表に従い、`overview.md` §4 の13作業項目のうち **実施者が「Sun*」または「共同」の行のみ** をEpic化対象とする。

- 実施者が空の行 → その場でヒアリングし（Block Aと同様、契約形態とのすり合わせに注意）、`overview.md` §4 に `Edit` で書き戻す。実質変更があれば `overview.md` の改訂履歴にも1行追記する
- 実施者が「クライアント」のみの行 → Epic化しない。隣接するSun* Epicの「依存関係」列に注記する（例: UAT開始はクライアント側日程に依存）

### Step 5: Story分解（`function-list.md` 連携）

`references/wbs-breakdown.md` の粒度判定基準に従い、要件定義／基本設計・詳細設計／開発・実装／単体テスト（UT）の各Epicについて、`function-list.md` の機能からStoryを生成する：

- 機能数が少ない（目安15件以下）→ 1機能 = 1Story
- 機能数が多い → 関連機能をグルーピングして1Story化し、グループ内容をユーザーに確認する

生成したStory ID を `function-list.md` の「関連WBS ID」列に `Edit` で書き戻す（既存の記入済みセルは上書きしない）。結合テスト（IT）／システムテスト（ST）／受入テスト（UAT）／ドキュメント作成／データ移行／本番環境構築／本番リリース作業／運用・保守／障害対応の各Epicは機能単位ではなく工程単位のStoryとする（詳細は `references/wbs-breakdown.md`）。

### Step 6: 工数の確定（Block B）

各Epic/Storyについて、Step 1の見積書(工数)から工数（人日）を取得できるものは反映する。取得できないものは `references/hearing.md` Block B に従ってヒアリングする。

### Step 7: 稼働キャパシティの確認（Block C）

`stakeholders.md` §2 の「アサイン工数（稼働）」列が空のメンバーについて、`overview.md` §1「契約形態」に応じた単位（ラボ型/SES→人日/月、請負→プロジェクト全体の総アサイン人日）でヒアリングし、`Edit` で書き戻す。実質変更があれば `stakeholders.md` の改訂履歴にも1行追記する。

### Step 8: 日程計算

マイルストーンの予定日を起点に、`references/wbs-breakdown.md` のデフォルト依存関係ルール（要件定義→設計→開発→UT→IT→ST→UAT→本番リリース、ドキュメント作成/本番環境構築は並行 等）と、工数÷稼働キャパシティから、各WBS行の開始日（予定）・終了日（予定）を算出する。`overview.md` §3「進め方」がアジャイルの場合は厳密な直列フェーズにせず、スプリント/機能単位の並行を許容して算出する。算出結果は関連マイルストーンID・依存関係列とあわせて `schedule.md` §3 に記載する。

### Step 9: 前提条件の記入

ヒアリング中に出てきたスケジュール上の前提（例: クライアント側レビューのリードタイム、特定メンバーの参画開始日）を `schedule.md` §1 に記載する。

### Step 10: ファイルへの反映・改訂履歴

各Stepで確定した内容は都度 `Edit` する。実質的な変更を行ったファイル（`schedule.md` は必須、`overview.md`/`stakeholders.md`/`function-list.md` は変更があった場合のみ）には、そのファイル自身の改訂履歴に日付・更新者（`plan-schedule skill` または対話中のペルソナ名）・内容を1行追加する。

### Step 11: 完了サマリ

作成したEpic/Story数、マイルストーン件数、算出したスケジュールの期間を要約する。未確定のまま残った項目（`overview.md` §4のヒアリング保留分、キャパシティ未確定メンバー等）を、後続Skill（`report-project`/REP等）が着手する前の前提として明示する。

## エラー時の対応

- 読めないファイル形式 → 上記「入力の受け取り方」のフォールバック文言で案内する
- 見積書(工数)とヒアリング結果が矛盾する（例: 見積書の工数とユーザーの発言が異なる）→ 両方の記載を提示し、ユーザーに確定してもらう
- 既存ファイルの実データを上書きしそうな場面 → 必ず確認を取ってから実行する
- 稼働キャパシティ・工数が最後まで確定しない → 該当WBS行の開始日・終了日は空欄のまま残し、Step 11の完了サマリで未確定事項として報告する（無理に日付を仮置きしない）

## 関連ファイル

- `references/hearing.md` — ヒアリングBlock A〜Dの詳細
- `references/wbs-breakdown.md` — Epic化条件・Story粒度判定・依存関係ルール・日程算出の考え方
- [`../../../docs/01_management/schedule.md`](../../../docs/01_management/schedule.md)
- [`../../../docs/01_management/overview.md`](../../../docs/01_management/overview.md)
- [`../../../docs/01_management/stakeholders.md`](../../../docs/01_management/stakeholders.md)
- [`../../../docs/02_requirements/function-list.md`](../../../docs/02_requirements/function-list.md)
