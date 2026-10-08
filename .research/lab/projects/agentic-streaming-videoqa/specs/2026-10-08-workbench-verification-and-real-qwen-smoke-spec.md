---
date: 2026-10-08
last_updated: 2026-10-08
project: agentic-streaming-videoqa
type: implementation
status: approved
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 8426194b6e42e34342f9ea4b58b64d52e69b0a99
related_specs:
  - 2026-10-07-workbench-runtime-workflow-record-simplification-spec.md
  - 2026-10-07-workbench-shell-entrypoint-simplification-spec.md
---

# Workbench 検証整理・launcher整合・実LongVideoBench/Qwen 3-Agent smoke spec

## 1. 目的

Workbenchの現行 `main` には、Situation / Summary / Answerの3-Agent RuntimeとRecord v2が既に統合されている。
一方で、Runtime簡略化前のMemory / Event / Evidence / ServerContext契約を前提とするtestが残り、
shell launcherにも既存specとの不整合が再発している。

本specでは、新しい研究ロジックを追加しない。
現在実装済みの3-Agent baselineを**検証可能な状態へ完成させること**を目的とする。

完了時には、次をすべて満たす。

1. 旧Runtime契約を参照するtestを現行Situation / Summary / Answer + Record v2へ追従させる。
2. Fake短時間回帰を `scripts/verify-runtime-smoke.sh` から再現可能にする。
3. 通常利用の `scripts/workbench.sh` ではLongVideoBenchを明示的に利用し、Dataset設定不足をFake Datasetへsilent fallbackしない。
4. machine-localなDataset path、GPU、venv、Qwen cacheをresearch server上で探索・検証し、tracked fileへ固定しない。
5. 実LongVideoBench + 実Qwen3-VLでSituation -> Summary -> Answerを通す**bounded E2E smoke**を1回成功させる。
6. 実行できない場合は、失敗地点と原因を切り分けて記録し、「未確認」を「成功」と扱わない。

Markdown trace機能は本specの対象外とする。

---

## 2. 現在確認できている実装状態

GitHub上の基準は

```text
RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
main@8426194b6e42e34342f9ea4b58b64d52e69b0a99
```

である。

### 2.1 実装済み

現行mainでは少なくとも次を直接確認できる。

- canonical ConfigのAgent roleは `situation / summary / answer`。
- top-level `memory`、`agents.memory` は現行default Configから削除済み。
- `workflow/situation.py`、`workflow/summary.py`、`workflow/answer.py` が存在する。
- `VideoQAWorkflow` は各windowでSituation -> Summary、EOFでAnswerを1回だけ実行する。
- Situation / Summary outputはplain text。
- Answerは `<1-based choice number>. <choice text>` をPython側で検証する。
- `RecordService` / `RunRecord` は `artifact_schema_version=2` を扱う。
- LongVideoBench Adapter、VideoStreamService、Qwen3-VL Adapterは現行コードに存在する。
- `configs/default.yaml` はLongVideoBench + Qwen3-VL + video_clip + 3 Agentを指す。

したがって、本specで3-Agent自体を再実装しない。

### 2.2 未完了または不整合

現在のGitHub mainでは、次を確認できる。

- 3-Agent Runtime統合commitの完了メッセージには、統合時にtest / smokeを実行していない旨が記録されている。
- 複数の既存testが削除済みの
  - `workflow.memory`
  - `workflow.events`
  - `workflow.final_output`
  - 旧 `ServerContext`
  - `observation_context_mode`
  - `memory_budget_tokens`
  等を参照している。
- `tests/test_e2e_fake.py` も旧 `ServerContext` / old stage contractを参照する。
- 現在の `scripts/verify-runtime-smoke.sh` はその旧testを呼ぶため、現行Runtimeに追従した回帰入口として未完成である。
- 現在の `scripts/verify-runtime-smoke.sh` は `PYTHONPATH` と `CUDA_VISIBLE_DEVICES` を上書きしており、2026-10-07 shell entrypoint specと不整合である。
- 現在のtracked `.env.example` にはresearch server固有のLongVideoBench absolute pathとGPU番号が入っており、machine-local値をtracked fileから分離する既存契約へ回帰している。
- `workbench.sh` は `LVB_ROOT` が設定された場合にはLongVideoBenchを渡すが、設定されない場合はPython側のserve registryがFake Datasetへfallbackできる。
- 現行 `configs/default.yaml` はDataset / modelは実設定だがquestion IDを固定していないため、CLI runでは `--question-id` またはquestion ID入りconfigが必要である。
- 現在のSituation / Summary / Answer + Record v2構成で、実LongVideoBench + 実Qwen3-VLをEOFまで通したEvidenceはGitHub上で確認できない。

