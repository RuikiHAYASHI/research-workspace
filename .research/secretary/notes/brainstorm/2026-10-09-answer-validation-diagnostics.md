---
date: 2026-10-09
project: agentic-streaming-videoqa
source_todo: null
topic: answer-validation-diagnostics
status: exploratory
tags: [brainstorm, answer, validation, diagnostics, record]
---

# Answer validation失敗の診断

## 出発点

初期Behavior実験では、20秒CanaryはAnswerまで成功した一方、長尺5条件は全windowのSituation / Summary処理後に `answer_validation_failed` で終了した。

失敗RunではAnswerの生出力がRecordへ残らず、形式失敗の具体内容を確認できない。

## 現行コードから確認できること

`workflow/answer.py` ではQwenの `response.text` を受け取った後、次の3段階で検証する。

1. `番号. 本文` の形式へfullmatchできるか。
2. 選択番号が1..Nの範囲内か。
3. 番号が指すchoice textと出力本文が、空白正規化・casefold後に完全一致するか。

いずれかで失敗すると `AnswerValidationError` をraiseし、`AnswerOutput` は作られない。

Qwen adapter自体は `ModelResponse.raw_output` に、

- text
- generated_tokens
- hit_max_new_tokens

を保持している。

しかし `RunRecord.fail()` は現在、

- exception type
- message
- category

だけを `status.error` へ保存する。

したがってAnswer validation失敗時には、Qwenの `response.text` / `raw_output` / elapsed / model infoが失われる。

## 現在の失敗Runから分かる範囲

`result.json.status.error.message` を確認すれば、少なくとも次のどれかは判別できる。

- 「番号. 選択肢文」形式ではない
- 選択番号が範囲外
- 選択番号とchoice textが一致しない

ただし実際のQwen textは保存されていないため、

- `2) ...`
- `The answer is 2. ...`
- `2. <choice> because ...`
- choiceの言い換え
- Markdown装飾
- 番号だけの回答

等のどれだったかは既存artifactから確定できない。

## 解釈

20秒Canaryでは同じvalidatorを通過しているため、validatorそのものが常に失敗するわけではない。

長尺5条件がすべて失敗した理由を、Summary長や768-token到達だけから断定することはできない。

最終SummaryはAnswerへ1本だけ渡されるため、Summaryが長いことは回答内容の品質には影響し得るが、「番号. exact choice text」の形式失敗原因とは別に検証する必要がある。

## 最有力の次対応

まずvalidatorの条件を緩和せず、失敗時のAnswer attemptを保存する。

保存したい情報:

- validation failure code
  - format_mismatch
  - choice_index_out_of_range
  - choice_text_mismatch
- response_text
- raw_output
- generated_tokens
- hit_max_new_tokens
- elapsed_seconds
- model_info
- prompt_id / prompt_hash / prompt_version
- generation

これにより、次の1件の実Qwen smokeだけで形式失敗の具体原因を確認できる。

## 保存設計候補

### 候補A: status.error.detailsへ保存

最小差分。

`AnswerValidationError` にdiagnostic情報を持たせ、`RunRecord.fail()` が安全にJSON化して `status.error.details` へ保存する。

利点:
- 現行 `answer=null` の意味を維持できる。
- Record schema変更が小さい。
- failed runの診断に十分。

### 候補B: top-level answer_attemptを追加

validated answerとraw attemptを明確に分離できる。

利点:
- research artifactとして意味がきれい。
- 成功/失敗を問わずAnswer attemptを保存しやすい。

欠点:
- Record / Presentation / Browserの変更範囲が広がる。

初回対応としては候補Aが有力。

## validator自体を緩める案について

raw outputを確認する前に緩めない。

例えば `2` だけを許可する、`2) choice` を許可する、説明文を切り捨てる等は、Answer semantic contractを変える。

まずraw outputを1件保存し、Qwenがどの形式を実際に返しているかをEvidenceとして確認してから判断する。

## 次の判断候補

1. 既存failed runの `status.error.message` を確認して3 failure branchのどれかを特定する。
2. Answer validation失敗時のdiagnostic保存をspec化する。
3. Fake testで3種類のfailureとraw output保存を確認する。
4. 実Qwenで短い1件だけsmokeし、raw Answerを観察する。
5. そのEvidenceを見てPrompt修正 / validator緩和 / max_new_tokens調整のどれが必要か判断する。


