---
date: 2026-10-08
last_updated: 2026-10-08
project: agentic-streaming-videoqa
type: implementation
status: approved
primary_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
primary_baseline_ref: main
primary_baseline_commit: b9cfaf2a3afe6967bd945b67bf0c65aa23f9f8db
related_repository: tamaki-lab/sequential_loader
related_github_reference: docs/target-frame-stream@76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc
related_specs:
  - 2026-10-08-workbench-run-artifact-trace-simplification-spec.md
source_brainstorm:
  - 2026-10-08-server-migration-offline-priorities.md
---

# Workbench UI重複表示削除 / partial window sampling cadence固定 spec

## 1. 目的

実Qwenをserve画面で確認した結果、現在のWorkbenchに次の2点が確認された。

1. 新しいFrames / Situation / Summary blockの下に、旧Stage rendererによるSituation / Summary出力が重複表示される。
2. 最終partial windowでも `frames_per_window` 個のtargetを再配置するため、通常windowとsampling cadenceが変わる。

本specではこの2点だけを修正する。

## 2. 現在の明示承認

2026-10-08、ユーザーは次の方針を明示承認した。

- Record v3の通常Browser画面では、下部の旧Stage出力を重複表示しない。
- raw model outputやPromptを削除するのではなく、既存の詳細dialogから必要時に確認できる状態を維持する。
- `window_seconds=4`, `frames_per_window=8` なら基準sampling intervalを0.5秒とする。
- 22秒動画の最終20--22秒windowは8枚へ再配分せず、20.0 / 20.5 / 21.0 / 21.5秒の4 targetとする。
- 最終partial windowでも通常windowと同じsampling intervalを維持する。
- `full_rgb` と `target_only` の両reader modeで同じsampling意味に揃える。

blocking ambiguityはない。

## 3. 現行実装の確認

### Workbench

確認時点:

```text
repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
branch: main
commit: b9cfaf2a3afe6967bd945b67bf0c65aa23f9f8db
```

UIでは `renderViewedTurn()` が同一turnに対して

```text
renderFrames(turn)
renderTurnStages(turn)
renderChunkBlock(...)
```

を呼ぶ。

新しい `renderChunkBlock()` はFrames / Situation / Summaryと詳細dialogへの導線を持つ。一方、`renderTurnStages()` は旧 `#stage-results` へSituation / Summaryのvalidated outputを再表示し、折りたたみ内にresolved Promptとraw outputを表示する。

したがってRecord v3の通常画面では同じsemantic outputが二重表示されている。

samplingでは `streaming/sampling.py::time_grid_targets(start, end, count)` が

```python
width = end - start
start + width * index / count
```

で常に `count == frames_per_window` 個のtargetを作る。

現行test `test_last_incomplete_window_uses_its_actual_duration_grid` も短い最終windowへ固定枚数を再配置する旧挙動を固定している。

default configは

```yaml
window_seconds: 4
frames_per_window: 8
reader_mode: target_only
```

である。

### sequential_loader

Workbenchの `target_only` はpublic APIの

```text
TimeGridSamplingPolicy
target_frame_stream
```

を利用する。

GitHub上でこのAPIを確認できる現在参照は

```text
tamaki-lab/sequential_loader
docs/target-frame-stream@76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc
```

であり、その `TimeGridSamplingPolicy.target_windows()` も最終partial windowへ固定 `frames_per_window` 個を再配置する。

ただしGitHubから、研究サーバ上で現在editable installされている `sequential_loader` のlocal checkout / branch / dirty stateは確認できない。実装時はCodex側で実体を確認し、古いremote branchをlocal実体の代用として扱わない。

## 4. Fix A: Record v3 BrowserのStage重複表示を削除

### 4.1 v3通常表示

Record v3のwindow表示は、新しいhuman-readable blockを正本とする。

```text
Frames
Situation
Summary
Prompt・入力
Summary details
```

