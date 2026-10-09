---
date: 2026-10-09
project: agentic-streaming-videoqa
source_todo: null
topic: situation-summary-audit-tool-ideas
status: exploratory
tags: [brainstorm, situation, summary, audit, visualization, tooling]
---

# Situation / Summary結果確認ツール案

## 出発点

初期Behavior実験では、SituationとSummaryの品質を全windowについて人手で追う必要がある一方、長尺条件ではwindow数が多く、trace.mdだけでは次を確認しづらい。

- 対応frameに対してSituationが妥当か
- previous Summary + current Situationからnew Summaryがどう変化したか
- 重要事実がどのwindowで消えたか
- 重複や矛盾がどこで増えたか
- W2/W4/W8やsampling条件間で同じ時間帯の認識がどう違うか

既存brainstormでは、全259 windowを最初からvisual verificationせず、textual screeningで怪しいwindowをflagし、flagged window + stratified sampleだけをvisual確認する二段階監査を有力としている。

## 候補1: Window Timeline Inspector

各windowを縦方向に並べ、1画面内で以下を表示する。

- window番号 / 時間範囲
- sampled frames / thumbnails
- Situation
- previous Summary
- new Summary
- Agent elapsed / token hit等

windowをクリックするとframesを拡大し、SituationとSummaryを同時に確認できる。

### 向く用途

- Situationのvisual verification
- 1 runを時系列に追う
- 人間が直感的に異常を見つける

### 評価

実装難度: 中
有用性: 非常に高い

## 候補2: Summary Evolution Diff Viewer

Summaryだけに特化し、

```text
Summary_{t-1}
   ↓
Situation_t
   ↓
Summary_t
```

をwindowごとに表示する。

Summary_{t-1}とSummary_tの差分を、

- 追加
- 削除
- 言い換え
- 重複

として色分けする。

単純な文字diffだけでなく、文単位diffを基本とする。

### 向く用途

- recursive rewriteによる情報消失の観察
- 同じ事実の反復
- どの更新で前半情報が落ちたかの特定

### 評価

実装難度: 小〜中
有用性: 現在の研究課題に対して非常に高い

## 候補3: Fact Survival Tracker

Situation / Summaryから確認対象となるfactを抽出し、各factについて時系列で追跡する。

例:

| Fact | Introduced | Last retained | Repeated | Contradiction |
|---|---:|---:|---:|---:|
| person wears red shirt | w3 | w17 | 8 | no |
| cup placed on table | w11 | w28 | 3 | w24 |

これにより、

- fact survival length
- deletion point
- repetition count
- contradiction introduction

を定量化できる。

### 注意

fact extractionを別LLMへ任せると新たなerror sourceが入るため、最初は人手tagまたは単純なsentence/fact候補抽出から始める方が安全。

### 評価

実装難度: 中〜大
研究評価への発展性: 高い

## 候補4: Cross-Run Synchronized Comparator

同一video/questionの複数Runを時間軸で同期し、

```text
Time 40-44s

W2       Situation / Summary
W4       Situation / Summary
W8       Situation / Summary
S025     Situation / Summary
S100     Situation / Summary
```

のように横並び比較する。

異なるwindow境界は絶対時刻でalignする。

### 向く用途

- Window長による認識差
- sampling密度によるvisual detail差
- 同じeventが条件ごとにどうSummaryへ残るか

### 評価

実装難度: 中
実験比較への有用性: 非常に高い

## 候補5: Automatic Flagging Dashboard

全windowを自動screeningし、怪しい箇所だけ監査queueへ出す。

初期flag例:

- Summary max token hit
- Summary lengthの急増 / 急減
- previous Summaryとの高重複
- previous Summaryから大きな削除
- 同一時間帯のrun間でSituationが大きく異なる
- 文途中で切れている
- Question関連keywordを含む
- Situation / Summaryで人物・物体・状態が急変

画面では、

```text
High priority
  w31  large summary deletion
  w44  max-token hit + truncation
  w52  cross-run disagreement
```

のように表示し、クリックすると候補1のWindow Inspectorへ遷移する。

### 評価

実装難度: 中
大量window監査への有用性: 非常に高い

## 現在の収束

最初のprototypeとしては、独立した5ツールを全部作るより、

1. Window Timeline Inspector
2. Summary Evolution Diff
3. Automatic Flagging

を1つのAudit Viewerにまとめる案が最有力。

これなら、

```text
全windowを自動screen
  -> 怪しいwindowをflag
  -> diffを見る
  -> 必要なwindowだけframeを確認
```

という現在のqualitative audit方針をそのままUI化できる。

次にCross-Run Comparatorを追加すると、W2/W4/W8およびsampling比較へ拡張できる。

Fact Survival Trackerは研究指標として魅力が高いが、fact extraction自体の評価が必要になるため第2段階候補とする。

## 未解決

- Audit Viewerを既存Workbenchへ統合するか、saved Record v3だけを読む独立read-only toolにするか
- diffを文字単位 / 文単位 / semantic fact単位のどこまで行うか
- flaggingを完全deterministic heuristicに限定するか
- cross-run alignmentをwindow境界ではなく絶対時刻で統一するか
