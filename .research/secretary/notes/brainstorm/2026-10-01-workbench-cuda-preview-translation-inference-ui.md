---
date: 2026-10-01
project: agentic-streaming-videoqa
source_todo: null
topic: workbench-cuda-preview-translation-inference-ui
status: exploratory
tags: [brainstorm, workbench, cuda, preview-cache, translation, inference-ui, prompt-ui, results-ui]
---

# Workbench CUDA・preview cache・翻訳・推論画面再設計の壁打ち

## 出発点

2026-10-01、Workbenchの推論画面で次のエラーが表示された。

`CUDA利用不可 (QwenCudaUnavailableError): CUDAが利用できません。PyTorchのCUDA環境を確認してください`

同時に、次の改善要望がある。

- 動画カードhover previewの初回・再訪速度を改善したい。
- 一度previewした動画は、1〜2分程度の短尺clipをcacheして再訪時に高速化したい。
- 表示用日本語訳はGoogle Cloud Translation APIを使う方針へ変更したい。
- 推論画面を大幅にコンパクト化し、設定ボタンからモデル・1 chunkの秒数・chunk内sample frame数等を変更したい。
- Prompt UIと実行結果表示も壁打ちして再設計したい。

本メモは探索記録であり、spec・実装許可ではない。

## 読み込んだ文脈

- Company project README: `.research/lab/projects/agentic-streaming-videoqa/README.md`
- 直近MTG: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-25-mtg.md`
- 既存brainstorm: `.research/secretary/notes/brainstorm/2026-09-30-workbench-inference-ui-prompt-library-and-qwen-video.md`
- Dataset Browser UI spec: `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-29-workbench-dataset-browser-ui-implementation-spec.md`
- Agent mode/readable memory spec: `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-agent-modes-and-readable-memory-spec.md`
- Dataset user-data/cache storage spec: `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-30-workbench-dataset-user-data-storage-spec.md`

現在の研究コード基準は `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `4f2546ef4a1dafd2ae2ba157c079d766ed023cb2`。Stage 4 storage specはapprovedだが、基準mainはStage 3までの実装である。

## 確認済み事実

### 1. CUDAエラーのアプリ側直接原因

`src/longvideoqa_workbench/agents/qwen3_vl.py` の `validate_cuda_runtime()` は、Qwen重みを読む前に次を確認する。

- `torch.cuda.is_available()`
- `torch.cuda.device_count()`

今回の `QwenCudaUnavailableError` は **`torch.cuda.is_available() == False` の場合だけ**発生する。したがってQwen生成中の失敗ではなく、PyTorch/CUDA runtimeのpreflight段階で停止している。

現在のREADMEにはUI/Fake確認用の起動例として `CUDA_VISIBLE_DEVICES=""` を設定する経路があり、この起動方法ではGPUを意図的に不可視化する。一方、実推論例は `CUDA_VISIBLE_DEVICES=3` としている。

GitHubからはSSH server上の実process環境、実際にimportされたtorch build、NVIDIA driver状態、local venv、`CUDA_VISIBLE_DEVICES` の実値は確認できないため、環境側の最終原因は未確認。

切り分け候補:

1. UI確認用commandの `CUDA_VISIBLE_DEVICES=""` をそのまま使っている。
2. serverを起動したPython環境にCPU-only / CUDA不整合のPyTorchが入っている。
3. `nvidia-smi`ではGPUが見えるが、server processからdriver/CUDA runtimeを利用できない。
4. qwen-preflightを確認した環境と、実際に`serve`を起動した環境が異なる。

同一venv・同一shellで `longvideoqa qwen-preflight` と `torch.__version__ / torch.version.cuda / torch.cuda.is_available() / torch.cuda.device_count()` を確認すれば次の原因まで切り分けられる。

### 2. hover previewの現在実装

`src/longvideoqa_workbench/browser/media.py`:

