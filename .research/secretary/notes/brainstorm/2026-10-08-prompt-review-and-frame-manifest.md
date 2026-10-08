---
date: 2026-10-08
project: agentic-streaming-videoqa
source_todo: null
topic: prompt-review-and-frame-manifest
status: exploratory
tags: [brainstorm, prompt, situation, summary, answer, frame-manifest]
---

# Prompt壁打ちとframe_manifest整理

## 出発点

実験開始前に、Situation / Summary / AnswerのPromptが現在の研究目的に合っているか、max_new_tokensの根拠、Prompt Library上の表示名の不統一を確認する。

本メモはPrompt品質の探索記録であり、実装specではない。

## 現在の方向性

- Situationは、現在程度の情報量を維持する。
- Situationを極端に短くして観測情報を捨てない。
- 代わりに「映像から直接支持されない事実を追加しない」を強化する。
- Summaryはprevious summaryとcurrent situationに存在しない事実を追加しないことを明記する。
- Answerはfinal summaryだけを根拠にし、既存の厳格な選択肢出力形式を維持する。
- 3 Agentに共通して「与えられた入力を越えた事実を作らない」という一貫した境界を持たせる。
- Prompt titleは日本語で統一する案が有力だが、最終確定は未実施。

## Situation Prompt 現在案

```text
Original video window: [{{chunk.start}}, {{chunk.end}}) seconds.
The clip timeline starts at 0 seconds and uses the target sample rate. Source-video frame IDs and actual absolute timestamps are authoritative.
Frame manifest:
{{chunk.frame_manifest}}

Describe the visible people, objects, actions, and meaningful state changes across the clip in chronological order.
Do not add facts that are not directly supported by the visible clip.
Do not infer unseen frames or future events, and do not answer any question.
Return only a concise plain text description.
```

### 意図

| 行 | 意図 |
|---|---|
| Original video window... | 現在clipが元動画のどの時間区間かを示す |
| clip timeline starts at 0... | clip内部時刻と元動画絶対時刻を混同させない |
| frame IDs / timestamps are authoritative | 時刻をQwenに推測させずコード側metadataを正本にする |
| Frame manifest | 入力frameと元動画上の対応を明示する |
| Describe visible people... | Situationの本体。人物・物体・動作・状態変化を時系列で記述する |
| Do not add facts... | 映像から直接支持されない意図・理由・出来事等を追加させない |
| Do not infer unseen frames or future events | 未観測・未来情報を推測させない |
| do not answer any question | QAではなく純粋な観測Agentに限定する |
| concise plain text | JSON等を避け、後段へ渡せる簡潔な自然文にする |

Situation出力の情報量は、例えば次程度なら許容範囲とする。

```text
The video starts with a woman holding a phone with a starry screen, showing the time as 11:43. She then lowers the phone and begins speaking, gesturing with her hand. The scene transitions to a black screen with the text "moving on" displayed in white.
```

ただし、"begins speaking" 等が視覚だけでは断定できない場合は、観測以上の断定を避ける必要がある。

## Summary Prompt 現在案

```text
Update the running summary of the video.

Previous summary:
{{previous.summary}}

Situation in the current window:
{{situation.description}}

Merge these in chronological order.
Preserve important facts and changes.
Do not add facts that are not present in the previous summary or the current situation.
Do not answer any question.
Return only the updated summary as plain text.
```

### 意図

| 行 | 意図 |
|---|---|
| Update the running summary... | 新規要約ではなく累積Summary更新であることを示す |
| Previous summary | 過去までの記憶を渡す |
| Situation in current window | 新しく追加する観測を渡す |
| Merge in chronological order | 時系列を維持する |
| Preserve important facts and changes | 過去の重要情報・状態変化を不用意に落とさない |
| Do not add facts... | previous/current inputに存在しない補完・創作を禁止する |
| Do not answer any question | QA最適化を避け、Summaryを質問非依存に保つ |
| updated summary as plain text | 更新済みsummaryだけを後段へ渡す |

未解決点は "important" の定義。QuestionをSummaryへ渡していないため、重要度はモデル自身が判断する。この曖昧さが長尺動画での情報消失・誤上書きにどう影響するかは実験で観察対象とする。

## Answer Prompt 現在案

