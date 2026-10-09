---
date: 2026-10-09
last_updated: 2026-10-09
project: agentic-streaming-videoqa
type: implementation
status: implemented
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
3. raw outputとvalidation結果を新しいMarkdownへ保存する。

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
answer-replay-YYYY-MM-DD_HH-MM-SS.md
```

既存fileを上書きしない。

最低限:

```markdown
# Answer Replay

- Source run:
- Source code version:
- Replay code version:
- Original status:
- Original error:
- Answer model:
- Prompt ID:
- Prompt version:
- Prompt hash:
- Generation:

## Question

...

## Choices

1. ...
2. ...

## Final Summary

...

## Raw Answer

...

## Validation

- Status:
- Code:
- Cause:
- Expected:
- Actual:
- Elapsed:
- Generated tokens:
- Hit max_new_tokens:
```

replay自体がvalidation失敗してもMarkdownを必ず生成する。

model load等、ModelResponse取得前に失敗した場合も、取得できた範囲のprovenanceと詳細なerror causeをMarkdownへ残す。

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
- existing normal run testsが非回帰。

実Qwen replayは実装成功条件に含めない。

## 12. Success Criteria

1. 実装中心が `diagnostics/answer_replay.py` に閉じている。
2. 新しいRun mode / Workflow / Sessionを追加しない。
3. 元Runはread-only。
4. 元RunのFinal Summaryと保存済みAnswer設定だけでAnswerを再実行する。
5. validation成否にかかわらずraw Answerを新規Markdownへ残す。
6. validation failureの原因が期待値と実際値を含めて人間向けに説明される。
7. current Prompt / current configへ依存しない。
8. Situation / Summary / video decodeを再実行しない。
9. 通常RunのAnswer保存契約を変更しない。
10. 短時間testが成功する。

## 13. Ambiguity Gate

### blocking

なし。

### non-blocking

- diagnostics packageの `__init__.py` 公開範囲。
- ModelResponse捕捉用の小さなwrapper/helper名。
- Markdown rendererを同file内private helperにするかどうか。
- CLI argument名の細部。

不要な抽象化を追加せず、既存styleに合わせる。

## 14. Spec Gate

ユーザーは2026-10-09に本specを承認し、実装とcommitを明示的に依頼した。

## 15. Implementation Handoff

- approved spec: 承認後、本spec
- 実装目的: failed RunのFinal SummaryからAnswerだけ再実行し、raw Answerとvalidation原因を別Markdownへ保存する。
- baseline: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `15063a7a0c7037cb1e484f10973b0bec16b02b98`
- core file: `src/longvideoqa_workbench/diagnostics/answer_replay.py`
- 対象外: Section 10
- success criteria: Section 12
- 長時間run: 未許可
- 実Qwen replay: 実装完了後に別途明示実行

## 16. Implementation Status — 2026-10-09

- 実装commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@4b0b25e`
- `diagnostics/answer_replay.py`で保存artifactからAnswerだけを1回呼び、raw responseと形式・選択番号・選択肢本文のvalidation結果を新規Markdownへ記録する。
- `longvideoqa answer-replay <RUN_ID>` と `./scripts/workbench.sh answer-replay <RUN_ID>` を追加した。
- compileall、Answer replayのFake/test-double 8ケース（validation 4種、model resolve/generate error、非上書き、CLI）、既存Fake三Agent CLI run、`bash -n` を確認した。
- Workbench `.venv` にpytestがないため、pytest runner自体での実行は未実施。テスト関数はPython 3.12上でfixture shimを使って実行した。
- 実Qwen replayは未実施。元Run artifact、通常Run経路、validator、Record schema、trace表示は変更していない。
