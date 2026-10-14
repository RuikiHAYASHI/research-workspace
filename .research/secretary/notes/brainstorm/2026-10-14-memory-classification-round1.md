---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-10-14 MTG: 問いに関連する論文候補を一覧化し、設定・Memory形式・保存単位・更新／検索方法を比較する"
topic: memory-classification-round1
status: exploratory
tags: [brainstorm, literature-review, memory, taxonomy, classification, streaming-videoqa]
---

# Memory保持形式の分類：1回目の当てはめ（15本）

## 位置づけ

- [判定基準メモ](2026-10-14-memory-retention-classification-criteria.md)の手順に従い、AIだけで15本を当てはめた1回目の結果。
- 下の1〜3の表は、2026-10-14時点の最新の分類（A〜G）で並べ直したもの。**1本の論文に、1つの分類から1つのコードだけ**を付けている（判定基準メモの基準2）。
  - 既定の方式（選ばない、追記のみ、時刻順に並べるだけ、全部渡す）はコードなし（`—`）。
  - 2本以上で出た組み合わせは「複合」コードにした。
  - 1つに絞るために落とした要素は、各表の下の「備考」に書いた。
- 「4. 追加・統合・修正の提案」以降は、提案時点の旧コード（C1〜C16など）で書かれている。新旧の対応は判定基準メモの対応表を参照する。
- 論文名のリンクは学会公式ページを優先し、無い場合はarXivとした（基準4）。発表先の詳細は付録Aを参照する。
- 表記：`?` は判定に迷いがあるもの。
- 記述の区別：「著者の主張」「実験で示されたこと」「私たちの推論（推論と明記）」「未確認」。

## 1. 分類A：記憶する情報

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| A0 | 映像そのもの | 映像を保存するだけで、何が映っているかは書かない | [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent] | 4 |
| A1 | 場面の説明 | 場所・人や物・動作を、文章などでまとめて書く | [StreamAgent], [Lando et al.], [VideoMultiAgents], [Response-G1] | 4 |
| A2 | 人・物ごとの記録 | 人や物1つにつき1件の記録を持ち、時間を通して追う | [VideoAgent] | 1 |
| A3a | イベント：区切りに使うだけ | イベントの切れ目で保存単位を分けるが、中身は映像そのもの | [StreamForest], [VideoLLaMB] | 2 |
| A3b | イベント：出来事を記録 | イベントごとに「何が起きたか」を書く | [OneStreamer], [Think While Watching], [EventMemAgent], [OASIS] | 4 |
| A4 | タスクの状態 | 質問への取り組みの途中経過を書く | （中心のコードとしては該当なし。[OASIS]が備考に該当） | 0 |

備考（1つに絞るために落とした要素）：
- [StreamAgent]：KV（映像そのもの）も持つ。判定ルール「映像と記述の両方なら記述の側」によりA1。
- [EventMemAgent]・[OASIS]・[Think While Watching]：代表フレームやKVなど映像も持つ。同じルールでA3b。
- [OASIS]：過去のQAをまとめた要約（A4）も持つ。中心はイベントの木なのでA3b。
- [VideoAgent]：2秒ごとのcaption（A1）も持つ。特徴的なのは人・物の表なのでA2。
- [VideoMultiAgents]：直前のgraphを参照するので、個体を追っている（A2）可能性がある。

## 2. 分類B：表現形式

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| B1 | 文章 | 自由に書いた文 | [OneStreamer], [Lando et al.] | 2 |
| B2 | 項目付きの記録 | 時刻や内容が欄に分かれている | [VideoAgent] | 1 |
| B3 | グラフ | 物と関係を点と線で表す | [VideoMultiAgents], [Response-G1] | 2 |
| B4 | 画像 | フレームを画像のまま残す | [SVMemAgent] | 1 |
| B5 | 視覚特徴 | 画像をエンコーダで数値に変換して残す | [StreamForest], [Flash-VStream] | 2 |
| B6 | KV cache | LLMが過去の入力を読んだときの内部データを残す | [MuKV], [StreamMem] | 2 |
| B7 | 内部状態 | 決まった大きさの数値を毎回更新して持ち越す | [VideoLLaMB] | 1 |
| B8 | 記録＋画像（複合） | 項目付きの記録と、その根拠になる画像を組で持つ | [EventMemAgent], [OASIS] | 2 |
| B9 | 文章・記録＋KV（複合） | 文章や記録と、過去入力のKVを並行して持つ | [StreamAgent], [Think While Watching]? | 2 |