v3では同じSituation / Summaryを `#stage-results` に再表示しない。

### 4.2 詳細情報

次は削除しない。

- raw model output
- resolved Prompt / Prompt snapshot
- model info
- generation
- validation
- elapsed time
- JSON detail

これらは既存の `run-detail-dialog` / 詳細tabsから必要時に確認する。

通常画面へraw outputを常時追加しない。

### 4.3 Legacy

Record v2 / Legacy read-only表示に旧 `renderTurnStages()` / `#stage-results` が必要なら、その互換経路だけに限定して残す。

v3のためにLegacy表示を削除しない。

逆にLegacy互換目的のrendererをv3へ常時適用しない。

### 4.4 対象外

今回、frame strip、Final Result card、Question / Choices、Prompt Library、translation、researcher viewの意味は変更しない。

## 5. Fix B: sampling cadenceを動画終端まで一定にする

### 5.1 configの意味

`frames_per_window` は、

> **完全な `window_seconds` 長のwindowに対して何個のtargetを置くか**

を意味する。

基準sampling intervalを

```text
delta = window_seconds / frames_per_window
```

とする。

### 5.2 target定義

各window `[start, end)` のtargetは

```text
start + k * delta
```

のうち

```text
start + k * delta < end
```

を満たすものだけとする。

`k` は0から始める。

したがってwindow開始時刻は常に最初のtarget候補になる。

完全長windowでは従来どおり `frames_per_window` 個になる。

partial windowでは実時間に応じてtarget数が減る。

### 5.3 具体例

```text
duration_seconds = 22
window_seconds = 4
frames_per_window = 8

delta = 4 / 8 = 0.5 sec
```

target:

```text
0--4   : 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5
4--8   : 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5
...
16--20 : 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5
20--22 : 20.0, 20.5, 21.0, 21.5
```

最終2秒だけ8枚を0.25秒間隔へ再配置してはいけない。

### 5.4 first-after-target規則

既存のfirst-frame-at-or-after-target規則は変更しない。

- future windowのframeを直前windowへ入れない。
- targetへ到達しなかった場合にfake frameで穴埋めしない。
- timestamp単調性の既存validationを維持する。
- target数が減ることと、実動画側でtargetへ到達できず採用frame数がさらに減ることを区別する。

### 5.5 full_rgb

Workbenchの `iter_time_grid_windows()` は上記deltaを動画全体で固定し、各boundaryへ同じdeltaを適用する。

現在の `time_grid_targets(start, end, count)` の「実window幅をcount分割する」意味は廃止する。

private helper名やsignatureは実装者が既存styleに合わせて変更してよいが、外部のExecutionSettingsは増やさない。

### 5.6 target_only

defaultの `target_only` でも同じtarget集合にする。

sequential_loader側の `TimeGridSamplingPolicy` が実際に現在環境で利用されている場合、そのpublic policyを同じdelta契約へ変更し、Workbench側とtarget timestampが一致することをtestする。

Workbench側だけを直し、default `target_only` が旧挙動のまま残る状態を実装完了としない。

## 6. Record / artifactへの影響

Record v3 schema自体は変更しない。

`result.json.turns[].window.frames[].target_timestamp_seconds` は新しいtarget集合を記録する。

`frames/` へ保存されるJPEG枚数も、最終partial windowでは新target数に応じて減る。

`trace.md` schemaは変更しない。

既存Runは変更・migrationしない。修正前のRunはその時点のsampling条件を保持する。

## 7. serve / run

`serve` と `run` は同じRunService / RunSession / streaming / workflow / Record経路を使用するため、sampling修正をentrypoint別に二重実装しない。

同一ExecutionSettingsなら、serveとrunで同じwindow target契約を使用する。

操作方法だけが異なる。

- serve: 人間がwindowごとにadvance
- run: ready / awaiting_next_turnを自動advance

## 8. 実装対象

### Workbench

主対象:

