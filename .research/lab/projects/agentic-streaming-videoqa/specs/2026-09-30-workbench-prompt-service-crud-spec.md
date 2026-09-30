---
date: 2026-09-30
last_updated: 2026-10-01
project: agentic-streaming-videoqa
type: implementation
status: approved
sequence: 3
sequence_total: 4
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: f575cf5a7a2093cbf22e57493a5e9b245a00e4ba
depends_on:
  - 2026-09-30-workbench-agent-workflow-config-spec.md
source_brainstorm:
  - 2026-09-30-workbench-refactor-architecture.md
  - 2026-09-30-workbench-inference-ui-prompt-library-and-qwen-video.md
---

# Workbench PromptService / CRUD / Version 履歴 spec

## 1. 目的

現状は`prompts/en/*.txt`のbuilt-inをallowlistし、Web textareaでRun単位の一時編集はできるが、名前付きPromptの選択・永続作成・編集履歴・削除/archiveがない。

このspecではPromptをAgent設定からlogical IDで選択可能にし、built-inとユーザーPromptを統合して扱う`PromptService`とBrowser UIを実装する。

## 2. Promptの種類

### 2.1 Built-in Prompt

Git管理下。研究コードのdefaultとしてversionedに保存し、通常UIから本文を直接上書きしない。

構造:

```text
prompts/
├── situation/
│   ├── image/
│   │   └── initial/
│   │       ├── prompt.en.txt
│   │       └── metadata.yaml
│   └── video/
│       ├── initial/
│       │   ├── prompt.en.txt
│       │   └── metadata.yaml
│       └── initial-with-memory/
│           ├── prompt.en.txt
│           └── metadata.yaml
├── memory/
│   ├── image/initial/...
│   └── video/initial/...
└── answer/
    ├── image/initial/...
    └── video/initial/...
```

初期prompt metadata:
- title: `最初のプロンプト`
- description: `実装時に作成したプロンプトです`
- language: `en`
- role: situation / memory / answer
- visual/context compatibility
- input_schema / output_schema
- immutable logical ID

### 2.2 User Prompt

Git repositoryではなくWorkbench persistent user-data rootへ保存する。

```text
<WORKBENCH_HOME>/prompts/
├── situation/<prompt-id>/
│   ├── metadata.json
│   └── versions/
│       ├── 0001.txt
│       ├── 0002.txt
│       └── ...
├── memory/...
└── answer/...
```

## 3. PromptService

`PromptService`だけがbuilt-in/user Promptの保存場所を知る。

公開操作:
- list(role, filters)
- get(prompt_id, version=None)
- create(role, title, description, body, metadata)
- create_from_builtin(builtin_id, ...)
- edit(prompt_id, body, title?, description?) -> new immutable version
- archive(prompt_id)
- restore(prompt_id)
- validate_compatibility(prompt_id, agent/workflow settings)
- resolve_for_run(prompt_id) -> body/version/hash/metadata snapshot

他packageはprompt file pathを直接読まない。

## 4. CRUD Semantics

- **Create**: name/title、description、bodyを保存しversion 1作成。
- **Edit**: 既存versionを上書きせず新versionを追加。
- **Delete UI**: 物理削除ではなくarchive。過去Runと履歴を壊さない。
- **Built-in**: archive/delete不可。編集操作はuser Promptへのcopyとして扱う。
- **History**: version番号、created_at、content hashを閲覧可能。
- **Run snapshot**: `resolved_prompts.json`等へlogical ID、version、hash、resolved bodyを保存。Library側を後で編集しても過去Runは変化しない。

## 5. Web UI

各Agent設定カードには大きなtextareaを常時出さず、
- 選択中Promptのtitle
- version
- 短いdescription
- `プロンプトを確認`ボタン
を表示。

Prompt画面で:
- Prompt一覧・検索/role filter。
- 本文確認。
- 選択。
- 新規作成。
- 編集。
- archive。
- version履歴。
- built-in/userの区別。

作成/編集では最初にtitleとdescriptionを入力し、本文editorへ進む。

日本語訳は**このspecでは生成しない**。metadataへlanguageと将来translationを関連付けられるID/hashを持たせ、英語sourceを正本とする。

## 6. Configとの関係

Stage 2 Configの`agents.<role>.prompt_id`はdefault Prompt ID。

Webで別Promptを選択したRunはruntime overrideとしてresolved Configへ反映する。PromptServiceはConfig defaultを書き換えない。

PythonコードはPrompt filenameやdefault Prompt本文をrole/modeでhard-codeしない。

## 7. Compatibility

