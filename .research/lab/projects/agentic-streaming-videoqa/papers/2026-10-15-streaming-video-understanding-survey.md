---
title: "Towards Online Interactors: A Comprehensive Survey on Streaming Video Understanding" まとめ
date: 2026-10-15
project: agentic-streaming-videoqa
status: draft
source: https://github.com/sotayang/Awesome-Streaming-Video-Understanding （同梱PDF Streaming_Video_Understanding_Survey.pdf、20ページ）
doi: 10.20944/preprints202606.1674.v1
tags: [survey, streaming-video-understanding, taxonomy]
---

# Streaming Video Understanding サーベイのまとめ

## 書誌情報

- タイトル: Towards Online Interactors: A Comprehensive Survey on Streaming Video Understanding
- 著者: Zhenyu Yang, Kairui Zhang, Qi Liu, Tiancheng Liu, Long Ying, Dizhan Xue, Qibin Hou, Shengsheng Qian, Changsheng Xu
- 公開: 2026年6月、Preprints.org（査読前プレプリント）。PDF作成日 2026-06-23
- 関連リポジトリ: Awesome-Streaming-Video-Understanding（2026-09-10の調査メモで見ていたリストと同じ）
- 対象: Video-LLMを使うStreaming Video Understanding。モデル72本（Table II、2024.04〜2026.03）、ベンチマーク・データセット26件（Table III）

読んだ範囲: PDF本文の全セクション（I〜VII）。図は本文の説明からの理解で、図そのものは見ていない。表はテキスト抽出のため、行と列の対応にずれがある可能性がある。

## 1. 問題設定

Streaming Video Understandingは「各時刻 t で、過去と現在のフレーム V≤t だけを見て出力 y_t を出す」設定と定義される（未来フレームは見えない）。

オフラインからストリーミングへ移ると、次の3つの課題が生じる。

| 課題 | 内容 |
|---|---|
| 時間への敏感さ | 答えの内容だけでなく「いつ出すか」も予測の一部になる |
| 長い文脈の扱い | KVキャッシュはメモリが線形、attentionの計算量が二乗で増え、終わりのないストリームでは保てない |
| 実時間の対話 | 入力のフレームレート以上の速さで処理し、割り込みやウェイクワードなしの対話も扱う |

著者の主張の中心は、この3つが**互いに制約し合う**ことにある。固定の計算予算では「頻繁で適切なタイミングの応答」「長い履歴の保持」「フレームごとの低遅延」を同時に最大化できない。

## 2. 全体の分類：Proactive と Reactive

サーベイは、**応答のきっかけ（trigger）を誰が決めるか**で全体を2つに分ける。

| | Proactive（能動） | Reactive（受動） |
|---|---|---|
| 応答のきっかけ | モデル自身が a_t ∈ {0,1} を決める。P(a_t \| V≤t) | ユーザーの質問 Q_t が来たとき。P(y_t \| V≤t, Q_t) |
| 主な課題 | 不確実な状況で「ちょうどよい瞬間」を判断する。早すぎ（証拠不足）と遅すぎ（見逃し）の両方を避ける | 長い履歴を、メモリと遅延を抑えたまま情報を保って持ち続ける |
| 中心となる能力 | 時間の認識（temporal awareness） | 規模を拡大できるMemory（scalable memory） |
| 位置づけ | 一般的な形 | Proactiveで a_t を外部（ユーザー）が決める特別な場合 |

## 3. タスクの分類と、それぞれが扱う課題

Fig. 3 の分類。Proactiveは「1つの質問に対して複数回の更新」、Reactiveは「1つの質問に1つの答え」という形をとる。

### 3.1 Proactiveのタスク

