---
date: 2026-09-30
project: agentic-streaming-videoqa
type: implementation
status: draft
sequence: 3
sequence_total: 4
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 2b5f8309ed380951d812c3f2191f57ce30fb7ccd
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
- 旧runtime textarea overrideを維持する必要はない。Prompt CRUDへ置き換える場合、直接本文overrideのAPIは明示deprecateして同一UIから利用しない。
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
1. 旧「本文をその場で直接textarea上書きしてRun」の機能を残すか。推奨: 通常UIからは廃止し、編集は必ずversion付きPromptとして保存する。再現性とUI単純化のため。

non-blocking:
- Prompt IDをUUIDにするかslug+UUIDにするか。人間向けtitleとは分離する。
- archive一覧のUI位置。

## 11. Gate

本書は`draft`。Stage 2 implemented後、blocking 1を承認してからapprovedへ上げる。
