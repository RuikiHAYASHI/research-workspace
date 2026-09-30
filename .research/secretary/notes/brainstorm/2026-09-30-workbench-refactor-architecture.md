---
date: 2026-09-30
project: agentic-streaming-videoqa
source_todo: null
topic: workbench-refactor-architecture
status: exploratory
tags: [brainstorm, refactor, architecture, workbench, prompt, artifact]
---

# Workbench現行構成の理解とリファクタ候補

## 2026-09-30 17:39 JST 現在地

ユーザーはvideo_clip・Situation/Memory/Answer・text memoryの実装完了後、サーバーが現在使えないため実動作確認はせず、まず現在コードのディレクトリ構成、各責務、prompt/output形式を理解してからリファクタリングを検討したい。

確認したGitHub正本:
- `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench@main`
- HEAD `2b5f8309ed380951d812c3f2191f57ce30fb7ccd`
- Company spec `2026-09-30-workbench-agent-modes-and-readable-memory-spec.md` は `implemented`
- Company記録では181 tests/compile/diff checkまで完了。実Qwen/GPU/LongVideoBench実データは未検証。
- 現在サーバーを起動しての再確認は行っていないため、以下はGitHub mainの静的読解を根拠とする。

## 現行レイヤ

- `core/`: 共通dataclass、Protocol、registry、設定/prompt変数のvalidation。
- `config/`: YAML recipe/profile、prompt ID、modeごとのprompt解決、stage別generation。
- `dataset/`: LongVideoBench/Fakeの質問・catalog・検索・閲覧metadata。
- `reader/`: sequential_loaderをWorkbenchの`FrameSample/VideoWindow`へ変換し、reader modeを隠蔽。
- `sampling/`: full_rgb系で使うfirst-after-targetのtime-grid window構築。
- `agent/`: Situation/Memory/Answer、pipeline orchestration、出力JSON validation、memory budget。
- `model/`: ModelAdapter実装。Qwen3-VLのimage_list/video_clip経路とFake model。
- `records/`: run単位のJSON/JSONL保存、status、append-only memory、human-readable projection。
- `interfaces/`: CLI/HTTP server/session/browser/library(SQLite)/media/translation。
- `web/`: static frontend。
- repository rootの`prompts/en/`: prompt asset。legacyとvideo v1が共存。
- `configs/`: profile/recipe。
- `tests/`: unit/acceptance/UI。
- `docs/`: 現行運用説明。

## 主要データフロー

`Web/CLI -> settings resolver -> dataset QuestionSample -> reader VideoWindow -> Situation -> validation -> Memory -> validation -> records -> 次window -> EOF Answer -> records -> GET human view`。

video_clipでは選択済みRGB frameだけを`ModelRequest.video_frames`として1本のvideoへ渡し、`sample_fps = frame_count/window_seconds`、processorには`frames_indices=0..N-1`, `do_sample_frames=False`。元動画上のsource frame ID/actual timestampはQwen内部metadataではなくprompt manifestと`chunks.jsonl`を正本として保持。

## prompt/output

video prompt:
- `chunk_understanding_video_v1.txt`: question/window/frame manifest + video、過去memoryなし。
- `chunk_understanding_video_with_memory_v1.txt`: 上記 + previous validated narrative。
- `evidence_aggregation_video_v1.txt`: validated Situation + previous narrative + frame manifest。
- `final_answer_video_v1.txt`: question/choices + validated memory context、EOFのみ。

Situation output:
`{window_summary, observations, unresolved}`。observationsはevent/state単位で、各要素は`start_seconds,end_seconds,description,evidence_frame_indices,question_relevance,certainty`。frame数との同数制約なし。

Memory output:
`{events,narrative,unresolved}`。eventは`event_id,start_seconds,end_seconds,description,evidence_frame_indices,certainty,importance_reasons,importance_explanation`。

Answer output:
`{answer,evidence_event_ids,evidence_frame_indices,evidence_timestamps_seconds,narrative_version}`。video modeでは選択肢本文、event/frame/timestamp/versionまで検証。全windowでevent 0件ならAnswerを呼ばず`insufficient_evidence`。

主artifact:
`execution_settings.json`, `resolved_prompts.json`, `run_status.json`, `chunks.jsonl`, `stages.jsonl`, `memory.jsonl`, `memory.json`, `turns.jsonl`, `final_answer.json`。
`memory.jsonl`がappend-onlyの記憶正本、人間用timelineは`RunRecord.readable_memory()`で`chunks.jsonl + memory.jsonl`からGET時に決定生成。

## リファクタ候補（未採用）

1. **最優先候補: `agent/pipeline.py`の分割**  
   現在556行で、stage実行関数、3 Agent wrapper、AgentTeam、orchestration、mode分岐、validation、record更新が同居。  
   候補: `agents.py`（3役割）、`orchestrator.py`（window/EOF state machine）、`stage_runner.py`（prompt/model call）、schema/validatorは現行別module維持。

2. **`interfaces/server.py`の分割**  
   約937行でTurnSession、ServerContext、HTTP handler、browser/library/media/translation routeを抱える。  
   候補: `sessions.py`, `run_service.py`, `http.py`。Web/API外部契約を変えず内部のみ分離。

3. **legacy image_list と video_clip schemaの責務分離**  
   `observations.py`/`events.py`に旧・新validatorが同居し、pipeline/configにmode分岐が散る。  
   候補: schema名を型/codec単位にまとめ、mode→schema/prompt/model payloadを一つのstrategy/contractへ集約。ただし過度な抽象化は避ける。

4. **prompt resolutionの分離**  
   `config/loader.py`がYAML解決に加え、mode/contextからprompt IDを書き換える。将来prompt CRUD/Agent別modelを入れると肥大化しやすい。  
   候補: `prompt_registry.py`またはPromptPresetResolverを分離。現行runのresolved prompt/hash互換が必須。

5. **`records/run.py`のread/write/view分離**  
   約547行でstatus/write/read/context/human projectionが同居。  
   候補: writer/read model/projectionを内部moduleへ分割。ただしartifact file formatは変更しない。

6. **frontend `web/app.js`分割**  
   約652行。settings/prompt/run polling/turn render/memory renderを分ける。将来prompt管理画面を追加する前に有効。

### 保留

- AgentごとのModelAdapterをすぐ別instance化するrefactorは、研究上のper-Agent model選択仕様とGPU lifecycleを先に決める必要があり、単なる整理としては触らない。
- prompt/output schemaの名前変更やartifact形式変更は再現性・旧run閲覧を壊すので、まず内部コード分割とtest維持を優先。
- `reader/`と`sampling/`の統合は、target_onlyがsequential_loader側のTargetFrameStreamを使い、full_rgbがWorkbench側samplingを使うため、現在は境界として意味がある。単にファイル数削減目的では統合しない。

## 次に比較したいrefactor軸

- 理解しやすさ: 1ファイルの責務数、Agentの入力→出力が追えるか。
- 研究変更耐性: prompt/schema/modelをAgent単位で差し替えやすいか。
- 互換性: 既存run artifact/API/UIを無変更で読めるか。
- test容易性: model callなしでstage/orchestrator/recordを独立検証できるか。
- 差分サイズ: 一回のrefactorで機能変更を混ぜないか。

現時点の第一候補は、**pipeline.pyをAgent実装とorchestratorへ分割 → server.pyをsession/service/HTTPへ分割**の順。prompt CRUD/Agent別modelなどの機能追加は、その後に別specで進める方が安全。
