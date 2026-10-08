---
date: 2026-10-08
project: agentic-streaming-videoqa
source_todo: null
topic: inference-efficiency-plan
status: exploratory
tags: [brainstorm, inference, experiment, efficiency, batch-run, qwen]
---

# 推論を効率的に回すための計画

## 目的

20秒・2分・10分のBehavior実験を、研究条件を壊さず、無駄なQwen loadや重複Runを避けて順番に回せる状態を作る。

効率化では「研究条件そのものを粗くして計算量を下げること」と「同じ研究条件をより無駄なく実行すること」を区別する。

## 現行実装から確認できること

- `longvideoqa run` を別processで繰り返すと、各processでServiceContainer / ModelServiceを作り直す。
- Qwen adapterはlazy loadであり、同一process内ではModelServiceがbackend/model_id単位でinstanceを再利用できる。
- RunServiceはactive Runを同時に1件だけ許可するため、単一GPUでcaseを逐次実行するbatch runnerと相性がよい。
- 1 WindowにつきSituationとSummaryの2回のmodel generateがあり、EOFでAnswerを1回実行する。
- 各Windowでthumbnail JPEGを生成・保存し、trace.mdの更新も行う。
- Video streamはRunごとにopenされるため、同じ動画を別条件で回すと現状は再decodeする。

## 最優先の効率化

### 1. 同一processのbatch runner

実験manifestを読み、1つのServiceContainer / RunServiceを維持したままcaseを1件ずつ順番に実行する。

```text
Qwen load 1回
   ↓
20秒 Canary
   ↓
2分 W2
   ↓
2分 W4
   ↓
2分 W8
   ↓
...
```

同じQwen modelを各Agent・各caseで再利用し、caseごとのprocess起動とmodel reloadを避ける。

初期段階ではGPU並列化しない。

### 2. 重複条件を実行しない

2分条件では、Window比較のW4（4秒 / 0.5秒 / 8 frames）とSampling比較のS050は同一条件なので1 Runを共用する。

同じ `video + QA + window_seconds + frames_per_window + Prompt + model/generation` の組を別名で二重実行しない。

batch runner側でcase IDは複数の分析軸から参照できても、実Runは一意にする案が有力。

### 3. Canaryで現在の実測速度を取得

最初に20秒、4秒Window、8 frames/windowを1 Runだけ実行する。

取得するもの:

- model初回loadを含む最初のSituation時間
- 2 Window目以降のSituation時間
- Summary時間
- Answer時間
- decode / artifactを含むRun全体時間
- frame保存量

この実測値を使い、2分・10分条件の概算ETAを作ってから長尺を開始する。

## 実験を段階的に回す

### Stage A: 20秒 Canary

1条件だけ。

- 4秒 Window
- 0.5秒 interval
- 8 frames/window

目的は速度校正とartifact確認。

### Stage B: 2分 controlled comparison

同じ動画・同じQAで、重複を除いた5条件。

| case | Window | interval | frames/window |
|---|---:|---:|---:|
| W2 | 2秒 | 0.5秒 | 4 |
| W4 / S050 | 4秒 | 0.5秒 | 8 |
| W8 | 8秒 | 0.5秒 | 16 |
| S025 | 4秒 | 0.25秒 | 16 |
| S100 | 4秒 | 1秒 | 4 |

全条件を始める前にCanaryの実測から所要時間を確認する。

### Stage C: 10分 stress test

最初から全条件を回さず、代表3条件から始める。

| 優先 | Window | interval | frames/window | 意図 |
|---|---:|---:|---:|---|
| 1 | 4秒 | 0.5秒 | 8 | long baseline |
| 2 | 16秒 | 2秒 | 8 | 中間coarse |
| 3 | 64秒 | 8秒 | 8 | extreme coarse |

この3条件のtrace / Answer / runtimeを確認してから、8秒・32秒・64秒16framesを追加する。

これにより、明らかな傾向が見えた後で不要な中間条件を大量に回すことを避ける。

## model call数を意識する

1 Runのmodel call数は概ね、

```text
2 × Window数 + 1 Answer
```

になる。

例:

- 20秒 / 4秒Window: 5 windows -> 約11 calls
- 2分 / 2秒Window: 60 windows -> 約121 calls
- 2分 / 4秒Window: 30 windows -> 約61 calls
- 2分 / 8秒Window: 15 windows -> 約31 calls
- 10分 / 4秒Window: 150 windows -> 約301 calls
- 10分 / 64秒Window: 約10 windows -> 約21 calls