| タスク | 内容 | 主に扱う課題 |
|---|---|---|
| Streaming Real-Time Narration | 実況のように、新しい出来事が起きるたびに重複しない説明を出し続ける | 話すタイミングと流れの自然さ |
| Continuous State Monitoring | 「人数を数えて」のような継続的な指示に対し、状態が変わるたびに答えを更新する | 状態変化の検出と更新の判断 |
| Event Conditioned Responding | 特定の条件や証拠が現れた瞬間にだけ応答する（警告、後回しにした回答など） | 証拠が十分になった時点の判断 |
| Proactive Multi-turn Interaction | 全二重の会話。ユーザー入力が有効かの判断、冗長な発話の中断、新しいターンの開始を行う | 対話の流れの管理 |

### 3.2 Reactiveのタスク

| タスク | 時間の向き | 主に扱う課題 |
|---|---|---|
| Real-Time Visual Perception | 現在 | 今の行動や属性を素早く捉える特徴抽出の効率 |
| History Backward Tracing | 過去 | 長期のエピソード記憶と、過去の手がかりの検索 |
| Future Action Prediction | 近い未来 | 現在の傾向からの予測と因果推論 |
| Contextual Multi-Turn QA | 対話履歴 | 「it」「he」などの照応の解決と、質問をまたいだ一貫性 |

この「現在・過去・未来」の分け方は、OVO-Bench（Backward / Real-time / Forward）や OVBench の分類とほぼ同じ。

## 4. 手法の分類

### 4.1 Proactive：応答のきっかけの決め方（4種類）

著者は4種類を、**判断を生成モデル本体から切り離していく度合い**の順に並べている。(1)から(4)へ進むほど1フレームあたりの計算コストは下がるが、外部のきっかけを信頼できるように設計する負担が増える。

| 種類 | 仕組み | 代表手法 | 対処する課題 | 残る問題（サーベイの指摘） |
|---|---|---|---|---|
| (1) Token駆動（EOS / Action Token） | 応答するかどうかを自己回帰の生成トークンで決める。EOSなら黙る | VideoLLM-online, VideoLLM-MoD, LION-FS, STREAM-VLM, VideoLLM-EyeWO, Streamo, ThinkStream, StreamingClaw, LiveCC, ProAssist, AssistPDA | 「いつ」と「何を」を1つのモデルで学習でき、システムが簡単になる | 黙るべきフレームが圧倒的に多い（1分・2FPSで29:1）ため、決して応答しない方向に偏る。言語能力が下がるおそれ |
| (2) 専用の分類ヘッド・検出器 | 軽量なヘッドや外部モデルが応答を判断し、LLMは呼ばれるまで動かない | MMDuet, ViSpeak, ToM, EgoSpeak, StreamReady, Proact-VL, ROMA, StreamBridge, Dispider, StreamMind, STRIDE, OpenHOUSE, **StreamAgent**, Em-Garde | 重いLLMを毎フレーム動かすコストを減らす。モジュールとして差し替えられる | 別々に学習したモジュール同士の連携がうまくいかないことがある。「話すタイミング」の注釈が高価で、他の分野へ一般化しにくい |
| (3) 不確実性・Perplexityによる検証 | 前に出した応答の、新しいフレームのもとでのPPLを計算し、PPLが急に上がったら応答を更新する | LiveStar | EOS方式の弱点（見た目が似たフレームで異なる振る舞いが必要になる、境界でEOSが紛らわしい）を避ける | 不確実性の指標と、実際の意味の変化が一致する保証がない。閾値の設計が必要 |
| (4) 視覚変化・イベント | 画素や特徴の変化、シーン転換をきっかけにする | TimeChat-Online, QueryStream, ColorTrigger | 何もないときのコストをほぼゼロにでき、エッジ機器に向く | 画素レベルの変化は意味の変化と一致しない。質問と無関係な変化でも応答してしまう |

(2) の中は、さらに「その時点での直接予測」「確信度などの段階的なスコア」「イベントや境界の構造を使うもの」「**未来を予測してスケジュールするもの（StreamAgent, Em-Garde）**」に分けられている。

### 4.2 Reactive：情報が流れる順の4段階

Reactiveは、情報がシステムに入ってから使われるまでの段階（ライフサイクル）で整理されている。