- cache機構自体は既に存在する。
- default preview clipは6秒、480px高、音声なし、H.264、`+faststart`。
- cache上限は512 MiB、古いfileから削除する。
- **sourceがMP4 + H.264なら「browser互換」と判定し、clip cacheを作らず元の長尺動画を直接返す。**
- 非互換の場合だけ短尺previewを生成してcacheする。

`src/longvideoqa_workbench/web/browser.js` / `media.js`:

- cardへの`pointerenter`直後にpreview URLを設定して即`play()`する。
- hover dwell/debounceはない。
- 離脱時は停止してsrcを外す。

したがって、LongVideoBenchの元動画がMP4/H.264なら、互換形式であることを理由に毎回元動画へアクセスしている可能性があり、再訪時の高速化cacheが効かない。

### 3. cache保存先との整合

2026-10-01 approvedのStage 4 storage specでは、将来のpreview cacheを次へ集約する契約になっている。

`<WORKBENCH_HOME>/datasets/<dataset-id>/cache/previews/`

今回のpreview高速化はこの保存先と整合する。ただしStage 4のapproved scopeは主に「cache routing / storage boundary」であり、previewを常に1〜2分clip化する挙動変更は別の要件である。Stage 4へ黙って混ぜず、後続specまたは明示的なStage 4改訂として扱うべき。

### 4. 翻訳の現在実装

現在は `src/longvideoqa_workbench/browser/translation.py` のArgos Translate 1.11.0を使うlocal display translation。

- annotation原文は変更しない。
- 日本語は表示専用。
- text hashをキーにtranslation cacheを永続化する。
- APIは `/api/browser/translation`、UIは原文question IDを維持する。

したがってGoogle Cloud Translationへ切り替える場合も、annotation / inference inputを英語原文のまま保持し、backendだけ差し替える設計が可能。

Google Cloud TranslationはBasic(v2)とAdvanced(v3)がある。今回の用途は短いQA/選択肢の英→日表示であり、機能要求だけならBasicでも足りる。AdvancedはIAM/ADC、glossary等の拡張を使いたい場合の候補。どちらでもcredentialをrepoへ保存しないこと、translation cacheを維持して無駄な再課金・再requestを避けることが重要。

### 5. 推論画面の現在構造

現行`index.html`は左側に常時表示の「実行設定」を持ち、profile、reader mode、visual input、過去text、question ID、window seconds、frames/window、resolved profile JSON、実行ボタンを縦に並べる。

中央には3 Agentのstage cards、Prompt Library、その下にrun/turn履歴、採用frame、stage output、memory等を縦に積む。

Prompt Service自体はStage 3で既にCRUD/version/snapshotまで実装済みで、Agentごとに`backend/model_id/prompt_id/generation`を持てるConfig構造も存在する。したがって次の課題はbackend契約より主にUI情報設計である。

## 解釈・推論

### CUDA

今回、もし直前の「画面動作確認」用commandで`CUDA_VISIBLE_DEVICES=""`を付けてserverを起動しているなら、それが最も単純で再現性のある説明になる。この場合はcode bugではなく、安全なUI確認commandと実推論commandの目的差が画面から分かりにくいことがUX上の問題。

したがって単にCUDAを直すだけでなく、推論画面に「GPU利用可能 / GPU非表示 / CUDA不可 / model dependency不足」を実行前に小さく表示すると再発防止になる。

### preview cache

「browser互換なら元動画を返す」という現在の最適化は、短いローカル動画には合理的だが、長尺動画 + HDD/NAS + hover UIでは適さない可能性がある。

hover用途ではcodec互換性より「軽量な短尺proxyがあるか」を優先した方がよい。

### inference UI

推論画面の第一目的は「選択済みQAに対し、現在のAgent設定を軽く確認して実行し、結果を追うこと」。全設定・JSON・Prompt本文を常時表示する必要はない。

研究用なので設定を隠し切るのではなく、**初期表示を簡潔にし、必要な時だけ深掘りできるprogressive disclosure**が合う。

## 採用候補

### A. CUDA: 実行前Environment Healthを追加

推論画面上部に小さいstatusだけ表示。