したがって、10分4秒baselineは64秒Windowより大幅に高コスト。

## batch runnerに持たせたい最低限の機能

- YAML等のmanifestでcaseを列挙。
- 1 model processを維持して逐次実行。
- caseごとに既存Record v3を独立保存。
- case_id -> run_id / statusをindexへ保存。
- 既に成功したcaseはresume時に再実行しない。
- failed caseを記録し、研究判断が不要な通常failureなら次caseへ進める。
- summary.csv等へ条件、正誤、runtime、window数、sampled frame数をprojectionする。
- 実行前にcase重複を検出する。

CUDA OOM、model load failure、dataset/source contract failure等、後続caseも成立しないsystem failureでは停止する方が有力。

## runtime比較時の注意

効率的な一括実験と「純粋なruntime benchmark」は分ける必要がある。

batch runnerでQwenを再利用すると、最初のcaseだけmodel初回loadコストを持ち、後続caseはwarm状態になる。

したがってBehavior / accuracy実験ではmodel再利用を優先し、単純なwall-clockだけでcaseを比較しない。

runtimeを研究結果として比較するときは、例えば次を固定する必要がある。

- modelを事前warm-upしてから各caseを測る。
- model load時間を別項目として扱う。
- decode/cache policyを全条件で揃える。

## 第2段階の最適化候補

batch runner実装後にprofileし、必要なものだけ採用する。

### A. 動画decode frame cache

同じ動画を複数条件で使うため、採用frameを再利用できればdecodeを減らせる可能性がある。

特に0.25 / 0.5 / 1 / 2 / 4 / 8秒gridは重なるframeが多い。

ただしcacheを使うRunと使わないRunでwall-clockを直接比較しない。sampling contractと実際のFrameSampleが同一であることをtestで保証する必要がある。

### B. artifact I/Oの削減

現状は各sampled frameをJPEG保存し、各Window後にtrace.mdを更新する。

profileでI/Oが無視できない場合、batch modeでは例えばfinal trace生成だけにする等を検討できる。

ただしRecord v3 / Browser契約との整合を先にspec化する。

### C. decodeとGPU推論のoverlap

CPUで次Windowをprefetchし、GPU推論中にdecodeする案。

研究入力を変えずにthroughputを上げられる可能性があるが、実装複雑度が上がるため初期対象にしない。

### D. GPU/model内部最適化

FlashAttention、quantization、別dtype、model batching等は推論結果やdependency、VRAM特性を変える可能性がある。

初期baselineのインフラ効率化とは分離し、必要なら別実験・specとする。

## 同一動画に複数QAがある場合の将来候補

現行3-AgentではSituationとSummaryはQuestion非依存で、AnswerだけがQuestion / Choicesを使う。

そのため将来、同一動画・同一streaming条件に複数QAを評価する場合は、

```text
動画処理 -> Situation/Summaryを1回
                      ↓
                final summary
                 ↙    ↓    ↘
              QA1   QA2   QA3
             Answer Answer Answer
```

のように、Situation/SummaryをQAごとに再計算しない設計が可能性としてある。

ただし現行Run / Recordは1 QuestionSampleを前提としているため、これは初期batch runnerとは分けて別specで扱う。

## 推奨する実装順

1. Prompt修正を完了し、実験baselineを固定。
2. 20秒Canaryを手動で1回実行して現在の速度とartifact量を取得。
3. manifest-driven batch runnerをspec化・実装。
4. 2分の5条件を同一processで逐次実行。
5. 10分は4秒 / 16秒 / 64秒の3条件だけ先に実行。
6. 結果とprofileを見て、8秒 / 32秒 / 64秒16framesを追加するか判断。
7. decode / artifact I/Oがボトルネックなら第2段階のcache / I/O最適化をspec化する。

## 現時点の最有力方針

最初の効率化ではモデルの数値計算自体を変えず、実験orchestrationの無駄を除く。

優先順位:

1. Qwen再loadをなくす。
2. 重複Runをなくす。
3. resume可能にする。
4. 短尺から実測して長尺を段階投入する。
5. profile後にdecode / artifact I/Oを最適化する。

これにより研究baselineを維持したまま、安全に実験throughputを上げる。