備考：
- 検索の目印にだけ使うembeddingはコードにしない。持っている論文：[StreamAgent], [EventMemAgent], [OASIS], [SVMemAgent], [VideoAgent], [Response-G1]。
- [VideoAgent]：captionも区間番号付きで表に入るのでB2にまとめた。
- [VideoMultiAgents]：テキスト担当のAgentが持つcaption（B1）もある。中心はgraphなのでB3。
- [Response-G1]：保存はグラフ、LLMへは文章にして渡す。
- [Think While Watching]：過去の視覚KVを保持しているかは推定（`?`）。保持していなければB2になる。

## 3. 分類C〜G：管理方式

### 分類C：書き込みタイミング

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C1 | 届くたび | フレームが届くたびに書く | [Flash-VStream], [SVMemAgent] | 2 |
| C2 | 一定間隔 | 数秒ごとなど、決まった間隔で書く | [StreamAgent], [Lando et al.], [Think While Watching], [OASIS], [MuKV], [StreamMem], [VideoAgent], [Response-G1] | 8 |
| C3 | 切れ目で | 映像が変わった所で区切って書く | [VideoLLaMB], [VideoMultiAgents], [OneStreamer]?（学習したモデルが切れ目で書く） | 3 |
| C4 | 短期は届くたび・長期は切れ目で（複合） | 届いたものをまず短期に入れ、切れ目ごとに長期へ移す | [StreamForest], [EventMemAgent] | 2 |

### 分類D：書き込みの選別

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 選ばない（既定） | 届いたものをそのまま残す | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [VideoLLaMB], [VideoAgent] | 8 |
| D1 | 質問に関係するもの | 実際の質問に関係する内容を選んで残す | [VideoMultiAgents], [Response-G1]? | 2 |
| D2 | 質問に依存しない重要度 | 質問が分からないまま、汎用の物差しで「役立ちそうなもの」を残す | [MuKV]（注目度）, [StreamMem]（仮の質問）, [Flash-VStream]（頻度）, [SVMemAgent]（学習した方針）, [Lando et al.]?（汎用の質問テンプレート） | 5 |

### 分類E：更新

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 追記のみ（既定） | 既存は変えず、新しい記録を足すだけ | [OneStreamer], [Lando et al.], [Think While Watching], [MuKV], [VideoMultiAgents], [Response-G1] | 6 |
| E1 | 全体を書き直す | 毎回Memory全体を作り直す（私たちのbaseline） | [StreamAgent]（テキスト側） | 1 |
| E2 | まとめる・縮める | 似た記録を1つにする、データ量を減らす | [StreamForest], [OASIS], [VideoLLaMB], [VideoAgent] | 4 |
| E3 | 捨てる・入れ替える | 古い・不要な記録を消す、別の記録と入れ替える | [SVMemAgent] | 1 |
| E4 | まとめて、溢れたら捨てる（複合） | 縮めたうえで、容量を超えたら捨てる | [EventMemAgent], [StreamMem], [Flash-VStream] | 3 |

備考：
- [OASIS]：過去のQAの要約は毎回全体を書き直す（E1）。中心はイベントの木なのでE2。
- [VideoAgent]：同じ物体の記録を統合する（re-ID）ためE2。

### 分類F：構造

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 時刻順に並べるだけ（既定） | 記録を時間順に並べるだけ | [Lando et al.], [Think While Watching], [VideoLLaMB], [StreamMem], [SVMemAgent], [VideoMultiAgents], [Response-G1] | 7 |
| F1 | 短期と長期に分ける | 直近の詳しい記録と、古い記録の置き場を分ける | [StreamAgent], [StreamForest], [EventMemAgent] | 3 |
| F2 | 親子の階層 | 粗いまとめ（親）と細かい記録（子）をつなぎ、子も実際に読み出せる | [OASIS] | 1 |
| F3 | 並列ストア | 同じ時間を、細かさや見方の違う複数のMemoryに同時に保存する | [MuKV], [Flash-VStream], [VideoAgent], [OneStreamer]? | 4 |