例:

`GPU: CUDA利用可 · 1 GPU · Qwen未ロード`

または

`GPU: 利用不可 — 設定を確認`

詳細を開くと:

- `CUDA_VISIBLE_DEVICES`
- torch version
- `torch.version.cuda`
- `torch.cuda.is_available()`
- visible device count
- model dependency status

をread-only表示する。

モデル重みloadとは分離したpreflight APIにする。

### B. preview: 1〜2分proxy cacheを再訪高速化に使う

方向性:

- MP4/H.264でも元動画を直接返すのを既定にせず、hover preview専用proxyを使う。
- 60〜120秒、候補default 90秒。
- 360p〜480p、音声なし、H.264、faststart。
- cache keyは単なるvideo IDではなく、source identity/signature + preview policy versionを含め、元動画更新時のstale cacheを避ける。
- 保存先はStage 4の `WORKBENCH_HOME/datasets/<dataset>/cache/previews/`。
- LRU/容量上限は維持。1〜2分化で512 MiBは小さくなる可能性があるため、実測後にquotaを決める。
- hover直後に毎回変換を始めず、200〜400ms程度のdwell後にrequestする候補。
- 大量事前生成はしない。

初回UXには2案ある。

1. **単純案:** 初回hoverでproxy生成完了まで待つ。実装は簡単だが初回がさらに遅い。
2. **有力案:** 初回は元動画を再生可能なら使いつつ、滞在した動画だけproxyを生成し、2回目からcacheを使う。ユーザー要望「一度見たものを次回高速」と一致する。ただしI/O二重化を避けるworker制御が必要。

現時点では2を有力候補とする。

### C. 翻訳: Google Cloud Translation backendへ切替

既存の表示専用契約を維持:

`English annotation (canonical) -> Google translation -> Japanese display cache`

- Agent入力・question ID・choice順は英語原文を正本にする。
- 日本語訳は表示だけ。
- cache hitならAPIを呼ばない。
- provider/version/source hashをcache keyへ含める。
- credentialは環境変数/ADC等で供給し、repoへ保存しない。
- API失敗時は英語原文へfallbackし、Dataset閲覧自体を壊さない。

初期実装では通常のQA表示用途に絞り、glossary等は必要になってから追加する。

### D. 推論画面: 「実行中心 + 設定drawer」へ変更

初期表示候補:

1. 上部: 選択済みdataset / video / questionの短いsummary。
2. 右上: `⚙ 設定`。
3. 中央: 3 Agentをコンパクトなカード/stepとして表示。
   - Agent名
   - model名
   - 選択中Prompt名 + version
   - 状態
   - `Prompt` ボタン
4. 下部: `推論を開始`。
5. 実行後は同じ領域を結果timelineへ拡張。

設定drawer:

- **動画入力**
  - 1 chunkの長さ（秒）
  - 1 chunkでsampleするframe数
  - visual input mode
- **Model**
  - Situation / Memory / Answerごとのmodel
  - 同一modelなら実instance共有
- **Memory / advanced**
  - previous text mode
  - token budget
  - generation parameters
  - reader mode / decoder内部値等

通常の研究操作で触る値と内部実装値を分ける。

### E. Prompt UI: Agentカードから専用panelを開く

main画面へPrompt全文textareaを置かない。

Agent cardのPrompt名を押すとpanel/drawerを開き:

- 一覧
- Prompt名
- 説明
- version
- 原文
- 日本語訳（read-only）
- 履歴
- 編集 / copy / archive

を表示。

既存Prompt ServiceのCRUD/version/snapshot契約をそのまま使う。Prompt日本語訳も推論に渡さず閲覧専用。

### F. 結果表示: timeline-firstを第一候補

Streaming VideoQAとして最も見たいのは「どの時間帯を見て、何を理解し、Memoryがどう更新され、最後に何を答えたか」。

各chunkを1行/1cardにして:

- `00:00–00:04`
- sampled frames strip
- Situation要約
- Memory update（追加/変更を短く）
- elapsed time

