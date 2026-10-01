---
date: 2026-10-01
last_updated: 2026-10-01
project: agentic-streaming-videoqa
type: implementation
status: approved
sequence: 7
sequence_total: 7
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: b868f4431e69d783632476752d3f41311a52b53a
depends_on:
  - 2026-10-01-workbench-inference-settings-prompt-ux-spec.md
source_brainstorm:
  - 2026-10-01-workbench-cuda-preview-translation-inference-ui.md
---

# Workbench Stage 7: Chunk結果・Researcher View・生出力確認 spec

## 1. 目的

現行Run画面はturn/stage結果、採用frame、Memory表示を縦に積み上げており、逐次処理の各chunkで「何を見て、Situationが何を理解し、Memoryへ何が追加されたか」を追いにくい。また研究者がmodelの生出力・Prompt snapshot・validation後の出力を確認するには情報が分散している。

Stage 7では、研究アルゴリズム上のSituation/Memory/Answer stageは維持しつつ、**人間向け表示は1 chunk = 1 block**へまとめる。左右矢印でchunk履歴を移動し、EOF後のFinal Answerを最後のblockへ追加する。

さらに「詳細を見る」と「研究者表示」を用意し、累積Memory、model生出力、Prompt/入力、validated JSONを英語原文と日本語表示の両方で確認できるようにする。

## 2. 現行出力契約

現行Workbench mainでは:

### Situation Agent

video modeのvalidated outputは:

- `window_summary`
- `observations[]`
- `unresolved[]`

`window_summary`を通常表示の代表textとして使える。

### Memory Agent

validated outputは:

- `events[]`
- `narrative`
- `unresolved[]`

`narrative`はcurrent chunkだけではなく過去を統合した累積working memoryであり、通常blockへ毎回全文表示しない。current chunkで追加された`events[].description`を「Memory update」として通常表示し、累積`narrative`は詳細へ置く。

### Answer Agent

EOF後のみ実行する。現行設計ではearly answerをしないため、Final AnswerはEOF前には存在しない。

### Artifact

`stages.jsonl`にはstageごとに:

- resolved_prompt
- prompt ID/hash
- input_summary
- raw_output
- validated_output
- structured_output
- error
- elapsed_seconds
- model_info

を保存する。

Qwenの現行`raw_output`は少なくとも:

- `text`
- `generated_tokens`
- `hit_max_new_tokens`

を持つ。

`memory.jsonl`にはwindow observation、event、narrative version等、`memory.json`には最新narrative、token_count、token_budget、version等を保存する。

## 3. Chunk carousel

### 3.1 1 chunk = 1 block

BackendではSituation → Memoryの2 stageを維持するが、通常UIは同一chunkの2 stageを1つへまとめる。

例:

```text
←                 Chunk 3                 →

00:08 – 00:12

[ frame ][ frame ][ frame ][ frame ]

Situation
A person opens the refrigerator and takes out a bottle.
[ 日本語訳 ]

Memory update
The person took a bottle from the refrigerator.
[ 日本語訳 ]

Situation  1.2秒
Memory     0.8秒

[ Prompt ]  [ 詳細を見る ]
```

### 3.2 navigation

- block左上に前へ戻る矢印。
- block右上に次へ進む矢印。
- 1画面で主表示するblockは1つ。
- 初期は最新完了chunkを表示する。
- 新しいchunkのturnが正常完了したら最新chunkを表示対象にしてよい。
- 過去chunkへ移動中にpoll更新が入っても、無断で最新へ飛ばさない。ユーザーが最新を見ている場合のみ新しい最新へ追従してよい。
- disabledな端では矢印をdisabled表示する。
- browser reload後も保存済みRun artifactから同じchunk順で閲覧できる。

### 3.3 通常表示

Situation:
- validated `window_summary`
- 原文がcanonical。
- 「日本語訳 / 原文」切替。

Memory update:
- current chunkで追加されたvalidated `events[].description`。
- eventが複数なら短いlistとして表示する。
- eventが0件なら「このchunkで追加された記憶はありません」等、捏造しない表示。
- 「日本語訳 / 原文」切替。

採用frame:
- 現行thumbnailが利用可能なら時間順strip。
- thumbnailがserver再起動後利用不可ならartifact上のframe/timestamp情報を維持し、存在しない画像を捏造しない。

Timing:
- Situation elapsed
- Memory elapsed

通常表示ではraw JSON全文、Prompt全文、累積Memory全文を常時出さない。

## 4. Final Answer block

EOF後にAnswer Agentが完了した場合だけ、carouselの**最右端**へFinal Answer blockを追加する。

順序:

```text
Chunk 1 → Chunk 2 → ... → Chunk N → Final Answer
```

Final Answer block:

- selected answer
- evidence event/frame/timestampの人間向け表示
- Answer elapsed
- 原文/日本語訳
- Prompt
- 詳細

Final Answer生成前は空のFinal Answer placeholderを置かない。

`insufficient_evidence`等でAnswerが生成されない場合は、既存run statusを明示し、存在しない回答を作らない。

