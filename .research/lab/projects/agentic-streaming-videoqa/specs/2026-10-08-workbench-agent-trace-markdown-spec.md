---
date: 2026-10-08
last_updated: 2026-10-08
project: agentic-streaming-videoqa
type: implementation
status: superseded
target_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 5a4de708b1ac645fe17452420fc85ab9226dd53d
depends_on:
  - 2026-10-07-workbench-runtime-workflow-record-simplification-spec.md
source_brainstorm:
  - 2026-10-08-server-migration-offline-priorities.md
superseded_by: 2026-10-08-workbench-run-artifact-trace-simplification-spec.md
---

# Workbench Agent Trace Markdown 出力 spec

> **Superseded:** Run artifact構成・Answer保存・frame永続化までscopeが拡張されたため、実装契約は `2026-10-08-workbench-run-artifact-trace-simplification-spec.md` へ置き換えた。本specから実装しない。

## 1. 目的

1本の動画・1つのQAを実行したとき、各windowでSituation AgentとSummary Agentが何を出力し、EOFでAnswer Agentが何を出力したかを、人間が一目で時系列確認できるMarkdown表として保存する。

このMarkdownは精度評価表ではない。現段階では正誤判定、failure分類、複数run比較を行わず、**3 Agentの実際のsemantic outputを見やすく並べることだけ**を目的とする。

NotionやMarkdown対応ツールへそのままコピーしやすい、余計な説明を含まない単純な表を生成する。

## 2. Authority / 関連specとの関係

本specの現在要求は、2026-10-08のユーザー判断を最優先とする。

採用済み判断:

- 人間確認用の形式はCSV / TSVではなくMarkdown表とする。
- 表で確認したいのはSituation Agent、Summary Agent、Answer Agentの出力。
- 現段階では正誤判定を行わない。
- 複数動画の一括比較を目的にしない。
- 時間的な処理単位の表示名は `Window` を用いる。
- Workbench内部の機械可読なJSON / JSONLは維持し、人間向けMarkdownはそこから生成する派生物とする。

本specは `2026-10-07-workbench-runtime-workflow-record-simplification-spec.md` のRecord v2契約を前提とする。

そのspecでは新Runの機械可読な正本を原則として、

```text
execution_settings.json
resolved_prompts.json
question.json
run_status.json
turns.jsonl
final_answer.json
```

とし、`turns.jsonl` に各completed windowのSituation / Summary結果、`final_answer.json` にAnswer結果を保存する契約としている。

本specはこの6 fileを置き換えない。新たに生成する `agent_trace.md` は**canonical Recordではなく、canonical Recordから決定的に再生成可能なhuman-readable projection**とする。

## 3. 現行GitHub実装の確認

2026-10-08確認時点のGitHub remote `main`:

```text
RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
main@5a4de708b1ac645fe17452420fc85ab9226dd53d
```

remote `main` では、まだ旧Situation / Memory / Answer契約と旧Record構成が残っている。

確認できる現行実装:

- `presentation/PresentationService` がread-only projectionを担当する。
- `presentation/text_trace.py` が時系列のテキストtraceを生成する。
- 現在は `run_trace.md` を生成している。
- 現在の `run_trace.md` はMarkdown表ではなく、Agent名と出力を縦に並べる形式。
- 現在のRecordは `chunks.jsonl / stages.jsonl / memory.jsonl / memory.json / turns.jsonl / final_answer.json` 等を使用する。
- 現在の `turns.jsonl` はwindow / finalの順序情報を持つが、Situation / Summary semantic outputそのものはRecord v2の形では格納されていない。
- `tests/test_presentation.py` は `run_trace.md` の生成と、Presentation failureがinferenceを失敗させないことを検証している。

したがって、**旧RecordへMarkdown表を追加実装してからRecord v2で作り直す二重実装は行わない。**

実装時は、依存specのRecord v2が `main` に取り込まれた状態を新しい実装基準とする。

## 4. 採用する出力

新Runのrun directoryに、次のderived artifactを生成する。

```text
<run_id>/
└─ agent_trace.md
```

内容は原則として表だけとし、タイトル、説明、Question、Choices、model、Prompt、設定値等を前置きしない。

標準形:

