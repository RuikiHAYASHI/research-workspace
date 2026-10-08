---
date: 2026-10-08
project: agentic-streaming-videoqa
source_todo: null
topic: initial-behavior-experiment-matrix
status: exploratory
tags: [brainstorm, experiment-design, window, sampling, longvideoqa]
---

# 初期Behavior実験の比較条件

## 出発点

Workbenchの実Qwen実行が通り始めたため、まずは大規模精度評価よりも、Situation / Summary / Answerがどの条件でどう振る舞うかを比較できる小規模な実験条件を整理する。

現在の標準設定は window_seconds=4, frames_per_window=8 で、sampling intervalは0.5秒。

## 中心となる問い

1. Window長だけを変えたとき、Situationの粒度とSummary更新頻度はどう変わるか。
2. Window長を固定してsampling intervalだけを変えたとき、視覚情報量と処理コストはどう変わるか。
3. 動画が長くなるにつれてSummaryが冗長化・情報消失・誤上書きを起こすか。
4. 最終Answerの正誤と、途中のSituation / Summaryの挙動がどう対応するか。

## 推奨する段階的比較

### Phase 0: 動作確認

- 動画長: 20--40秒
- Window: 4秒
- sampling interval: 0.5秒
- frames/window: 8
- 目的: E2E、artifact、Browser、正誤表示の成立確認。

### Phase 1: Window長の影響

| 条件 | 動画長 | Window | Sampling interval | Frames / full window | 主な比較 |
|---|---:|---:|---:|---:|---|
| W2 | 約120秒 | 2秒 | 0.5秒 | 4 | Situationを細かく切り、Summary更新回数を増やす |
| W4 | 約120秒 | 4秒 | 0.5秒 | 8 | 現在baseline |
| W8 | 約120秒 | 8秒 | 0.5秒 | 16 | 1回のSituationへより長い時間範囲を渡す |

120秒動画では総sampled frame数を約240枚に揃えつつ、W2=60 windows、W4=30 windows、W8=15 windowsとしてWindow groupingとSummary更新頻度の影響を分離する。

### Phase 2: Sampling密度の影響

| 条件 | 動画長 | Window | Sampling interval | Frames / full window | 主な比較 |
|---|---:|---:|---:|---:|---|
| S025 | 約120秒 | 4秒 | 0.25秒 | 16 | 高密度。細かな動作を拾えるか |
| S050 | 約120秒 | 4秒 | 0.5秒 | 8 | 現在baseline |
| S100 | 約120秒 | 4秒 | 1.0秒 | 4 | 低密度。速度と情報損失 |

### Phase 3: 動画長によるSummary蓄積劣化

| 条件 | 動画長目安 | Window数 | sampled frame数目安 | 観察目的 |
|---|---:|---:|---:|---|
| L30 | 30秒 | 約8 | 約60 | Situation / Summaryの基本挙動 |
| L120 | 2分 | 30 | 約240 | 複数window統合 |
| L600 | 10分 | 150 | 約1,200 | 長期Summaryの冗長化・忘却・誤上書き |

## 最初に回す推奨matrix

| No. | 目的 | 動画長 | Window | Interval | Frames/window |
|---:|---|---:|---:|---:|---:|
| 1 | Canary | 20--40秒 | 4秒 | 0.5秒 | 8 |
| 2 | Window比較 | 約120秒 | 2秒 | 0.5秒 | 4 |
| 3 | Baseline | 約120秒 | 4秒 | 0.5秒 | 8 |
| 4 | Window比較 | 約120秒 | 8秒 | 0.5秒 | 16 |
| 5 | Sampling比較 | 約120秒 | 4秒 | 0.25秒 | 16 |
| 6 | Sampling比較 | 約120秒 | 4秒 | 1.0秒 | 4 |
| 7 | 長尺trace | 約600秒 | 4秒 | 0.5秒 | 8 |

## 比較時に見る項目

