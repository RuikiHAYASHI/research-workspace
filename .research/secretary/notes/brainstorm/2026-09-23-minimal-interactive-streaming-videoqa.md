---
date: 2026-09-23
project: agentic-streaming-videoqa
source_todo: "2026-09-18 MTG: 操作可能なAgentデモと、長尺動画を逐次処理する2--3段階Streaming VideoQAを試作する"
topic: minimal-interactive-streaming-videoqa
status: exploratory
tags: [brainstorm, research, streaming-videoqa, agent, demo]
---

# 今週の最小操作可能 Streaming VideoQA の考察

## 出発点と読み込んだEvidence

- 2026-09-18 MTGでは、ボタン操作でAgentを起動し、段階ごとのpromptと入力条件を変えて結果を確認する最小デモ、および長尺動画を区間ごとにQwenへ渡して最終回答を得る2--3段階pipelineが次の実装対象とされた。
- 既存EgoCross Agentは、`current image -> observation -> text-only policy -> deterministic reducer -> next text state`を実装済みで、短い実Qwen traceで経路だけを確認している。最終QAや性能評価は未実施である。
- 既存Streaming Text Memory pipelineは、`sequential_loader`から1 frameずつ因果的に取り出し、text memoryを更新してEOF後にfinal answerを生成する実装まで成立している。一方、実Qwen / 実データsmokeと長尺での有効性は未検証である。
- 既存trace viewerのdraftはread-only artifact閲覧を対象としているため、操作から推論を開始する機能とは責務が異なる。

## 中心となる問い

長尺の逐次入力でfuture情報を混入させず、かつ利用者がstageごとのprompt・区間長・出力を比較できる最小システムを、研究上の比較可能性を失わずにどう作るか。

## 有力な全体構成

画面と推論を分離し、run artifactを境界にする。

```text
操作UI
  -> run configをsnapshot
  -> 同期的なPython pipelineを1 runとして起動
  -> immutable artifactを保存
  -> UIがrun status / stage outputを読む

dataset selection -> sequential chunk analysis -> rolling aggregation -> final answer
```

ここで「同期的」はAgent stagesがPython process内で順に完了することを指す。UIはrun開始後にstatusをpollしてよいが、複数サーバやAgent間の非同期通信、queue、node graphは導入しない。

## 推論pipeline候補

### 採用候補: 3段階（長尺の基本形）

1. **入力計画**: dataset / video / question / chunk長 / sampling規則から、先頭順のchunk境界を決める。これはLLM stageではなく、再現可能な設定解決として扱う。
2. **Chunk analysis**: `sequential_loader`でchunkを順に読み、当該chunk内の画像だけとquestionからQwenが観測・要約・不確実性を出す。chunk `k` の出力にchunk `k+1`以降を渡さない。
3. **Rolling aggregation + final QA**: `evidence_{k-1}`と`chunk_summary_k`から`evidence_k`を更新する。EOF後にquestionと`evidence_last`から最終回答を作る。

rolling aggregationを入れる利点は、全chunk textを無制限に連結してcontextを溢れさせないことと、時点`k`の回答候補を過去chunkだけで計算できることにある。final answerはEOF後の全過去Evidenceを使うため、offline評価の最終回答としては因果的である。

### 先に通してよい縮約形: 2段階

最初の少数chunk動画では、`chunk analysis -> final QA`として、全chunk summaryを一度だけfinal stageへ渡してよい。これは入出力を追いやすいが、長尺化するとcontext長と重要情報の選別が未解決になる。3段階版と同じartifact schemaを使い、aggregationをidentity（summary列の連結）として実装すれば移行しやすい。

### 既存frame-level Memoryとの関係

既存のframe-level text memoryをこのpipelineへ直ちに埋め込まない。chunk summaryとframe memoryを同時に変えると、失敗時に原因がchunking、prompt、memory updateのどれか区別できないためである。今週はchunk-level evidenceを最小単位とし、frame-level Agentは操作デモの対象として独立に扱う。後から「chunk内でframe-memoryを更新し、その終状態をchunk summaryへ渡す」比較条件として接続できる。

## UIの最小責務

- dataset / video / question、chunk長、sampling、各stageのpromptを入力できる。
- 実行前に設定を一つのrun configとして表示・確定し、実行後に編集しても過去runの条件は変わらない。
- `Run`で1つのPython processを開始し、stageごとの状態（queued/running/succeeded/failed）と既に保存された出力を表示する。
- stage output、chunk番号・時刻範囲、prompt version、入力設定、errorをrun artifactから表示する。ブラウザがQwenへ直接入力したり、既存artifactを上書きしたりしない。

最初はlocal loopback serverの`POST /runs`、`GET /runs/<id>`程度で足りる。起動するprocessは同期的なCLIとし、serverはrunの状態とartifactを仲介するだけに留める。read-only trace viewerを改造するかは保留とし、UIの実行責務がviewerのread-only契約を壊さないよう別endpoint / 別画面にする。

## 最低限固定したいartifact契約

