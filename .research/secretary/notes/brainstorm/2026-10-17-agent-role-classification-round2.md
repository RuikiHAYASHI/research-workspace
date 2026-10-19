---
date: 2026-10-17
project: agentic-streaming-videoqa
source_todo: "2026-10-14 2回目MTG: Memory保持以外の観点を2〜3個整理する（観点1：Agentの役割）"
topic: agent-role-classification-round2
status: exploratory
tags: [brainstorm, literature-review, agent, taxonomy, classification, task, streaming-videoqa]
---

# Agentの役割の分類：2回目

## 位置づけ

- 観点の優先度1位「Agentの役割」の分類の2回目。[1回目](2026-10-14-agent-role-classification-round1.md)の内容をすべて取り込み、分類A（モデルが担う段階）、分類C（判断の根拠）、評価タスクの表を作り直した。**このメモだけで1回目の情報もすべて読める。**
- 対象は1回目と同じ44本：[Memory分類の2回目当てはめ](2026-10-14-memory-classification-round2.md)の41本と、そこで「Memoryの定義外」とした3本（[VideoTree]★、[VideoAgent-Wang]★、[VideoINSTA]★）。この3本はAgent型の手法なので含めた。
- 根拠：
  - 1回目の当てはめは、AIが一次資料（arXiv HTML版、学会公式ページ、学会proceedings）を読んで行った。**林が原文で確認したものではない。**
  - 2回目は、1回目の判定根拠（付録B）と、Memory分類のメモ（[1回目](2026-10-14-memory-classification-round1.md)・[2回目](2026-10-14-memory-classification-round2.md)の表現形式とデータフロー）を組み合わせた。**論文は読み直していない。**
- 林からの指示（2026-10-17）：
  - 分類A、B、C…と評価タスクは、それぞれ独立した表にする。**1つの表の中で1本の論文は1行だけ。** 小分類がさらに分けられるときは、2段目・3段目の行を作る。
  - 1本が2つの小分類に当てはまるときは、統合した小分類（`O2+O4`など）を作る。
  - 分類Aでは、観測と読み出しを分ける。観測は「何を見るか」、残すは「frameかテキストか」で分ける。毎回書くnoteも、テキストで残すなら「残す」に入れる。計画は外す。
- 表記：
  - コードは観点を表す接頭辞を付けて `AGT-A` のように書く（Memory分類は `MEM-`）。表の中では接頭辞を省略する。
  - `★`：offlineの論文（動画全体を見られる設定）。`?`：判定が境界にあるもの（第5節）。
  - 記述は「著者の主張」「実験で示されたこと」「私たちの推論（推論と明記）」「未確認」を区別する。
  - 表の中で、同じ1段目・2段目が続くときは一番上の行にだけ書く。
- 論文名のリンクは学会公式ページを優先し、無い場合はarXivとした。全論文の公式URLとarXivのURLは付録Aにまとめた。

## 1. 「判断」として数えるもの（共通の前提）

「Agentを置くこと」と「Agentが実際に判断すること」は別、という区別（[重要な問いのメモ](2026-10-14-critical-literature-review-questions.md)のCritical 3）にもとづく。

- 数える：推論時に、モデル（LLM、VLM、学習した専用モジュール）が入力に応じて処理の分岐を選ぶこと。
- 数えない：類似度の閾値・FIFO・top-kなど、**固定の規則だけ**で決まるもの。
- 例外（2回目で変更）：分類Aの「残す」（W）だけは、選ぶ出力がなくても、モデルがテキストを書いてMemoryに残すなら数える（第2.1節）。

### 「処理の流れが固定で、規則だけで動く」とはどういうことか

次の2つが両方成り立つこと。分類Aの「なし」の行は、これに当たる。

1. **流れが固定**：実行される処理の順番と回数が、どの動画・どの質問でも同じ。
   - 例：「frameが届く → 符号化する → Memoryに足す → 容量を超えたら圧縮する → 質問が来たら検索する → 答える」が毎回この順番で必ず実行される。モデルの出力によって「次にどの処理をするか」は変わらない。
2. **選び方が規則**：何を残す・捨てる・取り出すかを、人が決めた式で選ぶ。
   - 例：質問との類似度が高い順にk個取り出す（top-k）、閾値を超えたら残す、古い順に捨てる（FIFO）、隣り合う似たframeを統合する。
   - 入力が違えば**結果**（どのframeが残るか）は変わる。しかし**選ぶ基準**（式）は人が決めていて変わらない。

具体例：

- [ReKV]：質問とKV cacheの類似度でtop-kを取り出す。どれを取り出すかは類似度の式で決まり、モデルが「これを取り出す」と選んでいるわけではない。
- [MovieChat]：短期Memoryがいっぱいになったら、隣り合う似たframeをまとめて長期Memoryへ移す。いつまとめるか（容量）も、どれをまとめるか（類似度）も規則。

判断がある例（対比）：

- [Response-G1]：モデルが毎時刻Yes / Noのtokenを出し、それで「答える／黙る」が分かれる。
- [SVMemAgent]：方策が「捨てる／どの枠と入れ替える」を出し、それでMemoryの中身が変わる。
- [VideoTree]★：質問が届くとframeを規則でクラスタに分けるが、その後LLMが各クラスタと質問の関連度を採点し、点の高いクラスタだけ追加のframeを見る。外側の流れ（いつ呼ぶか）は規則でも、「どこを詳しく見るか」がモデルの出力で変わるので判断あり。

見分け方（目安）：**「選ぶための出力」をモデルが出していて、それを変えると次に実行される処理が変わるか。** 変わるなら判断あり、中身（文章や特徴量）が変わるだけなら判断なし。いつAgentを呼ぶか（質問が届いたら呼ぶ、など）が規則であることは問わない。灰色の部分は第5節のK1・K2。

## 2. 分類A：モデルが担う段階（44本）

### 2.1 段階

| 段階 | 記号 | 数えるもの | 1回目のコード |
| --- | --- | --- | --- |
| 観測 | O | 元の映像のどこ・何を見るかを、モデルが選ぶ | A1 |
| 読み出し | R | 自分で作った記録から何を取り出すかを、モデルが選ぶ | A4 |
| 残す | W | モデルがテキストを書いてMemoryに残す（毎回必ず書くnoteも含む）、またはframe・記録を残す／捨てる／入れ替えるをモデルが選ぶ | A2、A3（とK3） |
| 答える時 | T | 今答えるか、黙るか、重いモデルを呼ぶかを、モデルが選ぶ | A5 |

- **計画（1回目のA6）は外した。** 計画は「何を判断するか」ではなく、観測・読み出し・答える判断を進めるための手段なので。1回目にA6を付けたのは[StreamAgent]、[VideoAgent-Fan]★、[OmAgent]★、[StreamArena]、[Em-Garde]、[M3-Agent]、[TraveLER]★の7本（各論文の計画の中身は付録B）。
- 「残す」だけは判断の有無ではなく「モデルがMemoryの中身を作るか」で数える。そのため、分類Aは「判断する対象」ではなく「**モデルが担う段階**」と呼ぶ。
- 「答えを書く」ことはどの論文でもモデルが行うので、段階に数えない。

### 2.2 観測と読み出しの境界

- **観測**：元の映像（frame）に当たって見る。
- **読み出し**：自分で作った記録（caption、要約、特徴量、graph）から取り出す。
- streamingでは、過去のframeは保存しない限り見直せない。そのため**streamingで過去の映像を呼び出すのは読み出し**とした（[Watch-Think-Interact]、[StreamArena]）。offline★で元の動画の好きな時刻を見に行くのは観測。
- この境界により、[VideoAgent-Wang]★の「検索文を書いてCLIPでframeを取り出す」は、元の動画のframeを探すので観測とした（1回目は観測と読み出しの両方）。

### 2.3 分類Aの表（1本1行）

- 1段目は担う段階の組み合わせ。2段目・3段目は、その行の論文をさらに分けられる場合だけ、第2.4節の小分類で分けた（分けられない行は`—`）。
- 該当論文の括弧の中は、2段目・3段目で使わなかった段階の小分類コード（参考）。
- 該当する論文がない組み合わせ（例：O+R、O+T、R+T）は載せていない。