### 2.3 GitHubから確認できないもの

以下はresearch serverのlocal stateであり、GitHubだけでは確認済みとしない。

- 現在のlocal worktree / dirty change。
- repository rootのuntracked `.env`。
- 実際のLongVideoBench配置。
- `.venv` の現在内容。
- local `sequential_loader` のinstall状態。
- Hugging Face model cache。
- 現在利用可能なGPU / GPU process。
- 未push commitやlocal-only output。

実装者はこれらを実装開始前にlocalで確認する。

---

## 3. Authority / 既存specとの関係

本specは次の2本のfollow-upである。

### Runtime / Workflow / Record simplification

`2026-10-07-workbench-runtime-workflow-record-simplification-spec.md`

研究契約として以下を維持する。

- Situation / Summary / Answer。
- Question非依存Situation / Summary。
- EOF Answer。
- Record v2。
- Legacy Run read-only。
- new RuntimeへMemory/Event/Evidence契約を戻さない。

本specはこの設計を変更せず、残ったtest・verification debtを解消する。

### shell entrypoint simplification

`2026-10-07-workbench-shell-entrypoint-simplification-spec.md`

以下を維持する。

- `.env` はmachine-localかつGit管理外。
- `.env.example` はplaceholder/exampleだけ。
- `.venv/bin/longvideoqa` / `.venv/bin/python` を使い、system Pythonへfallbackしない。
- `verify-runtime-smoke.sh` はFake短時間回帰専用。
- `verify-runtime-smoke.sh` は `PYTHONPATH` / `CUDA_VISIBLE_DEVICES` を設定・上書きしない。
- `workbench.sh` はforeground実行、Ctrl+C終了。

追加契約として、**user-facing `workbench.sh serve/run` はDataset設定不足をFake Datasetへsilent fallbackしない**。
Fake Datasetはtest / Fake smokeの明示経路に限定する。

---

## 4. 今回の最終状態

通常利用と検証を次のように分ける。

```text
./scripts/workbench.sh serve
    -> LongVideoBench browser
    -> QwenはRun開始までloadしない

./scripts/workbench.sh preflight
    -> Qwen dependency / CUDA visibility check
    -> model weightはloadしない

./scripts/workbench.sh run --question-id <real LongVideoBench question>
    -> LongVideoBench
    -> Qwen3-VL
    -> Situation -> Summary -> ... -> Answer
    -> Record v2

./scripts/workbench.sh verify
    -> verify-runtime-smoke.sh
    -> Fake Dataset + Fake Model
    -> fast regression only
    -> GPU / real dataset / model downloadなし
```

FakeとRealを同じcommandの暗黙fallbackとして混在させない。

---

## 5. Scope A: 現行Runtimeへtestを追従

### 5.1 原則

削除済みproduction codeをtestのために復活させない。

特に以下を「testを通すためだけ」に戻さない。

- `workflow.memory`
- `workflow.events`
- `workflow.observations`
- `workflow.final_output`
- generic old Agent / AgentService
- old ServerContext / TurnSession実体
- old Memory/Event/Evidence runtime contract
- `observation_context_mode`
- `memory_budget_tokens`

現在必要な外部挙動を検証するtestは新契約へ書き換える。
削除済みprivate helperだけを検証していたtestは削除してよい。

### 5.2 必須test範囲

少なくとも次を新契約で検証する。

#### Agent / Workflow

- Situation outputがplain text `situation_description`。
- SituationがQuestion / Choices / previous summaryを入力に持たない。
- Summaryがprevious summary + current situationを統合する。
- 2 window以上でSummaryが順次更新される。
- AnswerはEOFで1回だけ呼ばれる。
- AnswerはQuestion / Choices / final Summaryだけを利用する。
- 1-based choice numberとchoice textの不整合をPythonがrejectする。

#### Config / Prompt

- canonical Agent roleがSituation / Summary / Answer。
- top-level Memory設定を新Configへ復活させない。
- built-in Situation / Summary / Answer prompt compatibility。
- saved inference settingsから旧Memory fieldを新Runtimeへ復元しない既存compatibility。

#### Record v2