備考：
- [StreamForest]：「tree」と名乗るが、子を読み出さないためF2ではなくF1。
- [OASIS]：短期の映像窓も持つ（F1の要素）。中心は親子の木なのでF2。
- [OneStreamer]：局所のcaptionとイベントの要約を並べて持つためF3とした（`?`）。直近の視覚tokenは現在の入力窓なのでMemoryに数えない（基準0）。

### 分類G：読み出し

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| — | 全部渡す（既定） | Memory全体をLLMに入力する | [OneStreamer], [Lando et al.], [Think While Watching], [StreamForest], [VideoLLaMB], [StreamMem], [SVMemAgent], [VideoMultiAgents] | 8 |
| G1 | 検索して一部渡す | 時刻・意味・質問で選んだ記録だけを渡す | [StreamAgent], [MuKV], [Response-G1] | 3 |
| G2 | 詳細を見直す | 保存済みの画像・特徴をもう一度見る | [Flash-VStream] | 1 |
| G3 | 検索してから詳細を見直す（複合） | 記録を検索で選び、その保存済み画像・特徴を見直す | [OASIS], [VideoAgent], [EventMemAgent]? | 3 |

備考：
- [StreamAgent]：テキストの要約は全部渡し、KVは検索して渡す。違いを生むKV側の方式を採ってG1。
- [OASIS]：最初は粗い情報を全部渡し、答えられないときだけ検索して見直す。
- [VideoLLaMB]：過去の状態の列からcross-attentionで取り出すが、これは内部の状態更新に使うものでLLMへの入力の選び方ではないため、既定とした。

## 補足：設定・判断主体・容量上限の列（Memoryの小分類ではない）

| 項目 | 値 | 該当論文 |
| --- | --- | --- |
| 処理設定 | streaming | [StreamAgent], [OneStreamer], [Lando et al.], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [StreamMem], [Flash-VStream]（著者の主張）, [SVMemAgent], [Response-G1] |
| 処理設定 | offline | [VideoAgent], [VideoMultiAgents], [VideoLLaMB]（streaming変種あり） |
| Query時点 | 開始時から既知 | [VideoMultiAgents] |
| Query時点 | 途中で届く | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [Flash-VStream], [Response-G1] |
| Query時点 | 事前に不明 | [Lando et al.], [StreamMem], [SVMemAgent], [MuKV] |
| Query時点 | 動画の終了後 / 未確認 | [VideoAgent]（動画全体をMemoryにした後）, [VideoLLaMB]（未確認） |
| 区切り方 | 固定時間 | [StreamAgent], [Lando et al.], [MuKV], [StreamMem], [VideoAgent], [Response-G1] |
| 区切り方 | 見た目の変化 | [StreamForest], [EventMemAgent], [VideoLLaMB] |
| 区切り方 | 意味の変化 | [VideoMultiAgents]（方法は未記載） |
| 区切り方 | 学習したモデルの判断 | [OneStreamer] |
| 区切り方 | 複合・その他 | [OASIS]（固定窓＋後から意味でマージ）, [Think While Watching]（質問の到着時刻＋固定） |
| 区切り方 | なし | [Flash-VStream], [SVMemAgent] |
| 容量上限 | あり | [StreamForest], [StreamMem], [SVMemAgent] |
| 容量上限 | 一部あり | [EventMemAgent]（短期のみ）, [OASIS]（親の数のみ。子は残る）, [Flash-VStream]（Feature Bankは増える）, [VideoLLaMB]（過去状態の列は増える） |
| 容量上限 | なし（際限なく増える、または記述なし） | [StreamAgent]（KV）, [OneStreamer], [Lando et al.], [Think While Watching], [MuKV], [VideoAgent], [VideoMultiAgents], [Response-G1] |

- Query時点の値は重なりがある（[MuKV]が2か所に入っている）。「書き込み時に質問を知っているか」の3値へ置き換える案を検討中。

### 判断主体（書き込み／読み出し）

すべてAIによる当てはめ（`AI推定`）。

