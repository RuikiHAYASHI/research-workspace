---
date: 2026-09-10
project: null
source_todo: "Awesome-Streaming-Video-Understanding（https://github.com/Yang011013/Awesome-Streaming-Video-Understanding）を調査する"
topic: Awesome-Streaming-Video-Understanding の Models 調査設計
status: exploratory
tags: [brainstorm, research]
---

# Awesome-Streaming-Video-Understanding の Models 調査設計

## 読み込んだ文脈

- 2026-09-10 のTODOに Awesome-Streaming-Video-Understanding の調査が登録されている。
- 対象リポジトリは Streaming/Online Video Understanding を、時刻 t では未来フレームを参照せず、フレームが順次到着し、逐次更新する causal な推論として定義している。
- Research Workspace の現在の `.research/lab/projects/` には研究プロジェクトREADMEがまだ存在しないため、今回は project=null の exploratory brainstorm として扱う。

## 相談の出発点

Awesome-Streaming-Video-Understanding の Models に列挙された各モデル/論文でいう「Streaming」が、自分たちの想定する Streaming と同じかを判定したい。

自分たちの想定:

- 10秒程度の短い動画ではなく、数十分〜数時間以上の長時間動画が対象。
- 入力時点では、その時点までに到着したフレームしかモデルへ渡せない。
- 動画を時間順に細切れで逐次処理する。
- 将来フレームへの look-ahead や、動画全体を見た後の再処理を前提にしない。
- Streaming能力の実現に追加学習が必須である必要はない。

## 対象TODO

- Awesome-Streaming-Video-Understanding（https://github.com/Yang011013/Awesome-Streaming-Video-Understanding）を調査する

## 問い

中心問い:

- 各論文の「Streaming/Online」は、自分たちの想定する causal・逐次・長時間の Streaming と同じか。

サブ問い:

- future frame を本当に参照しない推論契約になっているか。
- フレーム/チャンクは時系列順に到着し、過去状態を更新しながら処理されるか。
- 動画全体を事前に読み込む前処理、global sampling、future-aware segmentation 等が混ざっていないか。
- 評価動画は実際に何分/何時間あるか。平均・中央値・最大値は何か。
- 長時間性は benchmark 名やタイトル上だけでなく、実験条件として確認できるか。
- query は動画開始前、途中、終了後のどのタイミングで与えられるか。
- 長期履歴を何で保持するか（KV cache、memory token、retrieval、hierarchical/event memory、compression 等）。
- Streaming実現のために専用学習/SFTが必要か、training-free か。

## アイデア候補

### 1. まず全モデルを浅くスクリーニングする

各論文について、abstract / project page / README / experiment section を使って以下を1行ずつ埋める。

- Causal input: Yes / Partial / No / Unclear
- Sequential processing: Yes / Partial / No / Unclear
- Future-aware preprocessing: None / Exists / Unclear
- Evaluated duration: average / median / max
- Long-horizon class: <10min / 10-30min / 30-60min / >=1h / near-infinite
- Query timing: pre-given / online / post-hoc / proactive
- Task: QA / dialogue / caption / proactive interaction / representation
- Memory mechanism
- Training requirement
- 自分たちとの一致度: A / B / C

### 2. 「Streaming」と「Long Video」を別軸にする

Streamingかどうかと、長時間動画を扱っているかは同一ではない。

- Streaming強・長時間強: 最優先
- Streaming強・長時間弱: 方式は参考になるが研究設定は不一致
- Streaming弱・長時間強: 長時間メモリ技術は参考になるが causal streaming の証拠不足
- Streaming弱・長時間弱: 優先度低

### 3. 真のStreamingを壊す隠れ前処理を確認する

論文本文だけでなく、可能ならコードの evaluation / dataloader / frame sampling も確認する。

特に見る点:

- 全動画から先に均等サンプリングしていないか。
- 全動画を読んで scene boundary を決めていないか。
- 質問を使って過去全体を再エンコードしていないか。
- current chunk 以外の future features が cache に混ざらないか。
- 評価時だけ offline protocol になっていないか。

## 仮説候補

