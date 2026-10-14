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

- [判定基準メモ](2026-10-14-memory-retention-classification-criteria.md)の手順（分類A / B / C、基準0〜4）に従い、AIだけで15本を当てはめた1回目の結果。
- 小分類の定義は判定基準メモのまま（まだ変更していない）。変更案は「4. 追加・統合・修正の提案」にまとめた。
- 論文名のリンクは学会公式ページを優先し、無い場合はarXivとした（基準4）。発表先の詳細は付録Aを参照する。
- 表記：`?` は判定に迷いがあるもの、`(補)` は補助的な要素。
- 記述の区別：「著者の主張」「実験で示されたこと」「私たちの推論（推論と明記）」「未確認」。

## 1. 分類A：記憶する情報

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| A0 | 意味を絞らない視覚内容 | フレーム・視覚token・KVをそのまま残し、何が写っているかを選んでいない | [StreamAgent], [StreamForest], [EventMemAgent], [OASIS], [VideoLLaMB], [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent] | 9 |
| A1 | Scene（場面・環境） | 場所や全体状況の記述 | [OneStreamer], [Lando et al.], [Think While Watching] | 3 |
| A2 | Entity（人・物体） | 個体ごとに同一性・属性・位置などを持つ | [OneStreamer], [Lando et al.], [Think While Watching], [VideoAgent], [VideoMultiAgents], [Response-G1] | 6 |
| A3 | Action / State change（動作・状態変化） | 「何をした」「どう変わった」の記録 | [OneStreamer], [Lando et al.], [Think While Watching], [VideoMultiAgents], [Response-G1], [EventMemAgent]? | 5〜6 |
| A4a | Event：区切りの単位としてのみ使う | イベント境界でMemoryを区切るが、中身は意味を絞らない視覚内容 | [StreamForest], [VideoLLaMB] | 2 |
| A4b | Event：出来事の記述として保持する | 区間が「何の出来事か」をcaption・ラベル・開始/終了時刻などで持つ | [OneStreamer], [Think While Watching], [EventMemAgent], [OASIS], [VideoAgent]? | 4〜5 |
| A5 | Task-oriented（質問に向けた情報） | 質問に関係する証拠、仮説、予測、未確認事項 | [OASIS], [Response-G1], [Lando et al.](補), [VideoMultiAgents](補), [Think While Watching]?, [SVMemAgent]? | 2〜6 |

## 2. 分類B：表現形式

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| B1 | Free text（自由文） | 構造を持たない文章（caption、累積Summary） | [StreamAgent], [OneStreamer], [Lando et al.], [VideoAgent], [VideoMultiAgents], [Response-G1] | 6 |
| B2 | Structured text（構造化テキスト） | 項目・時刻などを持つ記録（JSON、時刻付きイベント記録、表） | [Think While Watching], [EventMemAgent], [OASIS], [VideoAgent], [VideoMultiAgents] | 5 |
| B3 | Graph（グラフ） | nodeとedgeで表す関係構造 | [VideoMultiAgents], [Response-G1] | 2 |
| B4 | Raw frame（生フレーム） | 画素のまま保存するフレーム・代表フレーム | [EventMemAgent], [OASIS], [SVMemAgent] | 3 |
| B5 | Visual feature / token（視覚特徴・token） | 視覚エンコーダの出力token・特徴・embedding | 主：[StreamForest], [Flash-VStream]／補：[StreamAgent], [EventMemAgent], [OASIS], [SVMemAgent], [VideoAgent], [Response-G1] | 主2・補6 |
| B6 | KV cache（時間を越えて保持） | LLM内部の層ごとのkey/valueを後の時点まで残す | [StreamAgent], [MuKV], [StreamMem], [Think While Watching]? | 3〜4 |
| B7 | Latent / recurrent state（潜在・再帰状態） | 繰り返し更新される内部状態・memory token | 主：[VideoLLaMB]／補：[SVMemAgent] | 主1・補1 |

## 3. 分類C：管理方式