| 段階 | 対処する課題 | 代表手法 | 残る問題（サーベイの指摘） |
|---|---|---|---|
| (a) 入力の絞り込み（トークンの間引きと再利用、attentionの改良） | 冗長な視覚トークンが入ってくるのを防ぎ、遅延を下げる | STC, AutoGaze, SDQES, StreamChat(CVPR'25), StreamFormer, OmniStream | **将来の質問を知らずに捨てる**ため、後で必要になる手がかりを失うおそれがある |
| (b) 作業記憶の維持（KVキャッシュの管理・削除） | KVがO(T)で増えるのを抑え、O(1)にする | InfiniPot-V, StreamMem, StreamingAssistant, StreamingVLM, TaYS, VST | 質問を知らないまま削除するため、過去を振り返る推論の深さが限られる。削除ではなく、情報を保ったまま圧縮する方法が必要 |
| (c) 長期記憶の圧縮（階層化、要約、パラメータへの記憶） | 時間スケールの違う記憶を分け、長い履歴を小さく保つ | VideoChat-Online, StreamChat(ICLR'25), StreamForest, EventMemAgent, ProVideLLM, TWW, OVG-HQ-Unify, video-SALMONN S, HERMES | テキスト要約やパラメータ更新にすると**視覚的な根拠が戻らない形で失われる**（「10分前の背景のナンバープレートは？」に答えられない） |
| (d) 必要に応じた履歴の呼び出し（検索拡張） | 質問が来た時点で必要な過去だけを取り出す | ReKV, LiveVLM, StreamKV, StreamingTOM, CacheFlow, rLiVS, WeaveTime, Venus, V-Rex | 意味が似た断片をつなぐと**時間の順序と因果が壊れる**。「AがBを引き起こしたのか、似ているだけか」のような複数段の因果推論に弱い |

#### 段階ごとの「残る問題」の関係

各段階は前の段階の弱点を補う形になっているが、それぞれが新しい弱点を生んでいる。

```text
(a) 入力で捨てる     → 質問を知らないので、必要な情報まで捨てるおそれ
(b) KVを削除する     → 同じく質問を知らない。削除した情報は戻らない
(c) 要約・圧縮する   → 視覚の細部が失われる
(d) 検索で取り出す   → 時間の順序と因果のつながりが失われる
```

4つに共通するのは「**どの質問が来るかわからない状態で、何を残すかを決めなければならない**」という問題。

### 4.3 学習方法による分類

Fig. 4 では、上の分類に加えて、学習方法（学習なし、テスト時学習、SFT、RL）の軸でもモデルを並べている。Table II では72本の大半がQwen系（Qwen2〜Qwen3-VL）を使い、規模は2B〜8Bに集中している。

## 5. ベンチマークの分類

| 種類 | 対応する枠組み | 代表 | 見ている能力 |
|---|---|---|---|
| 複数ターンの対話・QA | Reactive | StreamingBench, SVBench, StreamBench, TemporalBench, RTV-Bench, OVBench, RIVER Bench, OST-Bench, StreamEQA, YT-Conversation, ODV-Bench, StreamingCoT | 未来を見ない制約、時間とともに答えが変わる問題、過去・現在・未来、記憶の衰え（RIVER）、身体を持つエージェントの場面、運転、CoT |
| 実時間のキャプション・実況 | 両者の中間 | LiveSports-3K / Live-CC-5M / Live-WhisperX-526K（LiveCC）, OmniStar-RNG（LiveStar）, QEVD-FIT-COACH | 何を言うかと、いつ言うか（TimDiffなど） |
| 能動的な応答とタイミングの評価 | Proactive | PROASSIST, ESTP-Bench, StreamGaze, ProactiveVideoQA, ProReady-QA, MMDuetIT, OVO-Bench, VAPDA-127K, OmniMMI, Live Gaming Benchmark | 応答のタイミング、早すぎと遅すぎへの非対称なペナルティ、異常の早期検出 |

ベンチマークについてサーベイが指摘する問題:

1. 複数の能力が混ざっており、短期の知覚と長期の推論・Memoryを分けて測れない。
2. 長い時間をまたぐ依存関係の評価が不十分。
3. Proactiveの評価も、多くは**あらかじめ決めた質問時刻や応答区間の注釈**に頼っている。そのため実質はReactiveに近く、開かれた場面で「いつ何を言うか」を決める能力は測れていない。
4. 対話の一貫性、時間推論、応答タイミングを別々に測っており、まとめて評価する枠組みがない。

## 6. まだ残る問題（Challenges）

### Proactive

1. **応答タイミングの判断**: 必要な証拠の量はタスクによって違い、共通の基準がない。
2. **長い時間のMemory管理**: 過去と予想される未来の両方に依存する。ためすぎるとメモリが足りず、削りすぎると重要な依存関係が失われる。
3. **実時間での推論効率**: 毎ステップの監視と判断のために、自己回帰のデコードを繰り返すコストが大きい。
4. **応答の頻度と粒度を適応させること**: 固定のきっかけ方式ではなく、タスクの複雑さや不確実性に合わせて変える必要がある。

### Reactive

1. **Memoryと情報の管理**: 将来の質問を知らないまま、固定の予算の中で重要な情報を残す。
2. **検索と推論**: 質問がいつ来るかわからず、時間の手がかりがない質問ほど、関連する区間を見つけにくい。圧縮表現では細部が足りない。
3. **計算と符号化**: 軽くすると意味の理解が落ち、表現力を上げると計算コストが上がる。

## 7. 今後の方向（Future Directions）

1. **ProactiveとReactiveを統合した構成**: 3層構成を提案している。
   - 下層: 常に動く軽量な「無意識」の知覚層（スライディングウィンドウのKVで、LLMは呼ばない）
   - 中層: きっかけの振り分け a_t = F(Q_t, E_t | V≤t)。ユーザーの質問 Q_t と、視覚変化や不確実性 E_t の両方を見る
   - 上層: 起こされたときだけ動く重いLLMによる推論
2. **効率的なMemory構成と階層的な文脈**: 「残すか捨てるか」の二択をやめ、短期の作業記憶と長期のエピソード記憶を分ける。予測の不確実性で削除を決める方式、KVの低ビット量子化、SSM（Mamba）や線形attentionの利用。
3. **エッジ向けのハードウェアとソフトウェアの協調設計**: トークンの間引きはFLOPsを減らしても、メモリ帯域が律速するため実時間は短くなりにくい。ブロック単位の間引きや専用アクセラレータ（SVPU）が必要。
4. **身体を持つAIの「視覚野」としての利用**: VLMからVLAへ移り、行動が次の入力を変える閉ループで評価する。指標もQA正解率から、タスク成功率や衝突回避へ移る。

## 8. サーベイ同士の比較

### 8.1 このサーベイが自分で示している比較（Table I）

| サーベイ | 年 | 主な対象 | ストリーミング設定 | オンライン対話 | きっかけの分類 | ストリーミング用ベンチマーク |
|---|---|---|---|---|---|---|
| Laghari et al. | 2023 | 動画配信の技術（圧縮、プロトコル） | △ | ✗ | ✗ | ✗ |
| Dao et al. | 2022 | 計算処理を中心としたライブ配信（システム、配信） | △ | ✗ | ✗ | ✗ |
| Tang et al. | 2025 | LLMによる動画理解全般 | △ | △ | ✗ | ✗ |
| Nguyen et al. | 2024 | 動画と言語の理解（構成、学習、データ） | ✗ | ✗ | ✗ | △ |
| Wu et al. | 2026 | MLLMによる動画の時間的グラウンディング | ✗ | ✗ | ✗ | ✗ |
| 本サーベイ | 2026 | Video-LLMによるStreaming Video Understanding | ✓ | ✓ | ✓ | ✓ |

✓は体系的に扱う、△は部分的に扱う、✗は明示的には扱わない。著者の自己評価であることに注意する。

### 8.2 2026年の近い分野のサーベイとの比較（私たちの整理）

以下の2本は**アブストラクトのみ確認**しており、本文は読んでいない。

| サーベイ | 公開 | 分類の軸 | Streaming Video Understandingとの関係 |
|---|---|---|---|
| 本サーベイ（Yang et al.） | 2026-06, Preprints.org | **応答のきっかけ**（Proactive / Reactive）と、Reactive内の**情報の流れの段階** | 動画に特化。ストリーミング設定そのものが対象 |
| From Static Inference to Dynamic Interaction: A Survey of Streaming LLMs（Tong et al., arXiv 2603.04592） | 2026-03（v3: 2026-04） | **データの流れと動的な対話**に基づく統一定義。ストリーミング生成・ストリーミング入力・対話型の構成が混在している状況を整理する | LLM全般が対象で、動画は一部と思われる（未確認）。「ストリーミング」の定義を広く与える側 |
| Agentic Video Understanding: A Survey（Deng et al., arXiv 2609.31713） | 2026-09 | **課題から設計への対応**: 文脈の限界→階層的な証拠Memory、証拠の少なさ→能動的な証拠の取得、時間の因果→状態と過程の追跡、多モーダルの曖昧さ→役割を分けた協調 | エージェント型の動画理解が対象。ストリーミングを扱うかは未確認 |

分類の切り口の違い:

- 本サーベイ: 「**いつ応答するか**」と「**履歴をどう持つか**」で分ける（システムの入出力の形に着目）
- Streaming LLMサーベイ: 「**データがどう流れるか**」で分ける（動画に限らない定義の整理）
- Agenticサーベイ: 「**どの課題に対してどの設計で対処するか**」で分ける（エージェントの判断の中身に着目）

## 9. このプロジェクトから見た読み方（私たちの推論）

以下はサーベイの主張ではなく、このプロジェクトの文脈から見た推論。

- 本サーベイでは StreamAgent は「Proactive / 分類ヘッド・検出器 / 未来を予測する判断」に入っている。Memoryの側からは整理されておらず、Agentの判断をMemory管理にも使う、という見方はこのサーベイの分類には出てこない。
- Reactiveの4段階は、どれも「将来の質問を知らずに何を残すか」で詰まっている。予習するAgentや、Summaryとは別にEventを記録する試みは、この問題に対する1つの答え方として位置づけられる可能性がある。
- (c) の「要約すると視覚の根拠が失われる」という指摘は、現在のSituation → Summary → Answerの構成にそのまま当てはまる。テキストの状態に加えて、元のフレームやクリップへの参照を残すかどうかは検討する価値がある。
- 現在進めているMemory分類（A〜G）やAgentの役割分類と比べると、このサーベイの分類は粗い（手法を1本につき1カテゴリに割り当てている）。Table IIの72本と自分たちのDBの論文リストを照合すると、抜けている論文の確認に使える。
- 未来を予測するProactiveの手法（StreamAgent, Em-Garde）は、サーベイ中でも数が少なく、「不確実性のモデル化と誤りの伝播」が課題として挙げられている。

## 10. 未確認事項

- 図（Fig. 1〜8）は見ていない。Table II・IIIはテキスト抽出のため、行の対応は原文で確認が必要。
- 比較した2本のサーベイは本文を読んでいない。
- 査読前のプレプリントであり、査読付きの版があるかは未確認。

## 関連文書

- [2026-09-10 Awesome Streaming Video Understanding 調査](../../../../secretary/notes/brainstorm/2026-09-10-awesome-streaming-video-understanding-investigation.md)
- [2026-10-14 Agentの役割の分類（1回目）](../../../../secretary/notes/brainstorm/2026-10-14-agent-role-classification-round1.md)
- [2026-10-14 Memory分類（2回目）](../../../../secretary/notes/brainstorm/2026-10-14-memory-classification-round2.md)
