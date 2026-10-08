---
date: 2026-10-09
project: agentic-streaming-videoqa
source_todo: null
topic: initial-inference-run-plan
status: exploratory
tags: [brainstorm, experiment, inference, runtime, git, batch-run]
---

# 20秒Canary + 2分5条件 推論計画

## 今回の範囲

今回は次まで実行する方向。

1. 20秒前後のCanary 1条件
2. 約2分動画のcontrolled comparison 5条件

2分条件は同一動画・同一QAを使用する。

| case | Window | Sampling interval | Frames / full window | Window数目安 |
|---|---:|---:|---:|---:|
| W2 | 2秒 | 0.5秒 | 4 | 60 |
| W4 / S050 | 4秒 | 0.5秒 | 8 | 30 |
| W8 | 8秒 | 0.5秒 | 16 | 15 |
| S025 | 4秒 | 0.25秒 | 16 | 30 |
| S100 | 4秒 | 1.0秒 | 4 | 30 |

W4とS050は同一条件なので1 Runだけ実行する。

20秒Canaryは4秒Window、0.5秒interval、8 frames/window。

したがって今回の実Run数は合計6 Run。

## trace.mdの表示案

各Runの `trace.md` 冒頭に、最低限次を表示する。

```markdown
# Run Summary

- Question: ...
- Ground truth: ...
- Model answer: ...
- Correct: ...
- Total runtime: ... s
```

ユーザー要望の「解答」はdatasetのground truth、「モデルの回答」はpredictionとして区別する。

`Total runtime` は `status.started_at` から `status.finished_at` までのwall-clock時間として扱う。
これにはmodel初回load、decode、Agent推論、artifact処理等が含まれ得る。

Window表は次の形を有力案とする。

| Window | Range | Situation Agent | Situation time (s) | Summary Agent | Summary time (s) | Window inference time (s) | Answer Agent |
|---:|---|---|---:|---|---:|---:|---|

`Window inference time` は、現在Record v3が既に保存している

```text
Situation elapsed_seconds + Summary elapsed_seconds
```

の和とする。

これにより、総実行時間のwall-clockとAgent推論時間を混同しない。

Window単位のdecode/JPEG/Record I/Oまで含むwall-clock時間は現在artifactに独立fieldが無いため、初回実験では新しい計測fieldを増やさず、必要性が確認された場合に別途追加する。

EOF行ではAnswer本文を表示し、Answerの `elapsed_seconds` は必要ならAnswer time列として追加できるが、今回の必須要件は冒頭の総実行時間と各WindowのSituation/Summary/合計推論時間とする。

## 実験実行前の順序

1. Prompt grounding / title統一を確定・実装する。
2. trace.mdの実行時間表示とbatch-run共通機能を実装する。
3. short Fake testでRecord / trace / resumeを確認する。
4. 20秒Canaryを実Qwenで1 Run。
5. Canary結果と所要時間を確認。
6. 2分5条件を同一processで逐次実行。
7. Run artifactを確認し、Companyへ実験ログを保存する。

## Git運用の推奨

### A. 共通実装branch

まず、今後も再利用する機能を独立branchで実装する。

例:

```text
feat/batch-run-trace-timing
```

ここで扱うもの:

- batch-run / experiment manifest reader
- Qwen instanceを同一processで再利用する逐次実行
- resume / succeeded case skip
- trace.md冒頭のQuestion / ground truth / model answer / total runtime
- WindowごとのSituation / Summary / Window inference time表示
- 関連Fake/unit test

実Qwen runはこの実装branchの作業には含めず、短時間testだけ行う。

実装確認後、この共通機能をmainへ統合してから実験branchを作るのが最もきれい。

### B. 今回のexperiment branch

共通機能が入ったmainから今回専用branchを作る。

例:

```text
exp/initial-behavior-20s-2min
```

このbranchでは研究コード本体を原則変更せず、今回の実験manifest / YAMLだけを追加する。

例:

```text
experiments/2026-10-09-initial-behavior-20s-2min.yaml
```

manifestには20秒1条件 + 2分5条件を記述する。

実験開始前にmanifestをcommitし、**そのcommitから6 Runを実行する**。
Run artifactの `code_version` には実行時HEADが保存される現行契約を利用し、どのコードから実験したか追跡できるようにする。

### C. 実験出力はGitへcommitしない

Record v3の、

- `result.json`
- `trace.md`
- `frames/`

は通常のresearch code Gitへcommitしない。

特にframesは容量が大きくなるため、output rootに保持する。

実験終了後はCompany側に、

```text
.research/lab/projects/agentic-streaming-videoqa/experiments/
2026-10-09-initial-behavior-20s-2min.md
```

のような実験ログを作り、

- code repository / branch / commit
- manifest
- question/video
- 各caseのrun_id
- correctness
- total runtime
- 主な観察結果
- 未検証事項

を記録する。

## 一branchにまとめる代替案

`feat/batch-run-trace-timing` と `exp/initial-behavior-20s-2min` を1本へまとめることも可能。

ただし、

- reusableな実験基盤の変更
- 今回だけの実験条件

が同じbranchに混ざり、どこまでがbaseline codeでどこからがexperiment definitionか分かりにくくなる。

そのため、今回は2段階を推奨する。

## 実験manifestイメージ

```yaml
experiment_id: initial-behavior-20s-2min
base_config: configs/default.yaml

cases:
  - id: canary-20s
    question_id: <20秒前後のQA>
    window_seconds: 4
    frames_per_window: 8

  - id: two-min-w2
    question_id: <2分QA>
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

  - id: two-min-s025
    question_id: <同じ2分QA>
    window_seconds: 4
    frames_per_window: 16

  - id: two-min-s100
    question_id: <同じ2分QA>
    window_seconds: 4
    frames_per_window: 4
```

Sampling intervalは `window_seconds / frames_per_window` の現行契約から決定されるため、manifestで独立指定しない案を第一候補とする。

## 現時点の推奨

- 今回の実験範囲は20秒1条件 + 2分5条件まで。
- 2分5条件すべてで総実行時間を記録する。
- trace.md冒頭にQuestion / ground truth / model answer / correct / total runtimeを置く。
- 各WindowではSituation時間、Summary時間、その和であるWindow inference timeを表示する。
- reusableなbatch/trace変更はfeature branch。
- 実験条件YAMLはexperiment branch。
- Run outputsはresearch code Gitへ入れず、Companyのexperiment logへ結果を残す。