| 1段目 | 1段目の説明 | 2段目 | 2段目の説明 | 3段目 | 3段目の説明 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| なし | どの段階もモデルが担わない（すべて規則で動く） | — | — | — | — | [StreamForest], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [MEMO], [LiveVLM], [StreamChat]?, [ReKV], [SAVEMem], [MovieChat], [MA-LMM], [QueryStream], [video-SALMONN S], [ProtoKV] | 15 |
| O | 観測だけを担う | O1 | どの時刻のframeを見るかを選ぶ | — | — | [ReWind]★?, [VideoTree]★ | 2 |
| | | O2 | どの区間を見るかを選ぶ | — | — | [VideoAgent-Wang]★ | 1 |
| R | 読み出しだけを担う | R1 | テキストの記録から取り出す | — | — | [VideoINSTA]★ | 1 |
| | | R4 | 保存した映像・視覚特徴から取り出す | — | — | [VideoStreaming]? | 1 |
| W | 残すだけを担う | W1 | frameを残す・捨てる・入れ替えるを選ぶ | — | — | [SVMemAgent] | 1 |
| | | W2a | 決まったタイミングでテキストを書いて足す | W2a1 | 見た内容を書く | [Lando et al.], [ProVideLLM], [Lando Edge] | 3 |
| | | | | W2a1+W2a2 | 見た内容と考えたことを、同じnoteに書く | [Think While Watching] | 1 |
| T | 答える時だけを担う | — | — | — | — | [StreamMind], [R3-Streaming] | 2 |
| O+W | 観測と残すを担う | — | — | — | — | [TraveLER]★（O1・W2a1） | 1 |
| R+W | 読み出しと残すを担う | R2 | graphから取り出す | — | — | [M3-Agent]（W2a1+W2a2） | 1 |
| | | R3 | テキスト＋画像の記録から取り出す | — | — | [OASIS]（W2a1） | 1 |
| W+T | 残すと答える時を担う | W2a | 決まったタイミングでテキストを書いて足す | W2a1 | 見た内容を書く | [Response-G1] | 1 |
| | | | | W2a2 | 考えたことを書く | [ThinkStream] | 1 |
| | | | | W2a3 | 自分の出力を残す | [StreamingVLM]? | 1 |
| | | | | W2a4 | 質問から作ったものを残す | [Em-Garde]? | 1 |
| | | W2c | 書くかどうかを選ぶ | — | — | [OneStreamer] | 1 |
| O+R+W | 観測・読み出し・残すを担う | O2 | どの区間を見るかを選ぶ | — | — | [OmAgent]★（R1・W2a1） | 1 |
| | | O2+O4 | 区間を選び、その区間にかける解析も選ぶ | — | — | [VideoAgent-Fan]★（R1・W2a1） | 1 |
| | | O4 | 映像にかける解析の種類を選ぶ | — | — | [EventMemAgent]（R3・W2a1）, [VideoMultiAgents]★?（R2・W2a1） | 2 |
| | | O5 | 映像を使うかどうかを選ぶ | — | — | [CogStream]?（R1・W2a3） | 1 |
| O+W+T | 観測・残す・答える時を担う | — | — | — | — | [StreamAgent]（O3・W2b） | 1 |
| R+W+T | 読み出し・残す・答える時を担う | W1 | frame（視覚特徴）を残す・まとめるを選ぶ | — | — | [Memento]?（R4） | 1 |
| | | W2b | テキストのMemory全体を書き直す | — | — | [Watch-Think-Interact]?（R4） | 1 |
| | | W2c | 書くかどうか・どこで区切るかを選ぶ | — | — | [StreamArena]（R3+R5） | 1 |

合計：15 + 3 + 2 + 5 + 2 + 1 + 2 + 5 + 5 + 1 + 3 = 44本（1段目ごと）。

2段目の基準：
- 2つ以上の段階を担う行では、その行の中で論文の違いが出る段階を使った（R+Wは読み出し、W+Tは残す、O+R+Wは観測、R+W+Tは残す）。
- 「なし」の15本は分けていない。分けるとすれば「規則でどこを選ぶか」（書き込み時か、検索時か）になるが、これはMemory分類のD・Eと同じ内容になるため。
- 「T 答える時だけ」の2本は分けていない。どちらも「答える／黙る」と「重いモデルを呼ぶ」の両方にまたがり、きれいに分かれないため。

備考：
- [StreamChat]?：captionを検索の目印としてだけ使うので「なし」。captionを中身として数えるなら「W」に移る（Memory分類で、本文と付録が食い違うとした論文）。
- [StreamingVLM]?・[Em-Garde]?：答える時の`?`は第5節のK4・K6。
- [ProVideLLM]：§4.4に「黙るよう学習」とあるだけで、応答の主な仕組みが書かれていないので、Tを付けていない（厳しめに数えるならW+T）。
- 「答えるか、もっと探すか」の選択はTではなく分類Fの「足りなければ追加」（F1）として扱う（K5）。
- 判断（分岐）があるのは、「なし」の15本と、「W」の行のW2aの4本（[Lando et al.]、[ProVideLLM]、[Lando Edge]、[Think While Watching]）を除いた**25本**。この4本は、モデルがテキストを書くだけで、選ぶ出力がどこにもない。分類B〜G（第3節）は、この25本に付ける。

### 2.4 小分類の定義

論文は第2.3節の表にだけ載せる。ここでは定義と、どの小分類に入れたかの理由だけを書く。

**統合した小分類**（`A+B`の形）：1本の論文が2つの小分類の両方に当てはまり、どちらが主とも言えないときに使う。「AとBの両方を行う」という意味の1つの小分類として扱う。

| コード | 意味 | 該当する理由 |
| --- | --- | --- |
| O2+O4 | 区間を選び、その区間にかける解析も選ぶ | [VideoAgent-Fan]★は、LLMが「区間を特定するツール」で区間を選び、次に「VQAのツール」でその区間に質問する。どちらもLLMが選ぶツールなので、両方の判断がある |
| R3+R5 | 自分の記録（テキスト＋画像）と外部の情報源の両方から取り出す | [StreamArena]は、Routerが記録の階層・graphを検索するツールと、Web検索のツールを選び分ける |
| W2a1+W2a2 | 見た内容と考えたことを、同じ記録に書く | [Think While Watching]のnoteは Focus / Evidence / State update の欄を持ち、見た証拠（Evidence）と見立て（State update）を一緒に書く。[M3-Agent]は出来事（見た内容）と知識（人の性格などの推論）を同じgraphに書く |

#### 観測（O）：何を見るか

| コード | 見る対象 | 定義 |
| --- | --- | --- |
| O1 | frame（時刻） | どの時刻のframeを見るかを選ぶ |
| O2 | 区間 | どのclip・区間を見る（見直す）かを選ぶ |
| O3 | frame内の領域 | frameのどこを切り出す・追跡するかを選ぶ |
| O4 | 解析の種類 | 同じ映像に、どの解析（OCR・物体検出・VQAなど）をかけるかを選ぶ |
| O5 | 映像を使うか | 映像を入力するかどうかを選ぶ |

- 候補だが今回の範囲で該当なし：解像度・fpsを選ぶ（どの細かさで見るか）。
- [VideoAgent-Wang]★：LLMが選ぶのは区間で、区間の中のframeはCLIPの類似度（規則）で取り出す。frameの選択は規則なので、O1+O2ではなくO2。
- [ReWind]★：選んだframeは高解像度で見るが、解像度は固定（選んでいない）。だからO1+O3ではなくO1。
- [VideoMultiAgents]★：Video Agentがどのツールで何を見るかは、1回目の根拠では詳しく分からない（推定、`?`）。
- [CogStream]?：「テキストだけで答えられるか」のflagで映像を入力しないことがあり、これを「映像を見るかどうか」の判断と読んだ（推定）。

#### 読み出し（R）：何から取り出すか

形式はMemory分類の分類B（表現形式）による。

| コード | 取り出す記録 | 定義 |
| --- | --- | --- |
| R1 | テキスト | caption・要約・QAなどの文章や項目付きテキスト |
| R2 | グラフ | 人・物と関係のgraph |
| R3 | テキスト＋画像 | 記録の文章と、その根拠のframe（代表frame）を組で持つもの |
| R4 | 映像・視覚特徴 | 保存したframe・clipの特徴量 |
| R5 | 外部の情報源 | Web検索など、動画の外の情報（単独の該当なし。R3+R5で使う） |

- [VideoAgent-Fan]★：captionの検索のほかに、物体のSQL（項目付き）も検索する。どちらもテキストなのでR1（統合しない）。
- [VideoINSTA]★：取り出すのは1つの質問の中で作ったイベントの記述（推定）。
- [Memento]?：質問との関連度で記録を選ぶ（K1、`?`）。
- [StreamAgent]：KVの取り出し（Selective Recall）はattentionの規則なので、Rに数えていない。

#### 残す（W）：frameかテキストか

