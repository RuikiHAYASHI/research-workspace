---
date: 2026-10-14
project: agentic-streaming-videoqa
source_todo: "2026-09-11 MTG: Agent系研究とMemoryの既存機能・未解決点"
topic: critical-literature-review-questions
status: exploratory
tags: [brainstorm, research, literature-review, memory, agent, anticipation]
---

# 10/14 文献調査の行き詰まりから研究上の重要な問いを再設定する

## 出発点（ユーザーの声）
- StreamAgentのRelated WorkからオフラインAgent論文を約1時間半読んだが、Memory保持・予習Agentとの関連が見えず方針をリセットした。
- Awesome Streaming Video Understandingを読み、StreamForestのmeta-event等の具体的Methodを追い始めたが、「自研究との差分を調べるのが優先で、現時点では実装詳細は不要」と気づいた。
- 今回は「明日のMTGまで何を軸に論文を読み、どの観点が決定的か」の壁打ち。分類体系や新規性の確定・実装を依頼していない。

## 権威ある現在文脈
- 2026-09-11 MTGの決定: Queryはt=0から既知、未来frameへアクセスしないchunk-level causal setting。Agent系Streaming VideoQAの「できる/できない」、Memory媒体（text/KV/feature）、動的chunk・multi-timescale・重要イベント・予測などを調査。StreamAgentが近く、Agentを使うだけでは研究差分にならない。
- 2026-10-02 MTGはAgent入出力・責務・promptを理解することを優先。
- 現行project READMEではAgent系機能・未解決点とMemory媒体の分類が未完了。
- 2026-10-09の実験分析brainstormでは累積Summaryの長期劣化（脱落、重複、矛盾、token上限）を未検証問題として整理。Answer validation failureをAnswer accuracy failureと混同しない。
- 10/14予習Agent brainstormでは「未来イベントの予測」と「将来の質問分布の予習」を異なる意味として整理。両方は未採択の探索候補。
- 既存の10/14 tree-strategyメモの「媒体・構造・更新操作・agent・設定は別軸」と整合するが、今回は調査優先順位をより絞る。

## 問題の立て直し
論文のジャンルやタイトル（Offline Agent、Visual Memory、Text Memory）を先に決めて全件読むと、具体的な研究の問いへつながらないまま脱線する。逆にStreamForestのmeta-event実装を最初からすべて追っても現在の研究差分への寄与は限定的。最初に「その論文から検証したい主張」を決めて関連箇所だけ読む。

## Criticalな調査観点（推奨・未採択）
### Gate: 本研究と比較できる設定か
- 動画が順に到着し未来のframeを見ないか。毎回全動画を読み直すpseudo-streamingと過去状態を再利用するincremental processingを区別。
- Questionは動画開始時に既知か、途中到着か、不明か。過去raw framesの再読込可否は別項目として記録。
- offline論文は直接の競合から保留できるが、memory policyを移植可能ならcomponent-paperとして利用する。

### Critical 1: 何を記憶し、何を捨てるか
- すべての場面を等しく残すか、重要イベントやQuestion-related factsを選ぶか。
- 選択は現在のQuestion・過去Memory・予測される未来・一般的な質問傾向のどれに依存するか。
- 「重要」をModel/Agentが意味的に決めるか、similarityやfixed budget等の規則が決めるか。

### Critical 2: 保存した情報をどう維持・更新・検索するか
- append, rewrite, update, merge, compress, discard, retrieve。1本の累積text要約を毎window再生成する方式と、immutable event recordsや二層記憶・階層要約を分ける。
- 過去factの生存、時間順、根拠への再アクセス、容量、遅延のtradeoff。
- Text/Visual/KVの媒体は重要な観察項目だが、媒体の二分だけでは研究差分は判断できない。

### Critical 3: Agentの予測は実際の観測・Memoryの意思決定を変えるか
- Future-event anticipation（次に何が・どこで起きるか予測して観測位置・密度・回答タイミング等を変える）と、future-query anticipation（まだ未知の将来質問に備え一般的に残す情報を選ぶ）を分離。
- 本研究はQuestion=t0既知なので、既知の質問に基づくaction planningは直接関連し、質問が未到着の研究は前提差を明記する。
- Agentを配置することとAgentがmemory write/deleteを実際に選択することは別。観測行動だけを変える論文を「agentic memory selection」と分類しない。