### 書き込み：何を、いつ残すか

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C1 | 全部残す | 入力をすべて一度はMemoryに入れる | [StreamAgent], [StreamForest], [EventMemAgent], [Flash-VStream], [VideoAgent] | 5 |
| C2 | 一定間隔で残す | 固定長のclip・segmentごとに書く | [StreamAgent], [Lando et al.], [Think While Watching], [OASIS], [MuKV], [StreamMem], [VideoAgent], [Response-G1] | 8 |
| C3 | 境界・変化で残す | 見た目や意味の変化点で区切って書く | [StreamForest], [EventMemAgent], [VideoLLaMB], [VideoMultiAgents] | 4 |
| C4 | 類似度・冗長性で残す | 似たものを統合・除外して残す | [StreamMem], [Flash-VStream], [VideoAgent] | 3 |
| C5 | 質問との関連で残す | 実際の質問に関係するものを残す | [Response-G1] | 1 |
| C6 | Agentの判断で残す | 学習した方策やモデル自身が書くかどうかを決める | [OneStreamer], [SVMemAgent] | 2 |

### 更新：既存のMemoryをどう変えるか

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C7 | 追記 | 既存を変えずに新しい記録を足す | [StreamAgent], [OneStreamer], [Lando et al.], [Think While Watching], [EventMemAgent], [OASIS], [VideoLLaMB], [MuKV], [VideoAgent], [VideoMultiAgents], [Response-G1] | 11 |
| C8 | 全体の書き直し | 前のMemory全体と新情報から、Memory全体を作り直す（私たちのbaselineもここ） | [StreamAgent]（テキスト側）, [OASIS]（QA summary） | 2 |
| C9 | 統合・圧縮 | 複数の記録をまとめる、tokenを減らす | [StreamForest], [EventMemAgent], [OASIS], [VideoLLaMB], [StreamMem], [Flash-VStream], [VideoAgent] | 7 |
| C10 | 削除 | 記録を捨てる、入れ替える | [EventMemAgent], [StreamMem], [Flash-VStream], [SVMemAgent] | 4 |

### 構造：どう配置するか

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C11 | 時刻順の一列 | 記録を時間順に並べるだけ | [Lando et al.], [Think While Watching], [VideoLLaMB], [StreamMem], [SVMemAgent], [VideoMultiAgents], [Response-G1] | 7 |
| C12 | 短期＋長期 | 直近の詳細と長期の記録を分けて持つ | [StreamAgent], [OneStreamer], [StreamForest], [EventMemAgent], [OASIS] | 5 |
| C13 | 階層 | 粗い記録と細かい記録を親子関係で持つ | [OneStreamer], [OASIS], [MuKV]? | 2〜3 |

### 読み出し：回答時にどう使うか

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| C14 | 全部渡す | Memory全体をLLMの入力にする | [StreamAgent], [OneStreamer], [Lando et al.], [Think While Watching], [StreamForest], [OASIS], [StreamMem], [Flash-VStream], [SVMemAgent], [VideoMultiAgents] | 10 |
| C15 | 検索 | 時刻・意味・質問で一部を選んで渡す | [StreamAgent], [EventMemAgent], [OASIS], [MuKV], [VideoAgent], [Response-G1] | 6 |
| C16 | 元データの再参照 | 選んだ記録の詳細データを後から見直す | [OASIS], [VideoAgent], [Flash-VStream]? | 2〜3 |

## 補足：設定の列（Memoryの小分類ではない）

| 項目 | 値 | 該当論文 |
| --- | --- | --- |
| 処理設定 | streaming | [StreamAgent], [OneStreamer], [Lando et al.], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [StreamMem], [Flash-VStream]（著者の主張）, [SVMemAgent], [Response-G1] |
| 処理設定 | offline | [VideoAgent], [VideoMultiAgents], [VideoLLaMB]（streaming変種あり） |
| Query時点 | 開始時から既知 | [VideoMultiAgents] |
| Query時点 | 途中で届く | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [Flash-VStream], [Response-G1] |
| Query時点 | 事前に不明 | [Lando et al.], [StreamMem], [SVMemAgent], [MuKV] |
| Query時点 | Memory構築後 / 未確認 | [VideoAgent]（構築後）, [VideoLLaMB]（未確認） |
| 区切り方 | 固定時間 | [StreamAgent], [Lando et al.], [MuKV], [StreamMem], [VideoAgent], [Response-G1] |
| 区切り方 | 見た目の変化 | [StreamForest], [EventMemAgent], [VideoLLaMB] |
| 区切り方 | 意味の変化 | [VideoMultiAgents]（方法は未記載） |
| 区切り方 | 学習したモデルの判断 | [OneStreamer] |
| 区切り方 | 複合・その他 | [OASIS]（固定窓＋後から意味でマージ）, [Think While Watching]（質問の到着時刻＋固定） |
| 区切り方 | なし | [Flash-VStream], [SVMemAgent] |

