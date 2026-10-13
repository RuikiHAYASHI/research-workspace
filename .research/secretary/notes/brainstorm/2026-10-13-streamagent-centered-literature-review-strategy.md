---
date: 2026-10-13
project: agentic-streaming-videoqa
source_todo: null
topic: StreamAgentを軸にした関連研究の深掘り方針
status: exploratory
tags: [brainstorm, research, literature-review, streamagent]
---

# StreamAgentを軸にした関連研究の深掘り方針

## 出発点

StreamAgentを一本の基準論文として読み、そこからAgent、Memory、Streaming、Long Video QAなどの観点別に関連研究を掘る。
関連論文はまずAbstract / Introduction / Related Work / Methodを中心に読み、必要な論文だけ深く追う方針を検討する。

## 現在の文脈

- プロジェクトREADMEでは、Agent系Streaming Video Understanding / VideoQAの既存機能と未解決点整理、およびMemory表現のtext / KV / feature等への分類が未完了マイルストーン。
- 2026-09-11の既存brainstormでは、StreamAgentをQuery semanticsを使って観測・待機・retrievalをagentが決める手法として整理済み。
- 現在の研究はSituation / Summary / Answerの逐次処理を持ち、Agentの責務・Memoryの保持と更新・Query-awareな情報選択が研究上の主要論点になっている。

## 推奨方針

### 1. 論文を読むのではなく「同じ問いを全論文に当てる」

各論文で少なくとも以下を揃える。

- Problem setting: offline / online / streaming、future accessの有無。
- Query timing: t=0で既知か、途中で到着するか。
- Input granularity: frame / clip / chunk / window。
- Agentの有無と役割。
- Agentのaction space: observe / wait / retrieve / summarize / discard等。
- Memory表現: text / KV / feature / event / hybrid。
- Memory update: append / rewrite / merge / prune / compress。
- Retrieval / selectionがquery-awareかquery-agnosticか。
- Long-termとrecent informationの分離方法。
- Training: training-free / SFT / streaming training等。
- Benchmarkと比較baseline。
- Ablationで何が効いたか。
- Limitationと未解決点。
- 自分の研究との差分。

この固定フォーマットで読むと、論文ごとの要約集ではなく比較可能な研究地図になる。

### 2. StreamAgentを「基準座標」にする

StreamAgentを最初だけ深く読み、以後の論文ではStreamAgentとの差分を中心に記録する。

例:

- StreamAgentよりMemory寄りか。
- Agentの意思決定がより強いか弱いか。
- Query-awareか。
- semantic text memoryかlatent/KV memoryか。
- observation policyまで変えるか、memory managementだけか。
- true streamingか、causal prefix evaluationだけか。

### 3. 関連論文を3種類に分ける

- Direct competitor: 問題設定と目的が近く、そのままRelated Workや比較実験候補になる。
- Component paper: Memory compression、retrieval、event segmentation、active perceptionなど一部分だけ直接関係する。
- Conceptual inspiration: Agent、episodic memory、anticipation等、設計思想は参考になるが直接比較対象ではない。

この区別をしないと、関連研究が増えるほど「全部重要」に見えて収束しなくなる。

### 4. 読む深さを3段階にする

#### Scan
Title / Abstract / Figure / Intro / Conclusionを読み、関係の有無を判定する。

#### Extract
関係があればRelated Work / Method / Experimentsの比較表・Ablationを読み、固定観点を埋める。

#### Deep Read
Direct competitorまたは自分の研究主張を左右する論文だけ、数式・implementation・supplement・codeまで読む。

最初から全論文をDeep Readしない。

### 5. Experimentsを省略しない

Methodまでで止めず、最低限以下を見る。

- 何と比較したか。
- どの設定で勝ったか。
- どのcomponentを外すと落ちるか。
- accuracy以外にmemory budget / latency / throughput等を測っているか。
- 本当にfuture informationを使っていないか。

新規性候補やbaseline設計は、MethodよりAblationから見つかる場合がある。

## 最初の探索順序候補

1. Agentic Streaming VideoQA / Video Understanding
2. Streaming Memory / Memory Compression
3. Long-video Agent / External Memory
4. Active Perception / Tool-use / Selective Observation
5. Event Memory / Hierarchical Memory
6. Anticipation / Future-aware planning
7. Query-aware retrieval / Query-conditioned memory

まずAgent系を集中的に掘り、その後Memory系へ進むのが現在の研究マイルストーンと整合する。

## 各論文の最小メモ

長い要約を毎回作らず、まず次だけ残す。

- 一言: この論文は何を解決するか。
- 手法: 何をどう保持・選択・更新するか。
- Streaming条件: future access / query timing / input granularity。
- Memory: 表現・更新・budget。
- Agent: 何を判断できるか。
- Evidence: 主なbenchmark / ablation。
- StreamAgentとの差分。
- 自分の研究への示唆。
- 次に読む引用1〜3本。

## 重要な注意点

- 「streaming」という語だけで同じ問題設定とみなさない。
- causal accessとincremental computeを分ける。
- Queryがt=0で既知か途中到着かを必ず記録する。
- memory capacityとmemory representationを分ける。
- semantic text summaryとKV cacheを同じMemoryとして一括りにしない。
- Related Workに出た論文をすべて読むのではなく、現在の比較軸を埋めるものだけ優先する。
- 既存研究の説明を集めるだけでなく、「この論文では何ができないか」を必ず1行書く。

## 現時点の方向性

最有力は、StreamAgentを基準論文として一度深く読み、その構成要素を比較軸へ分解した後、観点ごとにcitation graphを辿る方式。
特に最初はAgent系を優先し、Agentが何を意思決定しているか、Memoryへどこまで介入するか、Queryをいつ・どのように使うかを揃えて比較する。

## 未解決事項

- 文献メモを最終的にpapers/へ論文単位で残すか、横断比較資料を別途作るか。
- Related Work用の分類軸をAgent / Memory / Streamingで分けるか、問題設定 / Memory / Decisionの機能軸で分けるか。
- 最初のDirect competitor集合をどこまで広げるか。

## 次アクション候補

- StreamAgentを固定フォーマットで再読し、比較軸の基準表を作る。
- StreamAgentのRelated WorkからAgent系Direct competitorを5〜10本だけ一次抽出する。
- 各論文をScanし、Direct competitor / Component / Inspirationへ分類する。
- Direct competitorだけExtractし、比較表を作ってから次の探索方向を決める。
