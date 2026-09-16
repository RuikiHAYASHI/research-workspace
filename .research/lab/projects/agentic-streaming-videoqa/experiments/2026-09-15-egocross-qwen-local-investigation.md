---
date: 2026-09-15
project: agentic-streaming-videoqa
type: local-code-data-investigation
---

# EgoCrossとQwenのローカル調査

2026-09-15 JSTに `/mnt/HDD18TB/hayashi/` のファイル・JSON・コードを確認。以下はローカル版の調査結果。モデルロード・推論・学習は未実行。

## 所在

パスは `/mnt/HDD18TB/hayashi/` を基準とする。

| パス | 役割 |
|---|---|
| `data/EgoCross/` | 評価画像列、support set、時刻表示付き派生データ |
| `2026_03_hayashi_minipro/qwen3-VL-4B.py` | 3画像と質問を渡す短いQwen呼び出し例 |
| `2026_04_hayashi_LLaMA-Factory/infer_zeroshot.py` | EgoCross評価推論、任意LoRAマージ、提出JSON生成 |
| 同上 `infer_dynamic_icl.py` / `infer_domain_lora.py` | Few-shot / ドメインLoRA推論 |
| 同上 `configs/lora.yaml` | EgoCross学習設定 |
| `2026_09_hayashi_streaming_video_qa/` | 50Salads逐次読み出しsmoke。READMEではモデル・質問・memory未実装 |
| `sequential_loader/` | 逐次動画ローダー |

## データ実査

### 評価用

`data/EgoCross/egocross_testbed/egocross_testbed_imgs.json`

- 957問。画像参照・ユニークパスとも10,748件、1問1〜91枚。
- 全参照パスの存在を検証し欠損0。画像全件のデコード検証は未実施。
- 実体はJPEG 10,484枚、PNG 264枚。JPEG固定で扱わない。
- ドメイン別: CholecTrack20 183、EgoPet 183、EgoSurgery 100、ENIGMA 245、ExtrameSportFPV 246。
- カテゴリ別: Counting 114、Localization 284、Identification 398、Prediction 161。
- 実キー: `id`, `dataset`, `primary_category`, `question_type`, `question_text`, `options`, `original_video_fps`, `video_path`。
- **正解ラベルはない。** README記載のquestion_id・correct_option_letter・answer_text・detailed_answerは実JSONに存在せず、このJSONだけでは正解率を計算できない。
- LLaMA-Factory直下の同名JSONは、パース後の内容が一致。

`video_path` は動画でなく画像パスのリスト。`/egocross_testbed/...` を `/mnt/HDD18TB/hayashi/data/EgoCross/egocross_testbed/...` へ解決する。

READMEによる抽出頻度は通常0.5 FPS、CholecTrack20のVID25・VID111とEgoSurgeryは1 FPS。`original_video_fps` は元動画FPSであり、抽出画像間隔として使わない。標準JSONには各画像の明示timestampがなく、画像連番だけで元動画絶対時刻は確定できない。

### Support set

`data/EgoCross/EgoCross_support_set/train.json` は80問、animal / industry / xsports / surgery各20問。ドメイン別train JSONも存在。

- ShareGPT形式: `messages`（userの画像プレースホルダ・質問・選択肢とassistantの正解記号）、`images`（support setからの相対パス）、`domain`。
- 画像参照1,390件、ユニーク1,359枚、欠損0。実体も1,359枚（JPEG 792、PNG 567）。**READMEの1,259枚とは不一致。**
- domain別参照/ユニーク: animal 175/175、industry 348/317、xsports 200/200、surgery 667/667。
- dataset_info.jsonにLLaMA-Factory用のShareGPT定義がある。

### 時刻付き派生版

`egocross_testbed_time/egopet_itl_time_overlay.json` はEgoPetのinteraction temporal localization 66問、画像2,337枚。`time_overlay`, `sampled_fps: 0.5`, `timestamp_rule: sec = frame_index * 2.0` を持つ。先頭例のanswerは空欄。`/egocross_testbed_time/` をデータルートへ解決すると画像欠損0。標準版だけを置換する旧推論コードでは、この派生版のパスには対応しない。

## Qwen呼び出し