- System: window数、sampled frame数、Situation latency、Summary latency、total runtime、artifact size。
- Situation: 主要人物・物体・動作、window内時間変化、hallucination、冗長性。
- Summary: 重要情報保持、新観測統合、情報消失、誤上書き、冗長化、反復。
- Answer: prediction、ground truth、correct、Summary内に正答根拠があるか。

初期段階ではSituation / Summaryの自動点数化をせず、人間がtraceを読み挙動を比較する。

## 実験設計上の重要点

- Window長比較ではsampling intervalを0.5秒に固定し、総視覚frame量を概ね一定にする。
- Sampling比較ではWindowを4秒に固定し、frame密度だけを変える。
- 動画長比較ではWindow 4秒・interval 0.5秒を固定し、長期蓄積だけを見る。
- 初期段階では全軸のfull factorialを行わない。

## Dataset / QA選定

- 同一条件比較には同じ動画・同じQAを使う。
- 約120秒動画は、複数windowにまたがる出来事があり、静止1場面だけで答えが決まらず、OCRや音声だけに依存せず、人間がtraceを追いやすいものを優先する。
- 10分動画は、途中と後半で情報が追加され、Summary保持を観察できるQAを選ぶ。

## 現時点の有力方針

最初は7条件程度のsmall matrixでbehavior traceを集め、Window長・sampling密度・長尺Summaryのどこに問題が出るかを見てから、必要な軸だけ追加する。

accuracyの有意差を主張するconfirmatory experimentではなく、次の研究仮説とbaseline条件を選ぶためのexploratory experimentとして扱う。

## 保留

- 各条件を何問・何seed回すか。
- LongVideoBench内で具体的にどのQAを選ぶか。
- Situation / Summaryのhuman evaluation rubricをどこまで定量化するか。
- 10分より長い動画を初期比較へ入れるか。

## 2026-10-08 22:22 JST 追記: 10分動画でのlong-window / coarse-sampling stress test

ユーザー希望として、10分程度の動画に対して64秒Windowのようなかなり粗い時間解像度も試す方向を追加する。

これはWindow長だけのcontrolled ablationではなく、長尺動画を限られた観測回数・frame数で扱うscalability / stress testとして分ける。

有力な比較は、10分動画で `frames_per_window=8` を固定し、Window長を倍々に伸ばす系列。

| 条件 | 動画長 | Window | Frames / full window | Sampling interval | Window数目安 | 総sampled frame数目安 |
|---|---:|---:|---:|---:|---:|---:|
| B4 | 600秒 | 4秒 | 8 | 0.5秒 | 150 | 1,200 |
| C8 | 600秒 | 8秒 | 8 | 1秒 | 75 | 600 |
| C16 | 600秒 | 16秒 | 8 | 2秒 | 38 | 300 |
| C32 | 600秒 | 32秒 | 8 | 4秒 | 19 | 150 |
| C64 | 600秒 | 64秒 | 8 | 8秒 | 10 | 75 |

C64では64秒ごとにSituationを1回だけ実行し、1 Windowにつき8 frame、10分全体でも約75 frameだけを見る非常に粗い条件になる。

観察したいこと:

- 64秒分の出来事をSituationが一つの説明へまとめられるか。
- 8秒間隔のsamplingで重要イベントを見逃すか。
- Window数が約10まで減ることでSummary更新回数の減少が有利に働くか。
- sampling不足による失敗とSummary忘却による失敗を区別できるか。
- 計算時間と正答・trace品質のtrade-off。

この系列は複数要因を同時に変えるため、2 / 4 / 8秒Window・0.5秒interval固定のcontrolled comparisonとは別結果として扱う。

必要なら64秒Windowについて `frames_per_window=16`（4秒interval）も追加し、64秒という長いWindow自体の問題と8秒intervalという粗いsamplingの問題を部分的に切り分ける。


## 2026-10-08 22:22 JST 追記: Codexによる実験自動化の有力方式