```text
src/longvideoqa_workbench/web/app.js
src/longvideoqa_workbench/streaming/sampling.py
src/longvideoqa_workbench/streaming/reader.py  # target_only接続確認が必要な場合
tests/test_sequential_windows.py
Browser/UI関連test
docs/sequential-processing.md
```

必要な場合だけ周辺testを更新する。

### sequential_loader

local environmentでWorkbenchの `target_only` を実際に提供しているsourceをpreflightで特定する。

GitHub上の参照実装では主対象は

```text
src/sequential/target.py
tests/test_target_sampling.py
tests/test_target_stream.py
```

相当。

ただしlocal checkoutの現在構造をGitHub参照だけで決め打ちしない。

## 9. 実装前preflight

Codexはコード変更前に以下を確認する。

### Workbench

- current branch
- HEAD
- dirty state
- latest main
- `renderViewedTurn()`
- `renderTurnStages()`
- `renderChunkBlock()`
- `time_grid_targets()`
- `iter_time_grid_windows()`
- default reader mode

### sequential_loader

現在のPython environmentで

```python
import sequential_loader
print(sequential_loader.__file__)
```

等により、実際にimportされるsourceを特定する。

そのsourceがeditable local checkoutならbranch / HEAD / dirty stateを確認する。

GitHubの `docs/target-frame-stream` branchを、local source確認なしにcheckout元として仮定しない。

sourceが編集不能なinstalled wheelのみで、対応するcurrent source repositoryを一意に特定できない場合は、target_onlyをhackで迂回せず停止して報告する。

## 10. Test契約

### UI

Record v3 payloadについて:

- Situation semantic outputが通常画面に1回だけ表示される。
- Summary semantic outputが通常画面に1回だけ表示される。
- `#stage-results` にv3の重複Stage cardを生成しない。
- Prompt / raw model outputは詳細dialogから引き続き確認できる。
- Final Result cardを壊さない。
- Window navigationを壊さない。

Legacy fixtureが存在する場合は旧read-only表示の回帰も確認する。

### Sampling unit

最低限:

```text
duration=22, window=4, frames=8
last targets == (20.0, 20.5, 21.0, 21.5)
last target count == 4
```

さらに:

- full 4秒windowは8 targetのまま。
- partial 2秒windowを8 targetへ圧縮しない。
- partial幅がdeltaの整数倍でない場合も `target < end` を満たすbase cadenceのみを返す。
- unreached targetをfuture/fake frameで埋めない。
- full_rgb / target_onlyでtarget timestampsが同じ。

### Integration

Fakeまたは生成短動画による短時間経路で:

- serve-side projectionに重複Situation / Summaryがない。
- runとserve相当のstreaming pathが同じsampling contractを使う。
- Record v3の最終partial window frame metadataが期待target数になる。

実Qwen/GPU/LongVideoBench full runは本実装成功条件に含めない。

## 11. Git運用

### Workbench

最新 `main` から1本だけimplementation branchを作る。

推奨:

```text
fix/ui-dedup-partial-window-sampling
```

Stepごとにbranchを増やさない。

### sequential_loader

別repositoryの変更が必要なため、**そのrepositoryでも現在の実装元から1本だけbranch**を作る。

ただしGitHub default `master` にはtarget-frame public APIが確認できないため、local sourceを確認せず `master` から新規実装を作り直してはいけない。

現在のtarget-frame APIを実際に提供しているlocal branch / commitを基準に、その上へ1本のfix branchを作る。

どちらのrepositoryでも:

- 意味単位のmicro-commit
- 各commit後に最も近い短時間test
- 日本語タイトル + 本文5〜6行程度
- 本文は箇条書きにしない
- backup目的の旧fileを残さない
- main / masterへのmerge禁止
- remote push禁止
- PR禁止
- history rewrite禁止

最終merge / pushはユーザー確認後に行う。

## 12. 推奨micro-commit

