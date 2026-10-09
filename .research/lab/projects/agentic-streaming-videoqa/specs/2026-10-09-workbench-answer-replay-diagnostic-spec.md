---
date: 2026-10-09
last_updated: 2026-10-09
project: agentic-streaming-videoqa
type: implementation
status: approved
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 15063a7a0c7037cb1e484f10973b0bec16b02b98
source_brainstorm:
  - 2026-10-09-answer-validation-diagnostics.md
---

# Workbench Answer-only replay diagnostic spec

## 1. 目的

既存のfailed Runを動画先頭から再実行せず、保存済みFinal SummaryからAnswer Agentだけを1回再実行して、生出力とvalidation結果を確認できる診断機能を追加する。

今回は将来案Aである「通常RunのAnswer validation失敗時にraw outputを自動保存する変更」は実装しない。

## 2. 採用する構造

新しいRun mode、Workflow、Session、Record schemaは追加しない。

診断実装の中心は次とする。

```text
src/longvideoqa_workbench/diagnostics/
└── answer_replay.py
```

責務は次の3点だけ。

1. 元Runの `result.json` をread-onlyで読む。
2. 元Run保存時と同じAnswer条件でAnswer Agentを1回だけ呼ぶ。
3. 元の `trace.md` と同じ表示を基準にした新しいMarkdownへreplay結果を投影し、validation失敗時だけraw outputと詳細errorを追加する。

`RunService`、`RunSession`、`VideoQAWorkflow`、元Runの `result.json` / `trace.md` は変更しない。

## 3. Replay入力

元Runの保存済みartifactから次を使う。

- Question
- Choices
- 最後に保存されたSummary
- Answer backend
- Answer model_id
- Answer generation
- Answer Prompt snapshot
  - prompt_id
  - prompt_hash
  - prompt_version
  - body
- source code_version

current default configやcurrent PromptServiceからPrompt本文を解決し直さない。

元Run snapshotを正本とする。

## 4. 実行

Answer replayではSituation / Summary / video decode / frame samplingを実行しない。

概念入力:

```text
Question
+ Choices
+ Final Summary
+ original Answer Prompt body
+ original backend/model
+ original generation
-> existing Answer Agent
```

既存AnswerAgentと既存ModelAdapterを利用する。

通常RunのAnswer semantic contractは変更しない。

## 5. raw output捕捉

既存AnswerAgentがvalidation errorをraiseしても、診断側でModelResponseを捕捉できるようにする。

通常RunのAnswerAgentの保存挙動は今回は変更しない。

diagnostics側で必要なraw情報:

- response text
- raw_output
- generated_tokens
- hit_max_new_tokens
- elapsed_seconds
- model_info

既存Qwen adapterのModelResponseを正本とし、同じ回答生成処理を別実装しない。

## 6. エラー原因の記述

「validation failed」だけでは診断完了としない。

Markdownには、可能な限り次を明記する。

- validation status
- validation stage / code
- 人間向けの詳細な原因
- expected format / expected value
- actual raw output
- 選択番号が読めた場合、その番号
- その番号に対応するexpected choice text
- actual choice textとの差
- generated_tokens
- hit_max_new_tokens

少なくとも現行3 failureを区別する。

- format mismatch
- choice index out of range
- choice text mismatch

例:

```text
Validation failed: choice_text_mismatch.
The model selected choice 2, but the text after "2." did not exactly match choice 2 after the same normalization used by AnswerAgent.
Expected: "..."
Actual: "..."
```

将来Aを実装する場合も、同じ方針で原因を丁寧に記述する。

## 7. Markdown出力

元Run directory内へ新しいfileとして保存する。

```text
trace-answer-replay-YYYY-MM-DD_HH-MM-SS.md
```

既存の `trace.md` と元Run artifactは上書きしない。

新しいMarkdownは独自の長いreport形式ではなく、**元の `trace.md` がAnswer replay後に更新されたかのような形式**を正本とする。

基本形:

```markdown
# Run Summary

- Question: ...
- Ground truth: ...
- Model answer: ...
- Correct: ...
- Total runtime: ...
- Total inference time (recorded stages + replay Answer): ... s

| Window | Range | Situation Agent | Situation time (s) | Summary Agent | Summary time (s) | Window inference time (s) | Answer Agent |
|---:|---|---|---:|---|---:|---:|---|
| 1 | ... | ... | ... | ... | ... | ... | — |
...
| EOF | — | — | — | — | — | — | ... |

## Replay Metadata

- Source run: ...
- Source code version: ...
- Replay code version: ...
- Answer replay time: ... s
```

Question、Window表、Situation / Summary本文・時間は元Runと同じprojectionを使う。

replayがvalidation成功した場合は、EOFのAnswer Agentへvalidated Answerを表示する。元Runにground truth / correctが保存済みならそれも通常traceと同様に表示し、保存されていなければ `—` のままとする。ground truth取得のためだけに新しいdatasetアクセスを追加しない。

### 7.1 trace rendererの再利用

同じMarkdown形式を二重実装しない。

必要なら現在の `v3_text_trace(record)` から、`result.json` payloadを受け取るpure rendererを最小抽出し、

- 通常 `trace.md`
- Answer replay Markdown

の両方から利用する。

通常 `trace.md` の既存出力は変更しない。抽出前後で既存fixture testの文字列が一致することを確認する。

### 7.2 Total runtime

`Total runtime` は現在のtrace contractを維持し、

```text
status.finished_at - status.started_at
```

のwall-clockとする。

両timestampが存在しない元Runでは `—` とする。

Window inference timeの和を `Total runtime` と呼ばない。

