---
date: 2026-10-08
last_updated: 2026-10-08
project: agentic-streaming-videoqa
type: implementation
status: draft
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 59d4312dac242eba4eebace93c3f94a61979bc64
source_brainstorm:
  - 2026-10-08-prompt-review-and-frame-manifest.md
related_specs:
  - 2026-10-07-workbench-runtime-workflow-record-simplification-spec.md
  - 2026-09-30-workbench-prompt-service-crud-spec.md
---

# Workbench Prompt grounding / title統一 spec

## 1. 目的

実験開始前に、current defaultで利用する `video_clip` 向けSituation / Summary / Answer Promptを、現在の3-Agent責務に沿って明確化する。

今回の変更目的は次の2点。

1. Situation / Summary / Answerの各段階で、与えられた入力を越えた事実の補完・創作を抑える。
2. Prompt Library / Inference UIで表示されるbuilt-in初期Prompt名を3 Agentで同じ命名方式へ揃える。

Situationの情報量自体は現在程度を許容し、極端な短文化は行わない。削る対象は観測情報ではなく、入力から直接支持されない補完・推測である。

## 2. 現行実装とAuthority

基準:

- repository: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`
- branch: `main`
- commit: `59d4312dac242eba4eebace93c3f94a61979bc64`

現行default:

- `visual_input_mode: video_clip`
- Situation Prompt: `situation.video.initial`
- Summary Prompt: `summary.video.initial`
- Answer Prompt: `answer.video.initial`

現行3-Agent責務は2026-10-07 Runtime簡略化specを維持する。

- Situation: current windowだけを観測する。
- Summary: previous summaryとcurrent situationを統合する。
- Answer: EOFでQuestion / Choices / final summaryだけから回答する。

2026-10-02 MTGの「Promptが現在の役割に対して妥当かを壁打ちする」という決定と、2026-10-08 brainstormで整理したPrompt方針を今回の入力とする。

## 3. 採用する共通原則

3 Agentで、次の境界を一貫させる。

```text
Situation
  visible clipに直接支持されない事実を追加しない

Summary
  previous summary / current situationに存在しない事実を追加しない

Answer
  final summaryにない事実を想像して使わない
```

Situation / SummaryはQuestion / Choicesを受け取らない既存契約を維持する。

## 4. Situation Prompt

対象:

```text
prompts/situation/video/initial/prompt.en.txt
```

実装後の本文を次で固定する。

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

### 4.1 意図

| Prompt本文 | 意図 |
|---|---|
| `Original video window: [{{chunk.start}}, {{chunk.end}}) seconds.` | clipが元動画のどの時間区間かを伝える |
| `The clip timeline starts at 0 seconds and uses the target sample rate. Source-video frame IDs and actual absolute timestamps are authoritative.` | clip内部時刻と元動画絶対時刻を混同させず、コード側metadataを正本とする |
| `Frame manifest:` | 以下に各frameの対応情報があることを示す |
| `{{chunk.frame_manifest}}` | 実frame番号、実時刻、target時刻等を渡す |
| `Describe the visible people, objects, actions, and meaningful state changes across the clip in chronological order.` | 人物・物体・動作・状態変化を時系列で記述させる |
| `Do not add facts that are not directly supported by the visible clip.` | 映像から直接支持されない事実の追加を禁止する |
| `Do not infer unseen frames or future events, and do not answer any question.` | 未観測・未来を推測せず、QAを行わない |
| `Return only a concise plain text description.` | 観測情報を保ちつつ、冗長な形式やJSONを避ける |

「concise」は固定文数や固定token数を意味しない。現在確認した3文程度のSituation出力は許容範囲とし、観測事実を短文化のために落とす変更は要求しない。

## 5. Summary Prompt

対象:

```text
prompts/summary/video/initial/prompt.en.txt
```

実装後の本文を次で固定する。

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

### 5.1 意図

| Prompt本文 | 意図 |
|---|---|
| `Update the running summary of the video.` | 累積Summaryの更新役であることを示す |
| `Previous summary:` / `{{previous.summary}}` | 直前までの累積情報を渡す |
| `Situation in the current window:` / `{{situation.description}}` | current windowの新しい観測を渡す |
| `Merge these in chronological order.` | 過去から現在への順序を維持する |
| `Preserve important facts and changes.` | 重要な事実・状態変化を不用意に失わない |
| `Do not add facts that are not present in the previous summary or the current situation.` | 2つの入力にない事実の補完・創作を禁止する |
| `Do not answer any question.` | Question非依存のSummaryを維持する |
| `Return only the updated summary as plain text.` | 更新済みSummary本文だけを返す |

`important` の定義を今回のPromptで追加規定しない。QuestionをSummaryへ渡さない既存baselineを維持し、長尺実験で情報保持・情報消失を観察できる状態を残す。

## 6. Answer Prompt

対象:

```text
prompts/answer/video/initial/prompt.en.txt
```

本文は変更しない。

```text
Question: {{question}}
Choices:
{{choices}}

