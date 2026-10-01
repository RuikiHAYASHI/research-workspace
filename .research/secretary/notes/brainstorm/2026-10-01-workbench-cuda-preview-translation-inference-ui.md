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
