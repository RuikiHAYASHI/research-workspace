---
date: 2026-10-02
last_updated: 2026-10-02
project: agentic-streaming-videoqa
type: implementation
status: approved
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 33bb63ded6ed9a95d72108ed69d1860f618470a4
depends_on:
  - 2026-10-02-workbench-inference-agent-config-metadata-regression-fix-spec.md
---

# Workbench: Dataset未選択時folder API regression fix spec

## 1. 目的

Workbench Browser起動直後、Datasetがまだ選択されていない状態でfolder APIへ空のDataset IDが送られ、

```text
ValueError: dataset idが不正です: ''
```

というserver thread tracebackが発生するregressionを修正する。

Dataset選択前はfolder一覧を空として扱い、Dataset選択後だけDataset別libraryへアクセスする。
Browser初期表示、Dataset別user data分離、folder機能の既存contractは維持する。

## 2. 確認済み原因

基準はWorkbench `main@33bb63ded6ed9a95d72108ed69d1860f618470a4`。

### 2.1 Browser初期化

`src/longvideoqa_workbench/web/browser.js` の `DOMContentLoaded` は現在、

```javascript
await loadTranslationStatus();
await loadFolders();
await loadDatasets();
```

の順に実行する。この時点では `browserState.activeDataset === null`。

### 2.2 空Dataset ID送信

`loadFolders()` はDataset未選択時にもfolder endpointを呼び、queryが `dataset_id=` になる。

### 2.3 Server側

HTTP handlerはquery parameterをそのまま `context.browser.folders(...)` へ渡す。
`BrowserService.folders()` は `dataset_id is None` の場合だけ空配列を返すが、空文字 `""` はDataset IDとして扱い、
`UserDataService.library("") -> StoragePaths.validate_dataset_id("")` でValueErrorになる。

### 2.4 Root cause

Dataset未選択という正常なUI状態を、Client/Server境界で空Dataset IDという不正値へ変換していることが原因である。
LongVideoBench path、WORKBENCH_HOME、OUTPUT_ROOT、Qwen、GPUは本件の原因ではない。

## 3. 修正契約

### 3.1 Client guard

Dataset未選択時、`loadFolders()` はfolder APIへrequestしない。

- folder listは安全なempty stateへ初期化する。
- `activeFolder` はnullを維持する。
- serverへ `dataset_id=` を送らない。
- Dataset選択後は現在どおりDataset固有の `dataset_id` でfolder一覧を取得する。

### 3.2 Server defensive normalization

folder GET endpointまたは `BrowserService.folders()` の適切な既存境界で、missing dataset_id と empty dataset_id を「Dataset未選択」として同じempty resultへ正規化する。

ただし、非空の不正Dataset IDを無条件に握り潰さない。`StoragePaths.validate_dataset_id()` のstrict validation自体は維持する。

### 3.3 Existing Dataset separation

Dataset選択後のfolder CRUD / membershipは、現在のDataset別 `library.sqlite3` を使い続ける。global libraryへ戻さない。

## 4. Compatibility

- Dataset browserのDataset一覧・video一覧。
- Dataset別favorite / alias / recent / folder / membership。
- Stage 4のWORKBENCH_HOME storage contract。
- inference / Prompt / Run UI。
- Config / artifact format。
- LongVideoBench data path。

migrationは不要。

## 5. 対象外

- Qwen model load timingの変更。
- Transformersの `cap_pixels_per_frame` warning対応。
- Qwen processor token policy変更。
- Google翻訳provider変更。
- Dataset BrowserのUX再設計。
- folder schema再設計。
- WORKBENCH_HOME変更。
- 実Qwen/GPU run。

Qwenの `Loading weights` は本件と分離する。plain `serve` はadapter登録のみで、実モデルloadはmodel generate/tokenization経路で行う現在のlazy-load contractを変更しない。

## 6. Success Criteria

1. Browser初期表示でDataset未選択のままfolder APIに `dataset_id=` を送らない。
2. Dataset未選択状態でserver tracebackが発生しない。
3. folder GET endpointへdataset_id未指定でrequestしても200 + empty foldersになる。
4. folder GET endpointへ `dataset_id=` を明示してもserver thread exceptionにならず200 + empty foldersになる。
5. 非空の不正Dataset IDに対するstrict validationは維持する。
6. Dataset選択後は正しいDataset IDでfolder一覧を取得できる。
7. Dataset別folder DB分離を維持する。
8. Browser reload / URL復元時にDataset選択後folder表示が壊れない。
9. 関連Browser/API/storage testsが通る。
10. compile/import、`git diff --check` が通る。
11. 実Qwen/GPU/model download/長時間runを必要としない。

## 7. Ambiguity Gate

### blocking

なし。

### non-blocking