無理にcommit数を固定しないが、概ね次の意味単位を推奨する。

1. Workbenchのv3 Stage重複表示を削除し、Browser回帰testを追加。
2. Workbench full_rgbのfixed-cadence samplingとtestを更新。
3. sequential_loader target_only policyを同じfixed cadenceへ変更し、public API testを更新。
4. Workbench target_only integration parityと必要最小限のdocを更新。

各commitは独立して説明・検証できる範囲にまとめる。

## 13. 対象外

- Prompt変更
- Agent責務変更
- Summary内容の改善
- Answer format変更
- Record v3 schema変更
- dynamic window
- adaptive fps
- content-aware sampling
- Early Answer
- frame画像のMarkdown埋め込み
- Final Result card再設計
- 新dependency
- 実Qwen長時間run
- Dataset全件評価

## 14. Success Criteria

1. Record v3の通常Browser画面でSituationが二重表示されない。
2. Record v3の通常Browser画面でSummaryが二重表示されない。
3. raw output / Promptは詳細dialogから確認できる。
4. v2 / Legacy read-only互換を必要以上に壊さない。
5. full 4秒 / 8 framesのtargetsが0.5秒間隔の8個のまま。
6. 22秒動画の20--22秒windowが20.0 / 20.5 / 21.0 / 21.5の4 targetになる。
7. partial windowへ8 targetを圧縮再配置しない。
8. first-after-target規則とcausal window境界を維持する。
9. unreached targetをfake / future frameで埋めない。
10. full_rgbとtarget_onlyで同一設定から同じtarget timestampsを得る。
11. serveとrunでsampling contractを二重実装せず共有する。
12. Record v3 schemaを変更しない。
13. 既存Runをmigration / rewriteしない。
14. short unit / integration / Browser regressionが成功する。
15. 実Qwen/GPU/LongVideoBench full runを実装成功条件にしない。

## 15. Ambiguity Gate

### blocking

なし。

期待する外部挙動とsampling式はユーザー承認済みで一意。

### non-blocking

- v3で旧DOM node自体を残して空にするか、Legacy専用経路へ整理するか。
- fixed-cadence target helperの関数名 / signature。
- floating point境界を安全に扱うprivate実装詳細。
- sequential_loader側のtest file配置。
- Browser testを既存fileへ追加するか新規fileにするか。

既存styleと最小差分を優先する。

local sequential_loader checkoutのbranch / dirty stateはGitHubから未確認だが、これは実装preflightで確認可能な環境情報であり、sampling契約自体のblocking ambiguityではない。

## 16. Spec Gate

ユーザーは2026-10-08に「2点を修正したい」「今出力した通りで間違いない」「その方針で行く」と明示承認した。

したがって本specは **approved** とし、短時間testまでのimplementationへhandoff可能。

実Qwen / GPU / 長時間評価、merge、push、PRは別Gate。

## 17. Implementation Handoff

- approved spec: 本spec
- primary repository: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`
- baseline: `main@b9cfaf2a3afe6967bd945b67bf0c65aa23f9f8db`
- related repository: `tamaki-lab/sequential_loader` の現在環境で実際にtarget-only public APIを提供するcheckout
- GitHub reference containing current public API: `docs/target-frame-stream@76badb1c407a34de6f2dfa7e5d4040ef7c4b2ccc`
- UI delta: v3で旧Stage semantic outputの重複表示をやめ、詳細dialogは維持
- scientific delta: partial final windowでも `delta = window_seconds / frames_per_window` を維持
- scope: Section 8
- out of scope: Section 13
- success criteria: Section 14
- allowed verification: unit、Fake/生成動画streaming、HTTP/Browser短時間回帰、compileall、diff check
- long run: 未許可
- Git: repositoryごとに1 implementation branch、意味単位micro-commit、merge / push / PR禁止
- local-only unknown: sequential_loaderの現在checkout/dirty stateはCodex preflightで確認