## 2026-10-09 11:02 JST 生出力確認の具体方針

最優先は正誤判定ではなく、Answer Agentが実際に返したraw textを観察することとする。

### 1. validation失敗時にもraw Answerを保存する

現行 `AnswerAgent.run()` ではModelResponse取得後にvalidationし、失敗するとAnswerOutputが作られない。
そこで `AnswerValidationError` にdiagnostic情報を保持させる。

最低限:

- validation_code
- response_text
- raw_output
- elapsed_seconds
- model_info
- generation
- prompt_id / prompt_hash / prompt_version

`RunRecord.fail()` はerrorに `details` が存在すれば `status.error.details` へJSON-safeに保存する。

成功時のAnswer保存契約は変更しない。

### 2. trace.mdでもfailed Answer attemptを見られるようにする

failed Answer attemptがある場合はtrace末尾へ、

```text
## Failed Answer Attempt
Validation: ...
Raw output: ...
Generated tokens: ...
Hit max_new_tokens: ...
```

を表示する。

final Answer失敗後にもtraceを再生成し、result.jsonを直接開かなくても診断できるようにする。

### 3. 既存failed runは動画を再処理しない

既存の長尺failed runは全windowのSituation / Summaryが既に保存済み。
したがって診断では、

- result.json.question.question
- result.json.question.choices
- 最後のturnのsummary.summary
- config内のAnswer prompt / generation / model設定

を読み、Answer Agentだけを1回再実行すればよい。

これは元Runを変更せず、別のdiagnostic outputとして扱う。

Answerはtext-onlyなので、動画decodeやSituation / Summaryを再実行する必要はない。

### 4. raw outputを見てから契約変更を判断する

観察後に次を区別する。

- `2) ...` 等の軽微なformat差
- `The answer is ...` 等の説明追加
- choice本文の言い換え
- 番号だけ
- max_new_tokens到達
- その他の異常出力

Evidence取得前にvalidatorやPromptを緩和しない。


## 2026-10-09 11:15 JST Answer-only replay方針

Answer validation失敗の診断では、元Runを変更せず、保存済みartifactからAnswer Agentだけを再実行する方向を採用候補とする。

### 再利用する元Run情報

元Runの `result.json` から次を読む。

- `question.question`
- `question.choices`
- 最終turnの `summary.summary`
- `config.execution.agents.answer.backend`
- `config.execution.agents.answer.model_id`
- `config.execution.agents.answer.generation`
- `config.prompts` 内のAnswer Prompt snapshot
  - prompt_id
  - prompt_hash
  - prompt_version
  - body

現在のPromptServiceからPrompt本文を再解決せず、元Run snapshotのbodyを正本として使う。

### replay実行

概念的には次の入力だけでAnswer Agentを1回呼ぶ。

```text
Question
+ Choices
+ Final Summary
+ original Answer Prompt snapshot
+ original model/backend
+ original generation
-> Answer Agent
```

Situation / Summary / video decode / frame samplingは再実行しない。

元Runの `result.json`、`trace.md`、statusは変更しない。

### 新しいMarkdown出力

元Run directory内へtimestamp付きの別fileを作る案を第一候補とする。

```text
answer-replay-YYYY-MM-DD_HH-MM-SS.md
```

最低限次を含める。

```markdown
# Answer Replay

- Source run: ...
- Source code version: ...
- Original status: failed
- Original error: ...
- Answer model: ...
- Prompt ID / version / hash: ...
- Generation: ...

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
- status: passed / failed
- code: ...
- message: ...
- elapsed_seconds: ...
- generated_tokens: ...
- hit_max_new_tokens: ...
```

validationが失敗してもraw Answerを必ず出力する。

### 再現性の考え方

同じbackend / model_id / prompt snapshot / generation / final summaryを使う。
現在のAnswer Promptやcurrent default configに依存させない。

temperature=0のgreedy generationであっても、replayを「元Runとbit-exactに同じ出力になる」とは主張せず、同条件でAnswer段階だけを再実行するdiagnosticとして扱う。

### CLI候補

```bash
longvideoqa answer-replay --run <RUN_DIR_OR_ID>
```

または既存shell wrapperに

```bash
./scripts/workbench.sh answer-replay <RUN_ID>
```

を追加する。

実装では既存Qwen adapter / AnswerAgent / validationを再利用し、新しいAnswerロジックを複製しない。
