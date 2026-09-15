---
date: 2026-09-15
project: agentic-streaming-videoqa
topic: egocross-qwen-reference
status: reference
---

# EgoCross時代のQwen3-VL実装の参照メモ

## 位置づけ

`tamaki-lab/2026_04_hayashi_LLaMA-Factory` は、現在のStreaming VideoQA実装へコードをそのまま移植する対象ではない。
EgoCross固有のデータ処理、全frame一括入力、MCQ回答正規化、LoRA、Dynamic ICL、submission生成などは現在研究のscope外とする。

現在研究では、旧実装を **Qwen3-VLのモデルロードと単発推論呼び出しの参考実装** としてのみ参照する。

## 主な参照箇所

### `infer_zeroshot.py`

1. `load_model_and_processor()`
   - `Qwen3VLForConditionalGeneration.from_pretrained(...)`
   - `AutoProcessor.from_pretrained(...)`
   - `dtype` / `device_map` / attention implementation
   - `.eval()`

2. `infer_one()` 内のVLM呼び出し
   - `messages` 構築
   - `processor.apply_chat_template(...)`
   - image + text のprocessor入力
   - `model.generate(...)`
   - 入力token分を除外したdecode
   - `processor.batch_decode(...)`

参照元:
- https://github.com/tamaki-lab/2026_04_hayashi_LLaMA-Factory/blob/main/infer_zeroshot.py

## 現在研究へ持ち込まないもの

- EgoCross dataset固有path変換
- 複数frameの一括ロード・一括VLM入力
- A/B/C/Dの回答正規化
- submission JSON生成
- epoch tag等のEgoCross実験管理
- LoRA / PEFT merge
- domain LoRA
- Dynamic ICL / support retrieval
- LLaMA-Factory本体のtraining infrastructure

## 現在研究での置き換え

旧実装はModelScope経由で `AutoProcessor` と `Qwen3VLForConditionalGeneration` をロードしているが、現在研究では可能な限り Hugging Face Transformers 経由を優先する。

Hugging Faceの現行TransformersドキュメントではQwen3-VLが直接サポートされており、例えば以下の形でロードできる。

```python
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

model = Qwen3VLForConditionalGeneration.from_pretrained(
    model_id,
    device_map="auto",
    attn_implementation="sdpa",
)
processor = AutoProcessor.from_pretrained(model_id)
```

公式参照:
- https://huggingface.co/docs/transformers/main/model_doc/qwen3_vl
- https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct

現在のStreaming Text Memory実装では、このロード・generate・decodeのパターンだけを参考にし、入力は

```text
query + current frame + frame metadata + previous text memory
```

に置き換える。

モデルID/pathはCLIから指定可能とし、特定checkpointを研究仕様へ固定しない。
