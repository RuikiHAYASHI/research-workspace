---
date: 2026-09-11
project: null
source_todo: null
topic: Streaming VideoQA MTG explanation
status: exploratory
tags: [brainstorm, research]
---

# Streaming VideoQA MTG explanation

## 2026-09-11 MTGでの説明方針

調査内容の列挙ではなく、`問題設定 -> Streaming条件 -> 難しさ -> 既存研究 -> 今回の研究仮説 -> Ask` の順で説明する。

### 問題設定

通常のVideoQAでは、動画全体を参照してから質問に答える設定が多い。一方、今回考えたいのは、Queryを動画開始時点から与え、動画を時間順にchunkで受け取り、まだ到着していないfuture chunkを見ずに回答へ必要な情報を蓄積するStreaming VideoQAである。

### Streaming条件

Streamingの必須条件として最初に固定するのは以下に限定する。

- Queryは `t=0` から既知。
- 動画はchunk単位で時間順に到着する。
- `chunk_{t+1:T}` にはアクセスできない。

「過去動画全体を毎回再推論しない」「memoryを逐次更新する」「Queryでmemoryを選別する」はStreamingの定義ではなく、今回の提案手法・効率性の設計として後で説明する。

### 難しさ

長時間動画では、全visual情報をそのまま保持すると計算量・memory量が増え続ける。一方で古い情報を単純に捨てると、Queryへの回答に必要だった情報を失う可能性がある。したがって、`何を残し、何を捨てるか` が中心課題になる。

### 既存研究への接続

Awesome-Streaming-Video-Understanding掲載手法を、future frameを使わないこと、hidden offline preprocessingを避けること、長時間streamを扱えることからスクリーニングし、StreamingVLM / StreamForest / StreamMem / StreamAgentを重点調査した。

- StreamingVLM: bounded KVと逐次推論。
- StreamForest: event memory。
- StreamMem: bounded/query-agnostic memory。
- StreamAgent: query-aware agent decision。

### 今回の研究仮説

今回試したいのは、Sequential Loaderでfuture accessを環境側から禁止し、Agentが `Query + current chunk + これまで残した外部Memory` を見ながら、何を保持・要約・破棄するか判断する構成である。

```text
Query (t=0)
    +
current chunk
    +
External Memory
    ↓
Agent
    ↓
KEEP / SUMMARIZE / DROP
    ↓
next chunk
```

ここでMemoryは「過去に観測した動画から、最終回答のために残しておく情報」と定義し、KV cacheやhidden stateとは区別する。

### MTGでのAsk

- causal条件はchunk-levelで十分か、frame-levelまで要求するか。
- 最初の研究対象をVLM内部KVの改造ではなく、Sequential Loader + Query-aware External Memoryに置くか。
- 過去raw videoへの再アクセスを禁止し、Agentが捨てた情報は失われる設定にするか。
- baselineを current chunk only -> query-agnostic bounded memory -> query-aware bounded memory -> agent memory の順で比較するか。

## 現在の方向性

MTGでは「StreamingVLMを詳しく説明すること」自体を目的にせず、StreamingVLM等を根拠として、今回の研究では `future accessの制御` と `Query-awareな記憶判断` を分けて設計したい、という研究上の問いへつなげる。

## 2026-09-11 01:44 JST 更新: 研究案は指導側から既に提案済みの場合の流れ

研究案そのものを説得・提案する必要はない。MTGの役割は、指導側から提示された方向を受けて自分がどのように問題設定を理解し、どの既存研究を調べ、次の実験条件をどう解釈したかを確認することに置く。

推奨する説明順は次の通り。

1. **前回提案の受け止めを一文で確認**
   - 「前回いただいた、Streaming VideoQAでQueryを使いながら必要な過去情報を残す方向について、まず問題設定と既存研究を整理しました。」
2. **今回のStreaming VideoQAの定義を共有**
   - Queryはt=0から既知。
   - videoはchunk単位で時間順に到着。
   - future chunkにはアクセスしない。
   - memory更新やfull-prefix再推論禁止はStreamingの定義そのものとは分けて扱う。
3. **なぜ4論文を調べたかを説明**
   - future accessなし、hidden offline preprocessingなし、長時間streamを扱う仕組みという観点で候補を絞った。
4. **4論文は一言ずつのみ報告**
   - StreamingVLM = efficient incremental processing / bounded KV。
   - StreamForest = event memory。
   - StreamMem = bounded query-agnostic memory。
   - StreamAgent = query-aware agent decision。
   - 詳細は質問された場合だけ説明する。
5. **4本を通して得た整理を共有**
   - Streamingという共通ラベルでもcausal granularityとmemory設計は異なる。
   - 今回の研究に近い要素は一つの論文に全部あるのではなく、4本に分散している。
6. **認識確認のAskで終える**
   - chunk-level causalという理解でよいか。
   - past raw video rereadを許すか。
   - External Memoryをまず主対象としてよいか。
   - 初期baseline / dataset / video durationをどう置くか。

この構成では「難しさ」や「今回の研究仮説」は、先生がすでに研究方向を共有しているため独立した長い説明にせず、定義と既存研究の整理からAskへつなぐための短い補助説明に留める。

## 2026-09-11 12:58 JST 更新: StreamAgentとの近さと差分候補

StreamAgentは、Query semantics・過去memory・current clipを使ってAgentが次の観測や回答タイミングを決めるため、今回の `Query-aware Agent + Streaming Video` に最も近い既存研究である。したがって今後は「StreamAgentと似ている」こと自体ではなく、どの条件・memory contract・評価軸で差分を作るかを中心に整理する必要がある。

現時点の差分候補:

- **Query timing**: StreamAgentはstream途中でQueryが来る設定を含む。一方、今回はQueryを `t=0` から既知とし、最初のchunkからmemory write / keep / deleteをQuery-awareにできる。
- **主対象**: StreamAgentはanticipatory planning、回答タイミング、観測位置、KV selective recallまで含む。一方、今回はまず `何をMemoryに残すか` というmemory management自体を切り出して評価する方向が候補。
- **Memoryの定義**: 今回はVLM内部KVとは別のExternal Memoryを主対象に置き、`KEEP / SUMMARIZE / DELETE` をAgent actionとして明示する候補。
- **Access contract**: Sequential Loader側でfuture accessを禁止し、さらにpast raw video rereadも禁止するなら、「捨てた情報は本当に失われる」というより強いmemory selection problemにできる。
- **比較可能性**: current chunk only / query-agnostic bounded memory / query-aware bounded memory / agent memoryの段階比較により、Agent化そのものの効果を分離して測る候補。

この差分はまだexploratoryであり、新規性の主張として確定していない。特にStreamAgentの正式なQuery timing・memory update contract・raw video access条件と、今回採用する実験条件を並べて確認する必要がある。