| コード | 残すもの | 定義 |
| --- | --- | --- |
| W1 | frame（視覚） | frameや視覚特徴を残す／捨てる／入れ替える／まとめるを、モデルが選ぶ |
| W2 | テキスト | モデルがテキストを書いてMemoryに残す（以下の3つに分ける） |
| W2a | 書いて足す | 決まったタイミングで必ず書き、足していく |
| W2a1 | 観測の記録 | 見た内容を書く（caption・scene graph・行動ラベル・イベントの記録） |
| W2a2 | 推論のnote | 考えたこと（推論・状態の見立て）を書く |
| W2a3 | 自分の出力 | 自分の回答・実況をそのまま残し、後の入力に使う |
| W2a4 | 質問から作るもの | 質問から「見つけるべきもの」を書いて残す |
| W2b | 全体を書き直す | 決まったタイミングで、テキストのMemory全体を書き直す |
| W2c | 書くかを選ぶ | 書く／書かない、どこで区切って書くかを、モデルが選ぶ |

W2で数える範囲：
- **書くのは、答えるモデル自身でも、別のモデルでもよい。** 例：[Lando et al.]・[Lando Edge]?は、記録用のMLLMが一定時間ごとに説明文を書き、答えるのは別のLLM（[Lando Edge]が同じ構成かは推定）。私たちの3-Agent baselineも、Summaryを書くAgentと答えるAgentが別。
- **自分の回答・実況のログを残して後で入力に使うものも数える**（W2a3）。例：[CogStream]は過去の質問と自分の回答、[StreamingVLM]は自分が話した実況のテキスト（KVの形）を残す。
- 数えないもの：1つの質問の推論の中だけで作り、後の時点に持ち越さないcaption（Memory分類で「Memoryの定義外」とした[VideoTree]★、[VideoAgent-Wang]★、[VideoINSTA]★）。検索の目印としてだけ付けるcaption（[StreamChat]?）。

理由：
- W2bはMemory分類のE1（全体を書き直す）と同じ。[Watch-Think-Interact]?は、E1が数式からの推定なので`?`。
- [TraveLER]★：Summarizerが記録をまとめるが、Memory分類ではE2（まとめる）としたのでW2bではなくW2a1に入れた。
- [Memento]?：毎frame「直前のMemoryに融合／全体を少し更新／新しく追記」を選ぶ。Memoryは視覚特徴（Memory分類のB5）なのでW1。gateのスコアに固定の規則をかけるのでK1の`?`。
- [OneStreamer]：制御tokenで「局所caption／完了したeventの要約／黙る」を選ぶ。[StreamArena]：LLMがイベントの境界を予測して記録を書く。どちらもW2c。
- [Em-Garde]：質問から作る「見つけるべき視覚手がかり」の候補文。1回目はこれを計画（A6）とみなしたが、2回目はMemoryに残すもの（W2a4）として扱った。観測した内容ではない点はMemory分類のP3と同じ論点。
- W2aの論文でも、古い記録をまとめる・捨てるのは規則で行うものが多い（例：[OASIS]は似た隣接nodeをマージ、[ProVideLLM]は上限5件、[ThinkStream]・[StreamingVLM]は予算を超えたら古いものを捨てる）。

## 3. 分類B〜G：判断の性質（判断がある25本）

- 対象は第2.3節の最後に書いた、判断（分岐）がある25本。判断がない19本（「なし」の15本と、W2aだけの4本）には付けない。
- 1本1行（各表で1つのコード）。B・D・E・F・Gは1回目から1本1行だったので、表は1回目のまま。Cは1回目に複数のコードを付けていたので、1本1行になるよう作り直した（第3.2節）。
- 1回目は計画（A6）も判断に含めて付けた。分類Aから計画を外したが、B〜Gのコードは変えていない（影響があるのは主にEの「自由な文章」。第3.4節）。

