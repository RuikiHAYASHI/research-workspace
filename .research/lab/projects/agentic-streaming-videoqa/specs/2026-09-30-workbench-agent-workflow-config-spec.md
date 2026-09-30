---
date: 2026-09-30
project: agentic-streaming-videoqa
type: implementation
status: draft
sequence: 2
sequence_total: 4
baseline_repository: RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench
baseline_ref: main
baseline_commit: 2b5f8309ed380951d812c3f2191f57ce30fb7ccd
depends_on:
  - 2026-09-30-workbench-package-service-workflow-refactor-spec.md
source_brainstorm:
  - 2026-09-30-workbench-refactor-architecture.md
---

# Workbench Agent / Workflow Config 再設計 spec

## 1. 目的

現在はprofile/recipe/Python定数に設定責務が分散し、`video_clip`時のprompt IDやstage別生成上限がPythonコードで強制差替えされる。そのためYAMLを読んでも実際のAgent設定が分からない。

このspecでは**ユーザーが将来ブラウザから変更したい設定をConfigへ集約し、Python内部でprompt/model/generation等の実験設定を決めない**構造へ変更する。

## 2. 原則

- Canonical defaultはConfigファイルに置く。
- Python内にuser-selectableなprompt ID、model ID、generation値、window/frame条件をhard-codeしない。
- Python側defaultを許すのは、legacy artifact読取・schemaの安全なfallback・Config fileが存在しないことを明示エラーにするための最低限だけ。
- runtime/browser overrideはConfigServiceでdefaultへ重ね、resolved settingsをRunにsnapshot保存する。
- prompt本文はConfigへ書かず、logical `prompt_id`だけを指定する。
- modeに応じてPythonがprompt IDを勝手に差し替えない。不整合はvalidation errorにする。

## 3. 新しいDefault Config

canonical default例:

```yaml
dataset:
  adapter: longvideobench
  data_root_name: longvideobench

streaming:
  window_seconds: 4
  frames_per_window: 8
  reader_mode: target_only
  visual_input_mode: video_clip
  decoder_frames_per_sample: 16

memory:
  observation_context_mode: none
  memory_budget_tokens: 6000

agents:
  situation:
    backend: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: situation.video.initial
    enabled: true
    generation:
      max_new_tokens: 1024
      temperature: 0.0

  memory:
    backend: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: memory.video.initial
    enabled: true
    generation:
      max_new_tokens: 768
      temperature: 0.0

  answer:
    backend: qwen3_vl
    model_id: Qwen/Qwen3-VL-4B-Instruct
    prompt_id: answer.video.initial
    enabled: true
    generation:
      max_new_tokens: 384
      temperature: 0.0
```

question/video selectionはDataset BrowserやCLIのruntime inputであり、default Configへ特定question IDを固定しない。

## 4. ConfigService

`ConfigService`を外部窓口とし、次だけを担当する。

1. canonical default YAMLを読む。
2. CLI/Web runtime overrideをschema validation付きで適用する。
3. PromptServiceまたはStage 3までのprompt registryへ`prompt_id`の存在とrole互換性を問い合わせる。
4. AgentServiceが使うresolved Agent設定を返す。
5. Run開始時にresolved settings/hashをRecordServiceへ渡す。

ConfigServiceはmodelをloadせず、prompt本文を編集せず、runを開始しない。

## 5. YAMLからPromptを選択可能にする

各Agentの`prompt_id`はYAMLの値をそのままlogical IDとして解決する。

禁止:
- `visual_input_mode == video_clip`ならPython dictでprompt IDを強制置換。
- `previous_text`ならPython側で特定filenameへ強制置換。

代わりにPrompt metadataが例えば`role=situation`, `visual_input=video`, `context=previous_text|none`, `output_schema=window_observation_v1`を持ち、ConfigService/PromptServiceが互換性をvalidationする。

Stage 3導入前は現built-in promptのlogical ID mappingをConfig層に置いてよいが、Pythonのmode条件分岐で選ばない。

## 6. Browser設定への将来接続

WebはConfig file自体を直接編集しない。API経由でruntime overrideを送り、ConfigServiceがresolved configを作る。