を表示する。

上部または右側にFinal Answerを固定/強調し、生JSON、full prompt、raw model outputは各chunkの「詳細」に畳む。

これにより現行の「stage outputが縦に続いた後、別のmemory sectionを見る」構造より因果関係を追いやすい。

## 保留・反例

- 1〜2分proxyはpreview用途として長すぎる可能性がある。容量と初回encode時間を実測し、30/60/90/120秒を比較する余地がある。
- 初回元動画stream + 裏でproxy生成はI/Oを増やすため、共有HDD/NASの負荷が高い環境では逆効果になり得る。dwell、同時変換1本、cancel、cache hit率計測が必要。
- Google Cloud Translationは外部通信と課金が発生する。cacheを維持し、UIで翻訳失敗が閲覧失敗へ波及しない構造が必要。
- model選択を自由にしすぎると複数VLMを同時常駐させてVRAM不足を招く。UI上の「選択できる」とruntime上の「同時loadできる」を分離する。
- CUDA問題はGitHubだけではlocal環境の最終原因まで断定できない。まず同一server process環境でpreflight結果を取る必要がある。

## 現在の方向性

有力:

1. CUDAはまず環境を復旧し、後続UIではpreflight statusを常時小さく見せる。
2. previewはcodec互換性に関係なくhover専用proxy cacheを使う設計へ寄せる。
3. cache保存先はStage 4のDataset別`WORKBENCH_HOME`契約に合わせる。
4. 翻訳はGoogle Cloud Translationへ変更し、英語原文をcanonical、訳文をread-only cacheとする。
5. 推論画面は設定常時表示をやめ、`⚙ 設定` drawer + compact Agent cardsへする。
6. PromptはAgentカードからPrompt Library panelへ。
7. 結果はchunk timelineを主表示にし、raw情報を折り畳む。

## 次に判断すること

- CUDA: 実際のserve processが `CUDA_VISIBLE_DEVICES=""` で起動されているか。同一venvでpreflightした結果。
- preview: proxy長を60/90/120秒のどこから始めるか。候補defaultは90秒。
- translation: Google Cloud Translation Basic(v2)の単純構成で開始するか、Advanced(v3/ADC)を最初から使うか。
- inference UI: settingsを右drawerにするかmodalにするか。現状はdrawerを第一候補。
- result UI: timeline-firstを採用するか、Final Answerをより前面に置くanswer-firstとの比較。

## spec引き継ぎ候補

まだspec化していない。specへ進む場合は、Stage 4 storage実装との境界を明示し、少なくとも以下を分けて契約化する。

- CUDA runtime health/preflight UX
- hover preview proxy cache policy
- Google Translation provider変更
- compact inference settings / Prompt UI
- timeline-first result presentation


## 2026-10-01 12:42 JST 追記: CUDA切り分け・preview条件・UI方向性

### CUDAの追加Evidence

ユーザーがWorkbenchの実利用venvで次を実行した。

```text
CUDA_VISIBLE_DEVICES=3 longvideoqa qwen-preflight
{"cuda_visible_devices": "3", "cuda_available": true, "visible_device_count": 1, "logical_device_ids": [0]}
```

これにより、少なくとも当該venvで物理GPU 3を可視化した場合、PyTorchからCUDAが利用できGPU 1枚が論理ID 0として見えることを確認した。以前のブラウザ表示 `QwenCudaUnavailableError` はQwen/PyTorch自体の恒常的なCUDA不備ではなく、`serve` process側の起動環境差（例: UI確認用の `CUDA_VISIBLE_DEVICES=""`、別shell/venv、既存server process）が主要候補となる。実推論時は同じvenvでGPUを明示した`serve`を起動して確認する。

### Stage 4 main統合の確認

GitHub上のWorkbench `main` は `b868f4431e69d783632476752d3f41311a52b53a`、commit titleは「Stage 4: Dataset別 user data / cache storageを統合」。parentsはStage 3基点 `4f2546ef...` とStage 4側 `23a58e3...` の2本で、Stage→mainがmerge commitとして統合されている。README最終同期とDataset別cache routingもmainに存在する。