- new RunはRecord v2。
- `artifact_schema_version=2`。
- completed windowごとに `turns.jsonl` 1行。
- Situation / Summary semantic outputとmodel execution metadataが保存される。
- EOFで `final_answer.json` が更新される。
- `choice_index` は1-based。
- new Runでold memory/chunks/stages artifactを生成しない。
- Legacy Runはread-onlyで開ける。
- Legacy Runへ追記・resume・automatic migrationしない。

#### Runtime / API / Browser

- Run作成時点ではQwen/Fake modelを呼ばない。
- 1 click / 1 advanceで1 windowだけ進む。
- EOF後にAnswerへ進む。
- saved new Runをread-only projectionで再表示できる。
- Situation / Summary / Final Answerがnew-run UIへ出る。
- Dataset Browser / Library / Prompt Libraryの主要既存機能を壊さない。

#### CLI

- Fake CLI RunがEOFまで自動進行する。
- final answerとRecord v2が保存される。

### 5.3 repo-wide旧参照監査

production/test双方について、旧Runtime contractへの不要参照を検索する。

少なくとも検索対象:

```text
workflow.memory
workflow.events
workflow.observations
workflow.final_output
MemoryTask
ServerContext
TurnSession
observation_context_mode
memory_budget_tokens
evidence_aggregation
chunk_understanding
```

Legacy compatibility fixture、legacy artifact文字列、過去Run readerで必要な参照と、
誤って残ったruntime/test依存を区別する。

---

## 6. Scope B: `scripts/verify-runtime-smoke.sh`

このscriptは**Fake専用の短時間regression**として完成させる。

必須条件:

- `.venv/bin/python` のみを使う。
- `.venv/bin/python` が無ければ明示error。
- system Pythonへfallbackしない。
- `PYTHONPATH` を設定しない。
- `CUDA_VISIBLE_DEVICES` を設定・空文字化しない。
- repositoryのcurrent installed packageを使う。
- temporary WORKBENCH_HOME / outputを使い、user dataや既存runを汚さない。
- compileall。
- 現行Runtimeへ追従したtargeted pytest。
- Fake CLI run。
- Fake HTTP/API run。
- Situation / Summary。
- EOF Answer。
- Record v2保存。
- saved-run reload。
- Browser JS / APIの最低限smoke。
- 実Qwen、GPU、LongVideoBench、model downloadを呼ばない。

shell script自身の成功を、古いtestがたまたま存在することに依存させない。

---

## 7. Scope C: `scripts/workbench.sh`

`workbench.sh` は通常研究利用のuser-facing dispatcherとする。

### 7.1 Dataset contract

`serve` と `run` はLongVideoBenchを通常Datasetとする。

- `LVB_ROOT` が未設定なら、Fakeへsilent fallbackせず明示error。
- `LVB_ROOT` が存在しないpathなら明示error。
- 少なくとも `lvb_val.json` と `videos/` の存在を起動前に検査する。
- path検査でDataset内容全件を読み込む必要はない。
- Fake Datasetを通常launcherから暗黙利用しない。

Pythonのdirect CLIをtest内部でFake利用する既存能力は残してよい。
今回の必須変更はuser-facing shell側でFake/Real境界を明確にすることであり、
不要にPython public APIを壊さない。

### 7.2 subcommand

維持:

- `serve`
- `preflight`
- `run`
- `verify`
- help

`preflight` はDataset pathが無くてもQwen/CUDAだけを調べられるようにしてよい。
`verify` はFake専用なのでLVB_ROOTを要求しない。

### 7.3 Run

`run` はcanonical default configを維持してよい。

`configs/default.yaml` にはquestion IDを固定しない。
実LongVideoBench CLI runでは、

```bash
./scripts/workbench.sh run --question-id <question-id>
```

またはquestion ID入りrecipeを利用する。

question IDを勝手にtracked defaultへ固定しない。

引数不足でrun不能な場合は、Fakeへ切り替えず、必要な `--question-id` / configを示す明確なerrorにする。

### 7.4 tracked machine-local値を除去

少なくとも `.env.example` から以下を除去する。

- 実research serverのLongVideoBench absolute path。
- 実GPU番号。

placeholder/commentだけを残す。

例:

```bash
# LVB_ROOT=/path/to/LongVideoBench
# CUDA_VISIBLE_DEVICES=<gpu-id>
```

実値はuntracked `.env` のみに置く。

---

## 8. Scope D: research server上のenvironment / Dataset探索