```markdown
| Window | Situation Agent | Summary Agent | Answer Agent |
|---:|---|---|---|
| 1 | A man picks up a glass. | A man picks up a glass. | — |
| 2 | He pours water into the glass. | A man picks up a glass and pours water into it. | — |
| 3 | He places the glass on the table. | A man picks up a glass, pours water into it, and places it on the table. | — |
| EOF | — | — | 2. He places the glass on the table. |
```

## 5. 表の意味

### 5.1 Window列

Window列はAgent出力ではなく、時系列を追うための最小限の構造情報として残す。

- completed windowを1行ずつ表示する。
- 人間向け表示は1-basedとする。
- Record v2の `window.index` が0-basedなら、表示値は `window.index + 1`。
- 時刻範囲はこの表へ追加しない。
- `chunk` や `clip` ではなく `Window` と表記する。

### 5.2 Situation Agent列

Record v2のcanonical semantic output:

```text
turn.situation.situation_description
```

を表示する。

以下は表示しない。

- raw output。
- Prompt。
- generation settings。
- model info。
- elapsed time。
- frame metadata。
- validation metadata。

### 5.3 Summary Agent列

Record v2のcanonical semantic output:

```text
turn.summary.summary
```

を表示する。

各行には、そのwindow処理後のSummaryをそのまま表示する。

### 5.4 Answer Agent列

通常のwindow行では構造上適用されないため `—` とする。

EOF後に `final_answer.json` が存在するときだけ、最後に `EOF` 行を1行追加し、canonical semantic output:

```text
final_answer.answer
```

を表示する。

EOF行のSituation / Summary列は構造上適用されないため `—` とする。

最終SummaryをEOF行へ重複表示しない。最後のwindow行のSummaryを最終Summaryとして読める構造を維持する。

## 6. Markdown cell整形

Agent出力は意味内容を変えずに表示する。

Markdown tableを壊さないため、必要最小限の表示用escapeだけを行う。

必須:

1. 改行コードを正規化する。
2. cell内の改行は `<br>` へ変換し、1 Agent出力が1 table cell内に留まるようにする。
3. literal `|` はMarkdown table separatorとして解釈されないよう `\|` へescapeする。
4. Unicode、日本語、英語、句読点はそのまま保持する。
5. Agent outputを要約、切り詰め、翻訳、評価しない。

canonical JSON / JSONL側の値は変更しない。escapeは `agent_trace.md` のpresentation時だけ行う。

## 7. Source of Truthと生成責務

データフロー:

```text
Situation / Summary / Answer
        ↓
RunSession
        ↓
RecordService
        ↓
turns.jsonl / final_answer.json   # canonical
        ↓
PresentationService
        ↓
agent_trace.md                    # derived
```

原則:

- WorkflowはMarkdown file名やtable syntaxを知らない。
- AgentはMarkdown生成を知らない。
- RecordServiceはcanonical machine artifactを保存する。
- PresentationServiceまたはその配下のMarkdown rendererがread-onlyでMarkdownを生成する。
- MarkdownからJSON / JSONLへ逆変換しない。
- 同じcanonical Recordから再生成した場合、同じMarkdown内容になる決定的projectionとする。

## 8. 生成タイミング

最小要件として、completed windowのcanonical record保存後にtraceを更新でき、EOF Answer保存後に最終EOF行を含むtraceへ更新できるようにする。

期待挙動:

```text
Window 1 completed
  -> turns.jsonl更新
  -> agent_trace.md: Window 1まで

Window 2 completed
  -> turns.jsonl更新
  -> agent_trace.md: Window 1-2

...

EOF Answer completed
  -> final_answer.json保存
  -> agent_trace.md: 全Window + EOF
```

ただしMarkdown生成はinferenceの科学的正本ではない。

Markdown生成に失敗しても:

- Agent inference結果を失敗扱いにしない。
- canonical Recordを書き戻さない。
- run statusをMarkdown失敗だけで `failed` にしない。

既存のPresentation failure isolation方針を維持する。

## 9. Partial / Failed Run

### Partial run

EOF前でもcompleted windowが存在すれば、そのwindowまでの表を生成できる。

Answerがまだ無い場合はEOF行を生成しない。

### Failed run

失敗前にcompleted windowがcanonical Recordへ保存済みなら、その範囲までの表は生成可能としてよい。