Summary through the end of the video:
{{summary}}

Answer only after end-of-video has been reached. Compare the choices using only the final summary, not imagined content. Return only `<1-based choice number>. <exact choice text>` as plain text.
```

既存の、

- EOF後に回答する。
- final summaryだけを利用する。
- imagined contentを利用しない。
- `<1-based choice number>. <exact choice text>` だけを返す。

という契約を維持する。

## 7. Prompt title統一

current defaultの3 built-in video Promptの `metadata.yaml::title` を次へ統一する。

| prompt_id | title |
|---|---|
| `situation.video.initial` | `状況理解：初期プロンプト` |
| `summary.video.initial` | `要約：初期プロンプト` |
| `answer.video.initial` | `最終回答：初期プロンプト` |

`prompt_id`、role、language、visual_input_mode、input_schema、output_schema、legacy_idsは変更しない。

descriptionは今回変更しない。

## 8. frame_manifest維持契約

`frame_manifest` の生成ロジックは変更しない。

現行 `video_clip` では各採用frameについて次を保持する。

| field | 意味 |
|---|---|
| `video_ordinal` | Qwenへ渡したclip内でのframe順序 |
| `frame_index` | 元動画の実frame番号 |
| `timestamp_seconds` | 実際に採用したframeの元動画上の時刻 |
| `target_timestamp_seconds` | sampling policyが狙った目標時刻 |

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

`target_timestamp_seconds` は「samplingで見たかった時刻」、`timestamp_seconds` は「実際に採用したframe時刻」。

今回の変更で `workflow/_common.py::frame_manifest()`、sampling policy、frame timestamp契約を変更しない。

## 9. max_new_tokens

今回変更しない。

current defaultを維持する。

| Agent | max_new_tokens |
|---|---:|
| Situation | 1024 |
| Summary | 768 |
| Answer | 384 |

この値の研究上の妥当性は別の壁打ち・spec対象とし、本specのPrompt変更と混ぜない。

## 10. 変更scope

実装対象:

- `prompts/situation/video/initial/prompt.en.txt`
- `prompts/summary/video/initial/prompt.en.txt`
- `prompts/situation/video/initial/metadata.yaml`
- `prompts/summary/video/initial/metadata.yaml`
- `prompts/answer/video/initial/metadata.yaml`
- 上記変更を保証する既存testの最小更新

第一候補test:

- `tests/test_prompt_service.py`
- `tests/test_prompt_api.py`

実装上、現在のtest構造により別の既存test更新が必要な場合は、要求を保証する最小差分に限定する。

## 11. 対象外

- `max_new_tokens` / temperatureの変更。
- Situation / Summary / AnswerのAgent class、Workflow、input/output schema変更。
- `frame_manifest` のfield・生成方法・時刻計算変更。
- sampling contract変更。
- Answer Prompt本文変更。
- `image_list` 用Prompt本文・metadata変更。
- PromptServiceのversioning / CRUD / storage設計変更。
- User Promptの変更・migration。
- Prompt日本語訳の生成・保存。
- 実Qwen / GPU / LongVideoBench長時間実験。

## 12. Compatibility / reproducibility

- canonical Configの `prompt_id` は変更しないため、Config interfaceは維持する。
- built-in Prompt本文変更により、新しいRunのSituation / Summary prompt hashは変わる。これは意図したscientific deltaである。
- Answer本文は変更しないため、Answer prompt body/hashは本文変更由来では変えない。
- metadata title変更は人間向け表示のみで、Prompt role/schemaを変えない。
- 過去Runは保存済みPrompt snapshot/body/hashを正本として閲覧できる既存契約を維持する。
- built-in PromptはGit commit + body hashで変更を追跡し、Prompt ID自体は維持する。

## 13. 実装手順

1. Situation / Summaryのbuilt-in video Prompt本文をSection 4 / 5のexact textへ更新する。
2. Situation / Summary / Answerのvideo Prompt titleをSection 7へ更新する。
3. PromptService / APIの既存testを更新し、title・Prompt semantic boundary・既存schema互換を確認する。
4. 必要なら、resolved Situation Promptにframe manifestの現行4 fieldが残ることを短いunit testで確認する。ただしframe_manifest実装自体は変更しない。
5. 関連test、compile/import check、`git diff --check` を実行する。

## 14. Success Criteria

1. `situation.video.initial` がSection 4の本文と一致する。
2. Situation Promptに `Do not add facts that are not directly supported by the visible clip.` が含まれる。
3. `summary.video.initial` がSection 5の本文と一致する。
4. Summary Promptに `Do not add facts that are not present in the previous summary or the current situation.` が含まれる。
5. Answer Prompt本文が変更されない。
6. video built-in 3 PromptのtitleがSection 7と一致する。
7. Situation / SummaryにQuestion / Choicesが追加されない。
8. role / visual_input_mode / input_schema / output_schema / prompt_idが変更されない。
9. `frame_manifest` の4 fieldと意味が維持される。
10. canonical `max_new_tokens=1024/768/384` が変更されない。
11. PromptService / Prompt APIの関連短時間testが成功する。
12. compile/import checkと`git diff --check`が成功する。
13. 実Qwen/GPU/長時間runを実装成功条件にしない。

## 15. Ambiguity Gate

### blocking

なし。

今回の要求はcurrent defaultの `video_clip` Promptに限定し、Prompt本文とtitleのexact textを本specで固定する。

### non-blocking

- test assertionの具体的な分割方法。
- Prompt本文の末尾newline等、PromptServiceの既存読込規則で意味が変わらないformat detail。
- frame_manifest維持を既存testの拡張で確認するか、専用の小さなunit testで確認するか。

## 16. Spec Gate

本specは2026-10-08のPrompt壁打ちを実装可能な契約へ変換した **draft** である。

blockingな未決事項はないが、現在の依頼は「specとCodex用プロンプトの作成」であり、コード実装そのものの明示許可ではないため、ユーザーが本specを明示承認するまで実装を開始しない。

承認後:

```text
draft -> approved
```

としてengineering-taskへ引き継ぐ。

## 17. Implementation Handoff

- approved spec: 承認後、本spec
- 実装目的: video built-in Situation / Summary Promptへ入力外事実を追加しない制約を追加し、Situation / Summary / Answerの表示titleを日本語の統一命名へ変更する。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `59d4312dac242eba4eebace93c3f94a61979bc64`。実装直前に最新mainとlocal worktreeを再確認する。
- 変更scope: Sections 4, 5, 7, 10, 13
- 対象外・維持条件: Sections 6, 8, 9, 11, 12
- success criteria: Section 14
- 許可される短時間検証: PromptService / Prompt API unit tests、必要なFakeまたはprompt resolution test、compile/import、diff check
- 長時間run: 未許可。実Qwen / GPU / LongVideoBench runを開始しない。
- 未検証予定: Prompt品質の実モデル評価、max_new_tokensの妥当性、長尺動画でのSummary保持性能