ここは本specの重要なverification stepである。
GitHub上の値をlocal実体の代わりに使用しない。

### 8.1 repository / Git

実装開始時に確認:

- current working directory。
- `git rev-parse --show-toplevel`。
- current branch / HEAD。
- `git status --short`。
- `git worktree list`。
- mainとのmerge-base。
- userのdirty / untracked change。

既存dirty changeを勝手に消さない。

### 8.2 `.env`

確認順:

1. current repository rootの `.env`。
2. current shell environmentの
   - `LVB_ROOT`
   - `CUDA_VISIBLE_DEVICES`
   - `WORKBENCH_HOME`
   - `OUTPUT_ROOT`
3. `.env.example` / README / docsはhintとしてのみ利用。
4. 必要なら既存worktreeのmachine-local設定をread-onlyで確認する。

credentialやAPI keyの値をlog / Company / commitへ出さない。

`.env` が無い、またはstale pathなら、後述のDataset / GPU探索後に
**current repositoryのuntracked `.env`** を必要最小限で作成・修正してよい。

tracked fileへlocal値を移さない。

### 8.3 LongVideoBench

候補は次の順で探索する。

1. 現在の `LVB_ROOT`。
2. local `.env` に記録されたpath。
3. current tracked docsに残るpathはcandidate hintとしてだけ扱う。
4. expected research data parent配下で `lvb_val.json` をbounded searchする。

全filesystemを無制限に探索しない。
少なくともresearch data rootとして妥当なparentへ限定する。

正しいLongVideoBench rootの条件:

```text
<LVB_ROOT>/
├─ lvb_val.json
└─ videos/
```

さらにannotationを読み、

- 有効なquestion IDがある。
- 対象recordのvideo pathが `videos/` 配下に実在する。
- durationが取得できる。

ことを確認する。

absolute pathはmachine-local情報なのでtracked Company/spec/READMEへ固定しない。
完了報告では必要ならユーザーへlocal確認結果として示してよい。

### 8.4 project venv / dependency

確認:

- `.venv/bin/python`
- `.venv/bin/longvideoqa`
- packageがcurrent checkoutを参照しているか。
- `sequential_loader` import。
- `torch`
- `transformers`
- `accelerate`
- Pillow / PyYAML等のdeclared dependency。

新しいvenvを自動作成しない。

既存project dependencyの不足が判明した場合:
- 何が不足しているかを記録する。
- 大規模なCUDA/PyTorch再installや環境作り直しを勝手に行わない。
- 現在の環境を壊さない範囲で一意に修正できない場合は実Qwen smokeのblockerとする。

### 8.5 Qwen model cache

実Qwen smoke前に、

- `Qwen/Qwen3-VL-4B-Instruct` のlocal cache有無。
- processor / model snapshotがlocalで利用可能か。

を確認する。

本specは**大型modelの自動download許可を含まない**。
cacheが無ければ実Qwen runを開始せず、`model cache missing` として原因を記録する。

可能ならreal smokeはoffline/local-files-only相当の条件で行い、
意図しないdownloadを開始しない。

### 8.6 GPU

実Qwen smokeの直前に確認:

- `nvidia-smi`。
- visible GPU。
- free memory。
- 他processの利用状況。
- `./scripts/workbench.sh preflight`。

他人のprocessを停止しない。
GPUを横取りしない。

明確に利用可能なGPUがある場合だけ、untracked `.env` の
`CUDA_VISIBLE_DEVICES` を現在環境に合わせて設定してよい。

利用可能GPUが無い場合は、実装/testを完了できるところまで進め、
real Qwen smokeを `GPU unavailable/busy` として未完了で記録する。

---

## 9. Scope E: 実LongVideoBench + Qwen 3-Agent bounded E2E smoke

これはaccuracy評価ではなく、現在の配線が実環境で動くことを確認するsmokeである。

### 9.1 実行許可

本specをユーザーが明示承認して実装を依頼した場合、
**LongVideoBenchの実データと既存local Qwen cacheを使う1回のbounded GPU smoke** は許可されたものとして扱う。

許可しないもの:

- model weightの新規大規模download。
- dataset download。
- full validation評価。
- 複数questionのbenchmark。
- 長時間性能測定。
- training。
- 他人のGPU process停止。

### 9.2 smoke sampleの選定

固定absolute pathや固定question IDをspecへ焼かない。

