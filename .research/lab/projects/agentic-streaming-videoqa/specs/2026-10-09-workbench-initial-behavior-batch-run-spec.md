---
date: 2026-10-09
last_updated: 2026-10-09
project: agentic-streaming-videoqa
type: implementation
status: implemented
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 59d4312dac242eba4eebace93c3f94a61979bc64
source_brainstorm:
  - 2026-10-08-inference-efficiency-plan.md
  - 2026-10-09-initial-inference-run-plan.md
related_specs:
  - 2026-10-08-workbench-prompt-grounding-and-title-unification-spec.md
  - 2026-10-08-workbench-run-artifact-trace-simplification-spec.md
  - 2026-10-08-workbench-ui-dedup-partial-window-sampling-spec.md
---

# Workbench 20秒Canary + 3分5条件 batch-run spec

## 1. 目的

実験開始前にユーザーが次の2つのLongVideoBench Question IDを与えるだけで、Codexが実装を開始できる状態を作る。

- 20秒前後の動画に対応するQuestion ID
- 約3分の動画に対応するQuestion ID

実装完了後は、ユーザーが実装branchを確認してmainへmerge / pushし、そのmainから

```text
exp/initial-behavior-20s-3min
```

を作成すれば、experiment branch上で次の1コマンドだけで今回の6 Runを開始できる状態を最終目標とする。

```bash
./scripts/workbench.sh batch-run experiments/2026-10-09-initial-behavior-20s-3min.yaml
```

実験run自体は本specの実装検証には含めず、実Qwen / GPU runはユーザーがexperiment branch上で明示的にコマンドを実行した時だけ開始する。

## 2. 実装開始に必要なユーザー入力

実装者はコード変更前に、ユーザーから以下2値を受け取る。

```text
QUESTION_ID_20S=I2Fyzav8MxE_0
QUESTION_ID_3MIN=66dwcQ1Y048_0
```

今回の固定値は `I2Fyzav8MxE_0`（metadata duration 21.98秒）と `66dwcQ1Y048_0`（metadata duration 186.81秒）。どちらもLongVideoBench metadataに存在し、参照動画を確認済み。

両方が無い場合は実装を開始しない。

Question IDは今回のexperiment manifestへ固定するための値であり、spec設計上のblocking ambiguityではない。

実装開始時にDatasetService / LongVideoBench metadataから両IDが存在することを確認する。動画長を独自の閾値でrejectしない。実際のdurationはmanifest preflightまたは実験開始時に表示できるようにする。

## 3. 今回実行する6 Run

### 3.1 20秒Canary

20秒用Question IDを使う。

| case_id | Window | Sampling interval | Frames / full window |
|---|---:|---:|---:|
| `canary-20s` | 4秒 | 0.5秒 | 8 |

### 3.2 約3分 controlled comparison

3分用Question IDを5条件すべてで共有する。

| case_id | Window | Sampling interval | Frames / full window | Window数の目安 |
|---|---:|---:|---:|---:|
| `three-min-w2` | 2秒 | 0.5秒 | 4 | 約94 |
| `three-min-w4` | 4秒 | 0.5秒 | 8 | 約47 |
| `three-min-w8` | 8秒 | 0.5秒 | 16 | 約24 |
| `three-min-s025` | 4秒 | 0.25秒 | 16 | 約47 |
| `three-min-s100` | 4秒 | 1.0秒 | 4 | 約47 |

`W4` と `S050` は同一条件なので `three-min-w4` 1 Runだけとする。

Sampling intervalは現行contractどおり

```text
window_seconds / frames_per_window
```

で決まり、manifestへ独立fieldとして保存しない。

partial final windowも現行fixed-cadence target contractに従う。

## 4. Experiment manifest

repositoryへ次を追加する。

```text
experiments/2026-10-09-initial-behavior-20s-3min.yaml
```

schemaを次で固定する。