Final Answer生成後に専用別画面へ自動遷移する大改修はしない。Stage 7では同じcarousel内の最終blockとする。early answer導入時に表示契約を再検討する。

## 5. 「詳細を見る」

各chunk blockの「詳細を見る」はdrawer/modal等で開き、少なくとも次の4区分を提供する。

```text
[ Memory ] [ モデル生出力 ] [ Prompt・入力 ] [ JSON ]
```

### 5.1 Memory

このchunk処理完了時点のMemoryを人間向けに確認する。

表示:

- 累積`narrative`
- narrative version
- token_count / token_budget
- current chunkで追加されたevents
- eventのtime range/certainty/importance/evidence frame
- unresolved
- 必要ならchapters

日本語訳:

- narrative
- event description
- importance explanation
- unresolved

をStage 5のGoogle display translatorで表示可能にする。

原文は常に残し、日本語訳でartifactを上書きしない。

「現在」ではなく**選択chunk時点**のMemory versionを表示する。Chunk 3を見ているのにChunk Nの最新Memoryを誤表示しない。

### 5.2 モデル生出力

研究者がmodelの生成結果を加工前に確認できることを必須とする。

Situation / Memoryそれぞれについて:

- `raw_output.text`を「モデル生出力（原文）」として表示。
- raw textの「日本語訳」。
- copy button。
- generated_tokens。
- hit_max_new_tokens。
- validation success/error。
- validation errorがある場合はerror type/message。

Final Answer blockではAnswer Agentも同様。

重要:

- `validated_output`や`structured_output`を「生出力」と呼ばない。
- model raw textとvalidation後の値を明確に区別する。
- Answerはvalidation後にStageResult.outputが回答文字列へ変わり得るため、生出力の正本は`raw_output.text`とする。
- 翻訳結果は表示専用。JSON validationや研究artifactへ戻さない。

### 5.3 Prompt・入力

そのstageで実際に使用したrun snapshotを表示する。

Situation / Memoryごとに:

- Agent/model ID
- Prompt title/id/version/hash
- resolved Prompt本文
- Prompt原文/日本語訳
- generation max_new_tokens/temperature
- input_memory_version等のinput summary
- chunk start/end
- frame manifest / timestamp
- visual/context mode

表示対象は現在Prompt Libraryの最新版ではなく、`stages.jsonl` / `resolved_prompts.json`へ保存済みのrun snapshot。

### 5.4 JSON

研究/デバッグ用途としてmachine-facing情報を明示的に開ける。

- `structured_output`
- `validated_output`
- full `raw_output`
- `model_info`
- `input_summary`
- relevant artifact metadata

表示はread-only。通常blockへ常時出さない。

## 6. 研究者表示

結果領域にtoggle:

```text
[ ] 研究者表示
```

を置く。

### OFF

通常表示:

- frame strip
- Situation summary
- Memory update
- 日本語訳
- elapsed
- Prompt / 詳細導線

### ON

通常blockへ追加情報をcompact表示:

- Situation validation: OK / Error
- Memory validation: OK / Error
- Prompt version
- model ID
- generated token数
- max_new_tokens到達有無
- 「生出力」への直接導線

ONでもraw JSON全文をblockへ展開しない。情報量を増やしすぎず、詳細drawerへ素早く到達するためのresearch overlayとする。

toggleは表示設定でありrun条件ではない。Run artifact/settings hashへ含めない。session-local UI stateでよく、永続化は必須ではない。

## 7. Presentation boundary

Machine artifactをUI側で場当たり的に再解析せず、既存`PresentationService / RunProjection`へ必要なread-only projectionを追加する。

目標projection:

- turn/chunkごとのSituation/Memory stage
- window summary
- current-window events
- chunk完了時点のnarrative version
- token count/budget
- unresolved
- raw model text/metadata
- validation state
- prompt/input snapshot
- final answer

artifact formatの意味を変更せず、既存JSON/JSONLから決定的に生成することを優先する。

既存artifactだけで必要情報が存在する場合、新しい重複artifactを作らない。

## 8. Translation

Stage 5のGoogle display translatorを再利用する。

対象:

- Situation window_summary
- Memory current events
- Memory narrative
- unresolved/importance explanation
- model raw text
- Prompt
- Final Answer表示

原則:

- buttonで明示翻訳。
- cache hit時は外部APIを呼ばない。
- translation failureは該当翻訳だけerror表示し、Run閲覧を壊さない。
- 英語原文・artifact・validation inputを変更しない。
- API keyをbrowserへ返さない。

## 9. 対象外

- Situation/Memory Prompt schemaの変更。
- Memory algorithm/budget algorithmの変更。
- early answer/早押し。
- model reasoning chain-of-thoughtの取得や表示。表示するのはWorkbenchが実際に保存しているmodel response text/metadataのみ。
- 未保存のGPU内部state、attention、hidden stateの可視化。
- raw artifactの編集。
- Final Answer専用の別ページ。
- 実Qwen品質評価。

## 10. Compatibility