### 7.3 Total inference time

replay Markdownでは診断補助として、

```text
sum(all recorded Situation elapsed_seconds)
+ sum(all recorded Summary elapsed_seconds)
+ replay Answer elapsed_seconds
```

を `Total inference time (recorded stages + replay Answer)` として表示する。

これはmodel generate時間の合計であり、video decode、JPEG生成、Record I/O、ユーザー待機時間等を含まない。

元Runが途中停止している場合も計算可能だが、その場合は動画全体の総推論時間ではなく「保存済みstage分 + replay Answer」の合計であることをラベルで明示する。

### 7.4 validation失敗時だけ追加する診断節

validation成功時は基本trace + Replay Metadataだけでよい。

validation失敗時だけ、末尾へ次を追加する。

```markdown
## Answer Replay Error

### Raw Answer
...

### Raw output
...

### Model info
...

### Validation
- Status:
- Code:
- Stage:
- Cause:
- Expected:
- Actual:
- Answer replay time:
- Generated tokens:
- Hit max_new_tokens:
- Error detail:
```

`Expected` にはvalidationが実際に要求した形式またはchoiceを記載し、artifact復元条件の説明文を入れない。

model load等、ModelResponse取得前に失敗した場合も、新しいMarkdown自体は生成し、取得できたprovenanceと具体的なerror causeを末尾へ残す。

## 8. CLI

診断用entrypointとして、既存CLIから次を呼べるようにする。

```bash
./scripts/workbench.sh answer-replay <RUN_ID>
```

または内部CLIとして同等の `longvideoqa answer-replay` を公開する。

これは新しいRun modeではなくdiagnostic commandとする。

## 9. 再現性

同じbackend、model_id、Prompt snapshot、generation、Question、Choices、Final Summaryを使用する。

元Runとreplay時のcode_versionが異なる場合はMarkdownに両方を記録する。

temperature=0でもbit-exact再現を保証しない。「元Run保存条件を用いたAnswer-only diagnostic replay」と表現する。

## 10. 対象外

- 通常RunのAnswer validation失敗保存方式変更。
- `status.error.details` 追加。
- Record v3 schema変更。
- trace.md変更。
- validator緩和。
- Answer Prompt変更。
- max_new_tokens変更。
- Situation / Summary再実行。
- Browser UI追加。
- batch-run変更。
- 元Run artifactの上書き。

## 11. Verification

Fake ModelAdapterまたはtest doubleで少なくとも次を確認する。

- source RunからQuestion / Choices / Final Summary / Answer snapshotを復元できる。
- Answerだけを1回実行する。
- source `result.json` / `trace.md` を変更しない。
- validation successでもMarkdownが生成される。
- format mismatchでもraw outputと詳細原因が残る。
- out-of-rangeでも番号と範囲が残る。
- choice-text mismatchでもexpected / actualが残る。
- model generation前後のfailureでも可能な範囲の原因がMarkdownへ残る。
- output filenameが既存fileを上書きしない。
- replay MarkdownのRun SummaryとWindow表が通常traceと同じrenderer結果を基準にする。
- sourceにstarted_at / finished_atがあれば従来どおりTotal runtimeを表示する。
- Total inference timeが全recorded Situation / Summary時間とreplay Answer時間の和になる。
- sourceが未完了ならTotal runtimeを捏造せず `—` とする。
- validation successでは不要なraw/error節を出さない。
- validation failure時だけraw Answer / raw output / model info / 詳細validation原因を追加する。
- existing normal run testsが非回帰。

実Qwen replayは実装成功条件に含めない。

## 12. Success Criteria

1. 実装中心が `diagnostics/answer_replay.py` に閉じている。
2. 新しいRun mode / Workflow / Sessionを追加しない。
3. 元Runはread-only。
4. 元RunのFinal Summaryと保存済みAnswer設定だけでAnswerを再実行する。
5. 新しいMarkdownは通常 `trace.md` と同じRun Summary / Window表を基準にし、replay AnswerをEOFへ反映する。
6. validation成功時はraw diagnosticを常時表示せず、通常traceに近い簡潔な出力にする。
7. validation failure時だけraw Answer / raw output / model info / 詳細errorを追加する。
8. validation failureの原因が期待値と実際値を含めて人間向けに説明される。
9. `Total runtime` のwall-clock意味を変えず、別にrecorded stage + replay Answerの `Total inference time` を計算する。
10. current Prompt / current configへ依存しない。
11. Situation / Summary / video decodeを再実行しない。
12. 通常RunのAnswer保存契約を変更しない。
13. 短時間testが成功する。

## 13. Ambiguity Gate

### blocking

なし。

### non-blocking

- diagnostics packageの `__init__.py` 公開範囲。
- ModelResponse捕捉用の小さなwrapper/helper名。
- trace rendererをpure helperとしてどのprivate/public名で抽出するか。
- CLI argument名の細部。

不要な抽象化を追加せず、既存styleに合わせる。

## 14. Spec Gate

本specは現在 `draft`。

ユーザーが本specを承認した後に `approved` とし、engineering-taskへ引き継ぐ。

## 15. Implementation Handoff

- approved spec: 承認後、本spec
- 実装目的: failed RunのFinal SummaryからAnswerだけ再実行し、raw Answerとvalidation原因を別Markdownへ保存する。
- baseline: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `15063a7a0c7037cb1e484f10973b0bec16b02b98`
- core file: `src/longvideoqa_workbench/diagnostics/answer_replay.py`
- 対象外: Section 10
- success criteria: Section 12
- 長時間run: 未許可
- 実Qwen replay: 実装完了後に別途明示実行