### Critical 4: 何が実験で示されたか
- 保持・検索・予測・Agent選択を無効化したablationや適切なbaselineがあるか。
- 何のbenchmark、queryタイミング、memory budget、latencyで改善したか。
- 「著者ができないと示した」「論文で評価されていない」「現時点で自分が読めていない」を区別。

## 今夜の推奨ルート
1. 2つの質問に集中：「必要な証拠をMemoryに残せるか」「予測・Agentが残す/観測する情報を変えるか」。
2. 前提Gateが近いものを中心に、5分程度でAbstract/Introduction/Method図/ConclusionをScan。
3. 各論文に一行だけ残す: 「動画/Question設定、何を選んで残す/消す、Agentが何を決める、何が実証済みか、未確認」。未読は空欄か未確認。
4. 解けない問いが生まれた論文だけ、Method該当箇所とExperiments/Ablationまで進む。StreamForestのmeta-event分割の厳密手順は「event segmentation/merge」主軸にしたとき精読する。
5. MTGでは「何種類見つけたか」以上に、できること・未解決として残ること・自研究と前提が同じか・次に掘る質問を説明する。

## 論文例（既知の一次資料に基づく）
- StreamAgent https://arxiv.org/html/2508.01875 — compact text m_t + KV selective recallと、将来のtask-related evidence予測からcrop/追跡等の観測行動を制御。memory storeの重要イベントwrite/deleteをAgentが直接判断しているかとは別の問い。
- StreamForest https://arxiv.org/abs/2509.24871 — visual event treeをpenaltyに基づき統合、短期時空間windowを併用。Agentが重要事実を自然言語で選んで記録する研究とは区別。
- OneStreamer https://arxiv.org/abs/2610.01762 — Question未到着でもtime-grounded captionsと完了event summariesを記録する。自研究のtext event memory候補との比較が必要で、「テキストイベントを残すだけ」を新規性にはしない。
- LangRepo https://arxiv.org/abs/2403.14622 — iterative all-textual multi-scale repositoryのwrite/read。streaming protocolが同一かは別途確認が必要。

## 反例・保留
- Offline Agent論文を全部読むのは保留。もしAgentが有用なmemory write/delete policyを提供するなら関連部分だけ再利用可能。
- Event Memory/階層Memoryの「有無」だけでは新規性は判断不能。OneStreamerやLangRepo等の近接例が存在。
- すべてのAgentを「記憶を選ぶAgent」と扱うのは誤り。
- Text Summary劣化は未検証の仮説であり、早期windowのfact lossがどの原因によるかの定量化が必要。
- Question=t0既知なので「未来の質問を予習するAgent」が本当に主要課題かは未決（一般化のためのpriorとしては候補）。

## 次の判断（ユーザーがMTGで決める候補）
A. 「過去の重要証拠の保存・保持」と「Agentによる観測/保存の選択」のどちらを主軸にするか。
B. 最重要な失敗例を「古い事実の消失」「関連情報をそもそも観測・保存しない」「検索できない」「回答時期が不適切」のどれに置くか。
C. Question=t0既知を引き続き固定する場合、予習の意味をfuture-event predictionに絞るか、質問分布priorも候補に残すか。

## 関連文書
- .research/lab/projects/agentic-streaming-videoqa/README.md
- .research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md
- .research/secretary/notes/brainstorm/2026-10-14-memory-literature-review-tree-strategy.md
- .research/secretary/notes/brainstorm/2026-10-14-anticipation-and-text-memory-literature.md
- .research/secretary/notes/brainstorm/2026-10-09-initial-behavior-result-analysis.md

本メモはexploratory。TODO・README・spec・研究コードへの変更および研究方向の採択は行わない。


## 2026-10-14 01:26 JST 追加壁打ち：まだ絞らない横断探索

### ユーザーの判断
- A.重要情報の忘却 / B.重要情報の保存選択 / C.次の観測・予習 のいずれにも現時点では絞りたくない。明日のMTG前に広く調べて、方向を決めるための材料を集めたい。
- 従って前段の「Aを主軸として収束」などの案は採用扱いしない。研究テーマは保留、検索の問いだけ限定する。