### Preview仕様の方向性を更新

ユーザー意図は「長いpreviewを見たい」ことではなく、冒頭のタイトル画面等を避けて動きのある場面をhoverですぐ見たいこと。

採用方向:

- preview clip長は10〜20秒。初期候補は15秒。
- 長尺動画は60秒付近から開始。
- 60秒付近から15秒を確保できない短尺動画では、動画長に応じて開始点を前へずらす。
- hover dwell/debounceは入れず、pointer enter直後に再生要求を開始する。
- cache hit時は即再生を目標にする。
- 初回cache生成中はposter/loadingを維持し、生成後・次回hoverから高速化する。
- MP4/H.264でも元長尺動画を直接返す既存shortcutはhover preview用途では廃止候補。
- cache保存先はStage 4で実装済みのDataset別`WORKBENCH_HOME/.../cache/previews/`へ合わせる。

短尺動画の開始点はまだ数式として確定していない。有力案は「60秒を上限としつつ、preview尺を確保できない場合は終端直前に寄り過ぎない範囲で前へずらす」。タイトル回避と終端credits回避の両方を考える。

### 推論設定で現状扱っている項目

現行mainのConfig/画面には以下が存在する。

- `profile`: 既定設定セット。現在は内部設定をまとめて解決する入口。
- `reader_mode`: `full_rgb` / `target_only`。全frameをRGB化するか、sample対象frameだけRGB化するかというReader内部方式。
- `visual_input_mode`: `image_list` / `video_clip`。sampled frameを複数画像として渡すか、video入力として渡すか。
- `observation_context_mode`: `none` / `previous_text`。Situation Agentへ直前までの確定textを渡すか。
- `question_id`: datasetで選択した質問の内部ID。通常UIで手入力・常時表示する必要性は低い。
- `window_seconds`: 1 chunkの動画時間。
- `frames_per_window`: 1 chunkからsampleしてモデルへ渡すframe数。
- `decoder_frames_per_sample`: Reader/decoder内部の処理単位。通常ユーザーが毎回触る値ではない。
- `memory_budget_tokens`: 保持するtext memoryの上限。
- Agentごとの `backend`: model adapter種別（現在`qwen3_vl`）。
- Agentごとの `model_id`: 実際のmodel名。
- Agentごとの `prompt_id`: 選択Prompt。
- Agentごとの `enabled`: Agentを有効化するか。
- Agentごとの `max_new_tokens`: 1回の生成上限。
- Agentごとの `temperature`: 生成のsampling温度。
- `resolved_profile`: 上記を解決した内部JSON。通常利用者向けではなく開発者情報へ移す候補。

ユーザーが人間向け名称を決めるため、次の会話ではこれらの役割を説明し、表示名そのものはユーザー判断とする。

### Prompt UI追加要望

既存のAgentカード→Prompt Library panel方針を維持する。さらにPrompt本文にもQAと同様の「日本語訳」ボタンを置きたい。翻訳はread-only表示であり、推論へ渡すcanonical Prompt本文は英語原文を維持する。

### 結果表示の方向性を更新

timeline-first案から修正。

- **1 stage = 1表示block**とする。
- block左上に前stage矢印、右上に次stage矢印を置く。
- backendのturn/stage構造は保持しつつ、UIでは完了済み`turns[].stages[]`を時系列にflattenしたstage historyとして閲覧できる案が有力。
- 各blockにはchunk/time range、stage種別、出力、必要なら採用frame、処理時間をまとめる。
- Prompt全文/raw output等は詳細へ畳む。
- 実行を進めるたび最新stageを右端として追加するイメージ。
- EOF前はFinal Answerが存在しないため表示しない。
- EOF後にFinal Answer stageが生成されたら**一番右（stage historyの末尾）**へ追加する。
- 現段階ではFinal Answer生成後に専用画面へ大きく切り替える必要はなく、同じstage navigation内の最終blockでよい。
- 将来early-answer/早押し構成を実装した時点でFinal Answer表示方法を再設計できる。

