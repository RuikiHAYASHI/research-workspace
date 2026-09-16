---
date: 2026-09-16
topic: egocross-continuity-hypothesis-agent
status: exploratory
project: agentic-streaming-videoqa
---

# 前フレーム比較による Continuity Hypothesis Agent

## 問い

各フレームを独立に説明するだけのVLM観察器から、過去を参照して出来事の連続性を追うAgentへ、低い実装負荷で発展させられるか。

## 提案

基本の観察器が完成した後、Step 5を **Continuity Hypothesis Agent** とする。
各時刻で直前フレーム1枚と構造化された短期状態を保持し、VLMが現在フレームとの変化を比較する。同時に、次フレームで確認すべき具体的な仮説 `watch_next` を1〜2件だけ生成する。

```text
I[t-1], state[t-1] -- VLM --> I[t], change / event / watch_next --> state[t]
```

`state[t]` には、場面の要約、確定したevent log、未確定の仮説、次に確認する対象を含める。t=0では現在フレームだけを入力し、t>=1では前フレームと現在フレームの二画像を入力する。未来フレームは一切使わず、画像メモリも直前の1枚で一定とする。

## VLMの出力契約案

```json
{
  "observation": "現在フレームの観察",
  "change": {
    "new": [],
    "disappeared": [],
    "moved_or_changed": [],
    "unchanged": []
  },
  "action": "ADD | UPDATE | KEEP | FLAG_UNCERTAIN | CLOSE_EVENT",
  "event": "確定した出来事、または null",
  "resolved_watch": [],
  "open_hypotheses": [],
  "watch_next": [],
  "confidence": "low | medium | high"
}
```

例えば器具が対象に近付く場面では、最初のフレームで「把持する可能性」を仮説として置き、次フレームで実際に把持したかを確認する。変化がなければ `KEEP` を返すため、全フレームの類似したcaptionを積み上げず、意味のある変化だけをevent logに残せる。

## Agentとしての意味

Agentの行動は、フレームを選ぶことではなく、次に何を確認するかを決めることである。前時刻の `watch_next` が次時刻のVLMの比較観点を決め、結果が状態と次の仮説を更新する。JSONLに入力状態、action、根拠、更新後状態を残せば、判断の軌跡を検証できる。

ただし、これは入力や計算資源を能動的に制御しない「状態管理・仮説追跡Agent」である。フレームskip、追加観察、可変chunkなどをactionとして選ぶ能動的なAgentは、観察器と本案の検証後に別段階で扱う。

## 計画への位置付け

Step 4のQwenによるフレーム観察が実データで安定してから、既存のStep 5 Agent/Memory Controllerをこの案で具体化する。Step 4より前に入れると、画像読込・モデル呼出し・状態更新の失敗原因を切り分けられないためである。

Step 5のmicro Step候補:

1. `feat: add continuity agent state` — `watch_next` と状態schemaを定義する。
2. `feat: add adjacent-frame comparison prompt` — t=0は一画像、t>=1は前後二画像のVLM入力を実装する。
3. `feat: add hypothesis and event reducer` — actionに従い仮説とevent logを更新する。
4. `feat: append continuity trace` — 各時刻の入力状態、判断、出力状態をJSONLへ記録する。
5. `test: cover causal continuity loop` — Fake VLMで未来画像を渡さないこと、直前の`watch_next`を渡すこと、画像メモリが一枚で一定なことを確認する。

Qwenの実データsmokeは、1フレームのID 224ではなく、まず5フレームのID 1で前後比較を確認する。その後、既存の40件の定性seedでカテゴリ間の挙動を確認する。

## 判断

本案は「各フレームの説明」に留まらず、前フレームとの視覚的差分と前回の予測を用いて出来事を追う。追加モデル、学習、動画デコーダ、将来フレームを必要とせず、Qwen3-VLの複数画像入力と構造化出力だけで段階的に実装できるため、最初のAgent化として採用候補にする。