- empty resultのrender方法。
- normalizationをHTTP handlerで行うか `BrowserService.folders()` 内で行うか。

既存styleと最小差分を優先する。

## 8. Implementation Steps / Git Strategy

過去Stage 3/4/8と同じmain / Stage / Step laneを残す。

```text
main
  \
   stage-9-browser-folder-empty-dataset-fix
      \
       stage9-step01-reproduce-empty-dataset-folder-request
      \
       stage9-step02-guard-and-normalize-folder-request
      \
       stage9-step03-browser-folder-regression-audit
```

実装開始時は最新main、local branch/HEAD/dirty stateを再確認する。

### Step 1: regression再現

branch: `stage9-step01-reproduce-empty-dataset-folder-request`

- Dataset未選択時のfolder requestをtest化。
- empty `dataset_id` でserver側が落ちる現状を再現。
- Dataset選択後の正常folder取得testも確認。

候補: `tests/test_browser_api.py`、`tests/test_browser_integration.py`、browser script test。

### Step 2: Client guard + Server normalization

branch: `stage9-step02-guard-and-normalize-folder-request`

- `src/longvideoqa_workbench/web/browser.js`: activeDatasetなしならfolder APIを呼ばない。
- `src/longvideoqa_workbench/entrypoints/server.py` または `browser/service.py`: missing/empty dataset IDはempty folder list。
- 非空invalid IDのvalidationは維持。
- Step 1 testsを恒久regression testへ更新。

### Step 3: regression audit

branch: `stage9-step03-browser-folder-regression-audit`

- Browser初期load。
- Dataset選択。
- folder一覧。
- reload/URL復元。
- Dataset別library分離。
- related pytest。
- compileall。
- `git diff --check`。

実Qwen/GPU/LongVideoBench長時間runは行わない。

### Git rules

- 各Step branchはStage HEADから作る。
- Step branch内は意味のあるmicro-step commit。
- squashしない。
- Step→Stageはlocal `--no-ff`。
- Stage→mainはユーザー確認後に `--no-ff`。
- push/PR/Stage→main mergeは実装時の明示許可に従う。
- `git add .` せず対象fileだけstageする。

## 9. Implementation Handoff

- approved spec: 本書。2026-10-02、ユーザーが2件のregression fixを同一Stageで実装させるプロンプト作成を明示し、実装開始を承認した。
- 実装目的: Dataset未選択時のempty folder requestによるserver tracebackを解消する。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `33bb63ded6ed9a95d72108ed69d1860f618470a4`。着手時に最新mainを再確認。
- 変更scope: Section 3、Section 8。
- 対象外・維持条件: Section 4–5。
- success criteria: Section 6。
- 許可されている短時間検証: Browser/API/storage/Fake tests、compile/import、diff check。
- 長時間runの許可状態: 未許可。
- Git操作: 2026-10-02の共同実装指示により、Stage/Step branch作成、対象fileだけのmicro-step commit、Step→Stageのlocal `--no-ff` mergeは許可済み。remote push、PR、Stage→main mergeは未許可。
- 未検証予定: 実Qwen/GPU、長尺実データ性能。


## Joint Implementation Approval（2026-10-02）

ユーザーは、Dataset未選択時folder API regressionとvideo Situation/Memory `unresolved` schema contract regressionを、**同一の実装Stageでまとめて修正する**よう指示した。

この共同実装では、本書Section 8に記載した単独実装用Stage/Step branch名より、次の共同topologyを優先する。

```text
main
  \
   stage-9-dual-regression-fixes
      \
       stage9-step01-reproduce-dual-regressions
      \
       stage9-step02-fix-browser-folder-empty-dataset
      \
       stage9-step03-fix-video-unresolved-schema-contract
      \
       stage9-step04-dual-regression-audit
```

実装順:

1. 2件のregressionをそれぞれtestで再現・固定する。
2. Browser folder empty-dataset bugをClient guard + Server defensive handlingで修正する。
3. Situation / Memory video Promptの `unresolved` array contractをvalidatorと一致させる。
4. 両specのSuccess CriteriaとStage 6/7/8周辺回帰をまとめて監査する。

Git操作の許可境界:

- Stage branch作成: 許可済み。
- Step branch作成: 許可済み。
- 対象fileのみをstageしたmicro-step commit: 許可済み。
- Step→Stageのlocal `--no-ff` merge: 許可済み。
- remote push: 未許可。
- PR作成: 未許可。
- Stage→main merge: 未許可。共同Stage完了報告後にユーザー確認を待つ。
- 実Qwen/GPU、model download、Google Cloud Translation実API、長尺LongVideoBench run: 未許可。

本共同実装は2件のbug scopeをまとめて運用するだけであり、各specの修正契約・Compatibility・対象外・Success Criteriaは変更しない。
