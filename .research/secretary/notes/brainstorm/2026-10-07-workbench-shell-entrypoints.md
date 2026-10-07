---
date: 2026-10-07
project: agentic-streaming-videoqa
source_todo: null
topic: workbench-shell-entrypoints
status: exploratory
tags: [brainstorm, workbench, bash, runtime, cuda, environment]
---

# Workbenchのbash入口とローカル環境設定の整理

## 2026-10-07 時点の確認済み事実

GitHub上の `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` は `86947e3560f0ae644b3d164fcb3bbdf0caa936e5`。

現行 `scripts/verify-runtime-smoke.sh` は次を行う。

- repository rootを解決する。
- `.venv/bin/python` があれば使い、無ければsystem `python3`へfallbackする。
- `PYTHONPATH=src` を追加する。
- `CUDA_VISIBLE_DEVICES=""` をexportする。
- `compileall` を実行する。
- Fake HTTP / CLIのpytestだけを実行する。

したがって、このscriptは「Workbenchを通常利用できるか」の起動確認ではなく、Fake経路の短時間回帰検証である。

また、repositoryの `.gitignore` は既に `.env` を無視する。README上では現時点でも `.venv` の手動作成手順が記載されており、GitHub remote上では自動作成経路は直接確認できない。ユーザー報告では現在は `.venv` 自動構築を前提としている。

## 推奨方針

日常操作と検証を分離する。

ユーザーが通常触る入口は1本の `scripts/workbench.sh` に集約し、`serve / run / preflight / verify` のsubcommandを持たせる。

machine固有設定はrepository rootの `.env` に置き、Git追跡しない。

tracked側には必要なら `.env.example` だけを置き、具体的なGPU番号は固定しない。

### 推奨構成

```text
.
├─ .env                       # Git ignore。machine固有値
├─ .env.example               # 任意。tracked。変数名だけ示す
└─ scripts/
   ├─ workbench.sh             # 日常利用の唯一の入口
   └─ verify-runtime-smoke.sh  # Fake回帰専用。内部/開発用
```

初期段階では `scripts/lib/common.sh` 等へ分けない。workbench.shが肥大化した場合だけ後から分離する。

## .envの責務

候補:

```bash
LVB_ROOT=/mnt/.../LongVideoBench
CUDA_VISIBLE_DEVICES=3
PORT=8765
```

`WORKBENCH_HOME` と `OUTPUT_ROOT` はXDG defaultで十分ならbash側でdefaultを計算し、.envでは通常省略する。

GPUを変える場合はtracked fileを変更せず `.env` の `CUDA_VISIBLE_DEVICES` だけ変更する。

## workbench.shの責務

- repository rootへ移動。
- `.env` があればload。
- `.venv/bin/longvideoqa` と `.venv/bin/python` を使用。
- `.venv` が無い場合はsystem Pythonへfallbackせず、setup未完了として明示errorにする。
- XDG basedのWORKBENCH_HOME / OUTPUT_ROOT defaultを設定。
- `serve`: Browser serverをforeground起動。
- `preflight`: Qwen/CUDA確認。
- `run`: ConfigによるCLI run。
- `verify`: Fake smokeへ委譲。

通常コマンドを次まで短縮することを目標とする。

```bash
./scripts/workbench.sh serve
./scripts/workbench.sh preflight
./scripts/workbench.sh run
./scripts/workbench.sh verify
```

## verify-runtime-smoke.shの位置付け

このscriptは通常起動確認ではなく回帰test専用にする。

- CUDA/GPU設定を責務にしない。
- Qwenを起動しない。
- LongVideoBench実データを要求しない。
- compileall + Fake pytestを行う。
- system Python fallbackは廃止し、必ずproject `.venv` を使う。

実際にUIが立ち上がることを確認したい場合は `workbench.sh serve` を使う。実Qwen readinessは `workbench.sh preflight`、実Agent runは `workbench.sh run` と分離する。

## 推奨しない構成

`serve.sh / run.sh / qwen.sh / setup.sh / env.sh / verify.sh / common.sh` のように入口を細かく増やすことは現段階では避ける。利用者が1人であり、目的が実行コマンドの単純化なので、user-facing入口は1本のdispatcherの方が追いやすい。

また、tracked YAMLやtracked bashへ物理GPU番号を固定しない。

## 次アクション候補

この方針を採用する場合、現在の起動・検証運用だけを対象とする小さなimplementation specへ落とし込み、

- `.env` local config
- `scripts/workbench.sh`
- `verify-runtime-smoke.sh` の役割整理
- READMEの通常起動手順短縮

をまとめて変更するのが適切。


## 2026-10-07 ユーザー指示による運用修正

ユーザーが求める「動作確認」は、Fake test、compile、Qwen preflightではなく、
**実Qwen3-VLを用いて対象動画を最初からEOFまで処理し、3Agent経路を通ってFinal Answerが生成されることの確認**を指す。

したがって今後のユーザー向け標準手順では次を優先する。

- Qwen3-VLを必須とする。
- LongVideoBench実データを使う。
- Situation -> Summary -> Answerを最後まで実行する。
- EOF前に終了するpreflightやFake smokeを「動作確認」の主手順として案内しない。
- verify / preflight は必要なら内部開発用として残してもよいが、通常利用者向けの中心導線にはしない。
- CLIでの確認では、question_idを含む実Qwen recipeを使って1 QAをEOFまで通す。

現在確認済みの候補として、configs/recipes/p9h-target-only-10min-32frames.yaml は LongVideoBenchの
P9hDA0u6FO0_0 を対象に、Situation / Summary / Answerの全Agentで
Qwen/Qwen3-VL-4B-Instruct を使用し、最終回答まで実行する設定である。
