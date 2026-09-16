---
date: 2026-09-16
project: agentic-streaming-videoqa
repository: /mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation
branch: feat/step-07-agent-reproducibility
head: 061fae5
status: completed-short-smoke
---

# EgoCross text-state Agent 短時間実行ログ

## 実装対象

Qwen3-VLで現在画像だけを観測し、前frameまでのbounded text stateと観測文だけで次の状態更新を決める最小Agentを実装した。過去raw画像、画像embedding、future frame、最終QAは入力に含めない。

## 実装した経路

```text
current image -> Qwen3-VL observation
previous text state + observation -> Qwen3-VL text-only policy
validated JSON decision -> deterministic reducer -> next text state
```

stateは`scene_summary`、open event、`watch_next`、`uncertainties`で構成する。actionは`ADD`、`UPDATE`、`KEEP`、`FLAG_UNCERTAIN`、`CLOSE_EVENT`で、各frameのstate前後、policy生出力、parse済みdecision、処理時間を`frames.jsonl`に残す。

## 検証

- unit / CLI / fake model integration: `python3 -m pytest -q`で31件成功。
- 実Qwen 1 frame:
  ```bash
  CUDA_VISIBLE_DEVICES=2 .venv/bin/python scripts/observe_egocross.py --record-id 224 --max-frames 1 --agent --max-new-tokens 256 --output-root /tmp/egocross-qwen-agent-smoke
  ```
  Qwenは`FLAG_UNCERTAIN`を返し、空stateからuncertaintyを一件追加した。
- 実Qwen 5 frame:
  ```bash
  CUDA_VISIBLE_DEVICES=2 .venv/bin/python scripts/observe_egocross.py --record-id 1 --max-frames 5 --agent --max-new-tokens 256 --output-root /tmp/egocross-qwen-agent-smoke
  ```
  `frames.jsonl`は5行で、全行の`error`はnullだった。actionはframe 0が`ADD`、frame 1〜4が`UPDATE`だった。`run_metadata.json`にはmanifest SHA-256、record、sampling、model revision、package version、code revision、CLI引数、state/prompt versionを保存した。

## 制約

この結果は実装経路の短時間動作確認であり、Agentの有効性やQA性能を示す評価ではない。final QA、accuracy、全957件の実行、長時間GPU jobは行っていない。GPUの物理番号はsourceやartifactに固定せず、上記の実行commandでのみ指定した。
