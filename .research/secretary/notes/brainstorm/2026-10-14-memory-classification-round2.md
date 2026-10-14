---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-10-14 MTG: 問いに関連する論文候補を一覧化し、設定・Memory形式・保存単位・更新／検索方法を比較する"
topic: memory-classification-round2
status: exploratory
tags: [brainstorm, literature-review, memory, taxonomy, classification, streaming-videoqa]
---

# Memory保持形式の分類：2回目の当てはめ（1回目と合わせて41本）

## 位置づけ

- [判定基準メモ](2026-10-14-memory-retention-classification-criteria.md)の最新の分類（A〜G、1つの分類に1コード）で、新たに29本を調べ、[1回目の15本](2026-10-14-memory-classification-round1.md)と合わせて並べた。
  - 分類できたのは26本。3本はMemoryの定義外だった（「5. Memoryの定義外」）。
  - 1回目と合わせ、分類した論文は41本。
- 2回目の対象：既存メモの候補プールのうち1回目で扱わなかった23本と、該当が少ない小分類を埋めるための新規探索6本。
- 分類の定義は変更していない。今の分類に収まらなかった点は「6. 分類の追加・統合の提案」にまとめた（**未採用**）。
- 表記：
  - 論文名の後ろの `★` はofflineの論文（動画全体を見られる設定）。
  - `?` は判定に迷いがあるもの。
  - `—` は既定の方式（コードなし）。
  - `[新]` は2回目で追加した論文。
- 根拠の確かさ：2回目の論文は、ほとんどが本文の要約・抜粋を経由した読み取り（`原文（要約経由）`）。Mementoは公式PDFを直接読んだ。CogStreamとQueryStreamは公式コードも確認した。QueryStreamは本文を読めず、要旨とコードのみ。
- 記述の区別：「著者の主張」「実験で示されたこと」「私たちの推論（推論と明記）」「未確認」。