| 判断主体 | 書き込み | 読み出し |
| --- | --- | --- |
| 規則（固定の手順・閾値） | [StreamAgent], [Lando et al.], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [StreamMem], [Flash-VStream], [VideoAgent], [VideoMultiAgents], [Response-G1] | [StreamAgent], [OneStreamer], [Lando et al.], [Think While Watching], [StreamForest], [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [Response-G1] |
| 学習モジュール（専用の小さなネットワーク） | [VideoLLaMB], [SVMemAgent] | [VideoLLaMB]（内部の状態更新） |
| LLM・Agent（推論やツール呼び出し） | — | [EventMemAgent], [OASIS]（答えられないときだけ検索）, [VideoAgent], [VideoMultiAgents]（ツールの呼び出しのみ） |
| モデル自身の生成（回答と同じモデルが記録を出力） | [OneStreamer], [Think While Watching] | — |

- この15本では、書き込みをLLM・Agentが推論で決める論文はなかった（未確認）。

## 4. 追加・統合・修正の提案

各提案に、判定基準メモの条件と根拠論文を付けた。採否はユーザーと決める。

| # | 提案 | 種類 | 判定条件 | 根拠論文 | 状態 |
| --- | --- | --- | --- | --- | --- |
| 1 | 書き込みを「いつ書くか（タイミング）」と「何を残すか（選別基準）」に分ける | 分割 | C2が半数超。C1〜C3とC4〜C6が1本の論文で同時に付く | [MuKV], [StreamMem], [EventMemAgent] | **採用** |
| 2 | 選別基準に「質問に依存しない重要度」（attention・代理クエリ・密度・学習した方策）を新設 | 追加 | 既存コードに収まらない流れが2本以上で、研究の問いに関係 | [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent] | **採用** |
| 3 | 構造に「並列ストア」（粒度・解像度・視点の違うMemoryを同時に持つ）を新設 | 追加 | C11〜C13に収まらない構造が3本 | [MuKV], [Flash-VStream], [VideoAgent] | **採用** |
| 4 | 書き込み・読み出しの「判断主体」（規則／学習モジュール／LLM Agent／モデル自身の生成）を列で記録 | 列の追加 | C6が書き込み専用で、読み出し側の判断を表せない論文が3本 | [EventMemAgent], [OASIS], [VideoAgent] | **採用** |
| 5 | A1とA3を「一般的な場面記述」に統合し、A2はEntityを独立した単位（ID・node・表の行）で持つ場合だけにする | 統合 | A1・A2・A3がcaption系の論文で常にセットで出る | [OneStreamer], [Lando et al.], [Think While Watching] | **採用** |
| 6 | 「質問による誘導」をA5からCの選別基準へ移し、A5は「タスクの状態（QA履歴・仮説など）」に絞る | 移動 | 分類間の重複（A5とCの質問関連が常にセット） | [Response-G1], [VideoMultiAgents], [Lando et al.] | **採用** |
| 7 | コードは増やさず判定ルールを明確にする（下記7-1〜7-6） | ルール | — | 下記 | **採用** |

### 提案の補足

- **提案2の研究上の意味（推論）**：4本とも「質問は未知だが、何らかの重要度で選ぶ」。私たちの設定は質問が開始時に既知なので、「質問との関連」で選べる。この違いが比較点になりうる。
- **提案4の推奨**：Agentの役割は大枠の「Agent」軸で扱う予定なので、Memory軸の中でコードを細かく増やさず、列として記録してAgent軸の材料にする。
- **提案6の内訳**：A5には中身の違う3種類が混在している。

  | 中身 | 該当論文 | 提案後の扱い |
  | --- | --- | --- |
  | 実際の質問に誘導された内容 | [Response-G1], [VideoMultiAgents] | Cの選別基準「質問との関連」へ |
  | 想定される質問・質問の分布に誘導された内容 | [Lando et al.]（汎用質問テンプレート）, [SVMemAgent]（学習による。推論） | Cの選別基準へ（提案2とも関係） |
  | 対話・QA履歴 | [OASIS] | A5に残す（単独例） |

- **提案7：判定ルールの明確化**

  | # | ルール | 適用例 |
  | --- | --- | --- |
  | 7-1 | 時刻や項目を独立した属性として持つならB2、文中に時刻が書かれているだけならB1 | B1：[OneStreamer]／B2：[Think While Watching], [EventMemAgent], [OASIS] |
  | 7-2 | Bは保存形式で判定し、LLMへの入力形式は備考に書く | [Response-G1]（保存B3、入力B1） |
  | 7-3 | 子nodeを実際に参照できる場合だけC13。名前だけの「tree」は中身で判定する（基準1） | [StreamForest]はroot nodeだけを読むのでC12、[OASIS]はC13 |
  | 7-4 | C16は「保存済みの詳細データ（key frame・高解像度特徴）の再参照」と定義し直す。元動画を見直すかは処理設定の列で表す | [OASIS], [Flash-VStream], [VideoAgent] |
  | 7-5 | 固定区間のcaptionはA4bとしない。A4bは区間が出来事として扱われる場合に限る | [VideoAgent]をA4bから外す |
  | 7-6 | 追記（C7）は違いを生まないため、代わりに「容量上限：あり／なし」を記録する | C7が11本。Summaryの肥大化の懸念とも関係 |

### 保留（単独例）

| 内容 | 該当論文 | 備考 |
| --- | --- | --- |
| 前状態を条件にした逐次生成 | [VideoMultiAgents] | [Lando et al.]では任意の設定で、使うと精度が低下 |
| 質問の到着時刻による区切り | [Think While Watching] | — |
| 書き込みがモデル自身の出力tokenそのもの | [OneStreamer], [Think While Watching] | 提案4の判断主体の列で表せるのでコードは作らない |
| B7（潜在・再帰状態） | [VideoLLaMB] | 2回目で他の該当論文を探す |
| C5（質問との関連で残す） | [Response-G1] | 提案6を採用すると該当が増える |

## 5. 当てはめから見えたこと（私たちの推論）

1. **「Event」の中身と区切り方は一致しない**：出来事の記述（A4b）を持つ論文はあるが、区切りに使う信号は見た目の変化（[StreamForest], [EventMemAgent]）か固定窓（[OASIS]）が中心だった。意味的な区切りは、学習したモデルの判断（[OneStreamer]）と、方法が未記載の[VideoMultiAgents]だけ。15本の範囲での観察であり、一般化はしない。
2. **質問が開始時から既知のstreaming設定は、この15本では見当たらない**：streaming論文の質問は「途中で届く」か「事前に不明」で、開始時から既知なのはofflineの[VideoMultiAgents]だけ。streaming論文で「質問に関係するもの」を選んで書く（C5）のは[Response-G1]だけで、それも質問が届く前の扱いが不明。比較の仕方を考える材料になるが、「存在しない」とは断定しない（未確認）。
3. **累積テキストの書き直し（C8）はまれ**：私たちのbaselineと同じC8は[StreamAgent]（テキスト側）と[OASIS]（QA summary）だけ。[StreamAgent]の著者は、再帰要約で初期の細部が失われることを認め、KVで補っている。私たちの「Summaryの情報脱落」の懸念と同じ方向の著者の主張だが、私たちの設定で検証したわけではない。
4. **前の記述を条件にすると悪化する報告がある**：[Lando et al.]では、直前の記述を入れると精度が下がった（実験結果。著者の解釈は誤りの雪だるま式の増幅）。私たちのSummary Agentは直前のSummaryを入力にしているので、関連する知見として残す。

## 6. 未確認・要確認

- [EventMemAgent]の発表先：既存メモ（[3論文Level 2試験調査](2026-10-14-three-paper-memory-level2-pilot.md)）では「ECCV 2026 Springer論文集で確認」とあるが、今回は著者GitHubの記載しか見つからなかった。
- [Think While Watching]の採録（GitHubの自己申告のみ）。[Lando et al.]のSpringer公式ページ。
- [StreamForest]・[EventMemAgent]・[VideoLLaMB]は要約経由の読み取りを含むため、節番号・数値は原文で再確認が必要。
- [Response-G1]：質問が届く前のgraphの作り方が不明（2026-10-14にarXiv HTMLで再確認）。
  - 著者の記述：各clipのgraph生成を質問で条件付けている（"we condition the scene graph generation on the user query"、G_t = S(C_t; Q)）。Memoryは開始時からのgraphの列 {G_1, …, G_t} である。
  - 書かれていないこと：質問は途中（t_ask）で届くのに、それより前のclipのgraphをどう作るか（質問なしで作るのか、質問が届いてから作り直すのか）。
  - 確実に言えること：質問は読み出し（質問をgraphにして類似graphを検索）と回答に使われる。
  - このためC5は `?` とした。clipが時刻tを中心にしており、未来のフレームを含む可能性がある点も未解決。
- [VideoLLaMB]：QAでのQuery時点と、LLMへ何を渡すか。
- [MuKV]：過去KVの保存先（GPUかCPUか）と、全履歴にattentionするかどうか。

## 7. 次に決めること

1. （済）提案1〜7はすべて採用し、判定基準メモへ反映した（2026-10-14）。
2. （済）1本の論文に同じ分類のコードが多く付く問題：既定はコードなし＋複合コードで対処し、分類をA〜Gに分けた（2026-10-14）。
3. Query時点の値の整理（検討中）。
4. 2回目で探す対象：単独例・未確認の小分類（B7、C5、A5の新しい定義、質問が開始時から既知のstreaming論文）を埋める候補。

## 付録A：対象論文と発表先

| 論文 | 発表先 | 根拠の確かさ | arXiv |
| --- | --- | --- | --- |
| [StreamAgent] | arXiv（採録未確認） | 原文 | 2508.01875 |
| [OneStreamer] | arXiv（採録未確認） | 原文 | 2610.01762 |
| [Lando et al.] | ICIAP 2025（著者ページ記載。Springer公式ページ未確認。表のリンクはarXiv） | 原文 | 2506.16450 |
| [Think While Watching] | arXiv（採録未確認。GitHub READMEに「ECCV 2026」とあるが公式未確認） | 原文 | 2603.11896 |
| [StreamForest] | NeurIPS 2025 | 原文（要約経由） | 2509.24871 |
| [EventMemAgent] | 要確認（上記6） | 原文（要約経由） | 2602.15329 |
| [OASIS] | CVPR 2026 | 原文 | 2604.17052 |
| [VideoLLaMB] | ICCV 2025（公式題：Long Streaming Video Understanding with Recurrent Memory Bridges） | 原文（要約経由） | 2409.01071 |
| [MuKV] | CVPR 2026 | 原文 | 2605.22269 |
| [StreamMem] | CVPR 2026 Workshop（VidLLMs、Poster）。ICLR 2026は不採択 | 原文 | 2508.15717 |
| [Flash-VStream] | ICCV 2025 | 原文 | 2506.23825 |
| [SVMemAgent] | ECCV 2026 Workshop（WearableAI） | 原文 | 2609.18540 |
| [VideoAgent] | ECCV 2024（Fan et al., Memory-augmented。Wang et al.の同名論文とは別） | 原文 | 2403.11481 |
| [VideoMultiAgents] | arXiv（採録未確認） | 原文＋コード | 2504.20091 |
| [Response-G1] | ACL 2026（Long） | 原文 | 2605.07575 |

- 「原文（要約経由）」：本文全体を直接取得できず、要約・抜粋を経由した読み取りを含む。

## 付録B：各論文のMemoryのデータフロー

- **[StreamAgent]**：clipごとに視覚KVを長期KV（CPU）へ追記する。同時に、caption C_t からテキストmemory m_t を再帰更新する。回答時は、質問とkeyの類似度でKVを取り出す。テキストの再帰要約で初期の細部が失われることを、著者自身が認めている。
- **[OneStreamer]**：各時刻にモデル自身が `</Observe>`（局所caption）・`</Summary>`（完了eventの要約）・`</Silence>` を生成し、captionを追記する。古い視覚tokenはFIFOで外れるが、captionは残る。全記録を直近の視覚tokenと一緒に渡す。
- **[Lando et al.]**：固定clipごとに外部MLLMがテキスト記述を作り、追記する。質問時にMemory全体を推論用LLMへ渡す。直前の記述を条件に入れると精度が下がった（Table 3）。
- **[Think While Watching]**：segmentごとに、欄構成（Focus / Evidence / State update）のnoteを生成して追記する。質問時は、全noteと受信済みの映像にattentionをかけて回答する。
- **[StreamForest]**：短期窓から溢れた視覚tokenを、類似度が極小の位置で区切ってevent nodeにする。上限を超えると、隣接nodeをtoken mergeで統合する。質問時はroot nodeすべてと短期窓を渡す。
- **[EventMemAgent]**：短期Memory（STM）のeventが溢れると、長期Memory（LTM）へ「代表フレーム＋caption＋embedding＋変化ログ」として移す。質問時はAgentが検索・OCR・物体検出を選んで呼ぶ。
- **[OASIS]**：固定窓ごとに「key frame＋MLLM要約＋embedding」の葉nodeを作り、類似した隣接nodeをマージして木にする。質問時は、まず粗い情報だけで回答を試み、不十分なときだけforestを検索してkey frameを追加する。
- **[VideoLLaMB]**：segmentごとに、memory token（32 token）を再帰的に更新する。過去のmemory tokenの列からcross-attentionで情報を取り出し、状態の更新に使う。
- **[MuKV]**：8秒segmentごとに、3粒度のKVをattentionと周波数のスコアで選別し、時刻付きで保存する。質問時は粒度ごとに検索し、粗い粒度から細かい粒度へrerankする。
- **[StreamMem]**：類似フレームを統合し、汎用の代理クエリ（chat template）からのattentionで重要なtokenを残して、固定予算のKVを保つ。質問時は全体を使う。
- **[Flash-VStream]**：低解像度特徴をクラスタ重心として統合（CSM）し、大きなクラスタに対応するフレームの高解像度特徴をFeature Bankから取り直す（DAM）。質問時は全体を渡す。
- **[SVMemAgent]**：学習したAgentが、新しいフレームを捨てるか、どのslotと入れ替えるかを決める。質問時は固定slotのフレームを凍結VideoLLMへ渡す。
- **[VideoAgent]**：動画全体を2秒segmentのcaptionと特徴に変換し、物体の追跡・同一性判定の結果をSQLに入れる（offline）。質問時はLLMが4種のツールでMemoryを検索し、元segmentも見直す。
- **[VideoMultiAgents]**：意味の変化で区切ったchunkごとに、直前のgraphを参照しながらscene graphを生成する（offline）。Graph Agentが全graphをテキストとして受け取る。
- **[Response-G1]**：各時刻のclipからscene graphを生成し、テキスト化と埋め込みをして追記する。質問をgraphに変換して類似graphを検索し、黙るか応答するかを判断する。

## 修正履歴

| 日時 | 変更 | 理由 |
| --- | --- | --- |
| 2026-10-14 | 初版作成（論文別の対応表を中心とした構成） | 1回目の当てはめ結果の記録 |
| 2026-10-14 | 構成を変更：分類の定義と該当論文を隣り合わせにした表を先頭に置き、論文名を短い名前のリンクにした。論文別の詳細は付録へ移した。内容（判定結果・提案）は変更なし | 論文別の多列表が見づらいため（ユーザー指示） |
| 2026-10-14 | 定義を短い平易な文に書き直した。提案4（判断主体の列）と提案6（A5の質問誘導をC5へ移動）を採用し、該当論文を移した。判断主体の表を追加した | 定義が分かりにくかったため。提案4・6はユーザーが採用 |
| 2026-10-14 | 提案1〜7をすべて採用し、1〜3の表を新しい分類で並べ直した（A3・C6・C7は欠番、C17・C18を新設）。A4の名前に「イベント」を明記。Query時点「Memory構築後」を「動画の終了後」に改称。容量上限の列を追加。Response-G1の原文を再確認し未確認事項を更新 | ユーザーが提案をすべて採用。A4が分かりにくいとの指摘 |
| 2026-10-14 | 分類をA〜Gに分けて番号を振り直し、1〜3の表を「1つの分類に1つのコード」で並べ直した（既定はコードなし、複合コードB8・B9・C4・E4・G3、落とした要素は備考へ） | 同じ分類のコードが多く付くのを避けるため、C18まで番号が伸びて分かりにくかったため（ユーザー指示） |

## 関連文書

- [判定基準メモ](2026-10-14-memory-retention-classification-criteria.md)
- [3論文Level 2試験調査](2026-10-14-three-paper-memory-level2-pilot.md)
- [Awesome Streaming Memory仕分け](2026-10-13-awesome-streaming-memory-paper-priorities.md)
- [オンライン動画Agent候補](2026-10-13-online-streaming-video-agent-literature-candidates.md)
- [offline VideoQA Agent](2026-10-13-offline-videoqa-agents-memory-related-work.md)
- [予習AgentとText Memory](2026-10-14-anticipation-and-text-memory-literature.md)

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