- Situation→Memory→EOF Answerの実行順序を維持。
- existing run artifactを閲覧可能。
- reload後のread-only履歴を維持。
- active sessionだけのframe thumbnailが再起動後に消える現契約を誤魔化さない。
- model raw outputとvalidated outputを区別。
- Japanese display translationを推論入力に使わない。
- researcher toggleは研究条件を変えない。
- current chunk block化はpresentationのみで、Machine artifact/schemaの科学的意味を変えない。

## 11. Success Criteria

1. 完了済みwindowごとに1つのchunk blockがあり、左右矢印で順番に移動できる。
2. chunk blockでSituation `window_summary`とcurrent-window Memory event descriptionが同時に確認できる。
3. 各representative textを原文/Google日本語訳で切替可能。
4. Situation/Memory elapsedと採用frameをchunk単位で確認できる。
5. EOF前にFinal Answer blockが表示されない。
6. EOF Answer成功後、Final Answerがcarousel最右端へ追加される。
7. selected chunkの詳細Memoryが、そのchunk完了時点のnarrative version/token count/budget/events/unresolvedを表示する。
8. 詳細「モデル生出力」でSituation/Memory/Answerの`raw_output.text`を確認できる。
9. raw model textを日本語訳でき、copy可能。
10. raw/validated/structured outputのlabelが混同されない。
11. validation failure時も保存されたraw outputとerrorを研究者が確認できる。
12. Prompt・入力tabでrun snapshot Prompt/model/generation/frame manifestを確認できる。
13. Prompt Libraryを後から編集しても過去Run詳細は変わらない。
14. 研究者表示OFFで通常画面がcompact、ONでvalidation/token/prompt/model情報が追加される。
15. old run/reload/Fake/API/browser/presentation testsに非回帰。
16. 実Google API・実Qwen/GPUを必須検証にしない。

## 12. Ambiguity Gate

blocking:
- なし。2026-10-01、ユーザーは「1stage 1block」案を出した後、Situation/Memoryの出力契約を確認した上で、両者が短く確認できるならまとめたいと明示した。現行schemaではSituationの`window_summary`とMemoryのcurrent-window eventsを代表表示にできるため、backend stageは分離したままUIを1 chunk blockへまとめる。
- 同日、ユーザーは「詳細を見る」で人間向けMemoryとmodel生出力の双方、日本語訳、研究者が生出力を確認できる工夫を要求し、「研究者表示」を明示採用した。壁打ち終了後にspec化と実装handoffを指示した。

non-blocking:
- carousel animation。
- drawer/modalのサイズ。
- Eventが複数ある際のbullet/card細部。
- researcher toggleのicon/position。
- JSON syntax highlighting。既存dependencyなしで単純pre表示でも成功条件を満たす。

## 13. Implementation Steps

Stage branch名の推奨: `stage-7-run-results-researcher-view`。

Stage 6完了後の最新mainを基準に着手する。

1. Presentation projection
   - chunk単位にSituation/Memory/memory-version/raw/prompt情報を決定的に集約。
   - old run fallback。
   - presentation unit tests。
2. Chunk carousel
   - 1 chunk block。
   - arrows/latest/history behavior。
   - final answer last block。
3. Detail drawer
   - Memory。
   - model raw output。
   - Prompt/input。
   - JSON。
4. Translation / Researcher View
   - Google表示翻訳。
   - researcher toggle。
   - validation/token/model metadata。
5. Stage 7 regression
   - Fake run、validation failure fixture、reload/read-only old run、browser/API/presentation、compile。
   - 実Qwen/GPU/外部Google課金なし。

Git操作は別途明示許可が必要。許可後にStage/Step topologyを作る場合はmain / Stage / Stepが追える`--no-ff`方針を維持する。

## 14. Gate

2026-10-01、ユーザーは研究者視点でraw model outputを確認可能にすること、Memoryを人間向けに日本語訳付きで確認すること、「研究者表示」toggleを採用することを確定し、壁打ち終了後にspec化・実装handoffを指示した。

本specは既存artifactに保存済みの値をpresentationへ投影することを基本とし、推論schemaやアルゴリズムを追加で変更しない。blockingな未決事項はないため`approved`とする。

## 15. Implementation Handoff

- approved spec: 本書
- 実装目的: Run結果を1 chunk 1 blockのcarouselで閲覧可能にし、Final AnswerをEOF後の最終blockへ置き、詳細Memory・model生出力・Prompt/input・JSONと研究者表示を提供する。
- 基準repository/commit: 現時点 `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `b868f4431e69d783632476752d3f41311a52b53a`。着手はStage 6統合後の最新mainを再確認する。
- 変更scope: Section 3–8、Section 13。
- 対象外・維持条件: Section 9–10。
- success criteria: Section 11。
- 許可されている短時間検証: Presentation/Fake/API/browser、validation failure fixture、old run/reload、fake translation、compile/import、diff check。
- 長時間runの許可状態: 未許可。実Qwen/GPU、実Google API課金、長尺全件runを開始しない。
- Git操作: 別途明示許可が必要。
- 未検証予定: 実Qwenの実際のsummary長・Memory readability・Google実APIの翻訳品質。