## 1. 分類A：記憶する情報

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| A0 | 映像そのもの | 映像を保存するだけで、何が映っているかは書かない | [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [LiveVLM][新], [StreamChat][新], [VideoStreaming][新], [ReKV][新], [SAVEMem][新], [MovieChat][新], [MA-LMM][新], [StreamMind][新], [R3-Streaming][新], [Memento][新], [QueryStream][新], [ReWind]★[新], [video-SALMONN S][新], [ProtoKV][新] | 18 |
| A1 | 場面の説明 | 場所・人や物・動作を、文章などでまとめて書く | [StreamAgent], [Lando et al.], [VideoMultiAgents]★, [Response-G1], [Lando Edge][新], [Watch-Think-Interact][新], [ThinkStream][新], [StreamingVLM][新] | 8 |
| A2 | 人・物ごとの記録 | 人や物1つにつき1件の記録を持ち、時間を通して追う | [VideoAgent]★, [M3-Agent][新] | 2 |
| A3a | イベント：区切りに使うだけ | イベントの切れ目で保存単位を分けるが、中身は映像そのもの | [StreamForest], [VideoLLaMB]★, [MEMO][新] | 3 |
| A3b | イベント：出来事を記録 | イベントごとに「何が起きたか」を書く | [OneStreamer], [Think While Watching], [EventMemAgent], [OASIS], [ProVideLLM][新], [OmAgent]★[新], [StreamArena][新] | 7 |
| A4 | タスクの状態 | 質問への取り組みの途中経過を書く | [CogStream][新]（過去のQA）, [TraveLER]★[新]（下位の質問と回答、不足情報）, [Em-Garde][新]?（質問から作った監視リスト） | 2〜3 |

備考：
- [StreamingVLM]：古い映像は捨て、モデル自身が書いた実況テキストのKVだけが長く残るためA1。
- [ThinkStream]：長く残るのはモデルが生成した推論テキスト（のKV）なのでA1。過去の応答も残るのでA4の要素もある。
- [StreamChat]：各nodeにcaptionも付くが、本文では検索の目印として説明されているためA0。付録ではcaptionもLLMに渡すと書かれており、論文内で食い違う（その場合はA1）。
- [MEMO]：物体ごとの追跡を持つが、検索の目印となる埋め込みだけなのでA2にしない。
- [Em-Garde]：「これから起きるはずの出来事」の説明で、観測した内容ではない。A4に入れてよいかは提案P3で検討。

## 2. 分類B：表現形式

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| B1 | 文章 | 自由に書いた文 | [OneStreamer], [Lando et al.], [ProVideLLM][新], [Lando Edge][新], [CogStream][新], [Em-Garde][新] | 6 |
| B2 | 項目付きテキスト | 時刻や内容が欄に分かれたテキスト | [VideoAgent]★, [Watch-Think-Interact][新], [OmAgent]★[新], [TraveLER]★[新] | 4 |
| B3 | グラフ | 物と関係を点と線で表す | [VideoMultiAgents]★, [Response-G1], [M3-Agent][新] | 3 |
| B4 | 画像 | フレームを画像のまま残す | [SVMemAgent], [MEMO][新] | 2 |
| B5 | 視覚特徴 | 画像をエンコーダで数値に変換して残す | [StreamForest], [Flash-VStream], [StreamChat][新], [SAVEMem][新]?, [MovieChat][新], [MA-LMM][新], [StreamMind][新], [R3-Streaming][新]?, [Memento][新], [QueryStream][新], [ReWind]★[新] | 11 |
| B6 | KV cache | LLMが過去の入力を読んだときの内部データを残す | [MuKV], [StreamMem], [StreamingVLM][新], [LiveVLM][新], [ReKV][新], [ThinkStream][新], [ProtoKV][新] | 7 |
| B7 | 内部状態 | 決まった大きさの数値を毎回更新して持ち越す | [VideoLLaMB]★, [VideoStreaming][新], [video-SALMONN S][新] | 3 |
| B8 | 項目付きテキスト＋画像（複合） | 項目付きテキストと、その根拠になる画像を組で持つ | [EventMemAgent], [OASIS], [StreamArena][新] | 3 |
| B9 | テキスト＋KV（複合） | 文章または項目付きテキストと、過去入力のKVを並行して持つ | [StreamAgent], [Think While Watching]? | 2 |

備考：
- [StreamingVLM]・[ThinkStream]：テキストもKVの形で持つためB6とした。「生成したテキストのKV」をB9に含めるかは提案P4で検討。
- [VideoStreaming]：固定長の状態を、clipごとにスナップショットとして溜めていく。[video-SALMONN S]：学習中ではなく推論時に勾配で更新される重み（fast weight）を状態として持つ。どちらもB7とした（提案P5）。
- [ProtoKV]：KVの統計（中心・質量など）を固定数のプロトタイプとして持つ。B6とB7の中間。
- [SAVEMem]・[R3-Streaming]：保存しているのが視覚特徴かKVかが本文で明確でない（`?`）。

## 3. 分類C〜G：管理方式

### 分類C：書き込みタイミング

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C1 | 届くたび | フレームが届くたびに書く | [Flash-VStream], [SVMemAgent], [StreamingVLM][新], [LiveVLM][新], [ReKV][新], [SAVEMem][新], [MA-LMM][新], [StreamMind][新], [R3-Streaming][新], [Memento][新], [QueryStream][新], [ReWind]★[新], [ProtoKV][新] | 13 |
| C2 | 一定間隔 | 数秒ごとなど、決まった間隔で書く | [StreamAgent], [Lando et al.], [Think While Watching], [OASIS], [MuKV], [StreamMem], [VideoAgent]★, [Response-G1], [Lando Edge][新], [Watch-Think-Interact][新]?, [ThinkStream][新], [StreamChat][新], [VideoStreaming][新], [MovieChat][新], [StreamArena][新], [M3-Agent][新], [video-SALMONN S][新] | 17 |
| C3 | 切れ目で | 映像が変わった所で区切って書く | [VideoLLaMB]★, [VideoMultiAgents]★, [OneStreamer]?, [MEMO][新], [OmAgent]★[新] | 5 |
| C4 | 短期は届くたび・長期は切れ目で（複合） | 届いたものをまず短期に入れ、切れ目ごとに長期へ移す | [StreamForest], [EventMemAgent], [ProVideLLM][新] | 3 |
| （該当なし） | — | C1〜C4のどれにも当たらない | [CogStream][新]（回答のたびにQAを追記）, [Em-Garde][新]（質問が届いたときに1回）, [TraveLER]★[新]（Agentが選んだフレームを見たとき） | 3 |

### 分類D：書き込みの選別

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 選ばない（既定） | 届いたものをそのまま残す | 下の16本以外のすべて | — |
| D1 | 質問に関係するもの | 実際の質問に関係する内容を選んで残す | [VideoMultiAgents]★, [Response-G1]?, [QueryStream][新], [ReWind]★[新], [Em-Garde][新], [TraveLER]★[新] | 6 |
| D2 | 質問に依存しない重要度 | 質問が分からないまま、汎用の物差しで「役立ちそうなもの」を残す | [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [Lando et al.]?, [LiveVLM][新], [StreamChat][新]（動きの大きさ）, [SAVEMem][新]（固定の仮の質問5つ）, [R3-Streaming][新], [StreamArena][新] | 10 |

### 分類E：更新

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 追記のみ（既定） | 既存は変えず、新しい記録を足すだけ | [OneStreamer], [Lando et al.], [Think While Watching], [MuKV], [VideoMultiAgents]★, [Response-G1], [Lando Edge][新], [MEMO][新], [VideoStreaming][新], [ReKV][新], [OmAgent]★[新], [CogStream][新], [StreamMind][新], [Em-Garde][新], [QueryStream][新], [ReWind]★[新] | 16 |
| E1 | 全体を書き直す | 毎回Memory全体を作り直す（私たちのbaseline） | [StreamAgent]（テキスト側）, [Watch-Think-Interact][新]?, [video-SALMONN S][新]（状態の更新） | 3 |
| E2 | まとめる・縮める | 似た記録を1つにする、データ量を減らす | [StreamForest], [OASIS], [VideoLLaMB]★, [VideoAgent]★, [StreamChat][新], [MovieChat][新], [MA-LMM][新], [StreamArena][新], [Memento][新], [M3-Agent][新], [TraveLER]★[新] | 11 |
| E3 | 捨てる・入れ替える | 古い・不要な記録を消す、別の記録と入れ替える | [SVMemAgent], [ProVideLLM][新], [ThinkStream][新], [StreamingVLM][新], [LiveVLM][新], [SAVEMem][新], [R3-Streaming][新]? | 7 |
| E4 | まとめて、溢れたら捨てる（複合） | 縮めたうえで、容量を超えたら捨てる | [EventMemAgent], [StreamMem], [Flash-VStream], [ProtoKV][新] | 4 |

### 分類F：構造

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 時刻順に並べるだけ（既定） | 記録を時間順に並べるだけ | 下の20本以外のすべて | — |
| F1 | 短期と長期に分ける | 直近の詳しい記録と、古い記録の置き場を分ける | [StreamAgent], [StreamForest], [EventMemAgent], [ProVideLLM][新], [ThinkStream][新], [LiveVLM][新], [SAVEMem][新]（「hierarchy」と名乗るが、層を順に流れるだけ）, [MovieChat][新], [R3-Streaming][新], [video-SALMONN S][新], [ProtoKV][新] | 11 |
| F2 | 親子の階層 | 粗いまとめ（親）と細かい記録（子）をつなぎ、子も実際に読み出せる | [OASIS], [StreamChat][新], [StreamArena][新] | 3 |
| F3 | 並列ストア | 同じ時間を、細かさや見方の違う複数のMemoryに同時に保存する | [MuKV], [Flash-VStream], [VideoAgent]★, [OneStreamer]?, [Watch-Think-Interact][新]（テキストMemoryと元映像の保管庫）, [ReWind]★[新]（圧縮Memoryと高解像度特徴） | 6 |

### 分類G：読み出し

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 全部渡す（既定） | Memory全体をLLMに入力する | 下の21本以外のすべて | — |
| G1 | 検索して一部渡す | 時刻・意味・質問で選んだ記録だけを渡す | [StreamAgent], [MuKV], [Response-G1], [MEMO][新], [LiveVLM][新], [StreamChat][新], [VideoStreaming][新], [ReKV][新], [SAVEMem][新], [OmAgent]★[新], [CogStream][新], [Memento][新], [M3-Agent][新], [video-SALMONN S][新] | 14 |
| G2 | 詳細を見直す | 保存済みの画像・特徴をもう一度見る | [Flash-VStream], [Watch-Think-Interact][新] | 2 |
| G3 | 検索してから詳細を見直す（複合） | 記録を検索で選び、その保存済み画像・特徴を見直す | [OASIS], [VideoAgent]★, [EventMemAgent]?, [StreamArena][新], [ReWind]★[新] | 5 |

## 4. 質問を知る時点・区切り方

| 項目 | 値 | 該当論文 |
| --- | --- | --- |
| 質問を知る時点 | 知っている | [VideoMultiAgents]★, [ProVideLLM][新]（固定のタスク指示）, [Em-Garde][新], [QueryStream][新], [ReWind]★[新], [TraveLER]★[新] |
| 質問を知る時点 | 途中から知る | [Response-G1], [Think While Watching], [OneStreamer]?, [StreamAgent]?, [Watch-Think-Interact][新]?, [ThinkStream][新] |
| 質問を知る時点 | 知らない | 上記と下記以外のすべて（[OmAgent]★, [VideoAgent]★, [VideoLLaMB]★?を含む） |
| 質問を知る時点 | 未確認 | [MA-LMM][新] |
| 区切り方 | 見た目の変化 | [StreamForest], [EventMemAgent], [VideoLLaMB]★, [MEMO][新], [OmAgent]★[新], [CogStream][新]（読み出しのたびにクラスタリング） |
| 区切り方 | 意味の変化 | [VideoMultiAgents]★（方法は未記載）, [StreamArena][新]（LLMが境界を予測し、時間の上限と組み合わせる） |
| 区切り方 | 学習したモデルの判断 | [OneStreamer], [ProVideLLM][新]（行動の予測が変わったとき） |
| 区切り方 | 固定時間・なし・その他 | 上記以外 |

## 5. Memoryの定義外（分類表に入れない）

offlineで、1つの質問の推論の中でだけ一時的な表現を作り、後の時点に持ち越さないため、基準0（Memoryの定義）に当てはまらない。参考として、仮に分類した場合のコードを残す。

| 論文 | 定義外の理由 | 参考コード（仮に数えた場合） |
| --- | --- | --- |
| [VideoTree]★ | 質問ごとに動画全体をクラスタリングし、関連するクラスタを深掘りして、captionを時刻順に並べて回答する | A1 / B1 / D1 / F2 |
| [VideoAgent-Wang]★ | 一様に選んだフレームのcaptionから始め、自信が足りなければフレームを追加で取りに行く。状態は1問の中だけで使う | A1 / B1 / D1 |
| [VideoINSTA]★ | イベント分割・caption・要約を1問の推論の中だけで作る | A3b / B1 / C3 / D1 / G1 |

- [CogStream]も、映像部分は質問のたびに過去全体を最初から処理し直す（公式コードで確認）ため、Memoryに数えなかった。Memoryとして数えたのは過去のQA履歴だけ。

## 6. 分類の追加・統合の提案（未採用）

判定基準メモの条件に照らした提案。採否はユーザーと決める。

| # | 提案 | 種類 | 判定条件 | 根拠論文 |
| --- | --- | --- | --- | --- |
| P1 | C4を「短期は届くたび・長期へは**切れ目または溢れたとき**に移す」に広げる | 定義の拡張 | 「容量が溢れたら次の層へ移す」タイミングが複数の論文にあり、C1〜C4に収まらない | [MovieChat][新], [SAVEMem][新], [ProtoKV][新]（今はC1・C2に入れている） |
| P2 | Cに「対話のたび（質問・回答が届いたとき）」を新設 | 追加 | 既存コードに当たらない論文が2本 | [CogStream][新], [Em-Garde][新]（[TraveLER]★は単独例として備考） |
| P3 | A4を「タスク由来の情報（過去のQA・仮説・監視対象）」に広げる | 定義の拡張 | 質問から作った監視リストがA0〜A3bのどれにも当たらない（1本） | [Em-Garde][新] |
| P4 | B9に「モデルが生成したテキストをKVの形で持つ」場合を含める | 定義の明確化 | 生成テキストのKVを長期のMemoryにする論文が2本 | [StreamingVLM][新], [ThinkStream][新] |
| P5 | B7を「決まった大きさの状態（memory token・推論時に更新される重み・状態のスナップショット列）」と明記する | 定義の明確化 | B7に入れた3本で状態の持ち方が異なる | [VideoLLaMB]★, [VideoStreaming][新], [video-SALMONN S][新] |
| P6 | D1を「質問を使って、残すもの**または残し方（圧縮の仕方）**を決める」に広げる | 定義の拡張 | 選ぶのではなく、質問を条件に圧縮する論文がある | [ReWind]★[新]、未分類の候補VideoDetective |
| P7 | E1を「テキストに限らず、Memory全体を毎回作り直す（状態の更新を含む）」と明記する | 定義の明確化 | 状態を毎回更新する論文をE1に入れた | [video-SALMONN S][新] |

- **小分類の新設は2回目で1件（P2）だけ**だった。他は定義の拡張・明確化。新しい論文を入れても新しい小分類がほとんど出なくなったので、判定基準メモの「止める条件」にほぼ達したと考える（推論）。
- 1回目で該当が1本だけだった小分類は、すべて2本以上になった（A2、B2、B4、B7、E1、E3、F2、G2）。

## 7. 当てはめから見えたこと（私たちの推論）

1. **質問を最初から知っているstreaming論文が見つかった**：1回目の15本には無かったが、2回目で次の3本が見つかった。
   - [QueryStream]（ICLR 2026）：質問に関係し、かつ新しい視覚tokenだけを残す（D1）。私たちの設定（質問は開始時に既知）に最も近い先行研究。ただし本文は読めておらず、要旨と公式コードによる判定。
   - [ProVideLLM]（ICCV 2025）：最初から与えられるのは固定のタスク指示（「次に何をすべきか」など）で、個別の質問ではない。書き込みの選別には使っていない。
   - [Em-Garde]：Memoryは質問から作った監視リストだけで、映像は残さない。
   - 「質問を知っているstreaming設定で、映像のMemoryを質問で選んで書く」方式は、[QueryStream]が直接の先行例になる。私たちの研究で新規性を主張する際の比較対象として重要。
2. **テキストの要約全体を毎回書き直す方式（私たちのbaseline）は少ない**：E1は3本だけで、テキストの書き直しは[StreamAgent]と[Watch-Think-Interact]（推定）のみ。専用の探索でも、`summary_t = LLM(summary_{t-1}, 観測_t)` の形の論文は見つからなかった（未確認）。多くの論文は追記・統合・捨てる方式を採っている。
3. **長期Memoryは「映像そのもの」が最多**：41本中18本がA0。テキストで出来事を記録する（A3b）のは7本。
4. **意味で区切るイベント分割は依然として少ない**：意味の変化で区切るのは[StreamArena]（LLMが境界を予測）と、方法が未記載の[VideoMultiAgents]★だけ。多くは見た目の変化か固定時間。
5. **生成したテキストを長く残す新しい流れ**：[StreamingVLM]と[ThinkStream]は古い映像を捨て、モデル自身が書いた実況・推論のテキストを長期のMemoryにしている。これは私たちのSummaryと発想が近い。

## 8. 未確認・要確認

- [QueryStream]：本文を読めていない（OpenReviewが開けなかった）。ベンチマークで質問が届く前のフレームをどう扱うか。
- [Watch-Think-Interact]：E1（全体の書き直し）は数式からの推定。区切りの定義、Memoryの上限値。
- [StreamChat]：captionが検索の目印か中身か（本文と付録で食い違う）。
- [SAVEMem]・[R3-Streaming]：保存形式が視覚特徴かKVか。
- [StreamMind]：読み出しの方法と容量。
- 発表先：[MEMO]（ACM MM 2026、arXivのコメントのみ）、[ProtoKV]（ICML 2026、arXivのコメントのみ）、[LiveVLM]（DAC '26の記載のみ）、[Lando Edge]（VISAPP 2026、研究室ページのみ）、[TraveLER]★（EMNLP 2024、ACL Anthologyで未確認）、[Memento]（arXiv版が見つからない）。
- 2回目の論文は、ほとんどが要約経由の読み取り。中間発表で使う論文は原文で確認し直す。

## 9. 2回目では分類しなかった候補

| 論文 | 内容 | 備考 |
| --- | --- | --- |
| VideoDetective（arXiv 2512.17229） | 質問をMemory tokenの直前に置き、質問を意識して圧縮する | 「質問を知っている」設定の候補。暫定 B6 / C2 / D1 |
| Eyes Wide Open / VideoLLM-EyeWO（arXiv 2510.14560） | 質問が届いた後、モデル自身が圧縮率と高解像度の要求を決める | 「途中から知る」。arXivのコメントにNeurIPS 2025採録とある |
| PReM（arXiv 2609.23601）、Beyond Retrieval（arXiv 2609.04131） | 一定サイズの再帰状態、固定長の潜在Memory | B7候補。未読 |
| ObjectStream（arXiv 2607.28312） | 物体の潜在表現を起点にしたMemory | A2候補。未読 |
| Video Streaming Thinking（arXiv 2603.12262）、LifelongMemory、Vinci2（arXiv 2607.11523） | E1の探索中に見つかった論文。実際は追記・統合で、書き直しではなかった | — |

## 付録A：2回目の論文の発表先

| 論文 | 発表先 | arXiv |
| --- | --- | --- |
| [ProVideLLM] | ICCV 2025 | 2504.13915 |
| [Lando Edge] | VISAPP 2026（研究室ページの記載のみ） | 2602.22455 |
| [Watch-Think-Interact] | arXiv（採録未確認） | 2609.37035 |
| [ThinkStream] | arXiv（採録未確認） | 2603.12938 |
| [MEMO] | ACM MM 2026（arXivのコメントのみ、公式ページ未確認） | 2609.38900 |
| [StreamingVLM] | ICLR 2026 | 2510.09608 |
| [LiveVLM] | arXiv（採録未確認。本文にDAC '26の記載） | 2505.15269 |
| [StreamChat] | ICLR 2025 | 2501.13468 |
| [VideoStreaming] | NeurIPS 2024 | 2405.16009 |
| [ReKV] | ICLR 2025 | 2503.00540 |
| [SAVEMem] | arXiv（採録未確認） | 2605.07897 |
| [MovieChat] | CVPR 2024 | 2307.16449 |
| [MA-LMM] | CVPR 2024 | 2404.05726 |
| [OmAgent]★ | EMNLP 2024 | 2406.16620 |
| [CogStream] | AAAI 2026 | 2506.10516 |
| [StreamMind] | ICCV 2025 | 2503.06220 |
| [R3-Streaming] | arXiv（採録未確認） | 2605.17921 |
| [StreamArena] | arXiv（採録未確認） | 2608.05703 |
| [Em-Garde] | arXiv（採録未確認） | 2603.19054 |
| [Memento] | ICLR 2026 | 見つからず |
| [QueryStream] | ICLR 2026 | 見つからず |
| [ReWind]★ | CVPR 2025 | 2411.15556 |
| [M3-Agent] | ICLR 2026 | 2508.09736 |
| [video-SALMONN S] | ICML 2026 | 2510.11129 |
| [ProtoKV] | ICML 2026（arXivのコメントのみ、公式ページ未確認） | 2606.26762 |
| [TraveLER]★ | EMNLP 2024（arXivのコメントのみ） | 2404.01476 |
| [VideoTree]★ | CVPR 2025（定義外） | 2405.19209 |
| [VideoAgent-Wang]★ | ECCV 2024（定義外） | 2403.10517 |
| [VideoINSTA]★ | Findings of EMNLP 2024（定義外） | 2409.20365 |

- [StreamMind]（ICCV 2025、event-gated）と、[StreamArena]の中で提案されているStreamMindは別の手法。

## 付録B：2回目の論文のMemoryのデータフロー

- **[ProVideLLM]**：視覚tokenを短期の待ち行列に入れ、そこから押し出されるときにモデルが行動のラベルに言語化して長期のテキスト枠（最大5件）へ移す。
- **[Lando Edge]**：15秒ごとにMLLMが一人称の説明文を書いて追記し、映像は捨てる。質問が来たら全テキストをLLMに渡す。
- **[Watch-Think-Interact]**：区切りごとにモデルが旧Memoryと直近の記録から、上限内のテキストMemoryに書き直す。元映像は保管庫に置き、必要なら区間を指定して見直す。
- **[ThinkStream]**：clipごとに推論テキストを生成してKVとして残す。古い映像のKVは窓の外に出たら捨て、推論のKVは溜め続ける。
- **[MEMO]**：見た目の変化でchunkを区切り、元フレームを保存する。質問時はCLIPの類似度で上位3chunkを選んでフレームを渡す。
- **[StreamingVLM]**：1秒ごとに映像KVと実況テキストのKVを足し、予算を超えたら古い映像、次に古いテキストから捨てる。
- **[LiveVLM]**：届いたKVを短期窓に入れ、長期側はattentionの重要度で一定量だけ残す。質問時はページ単位で検索する。
- **[StreamChat]**：動きのあるフレームを溜め、まとめてk-meansで圧縮し、captionを付けて木の葉にする。親もまとめて作り、質問時は木を下りながら検索する。
- **[VideoStreaming]**：clipごとに前の状態と現在の特徴から64tokenの状態を作り、すべて溜める。質問時に関連する4つを選ぶ。
- **[ReKV]**：全フレームのKVをRAMやディスクに保存し、質問時に関連する64フレームのKVを取り出す。
- **[SAVEMem]**：短期・中期・長期の層へ順に押し出し、固定の仮の質問5つとの類似度で重要でないtokenを捨てる。
- **[MovieChat]**：短期の待ち行列が満杯になると、似た隣接フレームをまとめて長期Memoryへ移す。
- **[MA-LMM]**：フレーム特徴をMemoryに足し、長さの上限を超えたら似た隣接tokenを平均してまとめる。
- **[OmAgent]★**：シーンごとにcaptionを作り、時刻と一緒にDBへ保存する。質問時は時刻フィルタと検索で区間を取り出す。
- **[CogStream]**：過去のQAを追記し、質問時にLLMが関連するQAを選ぶ。映像は質問のたびに最初から処理し直す。
- **[StreamMind]**：毎フレーム、状態空間モデルで1tokenを作ってMemoryに入れる。gateがLLMを呼ぶかどうかを決める。
- **[R3-Streaming]**：届いたフレームの冗長なtokenを削り、古いものほど強く削る。
- **[StreamArena]**：4秒ごとにLLMがイベントの記録・代表フレーム・人や物の関係を書き、上限で上の層へまとめる。質問時はAgentが階層とグラフを検索し、フレームを見直す。
- **[Em-Garde]**：質問が届いたとき、LLMが「反応すべき出来事」の説明を数件作る。毎ステップ、直近2秒の映像と照合する。
- **[Memento]**：毎フレーム、直前のMemoryに融合するか、全体を少し更新するか、新しく追記するかを決める。質問との関連度で上位を選ぶ。
- **[QueryStream]**：質問に関係し、かつ新しい視覚tokenだけを残して追記する。
- **[ReWind]★**：質問を条件にしてフレームを2tokenに圧縮して溜める。最後に、質問との類似度で選んだフレームの高解像度特徴を取り直す。
- **[M3-Agent]**：30秒ごとに顔・声にIDを付け、出来事と知識のテキストをグラフに追加・強化する。質問時にAgentが繰り返し検索する。
- **[video-SALMONN S]**：推論しながら重み（状態）を更新し、別に冗長なtokenを捨てながらtokenのMemoryも持つ。
- **[ProtoKV]**：直近の窓から押し出されたtokenを、最も近いプロトタイプに統計として吸収する。
- **[TraveLER]★**：Agentが計画し、選んだフレームのcaptionと下位の質問・回答を記録する。足りなければ再計画する。

## 修正履歴

| 日時 | 変更 | 理由 |
| --- | --- | --- |
| 2026-10-14 | 初版作成：2回目の29本（分類26本、定義外3本）を調べ、1回目の15本と合わせて41本を分類A〜Gの表に並べた | ユーザー指示（全論文を探索して2回目の当てはめ） |

## 関連文書

- [判定基準メモ](2026-10-14-memory-retention-classification-criteria.md)
- [1回目の当てはめ](2026-10-14-memory-classification-round1.md)

[StreamAgent]: https://arxiv.org/abs/2508.01875
[OneStreamer]: https://arxiv.org/abs/2610.01762
[Lando et al.]: https://arxiv.org/abs/2506.16450
[Think While Watching]: https://arxiv.org/abs/2603.11896
[StreamForest]: https://papers.neurips.cc/paper_files/paper/2025/hash/6dd91fec726dbed8915a1fbadd91d1d2-Abstract-Conference.html
[EventMemAgent]: https://arxiv.org/abs/2602.15329
[OASIS]: https://openaccess.thecvf.com/content/CVPR2026/html/Liang_OASIS_On-Demand_Hierarchical_Event_Memory_for_Streaming_Video_Reasoning_CVPR_2026_paper.html
[VideoLLaMB]: https://openaccess.thecvf.com/content/ICCV2025/html/Wang_VideoLLaMB_Long_Streaming_Video_Understanding_with_Recurrent_Memory_Bridges_ICCV_2025_paper.html
[MuKV]: https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_MuKV_Multi-Grained_KV_Cache_Compression_for_Long_Streaming_Video_Question-Answering_CVPR_2026_paper.html
[StreamMem]: https://openreview.net/forum?id=siAEqckmUs
[Flash-VStream]: https://openaccess.thecvf.com/content/ICCV2025/html/Zhang_Flash-VStream_Efficient_Real-Time_Understanding_for_Long_Video_Streams_ICCV_2025_paper.html
[SVMemAgent]: https://openreview.net/forum?id=E0LVxLc5Pw
[VideoAgent]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/3241_ECCV_2024_paper.php
[VideoMultiAgents]: https://arxiv.org/abs/2504.20091
[Response-G1]: https://aclanthology.org/2026.acl-long.2042/
[ProVideLLM]: https://openaccess.thecvf.com/content/ICCV2025/html/Chatterjee_Streaming_VideoLLMs_for_Real-Time_Procedural_Video_Understanding_ICCV_2025_paper.html
[Lando Edge]: https://arxiv.org/abs/2602.22455
[Watch-Think-Interact]: https://arxiv.org/abs/2609.37035
[ThinkStream]: https://arxiv.org/abs/2603.12938
[MEMO]: https://arxiv.org/abs/2609.38900
[StreamingVLM]: https://iclr.cc/virtual/2026/poster/10008145
[LiveVLM]: https://arxiv.org/abs/2505.15269
[StreamChat]: https://proceedings.iclr.cc/paper_files/paper/2025/hash/ad2fa437f7c23e4e9875599c6065d18a-Abstract-Conference.html
[VideoStreaming]: https://proceedings.neurips.cc/paper_files/paper/2024/file/d7ce06e9293c3d8e6cb3f80b4157f875-Paper-Conference.pdf
[ReKV]: https://proceedings.iclr.cc/paper_files/paper/2025/file/67a9b444cbcd647572c88194619f72d5-Paper-Conference.pdf
[SAVEMem]: https://arxiv.org/abs/2605.07897
[MovieChat]: https://openaccess.thecvf.com/content/CVPR2024/html/Song_MovieChat_From_Dense_Token_to_Sparse_Memory_for_Long_Video_CVPR_2024_paper.html
[MA-LMM]: https://openaccess.thecvf.com/content/CVPR2024/html/He_MA-LMM_Memory-Augmented_Large_Multimodal_Model_for_Long-Term_Video_Understanding_CVPR_2024_paper.html
[OmAgent]: https://aclanthology.org/2024.emnlp-main.559/
[CogStream]: https://ojs.aaai.org/index.php/AAAI/article/view/38336
[StreamMind]: https://openaccess.thecvf.com/content/ICCV2025/html/Ding_StreamMind_Unlocking_Full_Frame_Rate_Streaming_Video_Dialogue_through_Event-Gated_ICCV_2025_paper.html
[R3-Streaming]: https://arxiv.org/abs/2605.17921
[StreamArena]: https://arxiv.org/abs/2608.05703
[Em-Garde]: https://arxiv.org/abs/2603.19054
[Memento]: https://proceedings.iclr.cc/paper_files/paper/2026/hash/3b5f4587a0bdb81ecc6ce9d82320a5c2-Abstract-Conference.html
[QueryStream]: https://openreview.net/forum?id=738HjJEbml
[ReWind]: https://openaccess.thecvf.com/content/CVPR2025/html/Diko_ReWind_Understanding_Long_Videos_with_Instructed_Learnable_Memory_CVPR_2025_paper.html
[M3-Agent]: https://iclr.cc/virtual/2026/poster/10009685
[video-SALMONN S]: https://icml.cc/virtual/2026/poster/61140
[ProtoKV]: https://arxiv.org/abs/2606.26762
[TraveLER]: https://arxiv.org/abs/2404.01476
[VideoTree]: https://openaccess.thecvf.com/content/CVPR2025/html/Wang_VideoTree_Adaptive_Tree-based_Video_Representation_for_LLM_Reasoning_on_Long_CVPR_2025_paper.html
[VideoAgent-Wang]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/10325_ECCV_2024_paper.php
[VideoINSTA]: https://aclanthology.org/2024.findings-emnlp.384/