### 3.1 分類B：構成

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| B1 | 1つのモデル | 回答と同じモデル、または単一のLLMが判断する | [OneStreamer], [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [CogStream], [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 12 |
| B2 | 複数のLLM Agent | 役割を分けた複数のLLMが判断する | [StreamAgent]?, [VideoMultiAgents]★, [OmAgent]★, [StreamArena], [Em-Garde], [M3-Agent], [TraveLER]★ | 7 |
| B3 | 専用の学習モジュール | 方策ネットやgateなど、判断専用に学習した部品 | [SVMemAgent], [VideoStreaming], [StreamMind], [ReWind]★ | 4 |
| B4 | 複合 | LLMと学習モジュールを組み合わせる | [R3-Streaming], [Memento] | 2 |

備考：
- [StreamAgent]：§3.1は「単一の軽量MLLM」と書くが、実装（§4.1）では計画用と対話用の2モデルを使う。
- [OmAgent]★：役割（Conqueror / Divider / Rescuer）は分かれているが、別々のLLMか同じLLMかは明記されていない（推定でB2）。
- [StreamArena]：役割の違う複数のworkerが、同じLLMのendpointを共有している（明記）。

### 3.2 分類C：判断の根拠（2回目で作り直し）

1回目は5つの根拠（C1 現在の観測、C2 Memory、C3 質問、C4 予測した未来、C5 確信度・自己評価）を複数付けていた。1本1行にするため、根拠の組み合わせを3段に分けた。

- 1段目：質問を使うか（1回目のC3）。25本中23本が使うので、まず使わない2本を分ける。
- 2段目：映像側の根拠として、今の観測（C1）とMemory（C2）のどちらを使うか。
- 3段目：それ以外に使う根拠（C4 予測した未来、C5 確信度）。

| 1段目 | 1段目の説明 | 2段目 | 2段目の説明 | 3段目 | 3段目の説明 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 質問なし | 質問を見ずに判断する | 観測＋Memory | 今の観測と過去の記録の両方を見る | — | — | [SVMemAgent], [StreamingVLM] | 2 |
| 質問あり | 質問を見て判断する | 観測 | 今見ているframe・区間だけを見る（過去の記録は使わない） | なし | 追加の根拠なし | [StreamMind], [Em-Garde], [VideoTree]★ | 3 |
| | | | | 確信度 | 自分の答え・情報の十分さの評価も使う | [VideoINSTA]★ | 1 |
| | | Memory | 過去の記録だけを見る | なし | 追加の根拠なし | [VideoAgent-Fan]★, [VideoStreaming], [OmAgent]★, [CogStream], [ReWind]★ | 5 |
| | | | | 確信度 | 自分の答え・情報の十分さの評価も使う | [VideoMultiAgents]★, [R3-Streaming]?, [VideoAgent-Wang]★ | 3 |
| | | 観測＋Memory | 今の観測と過去の記録の両方を見る | なし | 追加の根拠なし | [OneStreamer], [EventMemAgent], [OASIS], [Response-G1], [Watch-Think-Interact], [ThinkStream], [Memento], [M3-Agent] | 8 |
| | | | | 確信度 | 自分の答え・情報の十分さの評価も使う | [StreamArena], [TraveLER]★ | 2 |
| | | | | 予測した未来 | これから起きることの予測も使う | [StreamAgent] | 1 |

合計：2 + 4 + 8 + 11 = 25本。

備考：
- [SVMemAgent]は質問を見ずに、何を残すかを決める（質問も未来のframeも見えない設定、明記）。
- [StreamMind]：現在のframeの特徴は状態空間モデルの状態なので、過去の情報も暗に含む。
- [R3-Streaming]?：確信度を使うかは1回目で`?`だった。
- 1回目の各コードの本数（参考）：C1 現在の観測17本、C2 Memory21本、C3 質問23本、C4 予測した未来1本、C5 確信度6本。

### 3.3 分類D：判断のタイミング

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| D1 | 毎frame | frameが届くたびに判断する | [SVMemAgent], [Response-G1], [StreamingVLM], [StreamMind], [Memento] | 5 |
| D2 | 一定間隔 | clipごと・数秒ごとに判断する | [StreamAgent], [OneStreamer], [Watch-Think-Interact], [ThinkStream] | 4 |
| D3 | 切れ目・容量超過時 | イベントの切れ目や、容量を超えたときに判断する | （主なタイミングとしては該当なし） | 0 |
| D4 | 質問時のみ | 質問が届いたとき・回答するときだけ判断する | [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [VideoStreaming], [OmAgent]★, [CogStream], [Em-Garde], [ReWind]★, [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 13 |
| D5 | 複合 | 書き込みは一定間隔、検索は質問時など、判断ごとにタイミングが違う | [R3-Streaming], [StreamArena], [M3-Agent] | 3 |

備考：[Watch-Think-Interact]はMemoryの書き直しだけ区切りごと（D3）に行う。

### 3.4 分類E：行動の形式

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| E1 | 決まった選択肢 | 離散のaction・特殊token・段階評価 | [OneStreamer], [Response-G1], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [CogStream], [StreamMind], [R3-Streaming], [Memento], [VideoTree]★, [VideoINSTA]★ | 11 |
| E2 | ツール呼び出し | ツールの選択と引数 | [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [OmAgent]★, [StreamArena], [M3-Agent] | 7 |
| E3 | 自由な文章 | 計画文・検索クエリ文・候補文 | [StreamAgent], [Em-Garde], [TraveLER]★, [VideoAgent-Wang]★ | 4 |
| E4 | 数値 | スコア・確率・重みにtop-kや閾値をかける | [SVMemAgent], [VideoStreaming], [ReWind]★ | 3 |

備考：E3のうち[StreamAgent]・[TraveLER]★は計画文、[Em-Garde]は質問から作る候補文（2回目はW2a4）、[VideoAgent-Wang]★は検索クエリ文。分類Aから計画を外したので、計画文を除いて付け直すと[StreamAgent]はE1（待つか答えるかの決定関数）、[TraveLER]★は次に見る時刻の選択の形式（未確認）に変わりうる。

### 3.5 分類F：繰り返し

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| F0 | 1回で終わる | 判断は1回で、やり直さない | [OneStreamer], [SVMemAgent], [Response-G1], [ThinkStream], [StreamingVLM], [VideoStreaming], [CogStream], [StreamMind], [R3-Streaming], [Em-Garde], [Memento], [ReWind]★ | 12 |
| F1 | 足りなければ追加 | 情報が足りなければ、追加で観測・検索する | [StreamAgent], [EventMemAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Watch-Think-Interact], [OmAgent]★, [StreamArena], [M3-Agent], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 13 |
| F2 | 自分で検証して直す | 自分の答えや計画を検証して直す | （該当なし） | 0 |

備考：[TraveLER]★のEvaluatorは計画どおり進んだかも検査するのでF2の要素もあるが、主な働きは追加の観測なのでF1にした。

### 3.6 分類G：判断部分の学習

| コード | 小分類 | 定義 | 該当論文 | 本数 |
| --- | --- | --- | --- | --- |
| G0 | 学習なし | promptや既存モデルだけで判断する | [StreamAgent], [OASIS], [VideoAgent-Fan]★, [VideoMultiAgents]★, [Response-G1], [OmAgent]★, [StreamArena], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 11 |
| G1 | 教師あり学習 | SFTなどで判断を学習する | [OneStreamer], [StreamingVLM], [VideoStreaming], [CogStream], [StreamMind], [Memento], [ReWind]★ | 7 |
| G2 | 強化学習 | 強化学習で判断を学習する（SFTの後にRLを含む） | [EventMemAgent], [SVMemAgent], [Watch-Think-Interact], [ThinkStream], [R3-Streaming], [Em-Garde], [M3-Agent] | 7 |

## 4. 評価タスク（44本、1本1行）

論文が評価に使ったタスクで分けた。1回目は1本を評価したタスクの数だけ行に入れていたので、1本1行になるよう、評価したタスクの組み合わせで作り直した。各タスクの定義は第4.2節、組み合わせの決め方は表の下。

### 4.1 評価タスクの表

| 1段目 | 1段目の説明 | 2段目 | 2段目の説明 | 該当論文（VQA以外に評価したタスク） | 本数 |
| --- | --- | --- | --- | --- | --- |
| VQAだけ | VQA（TS1・TS2・TS4）だけで評価する | 選択肢 | 選択肢から答えるVQAだけ（TS1） | [Lando et al.], [Flash-VStream], [VideoMultiAgents]★, [Lando Edge], [ThinkStream], [MEMO], [SAVEMem], [video-SALMONN S], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★ | 11 |
| | | 自由記述 | 文章で答えるVQAだけ（TS2） | [MovieChat] | 1 |
| | | 選択肢＋自由記述 | TS1とTS2の両方 | [OASIS], [MuKV], [StreamMem], [SVMemAgent]?, [LiveVLM], [ReKV], [M3-Agent], [ProtoKV], [VideoINSTA]★ | 9 |
| | | 対話 | 複数ターンの対話（TS4）を含む | [StreamChat], [CogStream] | 2 |
| VQA＋能動的応答 | いつ答えるかも評価する（TS3）。生成・予測（TS5・TS6）は含まない | 選択肢 | TS1とTS3 | [OneStreamer], [StreamForest]?, [EventMemAgent]?, [Response-G1], [Watch-Think-Interact], [R3-Streaming], [Em-Garde], [QueryStream]? | 8 |
| | | 自由記述 | TS2とTS3 | [Memento] | 1 |
| | | 選択肢＋自由記述 | TS1・TS2とTS3 | [StreamAgent]? | 1 |
| | | 対話 | TS4も含む | [Think While Watching], [StreamArena]（TS8） | 2 |
| VQA＋区間・その他 | 区間を答える（TS7）などを含む。TS3・TS5・TS6は含まない | — | — | [VideoAgent-Fan]★（TS7）, [VideoStreaming]（TS7）, [OmAgent]★（TS7・TS8）, [ReWind]★（TS7） | 4 |
| VQA＋生成・予測 | 行動予測（TS5）や実況・キャプション生成（TS6）も含む | — | — | [VideoLLaMB]★（TS5・TS6・TS8）, [StreamingVLM]（TS6）, [MA-LMM]（TS5・TS6・TS8） | 3 |
| VQAなし | VQA（TS1・TS2）を使わない | — | — | [ProVideLLM]（TS5、TS4・TS6は補助）, [StreamMind]（TS3・TS5・TS6） | 2 |

合計：23 + 12 + 4 + 3 + 2 = 44本。

組み合わせの決め方（上から順に当てはめる）：
1. TS1・TS2のどちらも使わない → 「VQAなし」
2. TS5かTS6を含む → 「VQA＋生成・予測」
3. TS3を含む → 「VQA＋能動的応答」
4. TS7かTS8を含む → 「VQA＋区間・その他」
5. それ以外 → 「VQAだけ」

備考：
- `?`は、OVO-BenchのForward Active Respondingを含むことからTS3と推定したもの。[SAVEMem]と[ThinkStream]はForwardを評価していないので、TS3に入れていない。
- [Think While Watching]は、StreamingBenchとOVO-Benchを単一ターンと複数ターンの両方で評価している。
- [Watch-Think-Interact]：題名に「Multi-Turn」とあるが、複数ターンのベンチマークは確認できなかった（TS4は付けていない）。
- [VideoLLaMB]★のTS6は定性評価のみ。[ProVideLLM]のTS4・TS6は補助的な評価。
- この44本はstreaming VideoQAを主題に集めたため、VQAに偏っている可能性がある。

### 4.2 タスクの定義

1回目はT1〜T8と書いたが、分類Aの「T（答える時）」と紛らわしいのでTS1〜TS8に変えた。

| コード | タスク | 定義 | 評価した本数（1回目、重複あり） |
| --- | --- | --- | --- |
| TS1 | 多肢選択VQA | 選択肢から答えを選ぶ質問応答 | 35 |
| TS2 | 自由記述VQA | 文章で答え、GPTなどで採点する質問応答 | 19 |
| TS3 | リアルタイム・能動的応答 | いつ答えるかを含めて評価する（OVO-BenchのForward Active Respondingなど） | 13 |
| TS4 | 複数ターンの対話 | 同じ動画について続けて質問する | 5 |
| TS5 | 行動予測・手順理解 | 次の行動や手順を予測・認識する | 4 |
| TS6 | 実況・キャプション生成 | 動画の説明文や実況を生成する | 5 |
| TS7 | 時間的grounding | 質問に対応する区間を答える | 4 |
| TS8 | その他 | 上記以外：[VideoLLaMB]★（長い映像に埋めた情報を探すNIAVH）、[MA-LMM]（長期動画の分類）、[OmAgent]★（コード生成・知識QA）、[StreamArena]（外部検索を使う質問） | 4 |

- 「Streaming Video Understanding」は研究分野の名前で、VQAはその評価の形式の1つ。分野の代表的なベンチマーク（StreamingBench、OVO-Bench）も、多くは「ある時点で質問され、選択肢から答える」形。

### 4.3 参考：主なベンチマーク別の論文

ベンチマークは分類ではなく参考なので、1本が複数の行に入る。

| ベンチマーク | 該当論文 | 本数 |
| --- | --- | --- |
| StreamingBench | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [MuKV], [Response-G1], [Watch-Think-Interact], [ThinkStream], [MEMO], [LiveVLM], [SAVEMem], [R3-Streaming], [Em-Garde], [QueryStream], [video-SALMONN S], [ProtoKV] | 18 |
| Video-MME | [StreamAgent], [StreamForest], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [LiveVLM], [R3-Streaming], [QueryStream], [M3-Agent]（long）, [video-SALMONN S], [ProtoKV], [VideoTree]★ | 17 |
| OVO-Bench | [StreamAgent], [OneStreamer], [Think While Watching], [StreamForest], [EventMemAgent], [OASIS], [Response-G1], [Watch-Think-Interact], [ThinkStream], [MEMO], [StreamingVLM], [SAVEMem], [R3-Streaming], [Em-Garde], [QueryStream], [ProtoKV] | 16 |
| EgoSchema | [StreamAgent], [VideoLLaMB]★, [MuKV], [StreamMem], [Flash-VStream], [SVMemAgent], [VideoAgent-Fan]★, [VideoMultiAgents]★, [VideoStreaming], [ReKV], [TraveLER]★, [VideoTree]★, [VideoAgent-Wang]★, [VideoINSTA]★ | 14 |
| MLVU | [StreamAgent], [StreamForest], [MuKV], [StreamMem], [Flash-VStream], [Watch-Think-Interact], [LiveVLM], [ReKV], [R3-Streaming], [ProtoKV], [VideoTree]★ | 11 |
| LongVideoBench（私たちのbaselineで使用中） | [StreamAgent], [SVMemAgent], [Watch-Think-Interact], [ThinkStream], [StreamingVLM], [LiveVLM], [QueryStream] | 7 |
| RVS-Ego / RVS-Movie | [StreamAgent], [MuKV], [StreamMem], [SVMemAgent]（RVS-Egoのみ）, [LiveVLM], [ReKV], [ProtoKV] | 7 |
| QAEgo4D | [Lando et al.], [Lando Edge], [ReKV] | 3 |

## 5. 判定のルールと境界例（K1〜K9）

1回目のK1〜K6と、2回目で決めたK7〜K9をまとめた。「今の扱い」は2回目のコードで書いた。

| # | 迷った点 | 今の扱い | 該当論文 | 決めた時点 |
| --- | --- | --- | --- | --- |
| K1 | 学習したモジュールのスコアに、固定のtop-kや閾値をかけて選ぶ | 判断あり（`?`付き）。スコアは「選ぶために学習した出力」なので | [VideoStreaming]（R4?）, [ReWind]★（O1?）, [Memento]（W1?・R4?） | 1回目 |
| K2 | 既存モデルのattentionやCLIP類似度に、固定のtop-kや閾値をかけて選ぶ | 判断なし（「なし」）。選ぶために学習した出力ではないので | [ReKV], [video-SALMONN S], [QueryStream], [MuKV] | 1回目 |
| K3 | 毎回必ず書くnote・推論文・要約 | **2回目で変更**：テキストでMemoryに残すなら「残す」（W2a）に数える。ただし判断（分岐）には数えない | [Think While Watching], [ThinkStream], [OASIS]（統合後の要約） | 1回目→2回目 |
| K4 | 判断用の部品はなく、学習で「黙る」出力を身につけただけ | T（`?`付き） | [StreamingVLM] | 1回目 |
| K5 | 「答えるか、もっと探すか」の選択 | Tではなく、分類FのF1（足りなければ追加）として扱う | [OASIS], [M3-Agent], [VideoAgent-Wang]★ | 1回目 |
| K6 | 応答を固定規則で発火させた後、別のモデルが応答してよいか検証する | T（`?`付き） | [Em-Garde] | 1回目 |
| K7 | 自分の回答・実況をそのまま残すものを「残す」に数えるか | 数える（W2a3） | [CogStream], [StreamingVLM] | 2回目 |
| K8 | 1本が2つの小分類に当てはまるとき、どちらに入れるか | 主な方を選ばず、統合した小分類を作る（第2.4節） | [VideoAgent-Fan]★（O2+O4）, [StreamArena]（R3+R5）, [Think While Watching]・[M3-Agent]（W2a1+W2a2） | 2回目 |
| K9 | 答えるモデルとは別のモデルが書いたテキストも「残す」に数えるか | 数える。そのパターンも含むと定義に書いた（第2.4節） | [Lando et al.], [Lando Edge]? | 2回目 |

K7から出た考え（林、2026-10-17）：**残したものを何に使うかが大事。**
- 同じ「残す」でも、使い道が違う。例：
  - 回答の材料にする：[CogStream]（過去のQAを選んで答えに使う）
  - 次の書き込みの材料にする：[StreamAgent]（前のテキストMemoryから次のMemoryを作る）
  - 答える時の判断に使う：[Response-G1]（scene graphを検索して、黙るか答えるかを決める）
- Memory分類のG（読み出し）は「回答時にどう渡すか」だけを扱っている。回答以外の使い道（次の書き込み、判断）は、まだどの分類にもない。新しい分類にするかは未定（第9節）。

## 6. 当てはめから見えたこと（私たちの推論）

分類A（モデルが担う段階）について：

1. **44本中15本は、どの段階もモデルが担わない（「なし」）。** KVや視覚特徴のMemoryを圧縮する論文の多くはここに入る。Memoryの研究とAgentの研究は、かなりの部分で別の流れになっている。noteを書くだけの4本も合わせると、判断（分岐）を持たないのは19本。
2. **noteを含めると、「残す」は最も多い段階になる（「なし」以外の29本中22本）。** ただし16本はW2a（決まったタイミングで書いて足すだけ）で、その中身は観測の記録が10本、観測と推論の両方が2本、推論のnoteが1本、自分の出力が2本、質問から作るものが1本。**何を残すかをモデルが選ぶ**のは4本（W1の2本、W2cの2本）しかない。
3. **frame（視覚）を残すかをモデルが選ぶのは[SVMemAgent]と[Memento]?の2本だけ。** 視覚Memoryを持つ論文の多くは、残す・捨てるを規則で決めている。私たちの関心である「Memoryに何を残すかをAgentが決める」、特に視覚Memoryについては、44本の範囲ではほぼ空いている。
4. **全体を書き直すテキストMemory（W2b）は[StreamAgent]と[Watch-Think-Interact]?の2本。** 私たちのbaselineと同じ形。Memory分類2回目の「書き直す方式は少ない」と同じ結論。
5. **どの時刻・区間を見るか（O1・O2・O2+O4）を選ぶ6本は、すべてoffline★。** streamingで過去を見直すには保存した記録が必要なので、同じ判断が読み出し（R4）の形になる（[Watch-Think-Interact]）。streamingの観測は、今のframeのどこを見るか（[StreamAgent]）、どの解析をかけるか（[EventMemAgent]）、映像を使うか（[CogStream]?）に限られる。
6. **答える時（T）を含む11本は、すべてstreaming。** そのうち9本は「残す」も担う。
7. **読み出しを担う12本のうち9本はテキスト（R1〜R3、R3+R5）から取り出す。** 視覚の記録から取り出すことをモデルが選ぶのは3本（R4）だけ。

分類B〜G（判断の性質）について：

8. **予測した未来を判断の根拠にするのは[StreamAgent]だけ。** 観点2「先読み・予習」と直接つながる。先読みを観測や回答以外（例えば書き込み）に使う論文は、今回の範囲では見つからなかった（未確認）。
9. **offlineとstreamingで判断の作り方が違う。**
   - offline★の8本はすべて「質問を受けてから判断する」（D4）。7本は「足りなければ探し直す」（F1）で、学習なし（G0）。
   - streamingの論文は「毎frameか一定間隔で（D1・D2）、特殊tokenなどの決まった選択肢で（E1）」判断する形が多く、学習して身につける（G1・G2）。強化学習の7本はすべてstreaming。
10. **自分で検証して直す（F2）論文は0本。** 判断を繰り返す論文はあるが、どれも「足りなければ追加で見る」形だった。

評価タスクについて：

11. **評価はVQAに偏っている。** 23本はVQAだけで評価し、VQAを使わないのは[ProVideLLM]と[StreamMind]の2本。「なし」の15本のうち11本はVQAだけで評価している。
12. **答える時（T）を担う11本のうち9本は、能動的応答（TS3）で評価している。** 例外は[ThinkStream]（OVO-BenchのForwardを評価していない）と[StreamingVLM]（実況で評価）。
13. 質問を最初から知っているstreaming論文（[Em-Garde]、[QueryStream]）は、どちらも能動的応答（TS3）で評価している。私たちのLongVideoBenchを使った論文は7本。

私たちの3-Agent baseline（Situation → Summary → Answer）の位置：

14. 分類Aでは「W 残すだけ」のW2b（Summaryを毎回書き直す）に当たる（この組み合わせの論文は今はない）。判断（分岐）は持たないので、分類B〜Gは付かない（構成だけ見れば、役割を分けた複数Agent＝B2）。Summary Agentが何を残すかを選ぶようにすればW2c、frameを残す・捨てるを選ぶようにすればW1（[SVMemAgent]と同じ枠）。

## 7. 1回目のコードとの対応

| 1回目 | 2回目 |
| --- | --- |
| A0 判断しない | 「なし」。ただしnoteをテキストで残す4本（[Lando et al.]、[Think While Watching]、[ProVideLLM]、[Lando Edge]）は「W」に移った |
| A1 観測 | O（O1〜O5、統合したO2+O4） |
| A4 読み出し | R（R1〜R5、統合したR3+R5） |
| A2 書き込み、A3 更新・削除 | W（W1、W2a1〜W2a4、統合したW2a1+W2a2、W2b、W2c）。K3（毎回書くnote）も含める |
| A5 回答のタイミング | T |
| A6 計画 | 分類Aから外した |
| B、D、E、F、G | 変更なし |
| C1〜C5（複数可） | 質問の有無・映像側の根拠・追加の根拠の3段（1本1行） |
| タスクT1〜T8（1本が複数行） | TS1〜TS8に改名し、評価したタスクの組み合わせで1本1行にした |

1回目から判定が変わった論文：
- 「判断しない」→「W」：[Lando et al.]、[Think While Watching]、[ProVideLLM]、[Lando Edge]。
- W（残す）が付いた：[StreamAgent]、[EventMemAgent]、[OASIS]、[VideoAgent-Fan]★、[VideoMultiAgents]★、[Response-G1]、[ThinkStream]、[StreamingVLM]、[OmAgent]★、[CogStream]、[Em-Garde]。
- [VideoAgent-Wang]★：読み出しを外し、観測だけにした（第2.2節）。
- [Em-Garde]、[StreamAgent]ほか：計画を外した。[Em-Garde]の候補文はW2a4になった。

## 8. 未確認・要確認

- [SVMemAgent]、[StreamMem]：OpenReviewのページがbot認証で開けず、URLが同じ論文を指すかを確認できなかった。ブラウザで手動確認する。arXivのURLは付録Aにある。
- [QueryStream]：本文を読めていない（OpenReviewが開けなかった）。手法の閾値などは、公式GitHubのREADMEと第三者の論文解説ページによる判定（推定）。
- [OneStreamer]、[Think While Watching]、[CogStream]：本文の末尾（約1割）を読めていない。
- [Em-Garde]：応答するモデル（responder）のモデル名と判断方法が書かれていない。HTML版の「ICML」表記がテンプレート由来かどうかも未確認。
- [Memento]：付録の「dynamic correction strategy」を読めていない。gateの学習方法（end-to-endか）が明記されていない。
- [SVMemAgent]のRVS-Egoが自由記述かどうか（第4節の`?`）。
- 2回目の推定：[VideoMultiAgents]★の観測（O4?）、[Watch-Think-Interact]の書き直し（W2b?）、[VideoINSTA]★の読み出し（R1）、[Lando Edge]の構成（K9）、[TraveLER]★の行動の形式（第3.4節の備考）。
- 論文中の不整合（参考）：[MuKV]はk_gの値が本文中で2通りある。[VideoStreaming]は学習サンプル数が§3.4と付録Aで食い違う。[MovieChat]は注釈数がabstractと本文で食い違う。

## 9. 次にやること（候補）

- 「残したものの使い道」を新しい分類にするか決める（第5節のK7の後）。
- 分類E（行動の形式）を、計画を除いて付け直すか決める（第3.4節の備考）。
- 第8節の未確認・推定の点を原文で確認する。

## 10. Memory分類のメモへの反映候補（未反映）

1回目の確認で、次の点がMemory分類のメモ（1回目・2回目）と食い違っている。反映するかはユーザーと決める。

- 発表先の確認：[ProtoKV]はICML 2026の公式ページが見つかった。[TraveLER]★はEMNLP 2024（Main）の公式ページが見つかった。[QueryStream]はICLR 2026の公式ページが見つかった。
- リンクの修正：[VideoStreaming]と[ReKV]はPDFへの直リンクだったので、Abstractページに変えた。
- 処理設定の注記：[VideoLLaMB]★は構造がstreaming型で、評価はoffline。[Flash-VStream]、[VideoStreaming]、[MovieChat]は逐次に処理するが、評価や回答は動画を最後まで見てから行う。
- 名前の衝突：[StreamArena]が提案するAgentも「StreamMind」という名前で、ICCV 2025の[StreamMind]とは別物。
- 2回目メモのリンク崩れ：`[MovieChat][新]`のように、リンクの直後に`[新]`を続けて書いたため、Markdownが「新」という名前のリンク定義を探してしまい、リンクにならなかった。

## 付録A：論文の公式URLとarXiv

「確認」の列は、今回URLを開いて題名が一致したかどうか。

| 論文 | 正式な題名（略称と違う場合） | 発表先 | 公式ページ | arXiv | 確認 |
| --- | --- | --- | --- | --- | --- |
| [StreamAgent] | StreamAgent: Towards Anticipatory Agents for Streaming Video Understanding | arXiv（採録未確認） | — | [2508.01875](https://arxiv.org/abs/2508.01875) | OK |
| [OneStreamer] | — | arXiv（採録未確認） | — | [2610.01762](https://arxiv.org/abs/2610.01762) | OK |
| [Lando et al.] | How Far Can Off-the-Shelf Multimodal Large Language Models Go in Online Episodic Memory Question Answering? | ICIAP 2025（著者ページの記載のみ） | — | [2506.16450](https://arxiv.org/abs/2506.16450) | OK |
| [Think While Watching] | — | arXiv（採録未確認） | — | [2603.11896](https://arxiv.org/abs/2603.11896) | OK |
| [StreamForest] | — | NeurIPS 2025 | [NeurIPS](https://papers.neurips.cc/paper_files/paper/2025/hash/6dd91fec726dbed8915a1fbadd91d1d2-Abstract-Conference.html) | [2509.24871](https://arxiv.org/abs/2509.24871) | OK |
| [EventMemAgent] | — | arXiv（採録未確認） | — | [2602.15329](https://arxiv.org/abs/2602.15329) | OK |
| [OASIS] | — | CVPR 2026 | [CVF](https://openaccess.thecvf.com/content/CVPR2026/html/Liang_OASIS_On-Demand_Hierarchical_Event_Memory_for_Streaming_Video_Reasoning_CVPR_2026_paper.html) | [2604.17052](https://arxiv.org/abs/2604.17052) | OK |
| [VideoLLaMB]★ | Long Streaming Video Understanding with Recurrent Memory Bridges | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_VideoLLaMB_Long_Streaming_Video_Understanding_with_Recurrent_Memory_Bridges_ICCV_2025_paper.html) | [2409.01071](https://arxiv.org/abs/2409.01071) | OK |
| [MuKV] | — | CVPR 2026 | [CVF](https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_MuKV_Multi-Grained_KV_Cache_Compression_for_Long_Streaming_Video_Question-Answering_CVPR_2026_paper.html) | [2605.22269](https://arxiv.org/abs/2605.22269) | OK |
| [StreamMem] | — | CVPR 2026 Workshop | [OpenReview](https://openreview.net/forum?id=siAEqckmUs) | [2508.15717](https://arxiv.org/abs/2508.15717) | OpenReviewは開けず未確認 |
| [Flash-VStream] | — | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Zhang_Flash-VStream_Efficient_Real-Time_Understanding_for_Long_Video_Streams_ICCV_2025_paper.html) | [2506.23825](https://arxiv.org/abs/2506.23825) | OK |
| [SVMemAgent] | — | ECCV 2026 Workshop | [OpenReview](https://openreview.net/forum?id=E0LVxLc5Pw) | [2609.18540](https://arxiv.org/abs/2609.18540) | OpenReviewは開けず未確認 |
| [VideoAgent-Fan]★ | VideoAgent: A Memory-augmented Multimodal Agent for Video Understanding（Fan et al.） | ECCV 2024 | [ECVA](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/3241_ECCV_2024_paper.php) | [2403.11481](https://arxiv.org/abs/2403.11481) | OK |
| [VideoMultiAgents]★ | — | arXiv（採録未確認） | — | [2504.20091](https://arxiv.org/abs/2504.20091) | OK |
| [Response-G1] | — | ACL 2026（Long） | [ACL Anthology](https://aclanthology.org/2026.acl-long.2042/) | [2605.07575](https://arxiv.org/abs/2605.07575) | OK |
| [ProVideLLM] | Streaming VideoLLMs for Real-Time Procedural Video Understanding | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Chatterjee_Streaming_VideoLLMs_for_Real-Time_Procedural_Video_Understanding_ICCV_2025_paper.html) | [2504.13915](https://arxiv.org/abs/2504.13915) | OK |
| [Lando Edge] | Exploring Multimodal LMMs for Online Episodic Memory Question Answering on the Edge | VISAPP 2026（研究室ページの記載のみ） | — | [2602.22455](https://arxiv.org/abs/2602.22455) | OK |
| [Watch-Think-Interact] | — | arXiv（採録未確認） | — | [2609.37035](https://arxiv.org/abs/2609.37035) | OK |
| [ThinkStream] | Thinking in Streaming Video | arXiv（採録未確認） | — | [2603.12938](https://arxiv.org/abs/2603.12938) | OK |
| [MEMO] | MEMO: Multi-Level Entity-Aware Memory for Streaming Video Understanding | ACM MM 2026（arXivのコメントのみ） | — | [2609.38900](https://arxiv.org/abs/2609.38900) | OK |
| [StreamingVLM] | — | ICLR 2026 | [ICLR](https://iclr.cc/virtual/2026/poster/10008145) | [2510.09608](https://arxiv.org/abs/2510.09608) | OK |
| [LiveVLM] | — | arXiv（本文にDAC '26の記載） | — | [2505.15269](https://arxiv.org/abs/2505.15269) | OK |
| [StreamChat] | Streaming Video Understanding and Multi-round Interaction with Memory-enhanced Knowledge | ICLR 2025 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ad2fa437f7c23e4e9875599c6065d18a-Abstract-Conference.html) | [2501.13468](https://arxiv.org/abs/2501.13468) | OK |
| [VideoStreaming] | Streaming Long Video Understanding with Large Language Models | NeurIPS 2024 | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d7ce06e9293c3d8e6cb3f80b4157f875-Abstract-Conference.html) | [2405.16009](https://arxiv.org/abs/2405.16009) | OK（PDF直リンクから変更） |
| [ReKV] | Streaming Video Question-Answering with In-context Video KV-Cache Retrieval | ICLR 2025 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/67a9b444cbcd647572c88194619f72d5-Abstract-Conference.html) | [2503.00540](https://arxiv.org/abs/2503.00540) | OK（PDF直リンクから変更） |
| [SAVEMem] | Semantic-Aware Adaptive Visual Memory for Streaming Video Understanding | arXiv（採録未確認） | — | [2605.07897](https://arxiv.org/abs/2605.07897) | OK |
| [MovieChat] | — | CVPR 2024 | [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/Song_MovieChat_From_Dense_Token_to_Sparse_Memory_for_Long_Video_CVPR_2024_paper.html) | [2307.16449](https://arxiv.org/abs/2307.16449) | OK |
| [MA-LMM] | — | CVPR 2024 | [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/He_MA-LMM_Memory-Augmented_Large_Multimodal_Model_for_Long-Term_Video_Understanding_CVPR_2024_paper.html) | [2404.05726](https://arxiv.org/abs/2404.05726) | OK |
| [OmAgent]★ | — | EMNLP 2024 | [ACL Anthology](https://aclanthology.org/2024.emnlp-main.559/) | [2406.16620](https://arxiv.org/abs/2406.16620) | OK |
| [CogStream] | CogStream: Context-guided Streaming Video Question Answering | AAAI 2026 | [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/38336) | [2506.10516](https://arxiv.org/abs/2506.10516) | OK |
| [StreamMind] | StreamMind: Unlocking Full Frame Rate Streaming Video Dialogue through Event-Gated Cognition | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Ding_StreamMind_Unlocking_Full_Frame_Rate_Streaming_Video_Dialogue_through_Event-Gated_ICCV_2025_paper.html) | [2503.06220](https://arxiv.org/abs/2503.06220) | OK |
| [R3-Streaming] | An Efficient Streaming Video Understanding Framework with Agentic Control | arXiv（採録未確認） | — | [2605.17921](https://arxiv.org/abs/2605.17921) | OK |
| [StreamArena] | StreamArena: Toward Continuous, Interactive, and Long-Horizon Agentic Streaming Video Understanding | arXiv（採録未確認） | — | [2608.05703](https://arxiv.org/abs/2608.05703) | OK |
| [Em-Garde] | — | arXiv（採録未確認） | — | [2603.19054](https://arxiv.org/abs/2603.19054) | OK |
| [Memento] | — | ICLR 2026 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2026/hash/3b5f4587a0bdb81ecc6ce9d82320a5c2-Abstract-Conference.html) | 見つからず | OK |
| [QueryStream] | — | ICLR 2026 | [ICLR](https://iclr.cc/virtual/2026/poster/10011335) | 見つからず（[OpenReview](https://openreview.net/forum?id=738HjJEbml)） | OK（OpenReviewから変更） |
| [ReWind]★ | — | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Diko_ReWind_Understanding_Long_Videos_with_Instructed_Learnable_Memory_CVPR_2025_paper.html) | [2411.15556](https://arxiv.org/abs/2411.15556) | OK |
| [M3-Agent] | Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory | ICLR 2026 | [ICLR](https://iclr.cc/virtual/2026/poster/10009685) | [2508.09736](https://arxiv.org/abs/2508.09736) | OK |
| [video-SALMONN S] | — | ICML 2026 | [ICML](https://icml.cc/virtual/2026/poster/61140) | [2510.11129](https://arxiv.org/abs/2510.11129) | OK |
| [ProtoKV] | — | ICML 2026 | [ICML](https://icml.cc/virtual/2026/poster/63663) | [2606.26762](https://arxiv.org/abs/2606.26762) | OK（arXivから変更） |
| [TraveLER]★ | — | EMNLP 2024 | [ACL Anthology](https://aclanthology.org/2024.emnlp-main.544/) | [2404.01476](https://arxiv.org/abs/2404.01476) | OK（arXivから変更） |
| [VideoTree]★ | — | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Wang_VideoTree_Adaptive_Tree-based_Video_Representation_for_LLM_Reasoning_on_Long_CVPR_2025_paper.html) | [2405.19209](https://arxiv.org/abs/2405.19209) | OK |
| [VideoAgent-Wang]★ | VideoAgent: Long-form Video Understanding with Large Language Model as Agent（Wang et al.） | ECCV 2024 | [ECVA](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/10325_ECCV_2024_paper.php) | [2403.10517](https://arxiv.org/abs/2403.10517) | OK |
| [VideoINSTA]★ | — | Findings of EMNLP 2024 | [ACL Anthology](https://aclanthology.org/2024.findings-emnlp.384/) | [2409.20365](https://arxiv.org/abs/2409.20365) | OK |

- CVFのページはWebFetchでは開けなかったが、curlで開いて題名・著者が一致した。

## 付録B：各論文の判定根拠（要点）

判断がある25本と、noteを書くだけの4本。括弧の中は2回目のコード。「計画」は1回目にA6を付けた処理（2回目は分類Aに数えない）。

- **[StreamAgent]**：toolで入力frameの一部を切り出す・追跡する（O3、Eq.3）。決定関数で「待つか答えるか」を選ぶ（T）。3つの見通し（直後・少し先・遠い先）から計画候補を作って1つ選ぶ（計画、Eq.2）。予測した未来の出来事を根拠に使う（Cの「予測した未来」）。captionからテキストMemoryを再帰的に書き直す（W2b）。
- **[OneStreamer]**：制御tokenで、captionを書く・出来事の要約を書く（W2c）、黙る・保留する・答える（T）を選ぶ。SFTのみ。
- **[Lando et al.]**：固定clipごとに外部のMLLMがテキストの記述を作り、追記する（W2a1）。質問時にMemory全体を推論用LLMへ渡す。選ぶ出力はない（判断なし）。
- **[Think While Watching]**：segmentごとに、Focus / Evidence / State updateの欄を持つnoteを生成して追記する（W2a1+W2a2）。質問時は全noteと受信済みの映像にattentionをかけて答える。選ぶ出力はない（判断なし）。
- **[EventMemAgent]**：情報が足りないときだけ、Agentが時間・意味の検索を呼ぶ（R3）。OCRや物体検出で追加で見る（O4）。溢れたeventを「代表frame＋caption」として長期Memoryに移す（W2a1）。ReAct形式。GRPOで学習し、報酬は最終回答の正誤。
- **[OASIS]**：粗い推論で直接答えるか、検索するかを選ぶ（R3）。検索は最大1回（F1）。固定窓ごとにMLLMの要約とkey frameの葉nodeを作る（W2a1）。学習なし。
- **[SVMemAgent]**：新しいframeごとに、捨てるか、Memoryの枠（16枠）のどれと入れ替えるかを方策が選ぶ（W1）。質問は使わない。SFTの後にGRPO。
- **[VideoAgent-Fan]★**：GPT-4がツール（caption検索・区間の特定・VQA・物体Memoryの検索）を選び（O2+O4・R1）、質問を分解する（計画）。Memory（2秒segmentのcaptionと物体のSQL）は決まった処理で作る（W2a1）。
- **[VideoMultiAgents]★**：Text・Video・GraphのAgentが、それぞれツールを繰り返し呼ぶ（O4?・R2）。Organizerが答えをまとめる。chunkごとにscene graphを生成する（W2a1）。
- **[Response-G1]**：質問の後、毎時刻に「黙る／答える」をYes / Noのtokenで選ぶ（T）。各時刻のclipからscene graphを生成して追記する（W2a1）。scene graphの検索は類似度top-Kの規則。
- **[ProVideLLM]**：視覚tokenの待ち行列から押し出されるとき、モデルが行動のラベルに言語化して長期のテキスト枠（最大5件）へ移す（W2a1）。応答の主な仕組みは書かれていない（Tは付けていない）。選ぶ出力はない（判断なし）。
- **[Lando Edge]**：15秒ごとにMLLMが一人称の説明文を書いて追記し、映像は捨てる（W2a1）。質問時に全テキストをLLMに渡す。選ぶ出力はない（判断なし）。
- **[Watch-Think-Interact]**：区間ごとに「黙る／答える／過去の映像を呼び出す」を選ぶ（R4・T）。区切りごとにテキストMemoryを書き直す（W2b?）。呼び出した後、同じ時刻でもう一度判断する（F1）。SFTの後にRL。
- **[ThinkStream]**：区間ごとに推論文の後、黙るか答えるかを特殊tokenで出す（T）。推論文をKVとして残す（W2a2。残し方は固定の規則）。SFTの後にGRPO。
- **[StreamingVLM]**：実況のない秒に「...」を入れて学習し、いつ話すかを身につける（T?、K4）。自分の実況テキストをKVとして残す（W2a3）。KV cacheの管理は固定の規則。
- **[VideoStreaming]**：質問から作った指標と各clipの指標の類似度で、clipのMemoryを選ぶ（R4?、K1）。指標は学習済み。
- **[OmAgent]★**：課題を分類して部分課題の木に分解する（計画）。ツールを選び、元の動画の区間を見直す（O2・R1）。シーンごとにcaptionを作り、時刻と一緒にDBへ保存する（W2a1）。
- **[CogStream]**：LLMが、現在の質問に関連する過去のQAを選ぶ（R1）。同時に「テキストだけで答えられるか」のflagを出す（O5?）。過去のQAを追記する（W2a3）。検索用のLoRAをSFT。
- **[StreamMind]**：専用のgateが毎frame、LLMを呼ぶか（答えるか）を特殊tokenで決める（T、B3）。Memoryは状態空間モデルで毎frame1tokenを作る規則。
- **[R3-Streaming]**：readinessの部品が答えるか保留するかを決め、速いVLMが重いモデルへ回すかを決める（T）。Memoryの管理は規則。SFTの後にRL。
- **[StreamArena]**：Memory Writer（LLM）が4秒ごとにイベントの境界と記録を出す（W2c）。Routerが検索ツール（記録・Web）を選び（R3+R5）、部分課題に分ける（計画）。Front WorkerとMonitorが答えるタイミングを決める（T）。学習なし。
- **[Em-Garde]**：質問から「見つけるべき視覚手がかり」の候補文を作る（W2a4。1回目は計画）。発火は固定規則で、その後の応答を別のモデルが検証する（T?、K6）。SFTの後にGRPO。
- **[Memento]**：gateが「直前の記録に統合／全体を更新／新しく追加」を選ぶ（W1?、K1）。質問との関連度で記録を選ぶ（R4?）。frameごとに黙るか答えるかを出す（T）。
- **[ReWind]★**：全体を処理した後、指示文とMemoryのattentionで見直すframeを選び、高解像度で見る（O1?、K1）。
- **[M3-Agent]**：記憶用のMLLMがclipごとに出来事と知識を書く（W2a1+W2a2）。制御用の方策が検索文を書き、検索ツールを選ぶ（R2）。最大5回まで繰り返す（F1）。記憶用はSFT、制御用はRL。
- **[TraveLER]★**：Plannerが計画を作り（計画）、Retrieverが次に見る時刻を選び（O1）、Extractorが質問を作って答えを記録し、Summarizerが記録をまとめる（W2a1）。Evaluatorが情報の十分さを評価する（Cの「確信度」）。
- **[VideoTree]★**：LLMが各クラスタと質問の関連度を1〜3で採点し、それに応じて深く分けて追加のframeを見る（O1）。
- **[VideoAgent-Wang]★**：LLMがどの区間を探すかを選び、検索文を書いてCLIPでframeを取り出す（O2）。確信度が足りなければ追加で探す（F1）。
- **[VideoINSTA]★**：LLMが各イベントの情報量を採点し、上位から使う（R1）。確信度が最高でなければ次のclipを足して答え直す（F1）。

## 修正履歴

| 日時 | 変更 | 理由 |
| --- | --- | --- |
| 2026-10-17 | 初版作成：分類Aを段階の組み合わせ（重複なし）に再編し、観測を見る対象（O1〜O5）、残すをframe／テキスト（W1・W2）で細分した。A0の意味を具体例で説明した | ユーザー指示（観測は何を見るか、書き込みはframeかtextかで分け、表で論文が重複しないようにする） |
| 2026-10-17 | 観測と読み出しを分け（O・R）、読み出しをR1〜R4で細分した。テキストで残すnoteを「残す」に含め、W2をW2a〜W2cに分けた。計画を外す方針を確定した。[Memento]をW1にした | ユーザー指示（観測と読み出しを分ける、noteはtextで残すなら「残す」、計画は外す） |
| 2026-10-17 | 分類Aを1つの表（1本1行）にまとめ、2段目・3段目を作った。W2aを中身（観測の記録・推論のnote・自分の出力・質問から作るもの）で分けた。小分類の節は定義だけにした。方針を決めたい点（K7〜K9）を説明し直した | ユーザー指示（各分類は独立した表で1本1行、さらに分けられる小分類はもう一段分ける、決めたい点の説明） |
| 2026-10-17 | 表を「1段目・説明・2段目・説明・3段目・説明」の形にし、同じ段目が続く行は一番上だけに書いた。複数当てはまる論文は統合した小分類（O2+O4、R3+R5、W2a1+W2a2）に入れた。K7〜K9を決定として記録し、「残したものの使い道」を次の候補にした | ユーザー指示（表の見やすさ、複数当てはまる場合は統合、K7・K9は数えてそのパターンを定義に書く） |
| 2026-10-17 | 1回目との差分（第9節）を作り、2回目に載せていなかった1回目の節（タスク表、分類B〜G、境界例、推論、未確認、Memory分類への反映候補、付録A・B）を第10〜15節と付録に、1回目の位置づけ・判断の前提・分類Aを第9.1〜9.3節に転記した | ユーザー指示（タスク表を載せる、1回目から減った情報を差分として出して2回目に追記する） |
| 2026-10-17 | 1回目の内容を転記ではなく統合した：位置づけ・判断の前提を1つにし、分類B〜Gを分類Aの後に置いた。分類Cを1本1行の3段の表に作り直した。評価タスクをTS1〜TS8に改名し、1本1行の表に作り直した。境界例をK1〜K9の1つの表にした。推論・未確認・付録Bを2回目のコードで書き直し、重複した節（第9節の差分、1回目の分類Aの転記）を削除した | ユーザー指示（転記だけでなく、かぶる表を削除・分岐して統合する） |

## 関連文書

- [Agentの役割の分類：1回目](2026-10-14-agent-role-classification-round1.md)
- [Memory分類の判定基準](2026-10-14-memory-retention-classification-criteria.md)
- [Memory分類の1回目当てはめ](2026-10-14-memory-classification-round1.md)
- [Memory分類の2回目当てはめ](2026-10-14-memory-classification-round2.md)
- [文献調査の重要な問い](2026-10-14-critical-literature-review-questions.md)
- [2026-10-14 MTG議事録（2回目）](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-10-14-second-mtg.md)

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
[VideoAgent-Fan]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/3241_ECCV_2024_paper.php
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
[VideoStreaming]: https://proceedings.neurips.cc/paper_files/paper/2024/hash/d7ce06e9293c3d8e6cb3f80b4157f875-Abstract-Conference.html
[ReKV]: https://proceedings.iclr.cc/paper_files/paper/2025/hash/67a9b444cbcd647572c88194619f72d5-Abstract-Conference.html
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
[QueryStream]: https://iclr.cc/virtual/2026/poster/10011335
[ReWind]: https://openaccess.thecvf.com/content/CVPR2025/html/Diko_ReWind_Understanding_Long_Videos_with_Instructed_Learnable_Memory_CVPR_2025_paper.html
[M3-Agent]: https://iclr.cc/virtual/2026/poster/10009685
[video-SALMONN S]: https://icml.cc/virtual/2026/poster/61140
[ProtoKV]: https://icml.cc/virtual/2026/poster/63663
[TraveLER]: https://aclanthology.org/2024.emnlp-main.544/
[VideoTree]: https://openaccess.thecvf.com/content/CVPR2025/html/Wang_VideoTree_Adaptive_Tree-based_Video_Representation_for_LLM_Reasoning_on_Long_CVPR_2025_paper.html
[VideoAgent-Wang]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/10325_ECCV_2024_paper.php
[VideoINSTA]: https://aclanthology.org/2024.findings-emnlp.384/
