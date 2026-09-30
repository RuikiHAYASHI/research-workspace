---
date: 2026-09-30
last_updated: 2026-10-01
project: agentic-streaming-videoqa
type: implementation
status: draft
sequence: 4
sequence_total: 4
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 4f2546ef4a1dafd2ae2ba157c079d766ed023cb2
depends_on:
  - 2026-09-30-workbench-prompt-service-crud-spec.md
source_brainstorm:
  - 2026-09-30-workbench-refactor-architecture.md
---

# Workbench Dataset別 User Data / Cache Storage spec

## 1. 目的

現状、favorite/alias/recent/folder/translation cacheは単一`library.sqlite3`に保存され、dataset_idで論理分離されている。ユーザーはDataset追加時に状態が絡まないよう、少なくともDataset単位で保存場所を物理分離したい。またcacheもWorkbenchの同じ管理rootで把握できる構成を希望している。

このspecでは**Git repositoryの`src/`やworktreeにmutable user dataを置かず、1つのWorkbench user-data rootの下でdataset別state/cacheを整理する**。

「同じリポジトリ」は、Git管理コードrepositoryにcacheを入れる意味ではなく、**同じWorkbenchデータrootに集約する**と解釈する。Git worktree内にcacheを置くとdirty/untracked、複数worktree競合、誤commitの原因になるため採用しない。

## 2. Workbench Home

環境変数`WORKBENCH_HOME`で明示可能にする。未指定のdefaultは既存方針を継承し:
- `$XDG_DATA_HOME/longvideoqa-workbench`
- 未設定なら`~/.local/share/longvideoqa-workbench`

構造:

```text
<WORKBENCH_HOME>/
├── app/
│   └── settings.json
├── prompts/                    # Stage 3 user Prompt
│   └── ...
└── datasets/
    ├── longvideobench/
    │   ├── library.sqlite3
    │   └── cache/
    │       ├── thumbnails/
    │       ├── previews/
    │       └── translations.sqlite3
    ├── ego4d/
    │   ├── library.sqlite3
    │   └── cache/
    └── <dataset-id>/
        ├── library.sqlite3
        └── cache/
```

Run artifactの`output_root`はこのspecで移動しない。既存`outputs`/明示`--output-root`契約を維持し、scopeをuser Browser state/cacheに限定する。

## 3. Dataset別 Persistent State

各Datasetの`library.sqlite3`へ:
- favorite
- alias
- recent
- folder
- folder membership
を保存。

folderはDataset内の概念とし、Dataset横断folderは作らない。

DB内ではdataset_idを冗長保持してもよいが、path自体がdataset boundaryとなる。実装はmigrationとvalidationが単純になる方を選ぶ。

## 4. Cache

cacheも同じDataset directory内へ置く。ただしpersistent stateと意味を分ける。

- `cache/thumbnails/`: 再生成可能。
- `cache/previews/`: 再生成可能。
- `cache/translations.sqlite3`: 原文から再生成可能な翻訳cache。

cache削除でfavorite/folder/alias/Prompt/Run artifactが失われないこと。

BrowserService/StoragePathsはcache locationを解決し、Web/media codeがpathを直接組み立てない。

## 5. StoragePaths / UserDataService

1つの小さなpath resolverを置く。

例:
- workbench_home()
- dataset_root(dataset_id)
- dataset_library_db(dataset_id)
- dataset_cache_root(dataset_id)
- prompt_root()
- app_settings_path()

directory名はdataset adapterの安定IDから作り、video titleや外部自由文字列をpathへ直接使わない。

## 6. Migration

現行global DB:
`<XDG_DATA_HOME>/longvideoqa-workbench/library.sqlite3`

からDataset別DBへ**copy-only** migrationを行う。旧DBを削除・上書きしない。

要件:
1. preflightで旧DB有無とdataset_idごとの件数をread-only表示。
2. backup不要なcopy-onlyでも、migration前後の件数を記録。
3. videos/folder membershipをdatasetごとにcopy。
4. global folderは各Datasetへ同名folderとして必要なmembership分だけ作る。
5. translation cacheは旧DBから該当Datasetを判別できない現行schemaの場合、無理に移さず再生成cacheとして破棄可能扱い。旧DB自体は残す。
6. migration完了markerを`app/settings.json`等へ保存し二重importを防ぐ。
7. failure時は新DBだけをrollbackし旧DBを正本として残す。

自動silent migrationはしない。CLIまたはBrowserで明示実行し、件数確認後に新layoutへ切り替える。

## 7. CLI / Browser

通常利用ではpathを意識させない。

- Datasetを選択するとBrowserServiceが対応Dataset DB/cacheを自動使用。
- `--library-db`はStage 4後はdebug/test用途に限定するかdeprecate候補。通常は`WORKBENCH_HOME`/dataset IDから解決。
- Fake testsは一時`WORKBENCH_HOME`を指定して実user dataと完全分離。
- serverはforeground/8765/Ctrl+Cのまま。

## 8. 変更しないもの

- Dataset本体の実データpath。
- Run artifact/output root。
- Agent/Workflow。
- Prompt内容。
- Qwen/GPU。
- Dataset Browserのfavorite/folder semantics（Dataset横断folderを除く）。

## 9. Success Criteria

