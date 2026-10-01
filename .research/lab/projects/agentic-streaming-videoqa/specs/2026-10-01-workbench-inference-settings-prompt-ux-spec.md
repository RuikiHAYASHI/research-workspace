---
date: 2026-10-01
last_updated: 2026-10-01
project: agentic-streaming-videoqa
type: implementation
status: approved
sequence: 6
sequence_total: 7
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: b868f4431e69d783632476752d3f41311a52b53a
depends_on:
  - 2026-10-01-workbench-browser-preview-google-translation-spec.md
source_brainstorm:
  - 2026-10-01-workbench-cuda-preview-translation-inference-ui.md
---

# Workbench Stage 6: 推論設定・Prompt・設定呼び出し UX spec

## 1. 目的

現行Inference画面は、内部実装名やresolved JSONを常時見せており、研究者が普段変更する設定と開発者向け設定が混在している。またPrompt LibraryはInference画面内へ長く展開され、Run開始前のPrompt選択とPrompt設計/CRUD、Run開始後のPrompt確認が同じ導線に混ざっている。

Stage 6では以下を実現する。

1. 普段変更する設定だけをcompactに見せる。
2. 実装寄り設定を「開発者用」に折りたたむ。
3. 既存`profile` selectを通常UIから外し、「設定を呼び出す」入口から最近使った設定とユーザーテンプレートを再利用できるようにする。
4. Prompt設計/CRUDを独立したPrompt画面へ移し、Inference設定ではRunで使うPromptの選択だけを行う。
5. Run開始後はsnapshotされたPromptをread-onlyで確認でき、日本語訳表示も可能にする。
6. Situation / Memory / AnswerでAgentごとのmodel IDを実際のruntimeへ反映し、同一model設定は1 instanceを共有する。

## 2. 現行実装の確認

基準はStage 4完了時のWorkbench `main@b868f4431e69d783632476752d3f41311a52b53a`。実装着手時はStage 5統合後HEADを再確認する。

- canonical Configは`streaming`、`memory`、`agents`を持つ。
- Agentごとに`backend`、`model_id`、`prompt_id`、`enabled`、`generation`を保存できる。
- PromptServiceはbuilt-in/user Prompt、version、archive、history、run snapshotを既に持つ。
- Run開始時にPrompt IDをresolveし、本文/version/hashを`ExecutionSettings`/artifactへsnapshotする。Active runの途中でPrompt Libraryを編集しても、そのrunのPromptは差し替わらない。
- UIは`profile`、`reader_mode`、`visual_input_mode`、`observation_context_mode`、Question ID、window、frame数、resolved profile JSONを左側に常時表示する。
- runtimeはConfig上のAgent別model_idを保持する一方、`VideoQAWorkflow`は現在1つの`ModelAdapter`をAgentTeamへ渡し、3 Agentで共有する。Agent別model selectionをUIだけ追加してはいけない。
- `decoder_frames_per_sample`は`full_rgb` legacy reader pathでのみ使われ、`target_only` pathでは使われない。

## 3. Inference画面の通常設定

通常表示は次を基本とする。

```text
推論設定

[ 設定を呼び出す ]

動画
  1 chunkの長さ        4 秒
  sample frame数       8 枚

Memory
  Memory保持上限       6000 tokens

Model
  Situation            Qwen3-VL-4B
  Memory               Qwen3-VL-4B
  Answer               Qwen3-VL-4B

Prompt
  Situation            最初のプロンプト   [変更]
  Memory               最初のプロンプト   [変更]
  Answer               最初のプロンプト   [変更]

[ 開発者用 ▸ ]
[ 内部設定を見る ]

[ 推論を開始 ]
```

### 3.1 通常表示に残す値

- `window_seconds`: 「1 chunkの長さ」
- `frames_per_window`: 「sample frame数」
- `memory_budget_tokens`: 「Memory保持上限」。Agent別生成上限ではなく、累積text Memory narrativeを保持する共通budget。
- Agentごとの`model_id`
- Agentごとの選択Prompt title/version

### 3.2 通常表示から外す値

