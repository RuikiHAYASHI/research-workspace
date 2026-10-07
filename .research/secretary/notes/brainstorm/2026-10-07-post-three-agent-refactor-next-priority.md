---
date: 2026-10-07
project: agentic-streaming-videoqa
source_todo: null
topic: post-three-agent-refactor-next-priority
status: exploratory
tags: [brainstorm, research, three-agent, workbench, evaluation]
---

# 3Agent理解・リファクタ後の次優先タスク整理

## 出発点

2026-10-07時点で、ユーザー報告では先週MTG後に次の2点が完了している。

- Situation / Summary / Answerの3Agentの責務・入出力の理解。
- 3Agentを理解しやすくするためのWorkbenchコード構造リファクタリング。

Company上では、2026-10-07の `2026-10-07-workbench-runtime-workflow-record-simplification-spec.md` に、Service / Runtime / Workflow / Record分離とSituation / Summary / Answerへの簡略化方針が整理されている。

一方、GitHub remote上の `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench` の `main` は `85bdda340e2609cc7c9525208c436b8b05ed6218` のままであり、今回ユーザーが完了したとするリファクタ後コードはGitHub remoteからは直接確認できない。したがって、以下では「リファクタ完了」はユーザー報告として扱い、remote実装確認済みとは扱わない。

## 現在の文脈

2026-10-02 MTG後のREADMEでは、未完了の主要事項として以下が残っている。

- 推論設定の矛盾とエラーを解消し、3段階Agentのエンドツーエンド実行を確認する。
- Promptの妥当性を検討する。
- 結果表示・サムネイル・メモリ内容を確認できるUIを整える。
- Qwen3-VLの複数frame入力とオーケストレーションの実装例を調査する。
- 実LongVideoBench・実Qwenでの品質と速度は未検証。

3Agent理解とコード構造整理が済んだ現在、次に必要なのは設計理解の追加ではなく、研究baselineとしての動作確認と最初のEvidence取得である。

## 推奨する次の順序

### 1. リファクタ後のFake経路を短時間回帰する

目的は研究実験ではなく、構造変更で既存機能を壊していないことの確認。

最低限:

- Dataset / Video / Question選択。
- Run開始。
- 2 window以上のSituation -> Summary更新。
- EOF時Answerが1回だけ実行される。
- Record v2保存。
- 保存Runのread-only再表示。
- CLIとBrowserが同じRunService経路を通る。

ここで失敗する場合は研究評価へ進まず、まず実装不具合として切り分ける。

### 2. 実Qwenで短いE2E canaryを1本通す

最優先。

長尺full runではなく、固定した1 QA・短い区間でSituation -> Summary -> Answerを実モデルで最後まで通す。

確認したいもの:

- Situationが現在windowだけから妥当な説明を返すか。
- Summaryが時系列情報を壊さず累積できるか。
- Answerが最終Summaryから選択肢を正しく選べるか。
- Prompt / generation settings / raw output / elapsed timeがRecordに残るか。
- 実Qwen固有のtoken、動画入力、GPU、prompt formatting問題がないか。

このcanaryは研究性能の結論ではなく「baselineが実モデルで成立する」Evidenceとする。

### 3. 1本の長め動画で質的trace reviewを行う

canary成功後、1本のLongVideoBench動画を先頭からEOFまで通す。

精度だけでなく、windowごとに次を見る。

- Situationで何を見落としたか。
- Summaryで何が消えたか・歪んだか。
- Summary長がどう増減するか。
- 最終Answerの誤りがSituation / Summary / Answerのどこ由来か。
- window長・frames per windowが十分か。

これにより次の研究課題を「Prompt改善」「Summary memory」「sampling/window」「Answer timing」のどこへ置くべきか判断できる。

### 4. 小規模baseline評価へ進む

1本のtrace review後に、固定した小規模subsetでbaselineを測る。

最低限候補:

- QA accuracy。
- 1 windowあたりSituation latency。
- Summary latency。
- Answer latency。
- total runtime。
- Summary文字数 / token数推移。
- failure category。

この段階ではmulti-timescale memoryやEarly Answer等を追加せず、まず最小3Agent baselineの基準値を作る。

## 採用候補

最有力の次タスクは、

> リファクタ後のFake smokeを短時間で確認した直後に、実Qwenで固定1 QAのSituation -> Summary -> Answer E2E canaryを通す。

理由は、現在の最大の未検証点が「理解・構造」ではなく「実モデルでこの最小baselineが本当に成立するか」だからである。

## 保留

- Promptの本格改善。
- Summary compression。
- Situation履歴retrieval。
- Early Answer / Readiness。
- 動的window。
- multi-timescale memory。
- UIの大規模改善。

これらはE2E canaryと1本のtrace reviewから失敗原因を見てから着手する方が比較可能性が高い。

## 次にユーザーが決めること

- まずFake回帰確認から行うか。
- すでにFake回帰済みなら、実Qwenの短いE2E canaryを次TODOとして採用するか。
- canary用にどのLongVideoBench QAを固定するか。

