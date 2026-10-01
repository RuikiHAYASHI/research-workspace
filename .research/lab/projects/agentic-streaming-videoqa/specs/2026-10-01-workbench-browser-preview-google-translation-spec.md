---
date: 2026-10-01
last_updated: 2026-10-01
project: agentic-streaming-videoqa
type: implementation
status: approved
sequence: 5
sequence_total: 7
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: b868f4431e69d783632476752d3f41311a52b53a
depends_on:
  - 2026-09-30-workbench-dataset-user-data-storage-spec.md
source_brainstorm:
  - 2026-10-01-workbench-cuda-preview-translation-inference-ui.md
---

# Workbench Stage 5: Preview高速化・Google表示翻訳・Dataset QA簡素化 spec

## 1. 目的

Stage 4後のDataset Browserについて、次の3点を改善する。

1. 長尺動画のhover previewで巨大な原動画を毎回読み始める挙動をやめ、冒頭タイトル等を避けた短いpreview clipをDataset別cacheへ保存して再利用する。
2. 現行Argos Translateのローカル翻訳をGoogle Cloud Translation APIへ置き換え、質問・選択肢だけでなく後続StageのPrompt/結果表示でも再利用できる表示専用翻訳境界を作る。
3. Dataset Browserの質問表示からQuestion IDを外し、質問文と選択肢だけを見せる。

推論アルゴリズム、Agent Prompt、Memory/Answer schema、Qwen生成内容は変更しない。

## 2. 現行実装の確認

基準はWorkbench `main@b868f4431e69d783632476752d3f41311a52b53a`。

- Stage 4でDataset別cacheは `<WORKBENCH_HOME>/datasets/<dataset-id>/cache/` へrouting済み。
- `BrowserMediaService.preview()` はMP4/H.264をbrowser compatibleと判定すると**原動画を直接返す**。その場合 `cache/previews/` の短尺cacheは使われない。
- browser側はpointer enter直後にpreview URLをvideoへ設定してplayする。hover dwell/debounceはない。
- 非browser-compatible動画だけ、先頭0秒から既定6秒をH.264へ変換してpreview cacheへ保存する。
- preview cache pruningは既定512 MiB、同時変換はSemaphore(1)。
- 質問表示は現在 `<question_id>: <question text>`。
- 翻訳は`LocalDisplayTranslator` + Argos Translate 1.11.0で、英語原文を正本にした表示専用英日翻訳とDataset別translation cacheを持つ。

## 3. Preview clip契約

### 3.1 clip長と開始位置

hover previewの既定clip長は **15秒** とする。

動画長を `D` 秒、clip長を `L = min(15, D)` とし、開始秒を次で決める。

```text
start = min(60, max(0, D - L - 5))
end   = min(D, start + L)
```

意図:

- 80秒以上の動画は原則60秒付近から15秒を見る。
- 60秒付近から15秒を確保しづらい短尺動画は開始位置を前へずらす。
- 可能な範囲で終端5秒を避け、credits等へ寄りすぎない。
- 15秒以下では先頭から全長をpreviewする。

開始点を「動き量解析」で自動探索する処理はこのStageでは入れない。60秒付近という単純で再現可能な規則を先に採用する。

### 3.2 hover挙動

- pointer enter/focus時は**待ち時間なし**でpreview requestを開始する。
- 200–400ms等のhover debounceは追加しない。
- cache hit時はcache済み15秒clipをRange対応で返し、即再生を目標とする。
- cache miss時はposter/loading表示を維持してclipを生成し、生成完了後に再生可能とする。初回だけ生成待ちが発生し得る。
- pointer leaveで現在の再生は止める。
- hoverしただけで全動画を事前batch生成しない。

### 3.3 cache生成