将来ブラウザで選択可能にする項目:
- Agentごとのbackend/model ID。
- Agentごとのprompt ID。
- Agentごとのgeneration。
- window seconds / frames per window。
- reader / visual input / observation context mode。
- memory budget。

Configのdefaultは「新規runを開いたときの初期値」。ブラウザ変更はRun単位のoverrideであり、default Configを自動上書きしない。

## 7. Compatibility

- 既存Runは`execution_settings.json`とresolved prompt snapshotから復元できること。
- 旧artifactに新Config schemaを後付けしない。
- repository内の既存profile/recipeは新schemaへ移行する。
- 外部でユーザーが独自作成した旧recipe YAMLについては**このspecでは互換保証しない**。必要性が確認された場合のみconverterを追加する。
- APIの既存runtime payloadはStage 1で維持し、Stage 2で新Config項目へmappingする。公開fieldを削除する場合はbrowser/CLIを同一microで更新する。

## 8. 変更しないもの

- Agentの推論順序・prompt本文・output JSON。
- Qwen video input。
- Records/Persistence。
- Prompt CRUD（Stage 3）。
- Dataset user data layout（Stage 4）。
- early answer。

## 9. Python hard-code監査

実装完了時に少なくとも次がConfigへ移動していること:
- `VIDEO_GENERATION_LIMITS`相当の1024/768/384。
- default model ID。
- built-in Agentごとのdefault prompt ID。
- new runのvisual/context/reader default。
- window/frame/memory budget default。

Pythonに残せるもの:
- enum/許容値。
- legacy field欠損時の互換default。ただし既存Runの意味を変えないもの。
- protocol/schemaの構造default。
- port等、このspec対象外のapplication operational default。

## 10. Success Criteria

- 1つのdefault Configを読むだけで3 Agentのmodel/prompt/generationとWorkflow sampling条件が分かる。
- YAMLでSituation/Memory/Answerのprompt IDを選択でき、Pythonが別promptへsilent差替えしない。
- 不整合prompt/model capabilityはrun開始前に明示validation error。
- Web/CLI/Fakeの既存挙動が新ConfigService経由で再現できる。
- resolved Configとprompt ID/hashがRunへ保存される。
- Config変更だけでAgentごとのgeneration値を変更できる。
- unit/Fake/compileで検証し、GPUは不要。

## 11. Ambiguity Gate

blocking:
1. **旧外部recipe YAML互換**: このspecはrepository同梱Configだけ移行し、外部独自旧YAMLは非互換としてよいか。推奨: よい。現在の研究コードを単純化し、既存Runはsnapshotで読めるため。

non-blocking:
- Config filenameを`default.yaml`か`workbench.yaml`にするか。
- YAML内部の`memory`を`workflow.memory`へネストするか。読みやすさを優先し過度に深くしない。

## 12. Implementation Steps / Git Strategy

Stage 2も、Stage 1と同じく**Stage branch → Step branch → micro-step commit**で進める。

- Stage branch: `stage-2-agent-workflow-config`
- Step branchは現在のStage branch HEADから作成する。
- Step完了後、対象testを通してmicro commitsをsquashせずStage branchへ**`--no-ff`でlocal merge**する。fast-forwardでStep branchのlaneを潰さない。
- push/PR/Stage→main mergeは別許可。

実装step:

1. `stage2-step01-config-schema-service`
   - canonical default YAMLとConfigService、schema validation。
2. `stage2-step02-agent-config-resolution`
   - Agentごとのmodel/prompt/generation解決とPython hard-code除去。
3. `stage2-step03-runtime-entrypoint-mapping`
   - Web/CLI runtime overrideを新ConfigServiceへ接続。
4. `stage2-step04-legacy-run-compat`
   - 既存Run snapshot復元とrepository同梱旧profile/recipe移行。
5. `stage2-step05-regression`
   - Config/Fake/API/CLI/compile回帰とhard-code監査。

各Step branch内では、独立して説明・検証できる最小変更ごとにcommitする。例: default YAML追加、ConfigService reader追加、prompt silent差替え除去、stage generation定数除去、API mapping更新をそれぞれ別commitにする。squashしない。

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

## 13. Gate

本書は`draft`。Stage 1 implemented後、blocking 1を承認してからapprovedへ上げる。
