---
date: 2026-10-06
project: agentic-streaming-videoqa
source_todo: "Situation / Memory / Answer Agentの責務・入出力・JSON形式・根拠データフローを整理する"
topic: three-agent-contract-simplification
status: exploratory
tags: [brainstorm, research, agent, streaming-videoqa, workbench]
---

# 3 Agent入出力・責務の簡略化

## 2026-10-06 21:10 JST 時点の整理

### 出発点

現行WorkbenchのSituation / Memory / Answer Agentは、Evidence frame、certainty、unresolved、event ledger、timestamp、narrative version等を扱い、初期実装として責務とI/Oが複雑になっている。

今回の壁打ちでは、まず最小のStreaming VideoQA baselineとして各Agentの責務を分離し、Qwenに既知metadataや不要な構造化JSONを生成させない方向を検討した。

## 現在の有力方向

### 1. Situation Agent

責務:
- 現在windowの映像を見て、純粋な状況説明を作る。
- Question / Choices / 過去Memory / Evidence選択を扱わない。

入力候補:
- `video_frames`
- `prompt`
- `sample_fps`
- `generation`

Qwen出力候補:
- plain textの `situation_description`

Backend:
- `window_index`
- `start_seconds`
- `end_seconds`
等の既知metadataとSituation出力を対応付けて保存する。

### 2. Memory AgentをSummary Agentへ簡略化

責務:
- 直前までの要約と現在windowのSituation descriptionを統合し、累積要約を更新する。
- Question / Choices / certainty / answer readiness / Evidence選択 / event listを扱わない。

入力候補:
- `previous_summary`
- `situation_description`
- `prompt`
- `generation`

Qwen出力候補:
- plain textの `summary`

データフロー:
```text
summary(t-1) -> previous_summary
situation_description(t)
        ↓
    Summary Agent
        ↓
      summary(t)
```

### 3. Answer Agent

初期baselineでは動画EOF後に1回だけ実行する。

責務:
- Question / Choices / 最終summaryを用いて最終回答を選ぶ。
- 動画frameを再観測しない。
- 初期構成ではanswer readiness判断を行わない。

入力候補:
- `question`
- `choices`
- `summary`
- `prompt`
- `generation`

Qwen出力候補:
- plain textの `answer`
- 例: `2. He puts the glass on the table.`

Backend:
- 選択肢番号と本文の一致等、決定的に検査できるものはコード側で検証する。

## 最小データフロー

```text
video window
    ↓
Situation Agent
    ↓
situation_description
    ↓
Summary Agent  ← previous_summary
    ↓
summary
    ↓
(next window)

...

EOF
    ↓
Question + Choices + final summary
    ↓
Answer Agent
    ↓
answer
```

## 現行設計から削除候補となったもの

初期baselineではQwen生成契約から以下を外す方向が有力。

- Situation:
  - `window_summary`
  - `observations[]`
  - `evidence_frame_indices`
  - `question_relevance`
  - `certainty`
  - `unresolved`
- Memory:
  - `events[]`
  - `event_id`
  - `importance_reasons`
  - `importance_explanation`
  - `certainty`
  - `unresolved`
  - `narrative`という名称（`summary`へ整理候補）
- Answer:
  - `evidence_event_ids`
  - `evidence_frame_indices`
  - `evidence_timestamps_seconds`
  - `narrative_version`

## Backendに残すべき情報

モデルから削除しても、再現性・デバッグ・時系列追跡のためBackendでは少なくとも以下を保存する候補。

- window index
- window start / end
- Situationの`situation_description`
- 各window後の`summary`
- 最終`answer`
- prompt snapshot
- generation settings
- model information
- elapsed time

特にSituation descriptionはwindow時刻と対応付けて履歴として残せば、Summaryが絶対時刻を文章中に保持しなくても元の時系列情報をBackend側に保持できる。

## 未決事項

1. Situation descriptionの適切な生成token数。
2. window長・sampling量とSituationの情報落ち。
3. Summaryの最大長、圧縮方法、長時間での古い情報消失。
4. SummaryだけをAnswerへ渡すbaselineで十分か。必要ならSituation履歴retrievalを後から追加する。
5. 内部class / StageName / artifact schemaまでSituation / Summary / Answerの名前へ合わせてrenameするか。
6. eventを削除した場合の現行`event_count == 0 -> insufficient_evidence`判定の置換。
7. 現行Answer validatorのEvidence chainをどこまで削除し、最小回答形式をどう検証するか。
8. 既存run / prompt snapshot / UI表示の後方互換。
9. 将来的な回答タイミング比較:
   - EOF-only Answer
   - Answer Agent自身による WAIT / ANSWER
   - 専用Readiness Agent

## 研究上の位置付け

EOF-onlyを最小baselineとして実装し、早期回答・readiness判断は後続比較候補とする。
将来的には「いつ回答するか」「全選択肢の状態が十分確定したか」を扱う研究案とのablationへ接続できる。

## 次のアクション候補

- この探索案を現行コードとの差分に落とし込み、削除・rename・保存契約・互換性を洗い出す。
- 実装へ進める場合はresearch-specでGateを通し、micro-step単位の実装計画を作成する。
- その前後でSituation / Summaryのtoken budget、Summary圧縮方針を最低限決める。