- browser-compatibleなMP4/H.264でもhover previewでは原動画shortcutを使わず、上記start/endの短尺proxyを生成・再利用する。
- outputはH.264 MP4、audioなし、`+faststart`、既存480p上限を維持する。
- 同時ffmpeg変換は既存どおり1本に制限する。
- 保存先はStage 4で確定済みの `<WORKBENCH_HOME>/datasets/<dataset-id>/cache/previews/`。
- cache keyは少なくともdataset内video identityに加え、preview policy versionを区別できるようにする。clip長/開始規則を変更した後に旧cacheを誤利用しないこと。
- pruningは既存512 MiB上限を維持する。容量変更は実測Evidenceなしに行わない。
- cacheは削除・再生成可能であり、favorite/folder/Prompt/run artifactを削除しない。

## 4. Google Cloud Translation契約

### 4.1 provider

表示用英日翻訳providerをArgos Translateから **Google Cloud Translation - Basic API v2** へ変更する。

選定理由:

- 今回必要なのは英語plain textから日本語plain textへの表示翻訳であり、glossary/document/custom model等は不要。
- Basic v2はAPI keyによる認証をサポートする。
- Advanced v3固有機能は現scopeでは不要。

API endpointはGoogle Cloud Translation Basic v2のtext translationを用い、source=`en`、target=`ja`、format=`text`、modelは標準NMT相当を使う。

### 4.2 credential

- API keyは環境変数 `GOOGLE_CLOUD_TRANSLATION_API_KEY` から読む。
- keyはGit repository、`WORKBENCH_HOME`、run artifact、browser response、logへ保存しない。
- HTTP requestではkeyをURL queryへ埋め込まず、`x-goog-api-key` headerで送る。
- key未設定・API無効・quota/HTTP失敗時は翻訳機能だけをunavailable/error表示とし、Dataset Browserや推論自体を失敗させない。
- unit/browser testは実Google API・課金を呼ばず、injectable fake backend/HTTP transportで検証する。

### 4.3 generic display translation

現行の「質問+選択肢専用」翻訳境界を、後続Stage 6/7からも使える**表示専用generic text translator**へ整理する。

必須操作:

- 1件または複数の英語textを日本語へ翻訳。
- provider/statusを取得。
- translation cacheを先に参照し、cache hit時はGoogle APIを呼ばない。
- 原文は常に保持し、翻訳結果をcanonical Prompt、dataset annotation、model output、run artifactへ上書きしない。

質問翻訳APIは既存UI互換を保ってもよいが、内部ではgeneric translatorを使う。

### 4.4 cache

- Dataset QA翻訳は既存のDataset別 `datasets/<dataset-id>/cache/translations.sqlite3` を維持する。
- Prompt Library等Datasetに属さない表示翻訳のため、`WORKBENCH_HOME/app/cache/translations.sqlite3` 相当のshared display cacheを追加してよい。path解決は`StoragePaths/UserDataService`へ集約し、Web codeが直接pathを構築しない。
- cache keyはprovider識別子、provider contract version、source language、target language、原文textを含むdigestとする。
- cache削除で正本データは失われない。

## 5. Dataset QA表示

Question IDは表示から外す。

変更後:

```text
質問文

1. 選択肢
2. 選択肢
3. 選択肢
4. 選択肢
```

維持:

- `question_id`はDataset adapter、selection state、URL、run設定、artifact、正解との対応に内部利用する。
- Question IDをannotationやAPI contractから削除しない。
- 「日本語訳 / 原文」buttonは維持し、Google translatorへ接続する。

## 6. 対象外

- 動画のoptical flow等を使った「最も動く場面」の自動探索。
- previewのbatch precompute。
- preview cache容量の実測なし拡大。
- Dataset本体・動画原本の変更。
- Prompt UI、推論設定UI、結果表示の大改修（Stage 6/7）。
- Agent Promptや推論入力を日本語へ置換すること。
- Google Translation Advanced v3、glossary、custom model。
- 実Qwen/GPU run。

## 7. Compatibility

- Stage 4の`WORKBENCH_HOME`とDataset別storage契約を維持する。
- cacheは再生成可能stateのまま。
- dataset annotationは英語正本のまま。
- translation failureで英語表示は継続できる。
- existing run artifact schemaは変更しない。
- Question IDは内部contractに残す。
- current hover pointer behavior（enterですぐrequest）は維持する。

## 8. Success Criteria

