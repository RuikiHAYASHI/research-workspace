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
