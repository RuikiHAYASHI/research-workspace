---
date: 2026-10-09
project: agentic-streaming-videoqa
source_todo: null
topic: initial-behavior-result-analysis
status: exploratory
tags: [brainstorm, experiment, analysis, window, sampling, summary, answer]
---

# Initial behavior実験の結果分析方針

## 現在のrun構成

- canary-20s: succeeded
- three-min-w2: failed at Answer validation
- three-min-w4: failed at Answer validation
- three-min-w8: failed at Answer validation
- three-min-s025: failed at Answer validation
- three-min-s100: failed at Answer validation

long-video条件は同一の約186.81秒動画・同一Questionを使う。

Canaryは別動画・別Questionなので、長尺5条件との精度比較には使わずpipeline smokeとして扱う。

## 比較を二系統へ分離する

### Window長比較

`three-min-w2 / three-min-w4 / three-min-w8`

固定:
- sampling interval = 0.5秒
- 同一video / question
- 全動画で概ね同数のsampled frames

変更:
- Window長
- frames / window
- Window数
- Situation / Summary call回数

見るもの:
- total runtime
- total inference time
- 1 WindowあたりのSituation / Summary時間
- Summary max token到達率
- Final Summaryの長さ・重複・情報保持
- Answer replay結果

### Sampling密度比較

`three-min-w4 / three-min-s025 / three-min-s100`

固定:
- Window長 = 4秒
- Window数
- 同一video / question

変更:
- sampling interval
- frames / window
- 全sampled frames

見るもの:
- Situation timeの増減
- Summary timeへの波及
- visual detailの増減
- Final SummaryでQuestion関連Evidenceが残るか
- Answer replay結果
- accuracy / cost tradeoff

## 最優先の分析順序

1. 5 failed RunすべてにAnswer replayを行い、raw Answer、validation原因、parse可能なchoiceを取得する。
2. result.jsonからWindow数、sampled frames、各Agent elapsed、started_at / finished_atを集計する。
3. Summaryのmax_new_tokens到達回数と率を集計する。
4. Final SummaryをQuestion / Ground truthと照合し、回答に必要なEvidenceが explicit / ambiguous / absent / contradictory のどれかを人手で分類する。
5. Answer replayのchoiceが得られれば、official validationとは別にdiagnosticとして正誤を確認する。
6. Window長比較とsampling密度比較を別々に解釈する。

## 推奨集計列

Quantitative:
- case_id
- window_seconds
- sampling_interval
- frames_per_window
- actual_windows
- sampled_frames
- model_calls (= 2 * windows + 1)
- source total runtime
- total inference time
- avg Situation time / window
- avg Summary time / window
- Summary max-token hits
- Summary max-token hit rate
- final Summary token count

Answer / quality:
- replay validation
- raw / parsed answer
- correctness if parseable
- final Summary evidence status
- short observation

## Summary max-token既知値

- W2: 78 / 94 = 約83.0%
- W4: 27 / 47 = 約57.4%
- W8: 0 / 24 = 0%
- S025: 29 / 47 = 約61.7%
- S100: 41 / 47 = 約87.2%

この値は「細かいWindowほど必ず悪い」とはまだ言えない。
W2ではSummary更新回数が増えるため飽和しやすく、S100ではvisual inputが疎でもSummary更新回数はW4と同じなので別原因も考える必要がある。

## 解釈上の注意

- Answer validation failureをaccuracy failureと同一視しない。
- Canaryの正誤を長尺5条件の精度比較へ混ぜない。
- failed traceがfinished_at反映前ならtotal runtimeはresult.jsonから計算する。
- Window inference timeの和とwall-clock total runtimeを区別する。
- Final SummaryがQuestion回答に必要なEvidenceを失っている場合、Answer Agentだけを責めない。
- replay raw outputがPrompt literal placeholderを返す場合は、Answer formatting / instruction-following問題としてSummary品質と分離する。