```yaml
experiment_id: initial-behavior-20s-3min
base_config: configs/default.yaml

cases:
  - id: canary-20s
    question_id: I2Fyzav8MxE_0
    window_seconds: 4
    frames_per_window: 8

  - id: three-min-w2
    question_id: 66dwcQ1Y048_0
    window_seconds: 2
    frames_per_window: 4

  - id: three-min-w4
    question_id: 66dwcQ1Y048_0
    window_seconds: 4
    frames_per_window: 8

  - id: three-min-w8
    question_id: 66dwcQ1Y048_0
    window_seconds: 8
    frames_per_window: 16

  - id: three-min-s025
    question_id: 66dwcQ1Y048_0
    window_seconds: 4
    frames_per_window: 16

  - id: three-min-s100
    question_id: 66dwcQ1Y048_0
    window_seconds: 4
    frames_per_window: 4
```

manifestはbase configのdataset/model/prompt/generation/reader/visual modeを継承し、各caseではQuestion ID、window_seconds、frames_per_windowだけをoverrideする。

今回のmanifest schemaへ将来用fieldを追加しない。

## 5. batch-run CLI

新しいCLIを追加する。

```text
longvideoqa batch-run
```

shell wrapperでは次を公開する。

```bash
./scripts/workbench.sh batch-run experiments/2026-10-09-initial-behavior-20s-3min.yaml
```

`scripts/workbench.sh` は既存 `run` と同様に、

- `LVB_ROOT`
- `OUTPUT_ROOT`
- `.env`

を利用する。

### 5.1 実行原則

batch-runは1 process内で、

1. manifestを読む。
2. base configを解決する。
3. dataset / manifestをpreflightする。
4. 1つのServiceContainer / RunServiceを作る。
5. caseをmanifest順に1件ずつ実行する。
6. 同じQwen model instanceをModelService経由で再利用する。
7. 1 caseがterminalになってから次caseへ進む。
8. 全case終了後にServiceContainerを閉じる。

GPU上で複数caseを並列実行しない。

### 5.2 single-run経路との共有

既存 `run` と `batch-run` でRun進行ロジックを重複実装しない。

必要なら現在の `run_command` にある、

```text
start_run
-> ready/awaiting_next_turnならadvance
-> terminalまでwait
```

をprivate helperへ抽出し、single-runとbatch-runの両方から利用する。

新しい汎用scheduler層は作らない。

## 6. Experiment-level index / resume

batch-runのexperiment-level状態はRecord v3とは分離する。

保存先:

```text
<OUTPUT_ROOT>/experiments/initial-behavior-20s-3min/index.json
```

最低限、各caseについて次を保持する。

```json
{
  "experiment_id": "initial-behavior-20s-3min",
  "manifest_path": "experiments/2026-10-09-initial-behavior-20s-3min.yaml",
  "cases": [
    {
      "case_id": "canary-20s",
      "run_id": "2026-10-09_...",
      "status": "succeeded"
    }
  ]
}
```

Agent出力やtrace本文をindexへ複製しない。詳細の正本は各Record v3とする。

同じmanifestでbatch-runを再実行した場合:

- index上で `succeeded` かつ対応Record v3も `succeeded` のcaseはskipする。
- failed / cancelled / record missingのcaseは新しいRunとして再実行できる。
- skipしたcaseも最終CLI summaryへ表示する。

resumeのために既存Record v3を上書きしない。

## 7. 重複case validation

manifest内で、

```text
question_id
window_seconds
frames_per_window
base configから解決したmodel / prompt / generation / reader / visual mode
```

が同一のcaseを複数定義した場合は、Qwenをloadする前にvalidation errorとする。

今回W4 / S050はmanifest上で1 caseだけにする。

## 8. trace.md Run Summary

Record v3の `trace.md` 冒頭を次の形式へ拡張する。

成功Runの概念例:

```markdown
# Run Summary

- Question: What does ...?
- Ground truth: 2. ...
- Model answer: 2. ...
- Correct: true
- Total runtime: 123.456 s

| Window | Range | Situation Agent | Situation time (s) | Summary Agent | Summary time (s) | Window inference time (s) | Answer Agent |
|---:|---|---|---:|---|---:|---:|
...
```

### 8.1 Question

`result.json.question.question` を使う。

### 8.2 Ground truth

成功時の `result.json.answer.ground_truth` から、choice indexとchoice textを人間向けに表示する。

1-based表示とし、既存ground truthが内部で0-basedの場合は現在Record v3のcanonical契約に従う。

### 8.3 Model answer

`result.json.answer.prediction.answer` を使用する。

### 8.4 Correct

`result.json.answer.correct` を使用する。

### 8.5 Total runtime

Run全体のwall-clockとして、

```text
status.finished_at - status.started_at
```

を計算する。

表示単位は秒、3桁小数。

これはmodel推論だけではなく、model初回load、動画decode、JPEG保存、Record / trace処理等を含み得る。

途中Runでは `finished_at` が無いため `Total runtime: —` としてよい。

failed / cancelledでもstarted_at / finished_atが両方あればwall-clockは表示できる。

## 9. Windowごとの実行時間

既存Record v3が保存している、

- `turn.situation.elapsed_seconds`
- `turn.summary.elapsed_seconds`

を利用する。

Window表へ次の3列を追加する。

- `Situation time (s)`
- `Summary time (s)`
- `Window inference time (s)`

`Window inference time` は決定的に、

```text
Situation elapsed_seconds + Summary elapsed_seconds
```

とする。

表示単位は秒、3桁小数。

これはWindow全体のwall-clockではなく、Situation / Summary model generateの合計時間である。

動画decode、thumbnail JPEG、Record I/O、trace書込の時間は含めない。

今回、新しいper-window wall-clock fieldはRecordへ追加しない。

## 10. EOF Answer表示

既存表のEOF Answer行は維持する。

Answer Agentの `elapsed_seconds` は既にRecord v3へ保存されているが、今回の必須表示項目へ新しいAnswer time列は追加しない。

必要になれば後続specで扱う。

## 11. 実験前Git cleanliness

batch-runは研究再現性のため、開始前に現在repositoryがdirtyか確認する。

dirty worktreeの場合は実Qwen caseを1件も開始せず、commit / stash等でcleanにするよう明示エラーで停止する。

single `longvideoqa run` / Browser serveの既存挙動は変えない。

Record v3の既存 `code_version` は実行時HEAD SHAを保存し続ける。

## 12. Prompt baselineとの関係

今回の実Qwen実験は、

```text
2026-10-08-workbench-prompt-grounding-and-title-unification-spec.md
```

のPrompt変更が実装・main統合された後に行う。

batch-run機能の実装・Fake検証自体はPrompt本文に依存しない。

実験manifestは `configs/default.yaml` のcurrent Prompt IDをそのまま利用し、Prompt本文をmanifestへ複製しない。

## 13. Git運用

### 13.1 Codex / 実装者が行う操作

最新mainを確認し、mainから **1本だけ実装branch** を作る。

推奨branch名:

```text
feat/initial-behavior-batch-run
```

Step branch / micro-step branchは作らない。

実装branch内で、独立して説明・検証できる意味単位ごとにmicro-commitを積む。

推奨するcommit単位は3前後。

1. batch-run / manifest / single-process model reuse / resume
2. trace.md Run SummaryとWindow timing
3. 今回のconcrete manifestと回帰test / wrapper仕上げ

実際の依存関係に応じて2〜4 commitに調整してよいが、小さすぎるcommitや複数責務の混在を避ける。

各commit後、その変更に最も近い短時間test / compile / smokeを行う。

実装branch完成時に全短時間回帰を行う。

### 13.2 Commit message

commit messageは日本語で、

