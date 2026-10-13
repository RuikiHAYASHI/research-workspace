---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-10-30 研究室内中間発表に向けた『はじめに』『関連研究』ストーリー検討"
topic: interim-presentation-storylines
status: exploratory
tags: [brainstorm, presentation, introduction, related-work, streaming-videoqa, research-direction]
---

# 10/30 中間発表：「はじめに→関連研究→研究課題」のストーリー10案

## 出発点・相談の目的

ユーザーは2026-10-30の研究室内中間発表で、現時点で完成した新手法や十分なQA結果を前提にせず、「今後こんなことを研究する」という発表を準備したい。まずは「はじめに」と「関連研究」のストーリー候補を10種類広げ、研究課題の見せ方を選ぶ。

今回の作業は候補の発散と仮の収束であり、研究手法の採択、既存研究の欠落を断定するgap claim、spec化、研究コード変更、TODO登録、発表資料そのものの作成ではない。

## 確認した文脈と根拠

- 現行SSOT: `.research/lab/projects/agentic-streaming-videoqa/README.md` （最終更新2026-10-14）。対象はQuestionを開始時から与え、未来にアクセスせずchunk-levelでvideo streamを逐次処理するOnline Streaming VideoQA。オンライン学習と混同しない。
- 2026-10-09 MTG: `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-10-09-mtg.md` 。Situation→Summary→Answerの単純baselineでLongVideoBenchの20秒程度・約3分動画を試行。長い実行時間、繰返し全体更新する累積Summaryの肥大化/情報脱落懸念、Answerのoutput validation失敗を確認。精度の検証とoutput validation失敗は区別する。
- 2026-10-14文献調査方針: `.research/secretary/notes/brainstorm/2026-10-14-streaming-videoqa-literature-review-plan.md` と `2026-10-14-memory-literature-review-tree-strategy.md` 。Text、Visual、KV、Hybrid、Event等のMemoryを媒体・構造・操作・streaming条件の別軸で比較。研究テーマは未決。
- 既存先行例: StreamAgent (https://arxiv.org/abs/2508.01875)、StreamForest (https://arxiv.org/abs/2509.24871)、OneStreamer (https://arxiv.org/abs/2610.01762)、StreamMem (https://arxiv.org/abs/2508.15717)。それぞれanticipation/視覚イベント階層/テキストイベント記憶/KV制約を扱うため、「Agentが新しい」「イベント保存が初めて」「KVで長期記憶する発想はない」等は主張できない。

## 共通の基本型

研究背景（なぜStreaming VideoQAか）
→ Online処理の制約（未来非参照、継続観測、過去情報保持、処理負担）
→ 観点を絞った関連研究（既存の代表的な対処）
→ なお検証すべき問い（論文で未対応と断定せず、まず自分の問いとして提出）
→ 当面の比較方針（baseline、評価観点、予定する小実験）。

完成していない手法・正解率・既存研究の弱点を事実として断定せず、「仮説」「今後検証」と表示する。

## 10のストーリー案

### 1. OfflineからOnlineへの転換型
- はじめに：従来の動画QAは全動画を見られる設定が多い。一方ストリームでは未来を見られず、過去を保持しながら答える必要がある。
- 関連研究：Offline長尺VideoQAと、厳密なStreaming VQAの処理条件・Memoryの違いを比較。
- 問い：未来情報に頼れないとき、どの情報保持/観測方法が有効か。
- 方針：Question=t0既知・future chunk参照禁止を統一し、逐次ベースラインを評価。
- 注意：Onlineにしただけで精度が高いとは言わない。

### 2. 忘却・要約劣化問題型
- はじめに：長時間入力を一度に保持できないため、逐次要約が必要になる。
- 関連研究：累積text summary、イベント追記、視覚特徴/KV保持、hierarchical memoryの違い。
- 問い：繰り返しSummaryを書き直す方式は、いつ・どの情報を落とすのか。
- 方針：既存baselineの累積Summaryで保持失敗を調べ、イベント別保存などと比較予定。
- 注意：情報脱落の懸念は観測済みだが、原因とQA精度の因果は未実証。

### 3. Memory表現のトレードオフ型
- はじめに：過去の映像を何として記憶するかがStreaming理解の本質。
- 関連研究：Text、Visual Token/Feature、KV Cache、hybrid。媒体と記憶単位（frame/chunk/event）を混同しない。
- 問い：長時間保持の情報量・検索容易性・資源負担はどう異なるか。
- 方針：各方式の保存更新・参照方法を比較し、当面のtext baselineの限界を評価予定。
- 注意：媒体分類だけで新規性は生まれない。

### 4. 「何を残すか」判断型
- はじめに：全フレームを記録し続けられず、どの観測が将来有用か不明。
- 関連研究：固定サンプリング、query-relevance、Agentによるkeep/discard、event boundary。
- 問い：情報の重要度を誰がどのタイミングで判断するべきか。
- 方針：一律保存/要約と、選択的保存/更新ポリシーの比較を構想。
- 注意：選択的保存自体に強い先行研究がある。

### 5. 長時間に離れたイベントの統合型
- はじめに：正答に必要な出来事が時間的に離れて現れる。
- 関連研究：短期・長期記憶、イベント単位のテキスト/視覚Memory、階層化。
- 問い：遠い出来事どうしの順序・状態変化を保存し、最後の推論に利用できるか。
- 方針：event gapや順序推論で、全体要約とイベント構造化の違いを検証。
- 注意：「イベントを保存する」というアイデアは既存研究にもある。

### 6. Question既知を活かした記憶型
- はじめに：質問と選択肢が動画開始時から分かれば、必要な観測を事前に意識できる。
- 関連研究：query-aware観測・記憶選択と、query-agnostic memoryを比較。
- 問い：質問に関係する情報を優先して残すことは有利か、逆に情報を見逃すか。
- 方針：question-aware vs question-independentの保存・抽出を同条件で比較。
- 注意：本研究のQuestion=t0条件を明記し、質問未知前提の論文とはprotocol差を示す。

### 7. 予習・将来予測Agent型
- はじめに：Streamingでは映像到着前に何を見るべきか判断することが難しい。
- 関連研究：受動的な視覚入力と、StreamAgent等のfuture-event anticipationによる観測計画。
- 問い：次に重要なイベントや注目対象を予測し、観測/記憶操作を調整できるか。
- 方針：予測なしの逐次処理と予測ありの制御を将来比較。
- 注意：将来の映像内容を予測することと、将来の質問分布を予習することは異なる。新規性未確定。

### 8. 精度と処理時間の両立型
- はじめに：長時間動画を逐次処理するだけでも、VLM呼出し回数や要約更新が増える。
- 関連研究：chunk長・frame sampling、memory圧縮、効率的なstreaming inference。
- 問い：どの処理単位・記憶更新が精度/保持情報量/時間のトレードオフに効くか。
- 方針：既存の約3分動画の条件差を診断し、Agent別時間とmemory保持の比較を計画。
- 注意：現行実行時間から実時間処理を達成したと主張しない。Answer validation失敗を精度低下と混同しない。

### 9. 証拠の蓄積・仮説更新型
- はじめに：動画前半の解釈が後半の証拠で覆ることがある。
- 関連研究：video temporal reasoning、hypothesis verification、逐次回答/待機。
- 問い：stream中で各選択肢の支持・反証・不明を更新すると誤認識を減らせるか。
- 方針：単純な要約→EOF回答と、選択肢状態更新方式の比較を構想。
- 注意：予測・回答時刻・消去法に隣接先行研究があるため、重複を調査する。

### 10. ベースラインの観察から出発型
- はじめに：動画を逐次認識し、過去の理解を蓄積してQAするシステムを構築した。
- 関連研究：既存Streaming VideoQAは何をMemoryに残し、どう更新・読出しするか。
- 現状観察：Summary全体更新で保持劣化の懸念、長い推論時間、Answer validation failure（互いに別問題）。
- 問い：最優先で解決すべき失敗箇所をどう切り分け、どのMemory/Agent方式を比較すべきか。
- 方針：既存3-Agent baselineを診断基盤にし、最小変更と先行研究の比較で研究課題を絞る。
- 注意：baseline実装自体を新規手法/研究成果の確証として主張しない。

## 暫定評価・収束

評価軸: 既存証拠との整合性、10/30までの実現可能性、関連研究への接続、研究の意義の伝えやすさ、過剰主張のリスク。

- **最有力：1＋2＋10を統合する案**。はじめにでStreaming条件（1）、具体課題でMemory保持（2）、現時点での問題意識の根拠としてbaseline観察（10）を示す。関連研究はText summary/Event/Visual/KV等の代表例を機構ごとに紹介する。
- **代替有力：3＋4**。実験結果が乏しくてもMemory設計の比較によって「何を残すか」を研究問いとして説明できる。ただし比較レベルで終わりやすい。
- **発展候補：6・7・9**。Agentらしさや研究差分の可能性はあるが、先行研究との重複確認とメカニズム具体化がさらに必要。
- **併記したい評価軸：8**。Latencyや計算資源はStreamingの価値に直結。ただし改善実績はまだ主張できない。
- 保留：現時点で単独ストーリーの採用、手法の確定、noveltyの断定、発表の枚数確定。

## 推奨する仮の発表骨格（案、未決定）

1. 背景：なぜ長時間のOnline Streaming VideoQAか。
2. 課題：未来非参照・限られた資源の中で過去情報を保持し、QAする。
3. 関連研究：過去情報の保持形式/更新方式（Text、Event、Visual、KV、hybrid）。
4. 未解決の問い（検証課題）：繰り返し更新の情報脱落、記憶内容の選択、時間・精度の両立。
5. 取り組み中：3-Agent最小baselineと初期観察（QA精度とは分ける）。
6. 今後：現象の計測、代表メモリ方式との比較、小さな設計改良と評価。

## 未解決事項・次の判断

- この中間発表では「長時間Memoryの保持」を主軸とするか、それとも「Agentによる観測・記憶の能動制御」を主軸とするか。発表ストーリーはこの選択で大きく異なる。
- 具体的に扱うVideoQA（Question=t0既知、Answer=EOF、MCQ）をどこまで前提としてスライドに書くか。
- 理論的Research gapはまだ未確定。比較文献を精読した後で「既存研究にない」と言うかを判定する。
- 明日のMTGや今後の文献調査で、紹介する代表論文と比較軸をさらに絞る。
- 次アクション候補：10案から1〜2案を選び、各スライドの見出し1文＋必要な関連研究図を紐づける（ユーザー採用までTODO化しない）。

## 関連ソース
- [Project README](https://github.com/RuikiHAYASHI/research-workspace/blob/main/.research/lab/projects/agentic-streaming-videoqa/README.md)
- [2026-10-09 MTG](https://github.com/RuikiHAYASHI/research-workspace/blob/main/.research/lab/projects/agentic-streaming-videoqa/meetings/2026-10-09-mtg.md)
- [Memory Literature Plan](https://github.com/RuikiHAYASHI/research-workspace/blob/main/.research/secretary/notes/brainstorm/2026-10-14-streaming-videoqa-literature-review-plan.md)