- Question ID入力欄
- `backend`
- `enabled`
- `decoder_frames_per_sample`
- `reader_mode`
- `visual_input_mode`
- `observation_context_mode`
- `max_new_tokens`
- `temperature`
- resolved profile JSON常時表示

Question IDはDataset Browserで選択した内部stateからRunへ渡す。Inference画面で通常ユーザーが手入力しない。

`backend`と`enabled`は既定contractを維持し、通常UIから編集しない。

`decoder_frames_per_sample`は**UIからのみ外す**。このStageで新しい算出式を発明せず、既存Config/旧run/full_rgb互換の内部値として保持する。将来この内部値自体を廃止・自動算出する場合はreader contract変更として別specにする。

## 4. 開発者用

「開発者用」を折りたたみsection/drawerとして用意し、内部enum値をそのまま人間へ見せない。

### 4.1 読み取り方式

`reader_mode`:

- `target_only` → 「採用フレームのみ展開」
- `full_rgb` → 「全フレームを展開」

### 4.2 モデルへの映像入力

`visual_input_mode`:

- `video_clip` → 「動画として入力」
- `image_list` → 「画像列として入力」

### 4.3 Situationへ渡す過去情報

`observation_context_mode`:

- `none` → 「過去のMemoryを渡さない」
- `previous_text` → 「直前までのMemoryを渡す」

### 4.4 Agent生成設定

Situation / Memory / Answerごとに:

- 最大出力token = `generation.max_new_tokens`
- temperature = `generation.temperature`

内部enum/valueはRun artifactでは従来どおり保存する。UI表示labelだけ日本語化する。

## 5. 「設定を呼び出す」

既存の`profile` selectは通常UIから外し、特別なbutton「設定を呼び出す」へ置き換える。

buttonからdrawer/modalを開き、次の2区分を見せる。

### 5.1 最近使った設定

現在の`output_root`に存在する過去Runの`execution_settings.json`から、直近の再利用可能な設定を提示する。

- 新しい設定履歴DBを重複作成しない。
- Run artifactを設定履歴のEvidenceとして利用する。
- question ID、video ID、datasetの個別選択は再適用しない。
- 再利用対象はstreaming/memory/Agent model/Prompt/generation/developer mode等のInference設定。
- 同一settings hash等で重複表示を抑えてよい。
- 古いRunで現在Configへ復元できない値は明示的に利用不可とする。silent変換しない。

### 5.2 テンプレート

ユーザーが「現在の設定をテンプレートとして保存」できる。

保存先はStage 4で予約済みの `<WORKBENCH_HOME>/app/settings.json`。

最小schema例:

```json
{
  "schema_version": 1,
  "inference_templates": [
    {
      "id": "...",
      "title": "...",
      "created_at": "...",
      "settings": { "...": "..." }
    }
  ]
}
```

要件:

- canonical defaultを「デフォルト」として呼び出せる。
- user templateはtitle付き。
- templateはDataset/questionの個別選択を含めない。
- template適用時も現在Dataset Browserで選択中の質問を維持する。
- Config schemaへ復元してvalidationしてから画面へ適用する。
- repository/worktreeへ保存しない。
- テンプレート編集管理を大規模CRUDへ拡張しない。現scopeは保存と呼び出し。

既存`ExecutionSettings.profile` fieldはlegacy/artifact互換のため残してよい。UIの「設定を呼び出す」は旧profile selectと同一概念にする必要はない。

## 6. AgentごとのModel設定とruntime

### 6.1 UI

Situation / Memory / Answerごとにmodel IDを選択/入力できる。

- 表示は短いmodel名を優先してよいが、内部では完全なmodel IDを保持する。
- canonical defaultは現行 `Qwen/Qwen3-VL-4B-Instruct`。
- backend選択UIは作らない。通常UIではQwen3-VL backendのままmodel IDだけを変更する。
- model weightsはselection時ではなくRunで必要になったときlazy loadする。
- test/UI表示だけでmodel downloadしない。

### 6.2 runtime

Config上のAgent別`model_id`を実際のAgent invocationへ反映する。

必須:

- Situationは`agents.situation`のbackend/model_id。
- Memoryは`agents.memory`。
- Answerは`agents.answer`。
- 同じ`(backend, model_id)`を複数Agentが選んだ場合、**同一lazy ModelAdapter instanceを共有**し、同じweightを3重loadしない。
- 異なるmodel_idなら別instanceとして扱う。
- instance pool/factoryの内部設計は既存Registry/Service境界へ最小差分で合わせる。
- Fake testsではroleごとに異なるfake model identityを注入でき、実GPUを使わずroutingを検証できる。
- Run snapshot/restartは各Agentのmodel_idを保持する。
- model load失敗やVRAM不足を別modelへsilent fallbackしない。

既存の`model_adapter/model_id` top-level compatibility fieldは旧run/API互換のため残してよいが、新runのAgent別設定の正本は`agents`とする。

## 7. Prompt UX

### 7.1 独立Prompt画面

上部navigationを少なくとも次の3つにする。

```text
[ データセット ] [ 推論 ] [ Prompt ]
```

現在Inference画面内へ縦に展開されるPrompt Libraryを独立Prompt viewへ移す。

Prompt viewは既存PromptService機能を再利用し:

- role filter
- 一覧/検索
- title/description/version
- built-in/user識別
- create
- copy
- edit(version追加)
- archive/restore
- version history
- English canonical body
- 「日本語訳 / 原文」表示切替

を提供する。

Stage 5のgeneric Google display translatorを使い、日本語訳はread-only。翻訳文をPromptServiceのcanonical bodyへ保存・推論入力へ利用しない。

### 7.2 Inference設定でのPrompt選択

Inference設定にはAgentごとに:

- 選択中Prompt title
- version
- 「変更」

だけを表示する。

「変更」はそのrole/current modeと互換なPrompt一覧を開き、**このrunで使うPromptを選択**する操作。

Prompt本文editorはInference設定へ常時置かない。

### 7.3 Active run中のPrompt

Run開始時に既存どおりbody/version/hashをsnapshotする。

Run開始後:

- 結果画面等の「Prompt」buttonは**そのstageで実際に使ったsnapshot**をread-only表示する。
- Prompt Library最新版へlive参照しない。
- 原文/日本語訳を切り替え可能。
- Active run途中でPromptを差し替える機能は作らない。
- Prompt Libraryで編集してもactive runは変化しない。

途中Prompt変更を研究機能として導入する場合は、run内で研究条件が変わるため別specとする。

## 8. 内部設定表示

現行`resolved_profile` JSONは常時表示しない。

「内部設定を見る」を明示クリックした場合のみdrawer/details等へ表示する。

表示内容はresolved Config/Agent settings等のデバッグ情報。API/Run artifactの正本ではなくread-only projection。

## 9. 対象外

- run途中でのPrompt差し替え。
- Prompt自動生成/自動最適化。
- backend種別をUIから変更する機能。
- model download manager。
- VRAM scheduler/offload policyの新規研究。
- decoder reader contractの再設計。
- early answer。
- 結果画面のchunk carousel/研究者表示（Stage 7）。
- 実Qwen/GPU性能評価。

## 10. Compatibility

- canonical Configを正本として維持。
- existing PromptService/run snapshot/version semanticsを維持。
- old run閲覧/restartを壊さない。
- Question IDは内部contractに残す。
- `decoder_frames_per_sample`内部contractを維持。
- model selectionだけでweightをloadしない。
- Prompt日本語訳はdisplay only。
- same model IDの3 Agentは従来と同等に1 adapter instanceを共有可能。
- CLIの既存single/default model経路はcanonical agentsが同一modelなら同じ意味を維持する。

## 11. Success Criteria

