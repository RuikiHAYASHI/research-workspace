# LongVideoBench Qwen3-VL初回実行

## 目的

実装仕様のStep 10を検証したうえで、Step 11としてLongVideoBenchの初期対象1問をQwen3-VLで一回だけ実行し、実行記録とGPU選択を確認する。

## 実行環境

- 実行日: 2026-09-24
- repository: `/mnt/HDD18TB/hayashi/2026_09_hayashi_longvideoqa_workbench`
- branch: `feat/step-11-initial-qwen-run`
- code version: `7544cd869d4bb9a1d05e64c932922304210b0e02`
- Python環境: repository直下の`.venv`
- PyTorch: `2.14.0+cu130`
- torchvision: `0.29.0+cu130`
- transformers: `5.17.0`
- accelerate: `1.15.0`
- GPU指定: `CUDA_VISIBLE_DEVICES=2,3`
- 可視GPU: 論理GPU 0・1の2枚。いずれもNVIDIA RTX A6000で、物理GPU 2・3に対応する。

## Step 10末尾確認

次の確認にすべて成功した。

- `python -m pip check`: broken requirementなし。
- `CUDA_VISIBLE_DEVICES=2,3 longvideoqa qwen-preflight`: CUDA利用可能、可視GPU数2、論理GPU ID 0・1。
- `Qwen3VLForConditionalGeneration`のimport。
- テスト: 43件成功。
- `python -m compileall -q src tests`: 成功。
- モデルキャッシュを確認し、preflightではモデル読込みと推論を行っていない。

`requirements-vlm.txt`はコミット`7544cd8`として`origin/feat/step-10-qwen-preflight`へ反映済みである。

## Step 11実行設定

実行コマンド:

```bash
CUDA_VISIBLE_DEVICES=2,3 .venv/bin/longvideoqa run \
  --config configs/longvideobench-p9h.json \
  --data-root longvideobench=/mnt/HDD18TB/hayashi/data/LongVideoBench \
  --output-root outputs
```

保存済み初期設定を実行中に変更していない。

- dataset adapter: `longvideobench`
- question ID: `P9hDA0u6FO0_0`
- model adapter: `qwen3_vl`
- model ID: `Qwen/Qwen3-VL-4B-Instruct`
- chunk: 60秒、1区間4画像
- subtitles: 無効
- generation: `max_new_tokens=256`、`temperature=0.0`
- model placement: `device_map="auto"`、`dtype="auto"`

## 結果

- run ID: `20260924T024103Z-c7dbf3f0`
- 状態: `succeeded`
- 実行時刻: 2026-09-24 11:41:03 JSTから11:49:43 JST
- failure reason: なし（`error: null`）
- 処理範囲: 初期対象1問、34区間、69段階
- GPU: 実行中に物理GPU 2・3だけが使用されていることを確認した。再起動、fallback、手動上書きは行っていない。
- モデル重み: ローカルキャッシュから読み込んだ。実行時の取得表示は0 bytesだった。

出力先:

```text
/mnt/HDD18TB/hayashi/2026_09_hayashi_longvideoqa_workbench/outputs/20260924T024103Z-c7dbf3f0
```

次の成果物を確認した。

- `run_status.json`
- `execution_settings.json`
- `chunks.jsonl`
- `stages.jsonl`
- `final_answer.json`

最終出力は「選択肢のいずれも正しくない」と回答し、クレジット画面の構成を根拠として挙げた。このStepでは正解ラベルとの照合や正解率評価を行わない。

## 対象外

LongVideoBench全件評価、正解率評価、学習、設定比較、追加runは実施していない。`outputs/`はGit管理対象外であり、既存出力を変更していない。
