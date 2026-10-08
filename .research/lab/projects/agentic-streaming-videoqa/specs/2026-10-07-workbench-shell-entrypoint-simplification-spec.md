---
date: 2026-10-07
last_updated: 2026-10-08
project: agentic-streaming-videoqa
type: implementation
status: implemented
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 86947e3560f0ae644b3d164fcb3bbdf0caa936e5
source_brainstorm:
  - 2026-10-07-workbench-shell-entrypoints.md
---

# Workbench shell entrypoint simplification spec

## 1. 目的

Workbenchの通常起動、Qwen preflight、CLI run、Fake smokeの入口を単純化し、
machine固有のGPU番号やDataset pathをGit追跡対象から分離する。

現在の `scripts/verify-runtime-smoke.sh` はFake回帰テスト専用であるにもかかわらず、
`CUDA_VISIBLE_DEVICES=""` を固定し、`.venv` が無い場合にsystem Pythonへfallbackする。
またREADMEの通常起動手順は環境変数とlongvideoqa引数を毎回手入力する構成になっている。

## 2. 実装基準と戻し方

現在のmainは `86947e3560f0ae644b3d164fcb3bbdf0caa936e5`。
このcommitと親 `85bdda340e2609cc7c9525208c436b8b05ed6218` の差分は
`scripts/verify-runtime-smoke.sh` の追加だけである。

実装branchは現在mainから作成し、最初のmicro-commitでこのscriptを削除する。
これによりhistory rewriteを行わず、一度追加前のtree相当へ戻してから新構成を作り直す。

## 3. 採用構成

```text
.env                         # Git管理外。machine-local
.env.example                 # Git管理。設定例のみ
scripts/
├─ workbench.sh              # user-facingの唯一の入口
└─ verify-runtime-smoke.sh   # Fake回帰専用
```

`.gitignore` は既に `.env` を無視しているため、新しいignore規則は追加しない。

## 4. .env

tracked bash/YAMLへ物理GPU番号を固定しない。

machine固有値の候補:

- `LVB_ROOT`
- `CUDA_VISIBLE_DEVICES`
- `PORT`
- 必要な場合だけ `WORKBENCH_HOME`
- 必要な場合だけ `OUTPUT_ROOT`

`.env.example` は具体的な研究サーバGPU番号を既定値にせず、例またはcommentとして示す。

## 5. scripts/workbench.sh

責務:

- repository rootを解決してそこへ移動する。
- `.env` が存在する場合だけ読み込み、その値を子processへexportする。
- `.venv/bin/longvideoqa` を唯一のCLI入口として使う。
- `.venv` / CLIが存在しない場合はsystem Pythonへfallbackせず明示errorにする。
- XDG basedの `WORKBENCH_HOME` / `OUTPUT_ROOT` defaultを用意する。
- `serve`, `preflight`, `run`, `verify` をsubcommandとして提供する。
- 引数なしは `serve` とする。
- serverはforegroundで起動し、Ctrl+C終了という既存運用を維持する。

標準利用:

```bash
./scripts/workbench.sh
./scripts/workbench.sh serve
./scripts/workbench.sh preflight
./scripts/workbench.sh run
./scripts/workbench.sh verify
```

`run` のdefault configは `configs/default.yaml` とし、先頭のpositional argumentでconfig pathを差し替えられる。
追加のCLI optionは既存longvideoqa commandへ透過する。

## 6. scripts/verify-runtime-smoke.sh

Fake短時間回帰専用とする。

- `.venv/bin/python` を必須にする。
- system Pythonへfallbackしない。
- `CUDA_VISIBLE_DEVICES` を設定・上書きしない。
- `PYTHONPATH` を手動設定しない。
- `compileall` と既存Fake HTTP / CLI integration testを実行する。
- 実Qwen、実GPU、LongVideoBench実データ、model downloadは行わない。

## 7. README

通常起動の第一手順を `./scripts/workbench.sh` に変更する。

READMEで明示する:

- この利用環境では `.venv` は事前に構築される前提であり、launcherは環境構築を行わない。
- machine-local設定は `.env` に置く。
- `.env` はGit管理外。
- GPU変更は `.env` の `CUDA_VISIBLE_DEVICES` 変更で行う。
- Qwen preflight / run / verifyも同じdispatcherから実行する。
- foreground起動とCtrl+C終了を維持する。

詳細な既存機能説明は要求に関係する範囲だけ更新し、研究ロジックやartifact契約は変更しない。

## 8. 対象外

- Python runtime / Agent / Workflow / Recordの変更。
- canonical Config schemaの変更。
- Dataset format変更。
- Qwen model挙動変更。
- `.venv` 作成機構そのものの新規実装。
- 長時間run、実Qwen/GPU run。
- mainへのmerge、push、PR。

## 9. Success Criteria

1. 実装branchの最初の変更で旧verify script追加が打ち消されている。
2. `.env` は引き続きGit ignoreされ、具体的GPU番号をtracked fileの既定値にしない。
3. `scripts/workbench.sh` がexecutableで、serve/preflight/run/verifyを提供する。
4. `.venv` 不在時にsystem Pythonへfallbackしない。
5. `verify-runtime-smoke.sh` がCUDA設定を変更しない。
6. `verify-runtime-smoke.sh` がproject `.venv` のPythonのみを使う。
7. bash syntax checkが通る。
8. dispatcherの引数転送をFake executableで短時間確認できる。
9. READMEの通常操作が短いlauncher command中心になる。
10. 研究コード、config、artifact schemaは変更しない。

## 10. Git運用

- 現在mainから1本の実装branchを作る。
- branch名: `refactor/workbench-shell-entrypoints`
- micro-commitを意味単位で積む。
- commit messageは日本語のタイトル + 箇条書きでない本文5〜6行程度。
- mainへのmerge、remoteへの追加push、PRは行わない。


## 11. Implementation Status — 2026-10-07

実装branch:

```text
RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
refactor/workbench-shell-entrypoints
head: a080ea4169134bcb6f4f2cef179890b7cfaec2f5
```

実装済み:

- 旧 `verify-runtime-smoke.sh` 追加を最初のcommitで打ち消し、親tree相当から再構築した。
- `.env.example` と `scripts/workbench.sh` を追加した。
- `workbench.sh` は `serve / preflight / run / verify` を提供し、引数なしは `serve` とする。
- `.venv/bin/longvideoqa` / `.venv/bin/python` を必須とし、system Pythonへfallbackしない。
- `verify-runtime-smoke.sh` はCUDA設定とPYTHONPATHを変更せず、Fake回帰だけを実行する。
- READMEと `docs/development.md` をdispatcher / `.env` 中心の手順へ更新した。
- tracked文書・exampleへ具体的なGPU番号を既定値として固定しない。

短時間確認:

- `bash -n` で両shell scriptの構文を確認した。
- Fake `.venv/bin/longvideoqa` を用いたharnessで `.env` のCUDA値、serve/preflight/runの引数転送を確認した。
- `.venv` 不在時にfallbackせずexit 1となることを確認した。
- Fake Python harnessで `verify-runtime-smoke.sh` が外部の `CUDA_VISIBLE_DEVICES` を変更しないことを確認した。
- Git tree上で両scriptがmode `100755` であることを確認した。

未実施:

- research serverの実 `.venv` 上での `./scripts/workbench.sh verify`。
- 実Qwen/GPU/LongVideoBench run。

このため、コード実装は完了しているが、本specのstatusは `approved` のままとし、
research serverでFake smokeが成功した後に `implemented` へ更新する。

## Implementation Status Addendum — 2026-10-08

The launcher contract was reverified on the current implementation branch. The project-venv Fake verification passes; `workbench.sh` syntax, CLI availability, no-fallback behavior, and valid-root argument forwarding passed an isolated fake-CLI harness. Missing and invalid `LVB_ROOT` stop serve/run explicitly, while preflight and verify run without it. `.env.example` contains placeholders only, `.env` remains ignored, and README usage is synchronized. The shell entrypoint implementation and verification criteria are complete.