表に以下は追加しない。

- Error列。
- Failure reason。
- Failed status。
- 正誤判定。

それらは `run_status.json` 等のcanonical artifactで確認する。

### Required field欠損

Record v2でcompleted windowに必須のSituation / Summary semantic outputが欠損している場合、架空のAgent出力を `—` で補完しない。

rendererはinvalid sourceとして扱い、derived artifact生成失敗として隔離する。

`—` は「そのAgentがその行では構造上実行されない」場合だけに使用する。

## 10. 既存run / Legacy互換

既存Legacy Runはread-only要件を維持する。

本specでは:

- Legacy artifactから新 `agent_trace.md` を自動backfillしない。
- Legacy artifactをRecord v2へmigrationしない。
- Legacy Runへ追記しない。
- 既存の `run_trace.md` が保存済みの場合、それを削除・書換えしない。

新Runで旧 `run_trace.md` と新 `agent_trace.md` を並行生成しない。

依存spec実装後も旧text trace renderer / `run_trace.md` 生成経路が新Run専用コードとして残っている場合、新 `agent_trace.md` への切替後にrepo-wide参照を確認し、不要な旧renderer / helper / testは削除または新責務へrenameする。

Legacy read-only表示に必要な処理まで削除しない。

## 11. canonical Record契約への影響

本specは `turns.jsonl` と `final_answer.json` のschemaをMarkdownのためだけに変更しない。

依存specのRecord v2に以下が存在することを前提とする。

```text
turn.window.index
turn.situation.situation_description
turn.summary.summary
final_answer.answer
```

もし実装済みRecord v2のfield名が同じ意味を保ったまま局所的に異なる場合は、最新approved specと実コードを照合し、Presentation側を現在schemaへ合わせる。

Markdownのためだけにduplicate fieldをcanonical Recordへ追加しない。

## 12. 対象外

本specでは以下を行わない。

- Situation / Summary / AnswerのPrompt変更。
- Agent model outputの変更。
- Agent精度評価。
- `○ / △ / ×` 等の判定。
- Failure Category。
- Ground Truth annotation。
- Question / Choices / Correct AnswerのMarkdown表示。
- Window start/end timeのMarkdown表示。
- frame thumbnailのMarkdown埋め込み。
- model / Prompt / generation / latencyのMarkdown表示。
- 複数動画・複数QA・複数Runの集計表。
- CSV / TSV出力。
- Excel / Spreadsheet出力。
- HTML table出力。
- Notion API連携。
- Markdownからの再実行 / resume。
- Legacy artifact migration。
- Browserの大規模UI変更。
- 新dependency導入。
- 実Qwen / GPU / LongVideoBench full run。
- model download。

## 13. 実装対象候補

依存spec実装後の実コードを再確認した上で、責務としては次を対象とする。

第一候補:

```text
src/longvideoqa_workbench/presentation/
tests/test_presentation.py
```

必要に応じて:

```text
src/longvideoqa_workbench/runtime/
src/longvideoqa_workbench/records/
tests/<runtime or record integration tests>
README.md / docs/development.md
```

ただし、Markdown rendererを追加するためにRecord / Workflowへ不要な抽象化を増やさない。

現在の `presentation/text_trace.py` が依存spec実装後も残っている場合は、責務をMarkdown表へ置き換えるか、実際の名前へrenameする。

backup目的で旧renderer copyを残さない。

## 14. 推奨実装順

Stepは実装順を示すだけで、Stepごとにbranchを作らない。

### Step 1: Markdown table renderer

- Record v2 projectionからWindow順にSituation / Summaryを取得する。
- Final AnswerがあればEOF行を追加する。
- cell escape helperを追加する。
- `agent_trace.md` の期待Markdown文字列をunit testで固定する。
- multiline、literal pipe、Unicodeを短時間testする。

verify:

- Presentation rendererのtargeted pytest。
- import / compile。
- `git diff --check`。

### Step 2: Run artifactへの接続

- completed window保存後にderived Markdownを更新できるよう接続する。
- EOF Answer保存後にEOF行を追加する。
- Presentation failureがrun successを変更しないことを維持する。
- 旧 `run_trace.md` の新Run生成を停止する。
- 不要になった旧text trace helper / aliasを参照監査後に削除する。