現時点では本文変更を急がず、既存Promptを維持する案。

```text
Question: {{question}}
Choices:
{{choices}}

Summary through the end of the video:
{{summary}}

Answer only after end-of-video has been reached.
Compare the choices using only the final summary, not imagined content.
Return only `<1-based choice number>. <exact choice text>` as plain text.
```

### 意図

| 行 | 意図 |
|---|---|
| Question / Choices | multiple-choice QAの入力 |
| Summary through end... | 映像を直接再参照せず最終Summaryだけを根拠にする |
| Answer only after EOF | Early Answerを禁止する |
| using only final summary | Final Summary外の情報を使わない |
| not imagined content | Summaryにない内容を想像しない |
| exact output format | Pythonで決定的にparse・validation・正誤判定できるようにする |

## 3 Agent共通の一貫した境界

```text
Situation:
  visible clipにない事実を作らない

Summary:
  previous summary / current situationにない事実を作らない

Answer:
  final summaryにない事実を想像して使わない
```

この一貫性をPrompt設計上の有力方針とする。

## frame_manifest

現行video_clip経路では、各採用frameについて以下をPromptへ渡す。

| field | 意味 |
|---|---|
| video_ordinal | Qwenへ渡されたclip内でのframe順序。0,1,2,... |
| frame_index | 元動画における実frame番号 |
| timestamp_seconds | 実際に採用されたframeの元動画上の時刻 |
| target_timestamp_seconds | sampling policyが狙った目標時刻 |

例:

```json
[
  {
    "video_ordinal": 0,
    "frame_index": 500,
    "timestamp_seconds": 20.0,
    "target_timestamp_seconds": 20.0
  },
  {
    "video_ordinal": 1,
    "frame_index": 513,
    "timestamp_seconds": 20.52,
    "target_timestamp_seconds": 20.5
  }
]
```

`target_timestamp_seconds` は「ここを見たかった時刻」、`timestamp_seconds` は「実際に採用したframeの時刻」。

frame_manifestの目的は、Qwenに元動画上の時間位置やframe対応を推測させず、コードで決めたmetadataを正本として渡すこと。

## Situationの情報量について

現在例程度の3文前後は「簡潔」の範囲として許容する方向。

Situationは映像から得た観測をSummaryへ渡す唯一の段階なので、極端に短くすると後段で復元できない。

したがって削る対象は「観測情報」ではなく、冗長表現・推測・入力にない補完。

## Prompt title統一案

現時点の有力候補:

| role | title |
|---|---|
| Situation | 状況理解：初期プロンプト |
| Summary | 要約：初期プロンプト |
| Answer | 最終回答：初期プロンプト |

内部prompt_id（situation.video.initial / summary.video.initial / answer.video.initial）は変更不要。

## max_new_tokens

現行値:

- Situation: 1024
- Summary: 768
- Answer: 384

Company / GitHub上では、この具体値に研究上の根拠や比較Evidenceは確認できていない。

現時点では暫定値として扱い、Prompt本文確定後に別途壁打ちする。

特にSummaryのmax_new_tokensは累積Summaryの実質的な容量制約に近く、長尺実験へ影響する研究パラメータになり得る。

## 未決事項

- Summaryの "important facts" をどこまで明示的に定義するか。
- Situationで視覚的に確証できない動作を "appears to..." 等へ弱める指示を入れるか。
- max_new_tokensを3 Agentでどう設定するか。
- Prompt title / descriptionの最終文言。
- image_list版Promptも同じ意味へ揃えるか。



## 2026-10-08 23:30 JST spec引き継ぎ

この壁打ち内容を、current defaultの `video_clip` built-in Promptに限定した実装draft specへ昇格した。

- spec: `.research/lab/projects/agentic-streaming-videoqa/specs/2026-10-08-workbench-prompt-grounding-and-title-unification-spec.md`
- status: `draft`
- scope: Situation / Summary Prompt本文、video built-in 3 Agentのtitle、関連test
- 維持: Answer本文、frame_manifest、sampling、max_new_tokens、Prompt ID / schema
- 実Qwen / GPU / 長時間run: 対象外

ユーザー承認後に `approved` へ移行し、engineering-taskへ引き継ぐ。