### Dataset Browser QA表示

現行mainでは質問表示が `<question_id>: <question text>` になっている。ユーザーはQuestion IDの先頭表示を不要と判断した。

採用方向:

- QA blockの視覚表示は質問文 + 選択肢だけにする。
- `question_id`は内部selection、URL、run contract、artifactでは維持する。
- IDを消すのはpresentationだけであり、dataset annotationや推論contractは変更しない。


## 2026-10-01 12:42 JST 追記2: 設定階層とchunk結果表示の収束

### 設定UIの階層化

ユーザー判断を受け、推論設定を次の4層へ分ける方向で収束する。

#### 1. 通常設定

日常的に変更する研究条件だけを見せる。

- 1 chunkの動画時間 (`window_seconds`)
- 1 chunkからモデルへ渡すsample frame数 (`frames_per_window`)
- text memory上限 (`memory_budget_tokens`)
- Situation / Memory / Answerのmodel (`model_id`)

`decoder_frames_per_sample`はユーザー入力ではなく、他設定から算出する内部値へ寄せる候補とする。

#### 2. Prompt

`prompt_id`は通常設定から外し、各AgentのPrompt UIへ集約する。

- Prompt名
- 説明
- version
- 英語正本
- 「日本語訳」切替
- 編集 / コピー / 履歴等

日本語訳はread-only displayで、推論に渡すcanonical本文は英語を維持する。

#### 3. 開発者用

通常利用で頻繁に触らない実装寄り設定をここへ移す。

- `reader_mode`
  - `target_only`等の内部値を直接見せず、日本語ラベルを付ける。
  - 有力表示例: 「採用フレームのみ展開」 / 「全フレームを展開」
- `visual_input_mode`
  - `video_clip` / `image_list`を直接見せず、日本語ラベルを付ける。
  - 有力表示例: 「動画として入力」 / 「画像列として入力」
- `observation_context_mode`
  - `none` / `previous_text`を直接見せず、日本語ラベルを付ける。
  - 有力表示例: 「過去の記憶を渡さない」 / 「直前の記憶を渡す」
- Agent generation
  - `max_new_tokens`
  - `temperature`
- 必要ならbackend等を診断情報として表示するが、通常編集対象からは外す。

`backend`、`Agent enabled`、手入力の`question_id`は通常UIから削除する方向。

#### 4. 内部設定 / 詳細情報

`resolved_profile` JSONは常時表示しない。明示的な「詳細」「内部設定を見る」等の操作をした場合のみ展開する。

### Profileの再定義

既存の`profile` selectを単なる設定項目として残すより、**設定の再利用機能**として再定義する方向。

候補機能:

- 過去に実行した設定を呼び出す「履歴」
- よく使う設定を保存する「テンプレート」
- 現在設定をテンプレートとして保存
- 既定テンプレート

通常のselectではなく、設定画面上部等の特別なbuttonからdrawer/modalを開くUIが適する。有力な入口表現は「設定を呼び出す」で、内部に「最近使った設定」と「テンプレート」を分ける。

この再定義では、既存のprofile概念とrun履歴、persistent user settingの責務整理が必要なため、実装spec時に保存形式を決める。

### Situation / Memoryの現在の出力契約

Workbench mainの現行Prompt/validatorを確認した。

Situation Agent (video mode)はJSONで次を返す。

- `window_summary`: 当該chunkの短い全体要約
- `observations[]`: 時間範囲、description、根拠frame、question relevance、certainty
- `unresolved[]`: 未解決点

Memory AgentはJSONで次を返す。

- `events[]`: event ID、時間範囲、description、根拠frame、certainty、importance reasons
- `narrative`: それまでの重要な出来事を統合したworking narrative
- `unresolved[]`: 未解決点

したがって両Agentとも「一言だけ」を返す契約ではない。ただし人間向け代表表示としてSituationの`window_summary`とMemoryの`narrative`を利用できる。