verify:

- 2 window以上のFake run。
- EOF前のpartial trace。
- EOF後のfinal trace。
- Presentation failure isolation test。
- Record canonical artifact非変更の確認。

### Step 3: 最終回帰

- repository-wide reference監査。
- 関連README / development docに `agent_trace.md` がderived human-readable artifactであることを必要最小限追記する。
- full短時間回帰を実施する。

verify:

- full short pytest。
- compileall。
- Fake CLI smoke。
- Fake browser/API smokeのうち現在の既存suiteに含まれる範囲。
- `git diff --check`。
- `git status`。

## 15. Git運用

### 15.1 実装開始条件

依存するRuntime / Workflow / Record簡略化specが実装され、新Record v2が `main` に存在することを確認してから本specを実装する。

実装開始時に必ず確認する。

- `main` の最新commit。
- 現在branch。
- dirty state。
- Record v2の実schema。
- PresentationServiceの現構造。
- 旧 `run_trace.md` の参照有無。

本spec記載の `baseline_commit: 5a4de...` はspec作成時のremote確認点であり、実装branchの固定起点ではない。

### 15.2 Branch

実装では、その時点の最新 `main` から**1本だけ**実装branchを作成する。

推奨branch名:

```text
feat/agent-trace-markdown
```

Stepごと、micro-stepごとにbranchを増やさない。

### 15.3 Micro-commit

実装branch内で、独立して説明・検証できる意味単位のmicro-commitを積む。

原則:

- 1 commit = 1つの目的として読める変更。
- 小さすぎるcommitへ過度に分割しない。
- 異なる責務を無関係に1 commitへ混在させない。
- 各commit後、その変更に最も近い短時間test / compile / smoke checkを実施する。
- 全体回帰は実装branch完成時に行う。
- squash前提にせず、変更理由を追える意味のある履歴を残す。

推奨する意味単位は、実コードの差分量に応じて概ね次の2つ。

1. Markdown rendererと単体test。
2. Runへの生成接続、旧trace整理、integration test / 必要な文書更新。

無理に2 commitへ固定せず、既存構造上1つの責務になる場合は過度に分割しない。

### 15.4 Commit message

commit messageは日本語で、**タイトル + 本文5〜6行程度**を基本とする。

本文は箇条書きにせず、文章で以下が分かる内容にする。

- 何を変更したか。
- なぜ変更したか。
- どの責務・経路へ影響したか。
- 何を検証したか。

例:

```text
Agent出力をMarkdown表へ投影する

Record v2のSituationとSummaryをwindow順に並べるrendererを追加した。
EOF後はAnswerを最終行へ加え、人間が3 Agentの流れを追える形式にした。
複数行と区切り文字は表示時だけescapeし、canonical Recordは変更していない。
Presentation層だけで生成することでWorkflowとAgentの責務を維持した。
関連するrenderer testとcompile checkで表形式と特殊文字を確認した。
```

### 15.5 旧実装削除

過去実装への復帰はGit historyを利用する。

- backup目的のold file / copy / aliasをrepository内へ残さない。
- 新経路から不要になったfile、alias、helper、legacy implementationはrepo-wide参照を確認して削除する。
- Legacy Runのread-only閲覧に現在必要な最小互換処理はLegacy責務として残す。

### 15.6 Codex / 実装者のGit権限

許可:

- 現在状態の確認。
- 最新 `main` から1本の実装branch作成。
- 実装。
- 短時間検証。
- micro-commit作成。

禁止:

- `main`へのmerge。
- remote push。
- Pull Request作成。
- 既存commit historyのrewrite。

実装完了時のゴールは、

> **実装branchの最新commit上で、本specの機能と短時間検証が正常に成立していること。**

最終的な `main` へのmergeとpushは、ユーザーが実装確認後に行う。

## 16. Success Criteria