1. 120秒動画でpreview cache miss時、開始60秒・約15秒のH.264 previewがDataset別cacheへ生成される。
2. 70秒動画では上記式に従い開始位置が前へずれ、終端5秒を可能な範囲で避ける。
3. 15秒以下の動画で範囲外seekせずpreviewできる。
4. browser-compatible H.264 MP4でも長尺原動画そのものをhover preview responseとして返さない。
5. 同一policy/videoの2回目hoverは既存cacheを使いffmpegを再実行しない。
6. hover開始に意図的なdebounceが入らない。
7. preview cacheはDataset A/Bで分離される。
8. Google API key未設定時、翻訳buttonは利用不可理由を示すがDataset Browserは動作する。
9. fake Google backendで質問・選択肢英日訳、cache hit、API failure fallbackを検証できる。
10. API keyがartifact/log/responseへ露出しない。
11. QA visual textからQuestion IDが消え、内部selection/runでは同じIDを使う。
12. Fake/API/browser/compile等の短時間検証が通る。実Google API・GPU・長尺全件runは必須検証にしない。

## 9. Ambiguity Gate

blocking:
- なし。2026-10-01、ユーザーは壁打ち終了を明示し、これまでの会話内容からspecを作って実装へ渡すよう指示した。Previewは「60秒付近から10–20秒」「hover直後に再生要求」、Google翻訳、Question ID非表示を採用済みである。

non-blocking:
- preview policy versionの内部文字列。
- cache file名/hash helper。
- Google REST transportの内部class/function名。
- loading表示のCSS詳細。
- generic translation API route名。既存API互換を保ち、Stage 6/7が再利用できれば既存styleに合わせる。

## 10. Implementation Steps

Stage branch名の推奨: `stage-5-browser-preview-google-translation`。

1. Preview policy/cache
   - start/end計算helper。
   - browser-compatible shortcutをhover proxy cacheへ置換。
   - policy-aware cache key、Range、prune、Semaphore非回帰。
   - unit/media tests。
2. Google display translator
   - Argos dependency/pathをGoogle Basic v2へ置換。
   - secret-safe credential、generic text translation、cache。
   - fake transport unit/API tests。
3. Dataset Browser polish
   - QA ID非表示。
   - Google翻訳button接続。
   - hover UI/browser regression。
4. Stage 5 regression
   - Fake Dataset、temp WORKBENCH_HOME、compile/import、関連pytest。
   - 実Google API、実Qwen/GPU、model downloadは行わない。

Git操作（branch/commit/merge/push/PR）はこのspec作成依頼から自動承認されたものではない。実装者は適用中のユーザー指示に明示許可がある範囲だけ実行する。Git Graphを作る場合は従来方針どおりStep→Stage、Stage→mainともfast-forwardを避けるが、merge自体の許可は別途必要。

## 11. Gate

2026-10-01、Workbench Stage 4がGitHub `main@b868f4431e69d783632476752d3f41311a52b53a`へmerge/push済みであることを確認した。

同日、ユーザーは「壁打ちは終わりました。今までの会話データからspecsを作成し、それを実装させるプロンプトを作成」と指示した。直前までにPreview尺・開始意図・hover即時性・Google翻訳・Question ID非表示について方向性を確定しており、blockingな未決事項はないため本書を`approved`とする。

## 12. Implementation Handoff

- approved spec: 本書
- 実装目的: Dataset Browserのpreviewを60秒付近から15秒のDataset別cacheへ変え、Google Cloud Translation Basic v2による再利用可能な表示翻訳を導入し、QA表示からQuestion IDを外す。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `b868f4431e69d783632476752d3f41311a52b53a`
- 変更scope: Section 3–5、Section 10。
- 対象外・維持条件: Section 6–7。
- success criteria: Section 8。
- 許可されている短時間検証: fake transport、media/unit、API/browser、temp WORKBENCH_HOME、compile/import、diff check。
- 長時間run/外部課金の許可状態: 未許可。実Google API呼出し、実Qwen/GPU、長尺全件run、model downloadを開始しない。
- Git操作: 別途明示許可が必要。
- 未検証予定: 実Google APIの課金環境での疎通、実HDD上の体感latency、実Qwen/GPU。