- `run_config.json`: dataset / sequence ID / question / resolved chunk boundaries / sampling / model ID / prompt本文またはhash / code revision。
- `chunks.jsonl`: chunk ID、開始・終了時刻、実際に使ったframe index・timestamp、chunk prompt version、summary、uncertainty、error、処理時間。
- `aggregation.jsonl`: chunk ID、直前evidence、現在chunk summary、更新後evidence、aggregation prompt version。
- `final_answer.json`: answer、根拠にしたchunk ID、final prompt version、入力evidenceのhash。
- `run_status.json`: stageごとの開始・終了・失敗理由。すべて新規run directoryへ保存し、resumeや暗黙の上書きはしない。

特にpromptを編集可能にするなら、画面上の表示だけでなく、実行したprompt本文またはcontent hashをartifactに残す必要がある。そうしないと、prompt engineeringの結果比較が再現できない。

## 因果性と評価で注意する点

- 区間を処理する前に動画全体をpreload・均等sampleしない。loaderは先頭から進め、chunkが閉じてからそのchunkの要約を生成する。
- final QAに「全chunk summary」を渡すのはEOF後なら許容されるが、stream途中の回答として表示するなら時点までのsummaryだけを使う。
- chunk内のframe選択（全frame、固定FPS、上限付き一様sampleなど）を曖昧にしない。最小実装では固定FPSまたは明示的な`max_frames_per_chunk`をrun configに残す。
- final回答へ根拠chunk IDを出させると、誤答・hallucinationをchunk出力まで遡って読める。ただし引用IDの正確さ自体は別途検証対象である。
- 同じ動画・question・chunk境界・modelでpromptだけを変えたrunを比較可能にし、chunk境界まで変える比較とは分ける。

## 採用候補・保留・棄却寄り

| 区分 | 内容 | 理由 |
| --- | --- | --- |
| 採用候補 | artifact中心のlocal UI + 同期的Python pipeline | MTGの操作性と単純な実行構成を両立する。 |
| 採用候補 | chunk analysisとrolling aggregationを分ける3段階 | 長尺化時のcontext制約を明示でき、途中Evidenceも検査できる。 |
| 保留 | 既存frame-level Agentをchunk内へ統合 | 研究上は有望だが、初週に複数のMemory設計を同時に変えない。 |
| 保留 | `sequential_loader`のAdapterの改名 | 現行コードの抽象化を確認してから判断する。dataset固有sourceを共通loader APIへ適合させる役割ならGoF Adapterと呼べるが、独立に変化するabstractionとimplementationを分離している場合にのみBridgeが適切である。 |
| 棄却寄り（初週） | node graph UI、分散Agent、live token streaming | 実装量が増え、prompt・chunking・因果入力の検証を遅らせる。 |
| 棄却寄り（初週） | final answerだけを保存する構成 | 中間失敗を診断できず、prompt変更の比較もできない。 |

## 最小の受入確認候補

1. 小さな動画を2 chunkだけ、先頭順に処理できる。
2. `chunks.jsonl`のchunk順・時刻範囲・input frameがconfigと一致し、future chunkを入力に含めない。
3. aggregation recordで前chunkのevidenceだけが引き継がれ、final answerはEOF後に一度だけ生成される。
4. UIからchunk長またはchunk promptを変えた別runを開始でき、両runのconfigとstage outputを並べて確認できる。
5. fake modelで上記の順序・artifact・失敗停止をtestし、実Qwen runは短い明示許可済みの範囲だけで確認する。

## 未決事項

- 最初に接続するdataset / 長尺動画と質問形式。
- chunk内のframe sampling規則、初期chunk長、token上限。
- chunk outputを自由文、構造化JSON、または両方のどれにするか。
- aggregationでEvidenceを固定長に圧縮するか、初回は全summary連結にするか。
- UIを既存read-only viewerに追加するか、run consoleを別画面にするか。

## Research Spec Handoff（未承認）

- 対象プロジェクト: agentic-streaming-videoqa
- 元依頼: 2026-09-18 MTGに基づく、操作可能なAgentデモと2--3段階Streaming VideoQAの考察。
- 採用方向: local UIが設定snapshotとartifact閲覧を担い、同期的Python pipelineがdataset selection、chunk analysis、rolling aggregation、final QAを順に実行する。
- 実装/実験候補: 2 chunkの短い動画でfake modelテストと短時間実Qwen確認を分離する。
- 比較対象・評価指標: 実行順と因果性、artifact完全性、prompt/設定の再現性、中間出力の診断可能性。初週にaccuracy主張はしない。
- 対象外: 分散通信、node UI、live token streaming、長時間GPU評価、frame-level Memoryとの統合。
- 主な未決事項: dataset、chunking / sampling、output schema、Evidence圧縮、UIの配置。
- 関連: `meetings/2026-09-18-mtg.md`、`experiments/2026-09-16-egocross-agent-text-state-smoke.md`、`specs/2026-09-15-streaming-text-memory-spec.md`、`specs/2026-09-18-egocross-trace-viewer-implementation-spec.md`。
