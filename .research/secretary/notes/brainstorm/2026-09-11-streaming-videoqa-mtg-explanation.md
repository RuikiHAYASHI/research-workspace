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