```text
<タイトル>

5〜6行程度の本文
```

とする。

本文は箇条書きにせず文章で記述し、

- 何を変更したか
- なぜ変更したか
- どの範囲へ影響するか
- 何を検証したか

が分かる内容にする。

### 13.3 旧実装

backup目的のfile / alias / helperをrepository内に残さない。

新経路によって不要になった実装はrepo-wide参照を確認後に削除する。

現在要件として必要なLegacy read-only責務は最小限維持する。

### 13.4 Codexへ許可するGit操作

許可:

- 現在状態確認
- 1本の実装branch作成
- 実装
- 短時間検証
- micro-commit

禁止:

- mainへのmerge
- remote push
- Pull Request作成
- history rewrite

実装完了のゴールは、実装branch最新commitで本specの機能と短時間検証が成立していること。

### 13.5 experiment branch

Codexによる実装完了後、ユーザーが実装を確認してmainへmerge / pushする。

その後、ユーザーが更新済みmainから次を作る。

```text
exp/initial-behavior-20s-3min
```

experiment branchでは原則コード変更を行わない。

そのbranch上で、

```bash
./scripts/workbench.sh batch-run experiments/2026-10-09-initial-behavior-20s-3min.yaml
```

を実行するだけで6 Runが開始される状態を完成条件とする。

experiment branchの作成、実Qwen run、結果commitは本実装taskでは行わない。

## 14. Run artifactのGit扱い

Record v3の、

- `result.json`
- `trace.md`
- `frames/`

およびexperiment-level `index.json` はresearch code repositoryへcommitしない。

既定の `OUTPUT_ROOT` 配下へ保存する。

実験終了後の研究上の結果はCompanyの

```text
.research/lab/projects/agentic-streaming-videoqa/experiments/
```

へ別途experiment logとして記録する。

## 15. 変更scope

想定変更箇所:

- `src/longvideoqa_workbench/entrypoints/cli.py`
- batch manifest parsingに必要な最小module
- `src/longvideoqa_workbench/presentation/web_view.py`
- 必要ならsingle-run / batch-run共通の小さなhelper
- `scripts/workbench.sh`
- `experiments/2026-10-09-initial-behavior-20s-3min.yaml`
- 関連unit / CLI / Record v3 / trace tests

新dependencyは追加しない。YAMLは既存PyYAMLを利用する。

## 16. 対象外

- 実Qwen / GPUで6 Runを実行すること。
- GPU並列化。
- model batching。
- FlashAttention / quantization / dtype変更。
- decode frame cache。
- JPEG保存削減。
- traceをWindowごとではなくfinalだけ生成する最適化。
- per-window decode / I/O wall-clock fieldの追加。
- `max_new_tokens` 変更。
- Prompt本文変更。
- sampling contract変更。
- multiple QAでSituation / Summaryを共有する仕組み。
- Record v3 schemaの大規模変更。
- 実験結果の自動Company書込。

## 17. Verification

### 17.1 manifest / batch

Fake dataset / Fake modelで、少なくとも次を確認する。

- manifestを読める。
- case overrideがQuestion ID / window / framesへ反映される。
- caseがmanifest順に逐次実行される。
- 同じModelService instanceが複数caseで再利用される。
- duplicate caseが実行前にrejectされる。
- succeeded caseをresume時にskipする。
- failed / missing caseを再実行できる。
- case -> run_id / statusがindexへ残る。
- single-run `run` が非回帰。

### 17.2 trace

Record v3 fixture / Fake Runで次を確認する。

- Questionが冒頭へ表示される。
- ground truthが表示される。
- model answerが表示される。
- correctが表示される。
- total runtimeがstarted_at / finished_atから決定的に計算される。
- Situation / Summary elapsedが3桁小数で表示される。
- Window inference timeが両者の和。
- pipe / newline escaping等の既存trace安全性を維持する。
- partial / running状態でもtrace生成が失敗しない。

