---
date: 2026-10-13
project: agentic-streaming-videoqa
source_todo: null
topic: StreamAgentに近いオンライン動画Agent研究の一次探索
status: exploratory
tags: [brainstorm, literature-review, streaming-video, memory, agent]
---

# StreamAgentに近いオンライン動画Agent研究の一次探索

## 出発点
StreamAgentの関連研究に一般的なvideo agent論文は存在するが、オンラインで動画を逐次処理するAgent研究が見つけにくいという疑問。

## 結論
動画ストリームの逐次処理を研究設定に含み、Agentによる判断またはMemory管理を扱う論文が2026年に複数存在する。単なる「Agentic VideoQA」と「Online Streaming Video Agent」は区別する。

## 原論文のabstract / HTML本文から確認した候補（2026-10-13）

- EventMemAgent (2026-02-17 / 2026-09-11 v2): event-boundary detection、event-granular sampling、イベント単位のstructured long-term memory、tool選択とRL。https://arxiv.org/abs/2602.15329
- SVMemAgent (2026-09-16): 未知の未来・動画長・質問の下で逐次フレームをdiscard / replaceしてfixed memoryを維持するagent。 https://arxiv.org/abs/2609.18540
- StreamArena / StreamMind (2026-08-06): continuous ingestionとquery-triggered prefix replayを区別。StreamMindはfrontend monitoringとbackend persistent multimodal memoryのmulti-worker構成。 https://arxiv.org/abs/2608.05703
- ThinkStream (2026-03-13): Watch-Think-Speak、逐次推論、回答タイミング判断、reasoning-compressed memory。https://arxiv.org/abs/2603.12938
- R3-Streaming (2026-05-18): memory compression・answer readiness・model routingの段階的制御。https://arxiv.org/abs/2605.17921
- Response-G1 (2026-05-08): streaming chunkからquery-guided scene graphを形成し、memory retrievalとsilence/response判断。https://arxiv.org/abs/2605.07575
- MEMO (2026-09-30 / 10-09 v2): entity-aware structured memoryとvisual evidenceへのon-demand retrieval。Agentを中核に据えた論文としては未確認。https://arxiv.org/abs/2609.38900

## 比較上の注意
- Future visual accessを遮断する（causal）ことと、ライブの各時点で状態を更新して再利用する（incremental/persistent）ことは異なる。
- StreamArena論文のAppendix Cはharness（prefix replay vs continuous ingestion）とmodel causal性を別次元で分類している。
- 「Online」「Streaming」を冠する論文も、実時間の継続推論か、質問時にcausal prefixをreplayするかはコード・評価protocolの詳細確認が必要。
- SVMemAgentではmemory update時に質問が未到着。自研究のQuery=t0既知と直接の条件差になる。
- EventMemAgentのevent境界検出・structured event memoryは、繰り返しSummary改稿での情報欠落を扱う研究候補と直接関係するが、自研究への性能的優位性は未検証。
- 新しい2026年論文の多くは、2025年初出のStreamAgentのRelated Workに掲載されない。

## 探索の方向
固定テンプレートや読む章は要求しない。各論文についてその都度「StreamAgentとの差分」「自研究との差分」「できていないこと」の3つを起点に自由に掘る。未記載と実証された限界を混同しない。

## 未確認
各論文の公開実装が厳密なonline/continuous executionを再現するか、実時間速度に達しているかは今回コード監査していない。StreamMindが示すprefix replay評価の注意を他候補へ自動外挿しない。