1. Inference初期画面で通常設定がwindow/frame/Memory budget/3 Agent model/3 Promptへ絞られる。
2. Question ID、backend、enabled、decoder_frames_per_sample、resolved JSONが常時表示されない。
3. 開発者用でreader/visual/context modeが日本語labelで選択でき、Agent別max_new_tokens/temperatureを変更できる。
4. 「内部設定を見る」を押したときだけresolved JSONを確認できる。
5. 「設定を呼び出す」で直近Run設定を再利用できるが、現在選択中questionを上書きしない。
6. 現在設定をtitle付きtemplateとして`WORKBENCH_HOME/app/settings.json`へ保存し、server再起動後に呼び出せる。
7. Situation/Memory/Answerで別model_idを設定するとFake model testで各roleへ正しくroutingされる。
8. 同じmodel_idを3 roleに設定した場合、model factory/adapter生成は1 instanceとなる。
9. model selection/UI testでQwen weightをload/downloadしない。
10. Prompt Libraryが独立viewになり、既存CRUD/version/historyを維持する。
11. Inference設定でAgentごとにPromptを選べる。
12. Run開始後はsnapshot Promptをread-onlyで確認し、Library編集後も表示内容が変わらない。
13. Prompt原文/Google日本語訳を切り替えられ、translation failureでcanonical body/runは壊れない。
14. existing Config/Prompt/run/restart/Fake/API/browser testsに非回帰。
15. 実Qwen/GPUは必須検証にしない。

## 12. Ambiguity Gate

blocking:
- なし。2026-10-01、ユーザーは通常設定/開発者用の分離、profileの「設定を呼び出す」化、Promptの独立設計とRun中snapshot確認、研究者がAgent modelを選べるUIについて方向性を確定し、壁打ち終了後にspec化と実装handoffを指示した。

non-blocking:
- drawer/modalの細かなCSS。
- model ID fieldをselect+editableにするかdatalistにするか。完全model IDを保持し、未選択時defaultを使うことが満たされれば既存styleに合わせる。
- recent settingsの表示件数。
- template ID生成方式。
- settings.json内のkey順。
- internal JSON drawerの具体的なアイコン。

## 13. Implementation Steps

Stage branch名の推奨: `stage-6-inference-settings-prompt-ux`。

Stage 5完了後の最新mainを基準に着手する。

1. Settings projection / app template storage
   - UIで扱う設定subset整理。
   - recent run settings projection。
   - `app/settings.json` template保存/呼び出し。
2. Per-Agent model runtime
   - model factory/pool。
   - AgentTeam/Workflow/CLI/serverへのrole別routing。
   - same-model instance sharing。
   - Fake regression。
3. Compact Inference settings
   - normal/developer/internal layers。
   - Question ID等の通常UI除去。
   - 日本語label。
4. Prompt dedicated view / run selection
   - Prompt navigation。
   - InferenceでPrompt選択。
   - snapshot read-only確認とGoogle日本語訳。
5. Stage 6 regression
   - Config/Prompt/template/restart/Fake/API/browser/compile。
   - 実Qwen/GPU/model downloadなし。

Git操作は別途明示許可が必要。許可後にStage/Step topologyを作る場合は従来のmain / Stage / Stepを視覚的に残す`--no-ff`方針を使う。

## 14. Gate

2026-10-01、ユーザーは壁打ち終了を明示し、会話で確定した設定UI/Prompt設計をspec化して実装へ渡すよう指示した。

本specでは、未確定だった`decoder_frames_per_sample`の扱いについて、研究挙動を推測で変えないため「UIから隠すが内部contractは現状維持」とした。自動算出式の導入はこのUI要件に不要であり、既存full_rgb互換を守る最小設計である。

Agent別modelについては、ConfigだけAgent別なのにruntimeが1 modelを共有する現行差分を解消し、UIと実際の実行を一致させる必要がある。same model時のinstance共有を維持する。

blockingな未決事項はないため本書を`approved`とする。

## 15. Implementation Handoff

- approved spec: 本書
- 実装目的: Inference設定を通常/開発者/内部へ整理し、設定履歴・テンプレート、独立Prompt画面、run snapshot確認、実際に反映されるAgent別model selectionを実装する。
- 基準repository/commit: 現時点 `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `b868f4431e69d783632476752d3f41311a52b53a`。着手はStage 5統合後の最新mainを再確認する。
- 変更scope: Section 3–8、Section 13。
- 対象外・維持条件: Section 9–10。
- success criteria: Section 11。
- 許可されている短時間検証: Fake model/factory、Config/Prompt/template/storage/API/browser、restart、compile/import、diff check。
- 長時間runの許可状態: 未許可。実Qwen/GPU、model download、長尺全件runを開始しない。
- Git操作: 別途明示許可が必要。
- 未検証予定: 異なる実Qwen modelを同時loadした場合のVRAM、実モデル品質/速度。