注意点としてMemoryの`narrative`はcurrent chunkだけの一言ではなく、過去Memoryを統合した累積的な文章になり得る。そのため長くなった場合のUI制御が必要。

### 結果表示の更新案: stage単位からchunk単位の見せ方へ

ユーザーの「SituationとMemoryが一言程度ならまとめて見たい」を踏まえると、backendでは2 stageのまま維持しつつ、**人間向け表示blockは1 chunkにまとめる**案が有力。

例:

```text
←                 Chunk 3  00:08–00:12                 →

[採用 frame strip]

状況理解
Person A opens the refrigerator and takes out a bottle.
[日本語訳]

記憶
A has taken a bottle from the refrigerator after entering the kitchen.
[日本語訳]

処理時間  Situation 1.2s / Memory 0.8s

[詳細]
```

「詳細」の中に次を格納する。

- Situation observations
- Situation unresolved
- Memory events
- Memory unresolved
- evidence frame IDs / timestamps
- Prompt
- raw JSON / raw model output
- model info

これなら研究上のstage境界は失わず、通常閲覧では1 chunkを一つのまとまりとして理解できる。

矢印navigationは**chunkごと**に進め、EOF後だけ最後のblockとしてFinal Answerを追加する案が自然。

```text
Chunk 1 → Chunk 2 → ... → Chunk N → Final Answer
```

ただし、stage単位の逐次デバッグが必要な場合は「詳細」内または開発者表示でSituation / Memoryを個別確認できるようにする。

### 日本語訳

結果表示にも各代表textの横へ「日本語訳」buttonを置く。

- Situation `window_summary`
- Memory `narrative`
- Final Answer（必要ならanswer text / evidence explanation）

翻訳はdisplay only、英語原文がcanonical。Google翻訳cacheをQA/Promptと共通化できる設計が望ましい。

### 現時点の削除・非表示候補

通常設定から削除または隠すもの:

- question ID input
- decoder_frames_per_sample input
- backend
- Agent enabled
- prompt_id（Prompt画面へ移動）
- reader_mode（開発者用へ）
- visual_input_mode（開発者用へ）
- observation_context_mode（開発者用へ）
- resolved_profile常時表示

残すもの:

- window_seconds
- frames_per_window
- memory_budget_tokens
- Agentごとのmodel_id

未確定:

- profileの保存・履歴データモデル
- memory narrativeが長文化した場合の代表表示ルール
- Final Answerの日本語訳対象範囲


## 2026-10-01 14:41 JST 追記: Memory上限・Prompt固定性・研究者向け生出力

### memory_budget_tokensの意味を訂正

現行実装を再確認した結果、`memory_budget_tokens=6000`はAgentごとの生成上限ではない。

- Situation / Memory / Answerごとの生成上限は各Agentの`generation.max_new_tokens`。
- `memory_budget_tokens`はMemory Agentが更新した累積`narrative`を保持する際の**共有テキストMemory budget**。
- `VideoQAWorkflow._commit_memory()`でMemory Agentのvalidated `narrative`へ`fit_narrative_to_budget(... token_budget=settings.memory_budget_tokens ...)`を適用する。
- そのcompact済みMemoryは次のMemory入力、Answer入力、設定によってはSituationのprevious textにも使われる。

したがってUIではAgent設定配下ではなく、独立した「Memory保持上限」「累積Memory上限」等として扱うのが正しい。

### Promptは現行runでは固定

現行ConfigServiceはrun開始前に各Agentの`prompt_id`を`PromptService.resolve_for_run()`で解決し、本文/hash/versionを含む`ExecutionSettings`へsnapshotする。TurnSessionはそのsettingsをrun中ずっと保持し、各chunkのSituation/Memory、EOFのAnswerは同じsnapshot済みPromptを使う。

したがって現行契約では:

- Situation Promptはrun中の全Situation stageで同一snapshot
- Memory Promptはrun中の全Memory stageで同一snapshot
- Answer PromptはEOFで同一run snapshotを使用
- Prompt Library上のPromptをrun途中で編集しても、active runのPromptを差し替える通常機構はない