local `lvb_val.json` と実在videoを調べ、
**利用可能なvalidation sampleの中から短時間確認に適した短い動画を1件**選ぶ。

選定時に記録する:

- question ID。
- video locator / relative path。
- duration。
- 選定理由。

正解labelは推論入力へ渡さない。

### 9.3 bounded config

tracked configをsmoke専用値へ書き換えない。

必要なら `/tmp` 等にlocal-only configを生成し、
current `configs/default.yaml` を基準に以下を維持する。

- dataset: longvideobench。
- backend: qwen3_vl。
- model: `Qwen/Qwen3-VL-4B-Instruct`。
- roles: Situation / Summary / Answer。
- reader: target_only。
- visual input: video_clip。
- prompt: current built-in Situation / Summary / Answer。

smokeは1〜2 window程度になるよう、選定動画durationに応じたwindow lengthをlocal-onlyで設定してよい。
目的は、

```text
real video decode
-> Situation(Qwen)
-> Summary(Qwen)
-> 次windowがある場合は再度Situation/Summary
-> EOF Answer(Qwen)
-> Record v2
```

をbounded回数で確認することである。

temporary configはcommitしない。

### 9.4 成功確認

real smoke成功時に最低限確認:

- command exit 0。
- `run_status.json.status == succeeded`。
- `artifact_schema_version == 2`。
- `turns.jsonl` にcompleted windowがある。
- Situation `situation_description` が空でない。
- Summary `summary` が空でない。
- `final_answer.json` のanswerが空でない。
- `choice_index` が1-based range内。
- `choice_text` とanswer textが対応する。
- model_infoがQwen3-VL backend/modelを示す。
- old Memory/Event artifactをnew Runで生成しない。

精度の良し悪しは本smokeの成功条件にしない。

---

## 10. 実装順

### Step 1: Preflight audit

- local Git / worktree / dirty state。
- current main / baseline staleness。
- `.env`。
- Dataset location。
- `.venv`。
- dependencies。
- model cache。
- GPUはこの時点ではread-only確認まで。

verify:
- 調査結果を短く整理し、ユーザー変更を壊さない実装branch基点を確定する。

### Step 2: test migration

- current 3-Agent / Record v2へtestを追従。
- obsolete testを必要に応じて削除。
- production old runtimeをtestのために復活させない。

verify:
- targeted Agent / Workflow / Record / Config tests。
- collection errorが無いこと。

### Step 3: Fake verify script修正

- stale targetを新testへ変更。
- `PYTHONPATH` / `CUDA_VISIBLE_DEVICES` override削除。
- Fake CLI/API/Browser/Record v2 smoke。

verify:
- `bash -n scripts/verify-runtime-smoke.sh`。
- `./scripts/verify-runtime-smoke.sh`。

### Step 4: workbench launcher修正

- serve/runのLVB_ROOT validation。
- silent Fake fallbackをuser-facing launcherから除去。
- machine-local値をtracked `.env.example` から除去。
- run引数不足時の明確な案内。

verify:
- `bash -n scripts/workbench.sh`。
- LVB_ROOT未設定でserve/runが明示error。
- valid temporary LVB root / fake CLI harnessで引数転送を確認。
- preflight/verifyはLVB_ROOTなしでも各責務どおり動く。

### Step 5: full short regression

実装branchで:

- full short pytest。
- compileall。
- Fake verify。
- CLI help。
- `git diff --check`。
- old runtime reference audit。

失敗は原因を切り分けてscope内で修正する。

### Step 6: real environment preparation

- actual LVB_ROOTを確定。
- local `.env` を必要なら修正。
- actual Qwen cache確認。
- GPU availability確認。
- `./scripts/workbench.sh preflight`。

### Step 7: bounded real E2E smoke

- local sample選定。
- local-only bounded config。
- LongVideoBench + Qwen + 3 Agent実行。
- Record v2を確認。

### Step 8: Company / docs同期

成功・失敗Evidenceを反映する。

- 本specに `Implementation / Verification Status` を追記。
- 実装commit、実行commandの種類、test結果、real smoke結果を記録。
- failureがあればSection 11形式で原因を記録。
- current stateが変わった場合だけWorkbench READMEをSituation / Summary / Answer + current launcherへ同期。
- Company project READMEは、現在状況が実際に変わった場合だけ最小更新。
- 既存10/7 Runtime / shell specのstatusは、各specの必須scopeとverificationが実際に完了した場合のみ更新する。