1. 新Runで `agent_trace.md` を生成できる。
2. Markdownは `Window / Situation Agent / Summary Agent / Answer Agent` の4列だけを持つ。
3. completed windowごとに1行あり、Window表示は1-based。
4. 各window行のSituationはcanonical `situation_description` と一致する。
5. 各window行のSummaryはcanonical `summary` と一致する。
6. 通常window行のAnswer列は `—`。
7. Final Answerが存在するときだけEOF行が1行追加される。
8. EOF行のAnswerはcanonical Answerと一致する。
9. EOF行のSituation / Summaryは `—`。
10. 最終SummaryをEOF行へ重複表示しない。
11. Agent outputの改行は `<br>` へ変換され、1 cell内に留まる。
12. Agent output内のliteral pipeがtable列を破壊しない。
13. Unicodeを保持する。
14. Agent outputを要約・翻訳・切詰め・評価しない。
15. Question / Choices / time / model / Prompt / latency /正誤等の追加列を作らない。
16. `agent_trace.md` はcanonical Recordから決定的に再生成可能。
17. Markdown生成はcanonical JSON / JSONLを変更しない。
18. Markdown生成失敗だけでinference/runをfailedにしない。
19. partial runでは保存済みcompleted windowまで表示し、Answerが無ければEOF行を作らない。
20. required semantic output欠損時に架空値を補完しない。
21. 新Runで旧 `run_trace.md` と `agent_trace.md` を二重生成しない。
22. Legacy Runをmigration / backfill / overwriteしない。
23. 不要になった旧trace実装をbackup目的で残さない。
24. 新dependencyを追加しない。
25. Fakeによる2 window以上の短時間integration testで最終Markdownを確認できる。
26. full短時間test / compileall / diff checkが成功するか、環境依存failureを明確に分離して報告する。
27. 実Qwen / GPU / LongVideoBench full runを実装成功条件に含めない。

## 17. Ambiguity Gate

### blocking

実装開始について1件ある。

- 依存する `2026-10-07-workbench-runtime-workflow-record-simplification-spec.md` のRecord v2が、2026-10-08時点のGitHub remote `main` では未確認である。

本spec自体のMarkdown表仕様にはblocking ambiguityはない。

実装時に旧Recordへ暫定対応を追加せず、Record v2が `main` に存在することを確認してから着手する。

### non-blocking

以下は現在のコードstyleに合わせて実装者が決めてよい。

- renderer関数名。
- `text_trace.py` をrenameするか、新しい名前へ置き換えるか。
- cell escape helperを同fileに置くかprivate helperへ分けるか。
- PresentationServiceからのprivate method名。
- targeted testの具体的な分割。

ただし単一用途のために新しい汎用formatter frameworkを作らない。

## 18. Spec Gate

本specは、2026-10-08のユーザー判断を実装可能な契約へ変換した**draft**である。

Markdownの内容・scopeについてはblockingな未決事項はない。

ただし、実装依存先のRecord v2がGitHub remote `main` にまだ確認できないため、本spec単独で旧Recordへ実装を開始しない。

ユーザーが本specを確認して明示承認し、かつ依存Record v2が実装済み `main` に存在することを確認した後、

```text
draft -> approved
```

として `engineering-task` へ引き継ぐ。

## 19. Implementation Handoff

- approved spec: 承認後、本spec
- 実装目的: Situation / Summary / Answerのsemantic outputを1本のMarkdown表へ時系列投影し、Notion等へそのまま持ち込めるhuman-readable traceを生成する。
- 基準repository: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`
- spec作成時確認commit: `main@5a4de708b1ac645fe17452420fc85ab9226dd53d`
- 実装基準: Record v2を含む実装済み最新 `main`
- 変更scope: Presentation Markdown renderer、runへのderived artifact生成接続、関連test、不要な旧trace整理、必要最小限の文書更新。
- 対象外: Section 12。
- success criteria: Section 16。
- 許可される短時間検証: renderer unit test、Fake 2+ window integration、partial/final trace、Presentation failure isolation、compileall、既存short pytest、Fake CLI/browser smoke、diff check。
- 長時間run: 未許可。
- Git: 最新mainから1 implementation branch、意味単位micro-commit、commit messageは日本語タイトル+本文5〜6行程度。main merge / push / PRは禁止。
- 旧実装: backup copy禁止。新Runから不要になった旧trace実装は参照監査後に削除。Legacy read-onlyに必要な最小処理だけ残す。
- 未検証予定: 実Qwen出力を用いたMarkdownの実見栄え、Notionへの実貼付操作、長尺動画での可読性。