これは再現性の面でも自然。よって有力UI方針:

1. Prompt設計/CRUDはInference設定とは別の**Prompt Library画面**へ置く。
2. Inference設定では各Agentが「このrunで使うPrompt」を選択する。
3. run開始後は各chunk/stageの「Prompt」buttonから、実際にsnapshotされたresolved Promptを**read-only**で確認する。
4. Prompt確認画面にも「日本語訳」を置く。
5. run途中でPromptを変更する機能は通常操作には入れない。将来必要になった場合は「途中から研究条件を変更したrun」として別の実験契約/履歴設計が必要。

### 研究者向け結果表示

ユーザー要望: 通常表示を簡潔に保ちつつ、研究者はmodelの生出力と蓄積Memoryを確実に確認できること。

有力構成は「通常表示 + 詳細drawer + 研究者表示toggle」。

#### 通常chunk block

- Situation `window_summary`
- 日本語訳button
- Memory update: current chunkで追加されたevent description群
- 日本語訳button
- Situation / Memory処理時間
- 採用frame strip
- 「詳細を見る」

#### 詳細drawer

上部をtab化する。

**Memory**
- 現在までの累積`narrative`
- event ledger
- unresolved
- version / token count / budget
- 英語原文 / 日本語訳の切替

**モデル生出力**
- Situation Agent
  - modelが返した原文text
  - 日本語訳
- Memory Agent
  - modelが返した原文text
  - 日本語訳
- Final Answer blockではAnswer Agentも同様
- copy button
- output validation成功/失敗状態

**Prompt・入力**
- snapshotされたresolved Prompt原文
- 日本語訳
- model ID / generation setting
- input memory version
- frame manifest / timestamp
- 必要ならbackend情報

**JSON / 内部情報**
- validated structured output
- backend raw metadata
- model info
- artifact参照

### 「生出力」の定義

Qwen3VLAdapterの現行`ModelResponse`は:

- `text`: model decode直後の文字列
- `raw_output.text`: 同じmodel文字列
- `raw_output.generated_tokens`
- `raw_output.hit_max_new_tokens`
- `model_info`: adapter/model/dtype/device map

Situation/MemoryではStageResultにmodel textを保持したうえでvalidated `structured_output`を別に持つ。Answerではvalidated後の`output`は回答文字列へ置き換わるため、**研究者向け「model生出力」はStageResult.outputだけに依存せず、Qwenの`raw_output.text`またはartifact上のraw model responseを正本として表示する**必要がある。

UI上は「モデル生出力（原文）」と「検証済み出力」を明確に分ける。

### 研究者表示toggle

Inference結果領域上部に「研究者表示」を置く案。

OFF:
- 通常のchunk summary + Memory updateのみ

ON:
- 各chunk blockにvalidation status
- model output preview
- prompt version/hash
- generated token数 / max token hit
- 詳細drawerへの直接導線

これにより、通常利用時の見やすさを壊さず、実験確認時には各stageの生出力へすぐ到達できる。


## 2026-10-01 Spec昇格

壁打ち終了。2026-10-01のユーザー指示により、確定内容を次のapproved implementation specへ昇格した。

- [Stage 5: Preview高速化・Google表示翻訳・Dataset QA簡素化](../../../lab/projects/agentic-streaming-videoqa/specs/2026-10-01-workbench-browser-preview-google-translation-spec.md)
- [Stage 6: 推論設定・Prompt・設定呼び出し UX](../../../lab/projects/agentic-streaming-videoqa/specs/2026-10-01-workbench-inference-settings-prompt-ux-spec.md)
- [Stage 7: Chunk結果・Researcher View・生出力確認](../../../lab/projects/agentic-streaming-videoqa/specs/2026-10-01-workbench-run-results-researcher-view-spec.md)

以後の実装判断はbrainstorm本文ではなく、上記approved specをAuthorityとして扱う。