---

## 11. 実行できなかった原因の記録契約

「失敗した」「環境の問題だった」だけで終わらせない。

失敗したstageごとに次を記録する。

```text
Stage:
Command / operation:
Expected:
Observed:
Failure category:
Confirmed cause:
Evidence:
Action taken:
Remaining blocker:
Retry condition:
```

failure categoryは少なくとも次から選ぶ。

- code / test regression
- stale test contract
- launcher / env loading
- missing or stale LVB_ROOT
- LongVideoBench annotation/video missing
- venv / package dependency
- sequential_loader
- Qwen model cache
- CUDA / GPU unavailable
- GPU busy / insufficient memory
- Qwen runtime / processor
- model output validation
- Record / filesystem
- unknown / not yet isolated

### 記録上の注意

- API key、credential、tokenを書かない。
- machine-local absolute pathをtracked Company文書へ恒久固定しない。
  - tracked文書では `<LVB_ROOT>`, `<REPO_ROOT>`, `<MODEL_CACHE>` のように表す。
  - actual pathはlocal terminal / Codex完了報告でユーザーへ示してよい。
- stack traceを丸ごとCompanyへ貼らず、root cause判断に必要な部分だけ記録する。
- 原因未確定なら「推測」をconfirmed causeとして書かない。

real smokeが失敗した場合、本specを `implemented` にしない。
コードとFake regressionが完了している場合は、その範囲を明示して `approved` のまま残す。

---

## 12. Success Criteria

### Tests / Runtime

1. pytest collectionで削除済みold runtime module import errorが無い。
2. Agent / Workflow / Config / Prompt / Record v2 / Runtime / API / Browser / CLIの必須testが現行契約で存在する。
3. 2 window以上のFake WorkflowでSummary更新とEOF Answer 1回を確認する。
4. new RunがRecord v2の6-file契約を満たす。
5. Legacy Run read-onlyを回帰確認する。
6. full short pytestが成功する。
7. compileallが成功する。
8. `git diff --check` が成功する。

### Fake verification

9. `./scripts/workbench.sh verify` がproject `.venv` で成功する。
10. verify scriptが `PYTHONPATH` を設定しない。
11. verify scriptが `CUDA_VISIBLE_DEVICES` を設定・上書きしない。
12. verifyはFake Dataset / Fake Modelのみで完結する。

### Launcher

13. `workbench.sh serve/run` はLVB_ROOT未設定時にFakeへsilent fallbackしない。
14. invalid LVB_ROOTを明示errorにする。
15. valid LVB_ROOTではLongVideoBench登録をCLIへ渡す。
16. tracked fileにresearch server固有Dataset absolute path / GPU番号を固定しない。
17. `.env` はGit管理外のまま。
18. `preflight` と `verify` はそれぞれQwen環境確認 / Fake回帰の責務を維持する。

### Real E2E

19. local Dataset locationを実体から確認する。
20. local Qwen cacheを確認し、未許可downloadを開始しない。
21. available GPUを確認し、他人のprocessを停止しない。
22. bounded 1件のLongVideoBench real sampleでQwen3-VL Situation -> Summary -> Answerを実行する。
23. real Runが `succeeded`。
24. Situation / Summary / Answerが空でない。
25. Answerがvalid 1-based choice。
26. Record v2が保存される。

### Reporting

27. 実行できなかった工程があれば、Section 11の形式で原因を記録する。
28. local-only stateとGitHub-confirmed stateを混同しない。
29. 実Qwen smokeが成功しない限り「3-Agent E2E確認済み」と記述しない。

---

## 13. 対象外

- Markdown Agent trace。
- 研究アルゴリズムの再設計。
- Situation / Summary / Answer prompt品質改善。
- accuracy比較。
- LongVideoBench全件評価。
- multi-seed / benchmark。
- training。
- model / dataset download。
- CUDA/PyTorch環境の大規模再構築。
- background常駐化。
- unrelated refactor。
- Legacy artifact migration。
- 他者processの停止。

---

## 14. Git運用

研究コードでは、現在のmainから**1本の実装branch**を作成する。

推奨branch:

```text
fix/workbench-verification-launchers
```

Stepごとにbranchを増やさない。

branch内で、独立して説明・検証できる意味単位でmicro-commitを積む。
各commitは1つの目的として読める変更単位とし、小さすぎる分割や異なる責務の混在を避ける。

想定commit境界:

1. stale testsを現行3-Agent / Record v2へ追従。
2. Fake verify scriptを現行Runtimeへ修正。
3. workbench launcherとtracked env exampleを修正。
4. 必要なREADME / regression説明を同期。

各commit後に、その変更へ最も近い短時間test / compile / smokeを実施する。
full regressionはimplementation branch完成時に行う。

commit messageは日本語で、

- タイトル
- 5〜6行程度の本文
- 箇条書きではない文章

とする。

本文には少なくとも、

- 何を変更したか。
- なぜ変更したか。
- どの範囲へ影響するか。
- 何を検証したか。
- 残る未検証があるか。

が自然文で含まれること。

本spec承認後はbranch作成とlocal commitを行ってよい。
**remote push、PR、main mergeは別の明示指示がない限り行わない。**

Company文書はCompany側の現行運用ルールに従う。

---

## 15. Ambiguity Gate

### Blocking

現時点の仕様上のblocking ambiguityはない。

実行時に判明し得る

- Datasetの実配置。
- `.env` の有無。
- GPU availability。
- model cache有無。
- venv dependency状態。

は設計判断ではなくlocal environment verificationであり、Section 8 / 11に従って探索・記録する。

### Non-blocking

- obsolete testを「rewrite」するか「delete」するかは、そのtestが現行public behaviorを検証しているかで決める。
- Fake smokeのtargeted pytest file構成は、現行test suiteへ合わせて最小構成にする。
- bounded real smokeのsampleはlocal Dataset実体から短時間向けに選ぶ。
- temporary smoke configのfilenameはlocal-onlyであり、tracked interfaceにしない。

---

## 16. Approval Gate

本specは2026-10-08時点では `draft` である。

ユーザーが本specを明示承認し、Codexへ実装を依頼した時点で `approved` へ更新してよい。

実装完了判定には、

- code/test修正。
- Fake verification。
- launcher修正。
- full short regression。
- **実LongVideoBench + Qwen bounded E2E smoke成功**。

が必要である。

real smokeがenvironment blockerで実行不能な場合は、
実装済み範囲と原因をSection 11形式で記録し、statusは `approved` のままとする。

---

# Implementation Handoff