- Awesomeリポジトリ全体の Streaming 定義は、自分たちの causal / sequential input の定義とかなり近い。
- ただし Models に並ぶ論文は、動画時間スケール、query timing、memory protocol、offline preprocessing の有無が大きく異なり、「Streaming」という語だけでは同一研究設定とみなせない。
- 最も近い論文は、near-infinite / >=1h の動画を、future frameなしで逐次処理し、固定または有界メモリで履歴を保持する系統になる可能性が高い。

## 実験・実装案

今回は実験ではなく文献調査を2段階で進める。

### Stage 1: 全モデルの一次スクリーニング

Models一覧を対象に、上記判定表を作る。ここでは1論文あたり深追いせず、明確にA/B/Cへ分類できる材料を集める。

### Stage 2: A候補の深掘り

A候補について以下を詳細化する。

- dataset / benchmark 名
- 実動画長の統計
- input arrival protocol
- chunk/frame rate
- memory update rule
- query arrival protocol
- training requirement
- causal性を壊す前処理の有無
- 実装コードでの入力順序・cache更新
- 自分たちの sequential loader / agent型Online VideoQAへ転用できる点

## 比較・評価軸

### 必須Gate

1. Causal: 時刻 t で future frame を参照しない。
2. Incremental: 新しいフレーム/チャンクが来るたびに状態を更新する。
3. Temporal order: 入力は前から後ろへ順番に処理される。

### 長時間Gate

- Strong match: >=1時間級、または平均が時間単位 / near-infinite を明示。
- Medium match: 10〜60分級。
- Weak match: 数分以下のみ。

### 一致度

- A: causal + incremental + sequential を満たし、時間単位の動画を実際に評価。
- B: causal streaming は満たすが、評価動画が短い/中程度、または長時間性のEvidenceが弱い。
- C: Streamingの意味が主に対話タイミング、効率化、captioning等で、自分たちの入力契約とは異なる、またはfuture-aware/offline処理を含む。

## 今回見えた方向性

予備確認:

- StreamingVLM は「infinite visual input」を対象にし、Inf-Streams-Eval では平均2時間超の動画を使う。自分たちの想定に非常に近い最優先候補。
- VideoLLM-online は sequential streaming dialogue を明示しているが、公開READMEではモデル世代により 10分 / 60分の設定がある。Streaming性は強いが、時間スケールは世代ごとに分けて見る必要がある。
- Flash-VStream は long video stream を online setting で評価し、Video-MME には最大1時間の動画が含まれる。強い候補だが、各benchmarkの実入力protocolを確認する必要がある。
- LiveVLM は training-free で streaming-oriented KV cache を構築し、online QAを行うため、学習必須ではない手法として重要候補。ただし、現時点の予備確認では時間単位動画のEvidenceをまだ確認していない。
- VideoLLaMB は streaming captioning を実装する一方、公開された長さstress testは最大約320秒であり、数時間級という観点では現時点では弱い。

## 次アクション候補

- Awesome README の Models 全件を一次スクリーニング表にする。
- まず StreamingVLM / VideoLLM-online / Flash-VStream / LiveVLM / StreamForest / StreamMem / Streaming Long Video Understanding / VideoLLaMB を優先して調べる。
- A候補に絞った後、論文本文だけでなく公式コードの dataloader / streaming inference / cache update / evaluation protocol を読む。
- benchmark側の動画長統計を論文の主張とは独立に確認する。

## Spec化候補

まだ exploratory。一次スクリーニングを終えて、どのモデルを深掘りするかと判定基準が確定した段階で、文献調査specへ昇格可能。

## 未解決の問い

- 「長時間」の最低ラインを厳密に 1時間以上とするか、10〜60分も比較対象として残すか。
- queryが動画終了後に与えられても、映像自体をcausalに一度だけ処理していれば対象に含めるか。
- フレームを1fps等で間引くことを許容するか。それとも到着した全フレームを逐次処理することを必須にするか。
- 現在のResearch Workspaceに、この調査を紐づける研究プロジェクトREADMEが未作成である点をどう扱うか。

## 関連ファイル

- `.research/secretary/todos/2026-09-10.md`
- `.agents/skills/brainstorm/SKILL.md`
- https://github.com/Yang011013/Awesome-Streaming-Video-Understanding