外部チャットAPIではなく、ModelScope経由でモデルをロードしてローカルでgenerateする。

### 最小例: minipro/qwen3-VL-4B.py

1. ModelScopeからQwen3VLForConditionalGeneration、AutoProcessorをimport。
2. `Qwen/Qwen3-VL-4B-Instruct` をfloat32、device_map autoでロード。
3. 同じIDのprocessorをロード。
4. messagesのuser contentに `{"type":"image","image":画像パス}` を複数置き、textに質問を置く。
5. apply_chat_templateをtokenize=True、add_generation_prompt=True、return_dict=True、return_tensors=ptで呼ぶ。
6. inputsをmodel.deviceへ移し、generate(max_new_tokens=128)。
7. 出力IDから入力ID長を除き、batch_decode(skip_special_tokens=True)。

### 実験用: LLaMA-Factory/infer_zeroshot.py

- load_model_and_processor: bfloat16、SDPA、device_map auto、eval。任意LoRAをPEFTでロードしてmerge_and_unload。
- infer_one: 1問の全画像をJSON順にPILでRGBロードし、画像プレースホルダと質問・選択肢をmessagesへ入れる。
- apply_chat_template(tokenize=False)の後、processor(text=[prompt], images=[images_list], padding=True, return_tensors=pt, min_pixels=..., max_pixels=...)。
- no_grad内でgenerate: max_new_tokens=16、do_sample=False、use_cache=True、temperature/top_p/top_k=None。
- 入力token分を除いてdecodeし、A〜Dへ正規化。

コードから整理したCLI例（未実行。対応依存環境とGPUが必要。957問全体を処理）:

```bash
cd /mnt/HDD18TB/hayashi/2026_04_hayashi_LLaMA-Factory
python infer_zeroshot.py \
  --model_path Qwen/Qwen3-VL-4B-Instruct \
  --gpu_id 0 \
  --min_pixels 3136 \
  --max_pixels 50176
```

任意で--lora_pathを指定できる。既定model_pathは `./output/egocross_lora_merged_final_test`。zeroshotという名前でもデフォルトが未学習ベースモデルとは限らない。入力JSONとsubmission_templateはコード内固定、出力はsubmissions/zeroshot/。

## 設定と環境

- configs/lora.yaml: egocross_train、qwen3_vl_nothink、rank64、alpha128、dropout0.05、cutoff_len32768、image_max_pixels128000、bf16。epochsの実値は6で、「2回」というコメントと不一致。
- examples/train_lora/qwen3vl_lora_sft.yamlはデモデータ指定でEgoCross用ではない。
- miniproの.venvのdist-info: torch2.11.0、transformers5.5.0、modelscope1.35.3、accelerate1.13.0。importとGPU動作は未確認。
- LLaMA-Factoryのpyprojectはtransformers>=4.55.0,<=5.2.0,!=4.52.0,!=4.57.0。minipro環境との共用可否は未確認。
- output/egocross_lora_merged_final_test/config.jsonとoutput/egocross_lora_merged_epoch5/config.jsonが存在。重みの完全性とロード可否は未検証。

## Streaming研究へ持ち込む際の論点

以下はコード読解からの整理で、実験結果ではない。

- 旧コードは1問の全画像を一括入力する。future frame遮断や呼び出し間のtext memory更新はない。
- use_cache=Trueは生成中のキャッシュで、呼び出し間の永続memoryではない。
- 再利用する中心はロード、messages整形、generate、入力tokenを除くdecode。
- 既存研究参照メモではquery + current frame + metadata + previous text memoryへ入力を変え、Transformers経由を優先する方針。今回その変更は未実装・未検証。
- 画像列の逐次入力は構成できるが、元動画全体のstreaming評価とは観測範囲が異なる。フレーム時刻と観測範囲の定義が必要。
- normalize_answerの正規表現[A-D]は通常単語内の文字も拾い、未検出時はAにするため、不正出力が隠れる。
- 画像読込失敗やOOMをskipして進む。提出JSON生成だけで全問成功とは判断できない。

研究文脈はプロジェクトREADMEとreferences/2026-09-15-egocross-qwen-reference.mdを参照。既存referencesは編集していない。