- approved spec: 本書（ユーザー明示承認後）
- 実装目的: 現行Situation / Summary / Answer + Record v2をtest可能に完成させ、Fake regressionと通常LongVideoBench launcherを分離し、実LongVideoBench + Qwenでbounded 3-Agent E2Eを確認する
- 基準repository: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`
- 基準branch: `main`
- 基準commit: `8426194b6e42e34342f9ea4b58b64d52e69b0a99`（実装開始時に最新mainとstalenessを再確認）
- 変更scope: Sections 5--11
- 対象外: Section 13
- success criteria: Section 12
- 許可される短時間検証: unit / pytest / compile / Fake CLI / Fake HTTP/API/Browser / shell harness / diff check
- real run: ユーザー承認後、local existing Dataset + existing local Qwen cacheを使うbounded 1-sample GPU smokeを許可
- model/dataset download: 未許可
- Git: mainから1 implementation branch + micro-commitまで許可。push / PR / main mergeは別許可
- failure handling: 実行不能原因をSection 11形式で記録し、未確認を成功扱いしない

## Implementation / Verification Status — 2026-10-08

**Status: approved.** Fake regression, test migration, and launcher work are implemented on `fix/workbench-verification-launchers`. The real Qwen E2E did not reach a valid Answer, so this spec remains approved and the three-agent real E2E is not confirmed.

Implementation commits on the research-code branch are `4fbb8d7` (obsolete test migration), `d3af02b` (remaining Config/Prompt contract cleanup), `623d808` (Fake verifier and LongVideoBench launcher), `41532b7` (Legacy Run read-only regression), `e641fc8` (README synchronization), `3ded238` (public API/lifecycle regressions and translation exception fix), `ec001a1` (verification coverage docs), `cf383ad` (isolated CLI user data), and `ec035ac` (atomic Record JSON writes). The branch is based on the confirmed current main commit `8426194b6e42e34342f9ea4b58b64d52e69b0a99`; no push, PR, or merge was performed.

### Tests and Fake verification

- `./scripts/workbench.sh verify`: passed. It uses only `<REPO_ROOT>/.venv/bin/python`, runs compileall and the current targeted Fake tests, and sets neither `PYTHONPATH` nor `CUDA_VISIBLE_DEVICES`.
- Full short pytest: passed (133 tests). `compileall`, CLI `--help`, `git diff --check main...HEAD`, Runtime/Workflow boundary audits, and the old Runtime reference audit passed.
- The Fake integration covers CLI and HTTP/API/Browser, Prompt and translation APIs, media ranges, Run restart/cancellation, validation, two Situation/Summary windows, EOF Answer, the six-file Record v2 contract, saved-run reload, and Legacy Run read-only behavior. Record JSON snapshots use atomic replace; a concurrent status-reader regression covers the CLI polling race found during final verification.
- A fake CLI harness confirmed missing/invalid `LVB_ROOT` stops serve/run and a valid root is forwarded with `configs/default.yaml` and `--question-id`. `preflight` and `verify` work without `LVB_ROOT`.

### Research server environment and Dataset

- Repository root `.env` was absent. It was created as an ignored local file with the discovered `<LVB_ROOT>` and one currently idle GPU selection; no credential was added. `.env` remains ignored and untracked.
- Shell `LVB_ROOT` and `CUDA_VISIBLE_DEVICES` were initially unset. `.venv/bin/python` and `.venv/bin/longvideoqa` exist. `sequential_loader` imports successfully; torch is `2.14.0+cu130` with CUDA available, transformers is `5.17.0`, and accelerate is `1.15.0`.
- `nvidia-smi` reported four NVIDIA RTX A6000 devices with about 48 GB free each and no compute process at the preflight and smoke checks. The bounded run used one idle GPU; no process was stopped.
- LongVideoBench was found under `<LVB_ROOT>`. Its `lvb_val.json` contains 1,337 validation entries and `videos/` exists. The selected short sample was question `GZFL58_pXPg_0`, relative locator `GZFL58_pXPg.mp4`, annotation duration 7.97 seconds and probed video duration 8.006672 seconds. The annotation-referenced video exists. The adapter passes question and choices to inference but does not include `correct_choice` in `QuestionSample`.
- `Qwen/Qwen3-VL-4B-Instruct` has a complete local snapshot in `<MODEL_CACHE>` (about 8.3 GB); model shards, index, processor, and tokenizer files resolve locally. `AutoProcessor.from_pretrained(..., local_files_only=True)` succeeded. The real run used Hugging Face offline flags, so it did not download model files or Dataset data.

### Real Qwen smoke result

- Command used a temporary config derived from `configs/default.yaml`, with `window_seconds=8.1`, and `--question-id GZFL58_pXPg_0`. It preserved LongVideoBench, Qwen3-VL-4B-Instruct, Situation/Summary/Answer, `target_only`, `video_clip`, and built-in prompts. Output was under `<TMP_OUTPUT>`; the temporary config was not committed.
- The real video decoded and one window completed. Situation and Summary were non-empty, and both recorded `model_info` with adapter `qwen3_vl` and model ID `Qwen/Qwen3-VL-4B-Instruct`.
- Run `20261008T035005Z-e9132d92` ended with status `failed`, `artifact_schema_version=2`, and one line in `turns.jsonl`. `final_answer.json` has null answer/index/text and completed window count 0. No successful answer or matching choice was recorded.


```text
Stage: EOF Answer Agent (Qwen3-VL)
Command / operation: one offline `workbench.sh run` using `<TMP_CONFIG>`, `<LVB_ROOT>`, and question `GZFL58_pXPg_0`
Expected: real decode -> Situation -> Summary -> valid EOF Answer -> succeeded Record v2
Observed: real decode, Situation, and Summary succeeded; CLI exited 2 after Answer validation; run status is `failed` and final answer fields are null
Failure category: model output validation
Confirmed cause: `AnswerValidationError` reports that the generated answer did not satisfy the required `number. choice text` format. The rejected model text was not persisted, so its exact wording is unavailable.
Evidence: `run_status.json` records category `answer_validation_failed` and type `AnswerValidationError`; `turns.jsonl` contains one non-empty Situation/Summary window with Qwen model info; `final_answer.json` has null answer fields.
Action taken: inspected the Record and GPU state; did not retry the real GPU run or change the built-in prompt/production answer contract.
Remaining blocker: Qwen's EOF output did not pass deterministic choice-format validation.
Retry condition: a separately authorized bounded smoke after deciding how to address the observed output-format failure.
```

No model/Dataset download, full evaluation, multi-question benchmark, training, long-duration performance run, remote push, PR, or main merge was performed.
