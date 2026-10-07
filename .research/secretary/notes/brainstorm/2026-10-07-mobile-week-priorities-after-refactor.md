---
date: 2026-10-07
project: agentic-streaming-videoqa
source_todo: null
topic: mobile-week-priorities-after-refactor
status: exploratory
tags: [brainstorm, weekly-plan, mobile, baseline, evaluation]
---

# 外出中に進める今週の優先事項

## 現在地

2026-10-07時点で、ユーザー報告では3Agentの理解とコード構造リファクタリングは完了。
Workbench shell入口の簡略化も実装branch上で完了しているが、research serverの実 `.venv` でのFake smokeは未実施。

次の実験上の主要Gateは、

1. research serverでFake smoke確認
2. 実Qwenで固定1 QAの短いE2E canary
3. 1本の長め動画で質的trace review
4. 小規模baseline評価

である。

## スマホだけでも今週進める価値が高い作業

### 1. E2E canary / trace reviewの評価表を先に決める

最優先。

実Qwenを回した後に「なんとなく動いた」で終わらないよう、各Agentの失敗を分類する観点を先に固定する。

- Situation: 現在windowの主要動作、hallucination、時系列誤り、重要情報の見落とし。
- Summary: 重要情報保持、新観測統合、誤上書き、情報損失・歪み・冗長化。
- Answer: final summaryに根拠があるか、根拠があるのに選択を誤ったか、summary不足由来か。
- System: window数、per-agent latency、total runtime、summary長推移、error/OOM/max token。

### 2. Qwen3-VL複数frame入力と既存Agent / Streaming VideoQAの調査を進める

Company READMEに残る未完了事項のうち、スマホで進めやすい。

- Qwen3-VLへ複数frameを画像列として渡す場合とvideoとして渡す場合の違い。
- Streaming / Online VideoQAで現在window認識と過去状態要約を分離する既存例。
- Memory表現がtext / feature / KV cache等のどこに置かれるか。
- EOF-only baselineとearly answer / readinessを持つ研究の差。

目的は手法を追加することではなく、現在の最小3Agent baselineを文献上どこに位置づけるか整理すること。

### 3. canaryで使うQAの選定基準を決める

実際のquestion ID決定はserver / Dataset Browserを見られる時でもよい。

- 動画全体が極端に長すぎない。
- 正解に必要な情報が1 windowだけで完結せず、複数windowをまたぐ。
- Situation -> Summaryの累積が必要。
- 正解理由を人間が動画から追いやすい。
- 最初のcanaryでは細かすぎる文字読み・音声依存・専門知識依存を避ける。

### 4. 研究主張候補の整理は軽く進める

- offline VideoQAとonline/streaming VideoQAでどのquestion typeに差が出るか。
- 各choiceの成立/否定がいつ確定するかを追跡すると回答可能時刻を定義できるか。
- fixed window / text summary baselineのどこで情報損失が起きるか。
- early answer/readinessが本当に必要になる失敗例は何か。

今週は仮説候補に留め、baseline Evidenceより先に実装へ進めない。

## 今週の優先度

最優先:
- canary / trace review評価表の確定
- Qwen3-VL multi-frame + Streaming/Agent関連調査

次点:
- canary QAの選定条件
- baseline後の研究仮説候補整理

後回し:
- Ego4D説明書
- 大規模UI改善
- Prompt最適化
- dynamic window
- multi-timescale memory
- Early Answer実装

## PCへ戻ったら最初に行うこと

```text
./scripts/workbench.sh verify
    ↓
./scripts/workbench.sh preflight
    ↓
固定1 QAで実Qwen E2E canary
    ↓
事前に決めた評価表でtrace review
```


## 2026-10-07 追記: 評価表はGround Truth記述を必須にしない

canary / trace review用の評価表は、各windowについて「実際に起きたこと」をユーザーが手入力する形式を標準にしない。

標準形はWorkbenchのrun artifactだけから埋められるようにする。

候補列:

| Window | Situation | Situation判定 | Summary | Summary判定 | Answerへの影響 | 備考 |
|---|---|---|---|---|---|---|

EOF後は別途、次を記録する。

| Final Answer | Correct? | Summaryに回答根拠が残っていたか | Failure source | 備考 |
|---|---|---|---|---|

ここでの判定は最初から厳密なGround Truth annotationを要求せず、
`○ / △ / ×` と短い備考を中心にする。

動画の実内容確認は、次の場合だけ追加で行う。

- Situationが正しいか判断できない。
- Summaryで情報が消えたかを確認したい。
- 最終誤答の原因をSituation / Summary / Answerへ切り分ける必要がある。
- 研究Evidenceとして人手確認済みのfailure caseを残したい。

つまり通常は「モデル出力のtrace表」を先に作り、
必要な行だけ動画へ戻って人手確認する二段階方式とする。