## 4. 追加・統合・修正の提案

各提案に、判定基準メモの条件と根拠論文を付けた。採否はユーザーと決める。

| # | 提案 | 種類 | 判定条件 | 根拠論文 |
| --- | --- | --- | --- | --- |
| 1 | 書き込みを「いつ書くか（タイミング）」と「何を残すか（選別基準）」に分ける | 分割 | C2が半数超。C1〜C3とC4〜C6が1本の論文で同時に付く | [MuKV], [StreamMem], [EventMemAgent] |
| 2 | 選別基準に「質問に依存しない重要度」（attention・代理クエリ・密度・学習した方策）を新設 | 追加 | 既存コードに収まらない流れが2本以上で、研究の問いに関係 | [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent] |
| 3 | 構造に「並列ストア」（粒度・解像度・視点の違うMemoryを同時に持つ）を新設 | 追加 | C11〜C13に収まらない構造が3本 | [MuKV], [Flash-VStream], [VideoAgent] |
| 4 | 書き込み・読み出しの「判断主体」（規則／学習モジュール／LLM Agent／モデル自身の生成）を列で記録 | 列の追加 | C6が書き込み専用で、読み出し側の判断を表せない論文が3本 | [EventMemAgent], [OASIS], [VideoAgent] |
| 5 | A1とA3を「一般的な場面記述」に統合し、A2はEntityを独立した単位（ID・node・表の行）で持つ場合だけにする | 統合 | A1・A2・A3がcaption系の論文で常にセットで出る | [OneStreamer], [Lando et al.], [Think While Watching] |
| 6 | 「質問による誘導」をA5からCの選別基準へ移し、A5は「タスクの状態（QA履歴・仮説など）」に絞る | 移動 | 分類間の重複（A5とCの質問関連が常にセット） | [Response-G1], [VideoMultiAgents], [Lando et al.] |
| 7 | コードは増やさず判定ルールを明確にする（下記7-1〜7-6） | ルール | — | 下記 |

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
2. **質問が開始時から既知のstreaming設定は、この15本では見当たらない**：streaming論文の質問は「途中で届く」か「事前に不明」で、開始時から既知なのはofflineの[VideoMultiAgents]だけ。「質問との関連」で書き込みを選ぶ論文も[Response-G1]の1本だけ。比較の仕方を考える材料になるが、「存在しない」とは断定しない（未確認）。
3. **累積テキストの書き直し（C8）はまれ**：私たちのbaselineと同じC8は[StreamAgent]（テキスト側）と[OASIS]（QA summary）だけ。[StreamAgent]の著者は、再帰要約で初期の細部が失われることを認め、KVで補っている。私たちの「Summaryの情報脱落」の懸念と同じ方向の著者の主張だが、私たちの設定で検証したわけではない。
4. **前の記述を条件にすると悪化する報告がある**：[Lando et al.]では、直前の記述を入れると精度が下がった（実験結果。著者の解釈は誤りの雪だるま式の増幅）。私たちのSummary Agentは直前のSummaryを入力にしているので、関連する知見として残す。

## 6. 未確認・要確認

- [EventMemAgent]の発表先：既存メモ（[3論文Level 2試験調査](2026-10-14-three-paper-memory-level2-pilot.md)）では「ECCV 2026 Springer論文集で確認」とあるが、今回は著者GitHubの記載しか見つからなかった。
- [Think While Watching]の採録（GitHubの自己申告のみ）。[Lando et al.]のSpringer公式ページ。
- [StreamForest]・[EventMemAgent]・[VideoLLaMB]は要約経由の読み取りを含むため、節番号・数値は原文で再確認が必要。
- [Response-G1]：質問が届く前に作ったgraphも質問に誘導されているか。clipが時刻tを中心にしており、未来のフレームを含む可能性があるか。
- [VideoLLaMB]：QAでのQuery時点と、LLMへ何を渡すか。
- [MuKV]：過去KVの保存先（GPUかCPUか）と、全履歴にattentionするかどうか。

## 7. 次に決めること

1. 提案1〜7の採否。
2. 採用した変更を判定基準メモへ反映し、変更履歴に記録する。
3. 2回目で探す対象：単独例・未確認の小分類（B7、C5、A5の新しい定義、質問が開始時から既知のstreaming論文）を埋める候補。

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