### 構造化された探索の入口
Streaming VideoQAでQAに必要な情報が使えなくなる地点を、以下のライフサイクルとしてみる。
1. 観測: 重要frameや領域を取り逃す。
2. Write/Selection: 観測したがMemoryへ保存しない。
3. Maintenance: 保存したがupdate/merge/compressで失われる。
4. Retrieval/Answer: Memoryにあるが選択・利用に失敗。
Anticipation / Agent policyはどの地点の意思決定に介入するかが本題であって「Agent系」だけでは比較軸にならない。

### 明日のMTG前に調べる5つの問い（研究テーマ選択ではなく検索トラック）
- 過去情報を何として・どの形で保存する？（text / visual / KV / hybrid、階層・短長期）
- 保存すべきものをどう選ぶ？（query-aware、query-agnostic、rule、agent）
- 先読みは何を変える？（将来の出来事/質問傾向、観測、保存、chunk長、応答タイミング）
- 保存情報をどう取り出す？（retrieval、過去の証拠へ再アクセスできる条件、最終QA）
- 利益を何で示す？（memory予算、fact保持、QA精度、latency、ablation）

### 対象を広く保つための比較Gate
- 最優先：future-free なオンライン/逐次入力、Question=t0既知。
- 周辺の構成技術：Queryが途中で与えられる/未知だが、Online Memory選択などが参考になる研究。
- 参考：Offline Agent/long-videoにMemory方策やretrieval設計がある研究。未来映像を先読みできるoffline方式はdirect competitor扱いしない。
- 推論時KVがあることと、長期保存・選択再利用するKV Memoryであることを分ける。
- 「研究ができないこと」「本文で未評価」「自分がまだ見ていないこと」を分ける。

### 広さを保った最初の6本（入口候補）
- Text write/read: LangRepo https://arxiv.org/abs/2403.14622
- KV budget: StreamMem https://arxiv.org/abs/2508.15717
- Visual event consolidation: StreamForest https://arxiv.org/abs/2509.24871
- Agent-driven frame keep/replace/discard: SVMemAgent https://arxiv.org/abs/2609.18540
- Future task-related evidence anticipation + adaptive perception: StreamAgent https://arxiv.org/abs/2508.01875
- Query-independent event caption memory + timely response: OneStreamer https://arxiv.org/abs/2610.01762

上記は各方向の存在例で、包括的なSurveyや公平な性能比較を完了したという意味ではない。StreamAgentはtext+KV併用、OneStreamerはtext+visual recent-windowなど多軸表現に注意。

### 2パス探索（非固定）
- パス1: 各論文Abstract・導入・図・結論を5–8分程度確認し、以下を一行ずつ書く。論文名/URL、解決対象、memory媒体、Agentが決めるaction、Query/future条件、疑問または未検証を短く残す。全欄強制入力しない。
- パス2: 異なる研究方向の間にある疑問（例: 観測制御と記憶選択を同時にする例は？ / text event ledgerでも長期保持は劣化？ / query t0既知なら選択が改善？）を検索。各方向につき関連論文を最大1〜2本追加する程度から始める。
- 論文にあるRelated Workを全件精読しない。どの問いへ貢献するかがわからなければ保留する。meta-eventの細部を掘る前に、何の比較を支えるか確認。
- MTGに持ち込むのは学会向け分類表の完成品でなく、「既に存在が確認できた仕組み」「条件差で比較不能なもの」「未確認だが調べる価値のある問い」「どの問題を先に深掘りすべきかという相談」。
- 発見した論文数を最大化することは目的ではない。異なるメカニズムが見つかり、未知の論点を1つ以上言語化できれば一次探索として十分。

### 反例・不確実性
- 現在のSummary劣化は観測/選択/更新/回答どこで起きたのか未検証であり、Memoryだけが原因と決め付けない。
- 質問未到着のSVMemAgent/OneStreamerからQuery=t0既知への直接性能一般化はできない。
- Text/Visualの媒体が異なっても、同じ「重要な情報を選ぶ」という方策があるので、媒体だけで排他的分類しない。
- 既存研究に無いことを主張するには本文・実験・関連研究を監査する必要がある。現段階では「今回の探索範囲で未確認」と表記する。

### 次の判断候補（まだ未承認）
- 4段階のどこが現在の実験で支配的な失敗か、先に診断するか。
- 「Questionが開始時既知」を固定し続けるか、将来質問未知にも広げるか。
- どの方式を比較するかをMTGで決めたらLevel 2/3精読に移る。今はspec作成、実装、TODO追加なし。