- LongVideoBench/Fake等でfavorite/alias/recent/folderが別SQLiteへ保存される。
- server再起動後も維持。
- Dataset Aのstate変更がDataset B DBを更新しない。
- thumbnail/preview/translation cacheはDataset別cacheだけへ書かれる。
- cacheを削除してもpersistent stateは残る。
- 旧global DBを破壊せず明示migrationでき、件数一致を確認できる。
- test用WORKBENCH_HOMEで実ユーザーデータを触らない。
- code repository/worktreeへmutable cache/user stateを作らない。
- Stage 4完了時にWorkbench repositoryの`README.md`を現行実装へ更新し、少なくとも`WORKBENCH_HOME`、Dataset別persistent state/cache配置、PromptService/Prompt Libraryの現在契約、通常起動・migration導線、旧`--library-db`/旧Prompt直接textarea説明の扱いが実装と一致する。
- README更新では未検証の実Qwen/GPU性能を成功済みとして記載しない。

## 10. Ambiguity Gate

blocking:
1. **cacheをGit repository内へ置くか**: 本specは置かず、同一Workbench user-data rootへ集約する。もしユーザーの「同じリポジトリ」がGit repositoryそのものを意味する場合は承認前に変更が必要。推奨は本spec案。
2. **migration実行方式**: 明示CLI/Browser操作でcopy migrationするか、自動初回migrationするか。本specは安全性から明示操作を推奨。

non-blocking:
- cache DB/file命名。
- migration markerのJSON key名。
- dataset folder ID sanitizerの内部helper。

## 11. Implementation Steps / Git Strategy

Stage 4は**Stage branch → Step branch → micro-step commit**で進める。

- Stage branch: `stage-4-dataset-user-data-storage`
- Step branchは現在のStage branch HEADから作成する。
- Step完了後、対象testを通してmicro commitsをsquashせずStage branchへ**`--no-ff`でlocal merge**する。fast-forwardでStep branchのlaneを潰さない。
- push/PR/Stage→main mergeは別許可。

実装step:

1. `stage4-step01-storage-paths`
   - `WORKBENCH_HOME`、StoragePaths/UserDataService、dataset root解決。
2. `stage4-step02-dataset-library-routing`
   - Dataset別`library.sqlite3`とBrowserService routing。
3. `stage4-step03-dataset-cache-routing`
   - thumbnail/preview/translation cacheのDataset別配置。
4. `stage4-step04-copy-migration`
   - 旧global DBからcopy-only migration、件数検証、rollback/marker。
5. `stage4-step05-cli-browser-regression`
   - migration操作、restart、Dataset間分離、cache削除非回帰、Fake tests。
6. `stage4-step06-readme-finalize`
   - Stage 1--4後の現行構成に合わせてWorkbench `README.md`を更新する。
   - `WORKBENCH_HOME`、Dataset別DB/cache、Prompt Library、canonical Config/runtime override、migration方法、foreground server運用を実装と一致させる。
   - 旧worktree固定手順、旧`prompts/en/*.txt`前提、通常UIでのPrompt本文直接textarea上書き、通常利用でのglobal `--library-db`等、現行実装と食い違う説明は削除または現行契約へ修正する。
   - READMEだけで通常利用の保存先とmigrationの安全境界を理解できることを確認する。

各Step branch内では、path resolver、DB routing、cache routing、migration各table、UI/CLI等を独立micro-step commitへ分ける。migrationとunrelated browser変更を同commitへ混ぜない。README更新も実装完了後の独立Stepとして扱い、実装前の予定を完成済みとして書かない。Step→Stage統合時にsquashしない。

**Stage/Step branch作成とmicro-step commit作成は明示許可済み**。remote push、PR、Stage→main mergeは未許可。

### Git history / commit message convention

- Git Graphで`main / Stage / Step`の関係が分かるよう、Step→Stageは`--no-ff` mergeを使う。
- 将来Stage→mainのmergeが別途承認された場合も`--no-ff`を基本とし、Stage laneを履歴に残す。
- micro-step commitは日本語で、1行目を`Stage N Step M: <変更タイトル>`とする。
- commit本文は空行を挟み、原則として次を記載する。

```text
変更内容:
- ...

理由:
- ...

検証:
- ...
```

必要なら`影響:`を加える。タイトルだけの短いcommit messageは避ける。
- Step merge commitも日本語でタイトル＋本文を残す。
- branchを作っただけでremote pushはしない。GitHubで進捗共有が必要な場合のpushは、その時点の明示指示に従う。

## 12. Gate

2026-10-01、Stage 3がWorkbench `main@4f2546ef4a1dafd2ae2ba157c079d766ed023cb2`で実装済みであることを確認した。

同日、ユーザーがStage 4へ移行する意向と、**Stage 4終了時点でWorkbench `README.md`も現行実装へ更新すること**を明示した。このREADME更新をSection 9のsuccess criteriaおよびSection 11の最終Stepへ追加した。

残るblockingはSection 10の2点のみ。

1. cacheをGit repository/worktree内へ置かず、`WORKBENCH_HOME`配下へ集約するか。
2. 旧global DB migrationを自動初回migrationではなく、CLI/Browserから明示実行するcopy-only migrationとするか。

この2点のユーザー承認後に本書を`approved`へ上げる。