- 現行8 txtの内容は意味を変えず新built-in directoryへ移行。
- 既存Runの`resolved_prompts.json`/prompt hashは読取可能。
- 旧runtime textarea overrideは通常UIでは廃止する。Prompt本文の変更は必ず名前付きUser Promptとして保存し、編集ごとにimmutable versionを追加する。直接本文overrideのAPIは同一UIから利用せず、必要ならlegacy互換の読取境界だけを残す。
- old Run閲覧はPromptServiceに元Promptが存在しなくてもsnapshotだけで成立する。

## 8. 対象外

- Prompt品質の科学的評価。
- Prompt自動生成。
- Prompt翻訳の自動生成。
- GitHubへuser Promptをcommit。
- dataset別Prompt分離（PromptはAgent/role単位で共通）。
- early answer Prompt。

## 9. Success Criteria

- 3 AgentそれぞれでPromptを一覧から選べる。
- 新規Promptを名前/説明付きで作り、server Ctrl+C→再起動後も残る。
- 編集でversionが増え、旧versionを閲覧できる。
- archive後は通常選択肢から消えるが履歴と過去Runは残る。
- built-in初期Promptに指定title/descriptionが表示される。
- Run snapshotにID/version/hash/bodyが残る。
- invalid role/schema Promptはrun開始前に選択不可または明示エラー。
- Fake/API/browser testsでGPUなし検証。

## 10. Ambiguity Gate

blocking:
- なし。2026-10-01、ユーザーが旧「本文をその場で直接textarea上書きしてRun」機能を通常UIから廃止し、Prompt変更はversion付きで保存する方針を承認した。

non-blocking:
- Prompt IDをUUIDにするかslug+UUIDにするか。人間向けtitleとは分離する。
- archive一覧のUI位置。

## 11. Implementation Steps / Git Strategy

Stage 3は**Stage branch → Step branch → micro-step commit**で進める。

- Stage branch: `stage-3-prompt-service-crud`
- Step branchは現在のStage branch HEADから作成する。
- Step完了後、対象testを通してmicro commitsをsquashせずStage branchへ**`--no-ff`でlocal merge**する。fast-forwardでStep branchのlaneを潰さない。
- push/PR/Stage→main mergeは別許可。

実装step:

1. `stage3-step01-builtin-prompt-layout`
   - built-in prompt directory/metadata再編とPromptService read path。
2. `stage3-step02-user-prompt-storage`
   - user Promptの永続保存、create/edit/version/archive/restore。
3. `stage3-step03-config-run-snapshot`
   - Configとのlogical prompt ID接続、Run snapshot ID/version/hash/body。
4. `stage3-step04-prompt-api-ui`
   - Prompt専用APIと選択/確認/作成/編集/archive/history UI。
5. `stage3-step05-regression`
   - restart永続性、old Run、built-in保護、Fake/API/browser回帰。

各Step branch内では、Prompt metadata、storage、versioning、API、UI等を独立micro-step commitへ分ける。巨大なCRUD一括commitにしない。Step→Stage統合時にsquashしない。

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

2026-10-01、Stage 2がWorkbench `main@f575cf5a7a2093cbf22e57493a5e9b245a00e4ba`で実装済みであることを確認した。

同日、ユーザーが以下を明示承認した。

- 旧「本文をその場で直接textarea上書きしてRun」機能は通常UIから廃止する。
- Prompt本文を変更するときは、名前付きUser Promptとして保存し、編集ごとに新しいimmutable versionを追加する。
- built-in Promptは通常UIから直接上書きせず、編集したい場合はUser Promptへcopyして扱う。
- 過去Runは保存済みPrompt snapshotから再現し、後続のPrompt編集で意味を変えない。

blockingな未決事項は解消したため、本書を`approved`とする。

## 13. Implementation Handoff

- approved spec: 本書
- 実装目的: built-in / User Promptをlogical IDで統合管理するPromptServiceを導入し、3 AgentそれぞれでPromptの選択・作成・version付き編集・archive・履歴確認を可能にする。
- 基準repository/commit: `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main` / `f575cf5a7a2093cbf22e57493a5e9b245a00e4ba`
- 変更scope: Section 2--7およびSection 11のStage 3 Step 1--5。
- 対象外・維持条件: Section 8。特にPrompt品質評価、自動生成、自動翻訳、Dataset別Prompt分離、early answer、実Qwen/GPU挙動は変更しない。
- success criteria: Section 9。
- 許可されている短時間検証: PromptService unit、Fake/API/browser、restart永続性、old Run snapshot互換、compile/import、diff check。
- 長時間runの許可状態: 未許可。実Qwen/GPU/長尺実データrunを開始しない。
- Git操作: Section 11に従いStage/Step branch作成、micro-step commit、Step→Stageのlocal `--no-ff` mergeは許可済み。remote push、PR、Stage→main mergeは未許可。
- 未検証予定: Prompt品質、実Qwen/GPU、長尺実データ上の性能。