現在のWorkbench実装を確認した結果、初期Behavior実験の自動化には **同一process内で複数Runを順番に実行するmanifest-driven batch runner** が最有力。

### 理由

現行 `longvideoqa run` は1回のCLI invocationごとに `ServiceContainer` と `RunService` を新規作成するため、shell loopで複数回呼ぶとprocess終了ごとにQwen runtimeも破棄される。

一方、`ServiceContainer.models` の `ModelService` は `(backend, model_id)` ごとにmodel instanceをcacheし、同一process内では同じQwen adapterを再利用できる。

したがって、複数条件を一括で実行する場合は、1つの `ServiceContainer` / `RunService` を作り、caseごとにExecutionSettingsだけを切り替えて順番に `start_run -> advance -> terminal` まで回す方が自然。

### 推奨interface案

例:

```yaml
experiment_id: initial-behavior-2026-10-08
base_config: configs/default.yaml

cases:
  - id: short-canary
    question_id: <20秒前後QA>
    window_seconds: 4
    frames_per_window: 8

  - id: two-min-w2
    question_id: <2分前後QA>
    window_seconds: 2
    frames_per_window: 4

  - id: two-min-w4
    question_id: <同じ2分QA>
    window_seconds: 4
    frames_per_window: 8

  - id: two-min-w8
    question_id: <同じ2分QA>
    window_seconds: 8
    frames_per_window: 16

  - id: ten-min-c64
    question_id: <10分前後QA>
    window_seconds: 64
    frames_per_window: 8
```

CLIイメージ:

```bash
./scripts/workbench.sh batch-run experiments/initial-behavior.yaml
```

### 実験runnerの責務

- manifestをvalidateする。
- base configを1回解決する。
- Qwenを同一processで再利用する。
- caseは並列化せず1件ずつ順番に実行する。
- 各caseは既存Record v3 Runとして独立保存する。
- case_idとrun_idの対応をexperiment-level indexへ残す。
- succeeded / failed、Answer、correct、total runtime、window数、sampled frame数等の比較用summaryを生成する。
- 1 case失敗時に全実験を停止するか次へ進むかはmanifestまたは明示契約で決める。
- 既存 `result.json` / `trace.md` / `frames/` を正本として再利用し、独自のAgent出力formatを作らない。

### experiment-level artifact案

個別RunのRecord v3を壊さず、別の薄いindexだけ追加する。

```text
<experiment-output>/<experiment-id>/
  manifest.yaml
  index.json
  summary.csv

<existing OUTPUT_ROOT>/
  <run-id-1>/
    result.json
    trace.md
    frames/
  <run-id-2>/
    ...
```

`index.json` はcase_id -> run_id / statusを主に保持し、Agent traceそのものを複製しない。

`summary.csv` は分析導入用projectionとして、case_id、question_id、duration、window_seconds、frames_per_window、sampling_interval、window_count、sampled_frame_count、runtime、prediction、ground_truth、correct、run_id程度に限定する案が有力。

### 初期実験での並列化

GPU memoryと比較条件の安定性を優先し、最初は並列runを行わない。1 model instanceを維持したままcaseを逐次実行する。

### Codexの役割

Codexにはrunner / manifest schema / short Fake testの実装を任せられる。

実Qwenで20秒・2分・10分を連続実行する行為は長時間runになり得るため、実装承認とは分離し、実際の実験起動は別の明示許可で行う。

### 棄却寄り

- shellで `longvideoqa run` を単純loop: 実装は最小だが、Qwen再loadとexperiment index管理が弱い。
- Browser自動操作: UI回帰には有効だが、研究実験のlauncherとしては脆い。
- 最初からSlurm / 複雑なjob scheduler: 現在の単一GPU/少数caseの探索には過剰。

### 次のspec候補

実装へ進む場合は、batch-run CLI、manifest schema、experiment-level artifact、failure policy、resume policy、実行許可境界をresearch-specで固定してからengineering-taskへ渡す。