### 17.3 branch-end regression

- 関連pytest
- repositoryの既存短時間pytest suite
- compileall / import check
- CLI help
- Fake batch-run smoke
- `git diff --check`
- clean status確認

実Qwen / GPUは実装検証で実行しない。

## 18. Success Criteria

1. 2つのQuestion IDをconcrete manifestへ固定できる。
2. manifestに20秒1条件 + 3分5条件の計6 caseがある。
3. W4 / S050の重複Runが無い。
4. `./scripts/workbench.sh batch-run <manifest>` が1 processで全caseを逐次処理する。
5. 同一Qwen modelはcase間で再loadせずModelServiceで再利用できる。
6. caseをGPU並列実行しない。
7. succeeded caseはresume時にskipできる。
8. duplicate conditionを実行前にrejectする。
9. experiment indexからcase_id -> run_id / statusを追跡できる。
10. 各Runは既存Record v3として独立保存される。
11. trace.md冒頭にQuestion / Ground truth / Model answer / Correct / Total runtimeが表示される。
12. 3分5条件を含む全RunでTotal runtimeを記録できる。
13. Window表にSituation time / Summary time / Window inference timeが表示される。
14. Window inference timeは既存elapsed_secondsの和であり、decode / I/Oを混同しない。
15. Answer Prompt / Prompt本文 / max_new_tokens / sampling contractは本specで変わらない。
16. dirty worktreeではbatch-runが実験開始前に停止する。
17. single-run / Browser / Record v3の既存主要経路が短時間testで非回帰。
18. 実装branchだけをCodexが作成し、merge / push / PRを行わない。
19. ユーザーがmain統合後にexperiment branchを作れば、1コマンドで6 Runを開始できる。
20. 実Qwen / GPUの6 Runは実装task中に開始されない。

## 19. Ambiguity Gate

### blocking

実装開始時に必要なのは次の2値だけ。

- 20秒用Question ID
- 3分用Question ID

これらが未入力ならCodexは実装を開始しない。

### non-blocking

- batch manifest parserを `entrypoints/cli.py` 近傍に置くか、小さな専用moduleへ分けるか。
- index JSONのkey順。
- private helper名。
- test fileの分割。
- CLI最終summaryの見た目。

既存architectureとtest styleへ合わせ、不要な抽象化を増やさない。

## 20. Spec Gate

本specは2026-10-09にユーザー承認され、`draft -> approved` へ更新後に実装を開始した。ユーザーから指定されたIDは `I2Fyzav8MxE_0`（21.98秒）と `66dwcQ1Y048_0`（186.81秒）。後者は約3分条件として扱う。

## 21. Implementation Handoff

- approved spec: 本spec（実装検証完了後、statusを`implemented`へ更新）
- 実装目的: 20秒・約3分の2 Question IDからconcrete experiment manifestを作り、single-process batch-run、resume、trace timingを実装して、main統合後のexperiment branchから1コマンドで6 Runを開始可能にする。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `9fc2a50ea11c54efd69b68b93c4652c5c78de06a`。着手直前にGitHub mainをfetchして確認。
- 実装branch: `feat/initial-behavior-batch-run`（`9d6b094`, `15063a7`）
- 変更scope: Sections 4--15
- 対象外: Section 16
- success criteria: Section 18。実装branchで達成し、既存pytest suite、Fake batch CLI smoke、compileall、CLI help、wrapper syntax、diff checkが成功。
- 許可される短時間検証: Fake/unit/CLI/Record/trace/compile/diff check。すべて実施済み。
- 長時間run: 未許可。実Qwen / GPU / 20秒・3分の実Runを開始しない。
- Git: branch作成 / implementation / verification / commitのみ。merge / push / PR禁止。
- 未検証予定: 実Qwenでのthroughput、実データ6条件のruntime、Prompt品質、科学的結果。実Qwen/GPU実験は起動していない。
