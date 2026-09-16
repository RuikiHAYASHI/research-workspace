---
date: 2026-09-16
topic: egocross-agent-text-state-design
status: exploratory
project: agentic-streaming-videoqa
source: 2026-09-16-continuity-agent-text-state-correction.md
---

# Agentらしさを持つtext stateの残し方

## 結論

全frameのcaptionを連結するのではなく、**場面要約・イベント台帳・次回確認リスト・不確実性**の4区画を持つ構造化text stateを推奨する。Agentはこのstateを読み、`ADD`、`UPDATE`、`KEEP`、`FLAG_UNCERTAIN`、`CLOSE_EVENT`のいずれかを選んで更新する。

これにより、過去画像を再入力せずに、前時刻までに何が確定したか、何が進行中か、次に何を確かめるかをcurrent frameの解釈へ引き継げる。

## 初期schema案

```json
{
  "scene_summary": [
    "現在の場面で安定して成立している事実"
  ],
  "event_ledger": [
    {
      "event_id": "e1",
      "claim": "対象への接近が始まった",
      "status": "open | confirmed | rejected",
      "first_frame": 3,
      "last_evidence_frame": 4,
      "evidence": "frame 4で対象との距離が縮まった"
    }
  ],
  "watch_next": [
    {
      "event_id": "e1",
      "question": "次frameで接触または把持が成立したか確認する"
    }
  ],
  "uncertainties": [
    "遮蔽のため対象物の種類は未確定"
  ]
}
```

`scene_summary`は安定した現状だけを短く保持する。`event_ledger`は変化のある出来事をID付きで追跡し、同一の出来事を次frameで更新できるようにする。`watch_next`は次のcurrent frameをどう解釈するかを決めるAgentの能動的な出力である。`uncertainties`は曖昧な推測を確定事実へ混ぜないために分離する。

## frameごとの更新

1. Observation VLMは`question + options + current frame`だけから観測文を生成する。
2. Policy VLMは`state_{t-1} + observation_t`をtextとして読み、actionを一つ選ぶ。
3. Deterministic reducerはaction schemaを検証し、stateを更新する。
4. traceにはobservation、state before、action、reason、state afterを保存する。

`KEEP`は変化がないframeでstateを膨らませない。`ADD`は新しいeventまたは仮説を追加する。`UPDATE`は既存eventの根拠や場面要約を更新する。`FLAG_UNCERTAIN`は判断不能な内容を不確実性へ隔離する。`CLOSE_EVENT`はwatch対象をconfirmedまたはrejectedとして閉じる。

## 初期のサイズ制約候補

- `scene_summary`: 最大3項目
- `event_ledger`: open eventを最大5件
- `watch_next`: 最大2件
- `uncertainties`: 最大2件
- closed event: event logには残すが、policy入力には直近要約だけを渡す

この上限は初期の実装上の候補であり、最終値はID 1の短い実Qwen runでstateの長さと更新品質を確認してからspecで固定する。

## 代替案と判断

全frame captionの連結は実装が単純だが、同じ内容を繰り返して長くなり、どの情報が未確定かが分からない。1本の自由形式summaryは短いが、Agent actionの対象を特定しにくい。イベント台帳とwatch listを分ける方式は、stateが増える理由とAgentの判断をtraceで検証できるため、今回の最初のAgent実装に向く。
