---
date: 2026-09-11
project: null
source_todo: "Awesome-Streaming-Video-Understanding（https://github.com/Yang011013/Awesome-Streaming-Video-Understanding）を調査する"
topic: Awesome-Streaming-Video-Understanding Models 全件比較
status: exploratory
tags: [brainstorm, research, streaming-video]
---

# Awesome-Streaming-Video-Understanding Models 全件比較

## 2026-09-11 13:18 JST: Models 21件の一次比較とMTG Notion同期

Awesome-Streaming-Video-Understanding の現在の `Models` セクション21件を、MTGで確認したい以下の軸で一次整理した。

- 論文タイトル / URL
- 動画長
- 手法の目的（効率、精度、interaction等）
- frame読みの観点でOnlineか
- Query timing
- Agent利用の有無

比較表は現在のMTG Notionページ末尾へ同期した。

- MTG Notion: https://app.notion.com/p/3d777f89f3cd80dab6c5f6efc924e337
- Source list: https://github.com/Yang011013/Awesome-Streaming-Video-Understanding

## 判定ルール

### Online

ここでの `Online` は **frame accessの観点**に限定する。時刻 `t` でfuture frameを先読みせず、到着したframe / clipを時間順に処理するかを見る。

これは次とは別軸である。

- 過去計算をKV等で完全に再利用しているか。
- 過去raw frameへ再アクセスできるか。
- memoryが固定長か。
- Query-awareにmemoryを書いているか。

### 動画長

論文や公開実装で確認しやすい代表的なbenchmark / model settingを記載した。各論文で評価protocolが異なるため、表中の秒・分・時間は厳密な横並び比較ではない。単一の上限が明確でないものは `benchmark依存` / `arbitrary-length` とした。

### Agent

- `Yes`: 明示的にAgent / Video agentとして構成されている。
- `Agent的`: decision module / cognition gate / proactive router等はあるが、明示的なAgent frameworkとは分けた。
- `No`: 通常のVLM / memory / cache / interaction modelとして扱う。

## 比較上の重要な確認事項

### Query timingは大きく異なる

frame accessとしてOnlineな手法は多いが、**Queryを動画開始時 `t=0` から既知にする設定は一般的ではない**。

特に今回の研究との比較で重要なのは次。

- **StreamMem**: 将来のQueryを未知としたquery-agnostic memory。stream中は実QueryなしでKV memoryを書く。
- **LiveVLM**: Questionが来る前からstreamをKV化し、Query到着後にshort / long-term KVをretrieveする。
- **StreamAgent**: Queryはtimestamp `t` で来る。その時点で証拠不足ならWAITし、`t` より後に新しく到着したframeを後から観測して回答できる。
- **StreamChat (2412.08646)**: Query後もdecoding中に新着frameを取り込み、answerを更新できる。
- **VideoStreaming (2405.16009)**: 動画をclip単位でstreaming encodeした後、post-hoc Queryを使って関連memoryを選択する。

したがって、今回の `Queryはt=0から既知 / future chunkは未到着なので見えない / 最初のchunkからQuery-awareにMemoryを管理する` という設定は、既存の多くのstreaming手法とはQuery timingで区別できる候補がある。ただし、これは新規性確定ではなく追加auditが必要。

## Agent利用の整理

明示的なAgent利用として特に重要なのは次。

- **StreamAgent**: anticipatory AgentがQuery/historyから観測・WAIT・recall等を決定。
- **STREAMCHAT (ICLR 2025, 2501.13468)**: 公式実装側でもVideo Agentとして記述される。

以下はAgent的なdecision構造を持つが、今回の一次表では明示的Agent frameworkと分けた。

- **LION-FS**: Fast Pathがresponse necessityを判定。
- **STREAMMIND**: Cognition Gateがevent-drivenにLLM起動を決定。
- **DisPider**: Perception / Decision / Reactionを分離し、Decision moduleがinteractionを制御。

## 21件の一次分類

1. StreamingVLM — Online / Query固定なし（commentary中心） / Agentなし
2. StreamForest — Online streaming mode / timestamp Query / Agentなし
3. StreamMem — Online / Query後着・query-agnostic write / Agentなし
4. StreamAgent — Online / timestamp Query + WAIT可能 / Agentあり
5. CogStream — Online simulation / ongoing Query / Agentなし
6. Proactive Assistant Dialogue Generation — Online / fixed Queryなし / end-to-end assistant
7. Flash-VStream — Online / asynchronous Query / Agentなし
8. LiveVLM — Online / Query後着 / Agentなし
9. StreamFormer — Online / current-timestamp task / Agentなし
10. LiveCC — Online commentary / fixed Queryなし / Agentなし
11. ViSpeak — Online / multimodal instructionがstream中に到着 / Agent的interaction
12. LION-FS — Online / proactive / Agent的decision router
13. STREAMMIND — Online / always-on proactive / Agent的Cognition Gate
14. STREAMCHAT (ICLR 2025) — Online / multi-round Query / Agentあり
15. DisPider — Online / mid-stream intent + proactive / Agent的Decision module
16. StreamChat (2412.08646) — Online / Query後も新着frameを利用 / Agentなし
17. MMDuet — Online / arbitrary-frame text interaction / Agentなし
18. VideoLLaMB — Partial（streaming captioningはOnline） / Agentなし
19. VideoLLM-MoD — Online streaming tasks / Query timingは中心設計でない / Agentなし
20. VideoLLM-online — Online / online dialogue・proactive / assistant型
21. VideoStreaming — Online sequential encoding / post-hoc Query / Agentなし

## 現在の解釈

今回の研究に対して最もクリティカルなのは、単に `Onlineか` ではなく、次の3軸を分けて比較すること。

1. **Observation causality**: future frameを見ないか。
2. **Query timing**: Queryがt=0 / stream途中 / stream終了後のどこで与えられるか。
3. **Memory control**: QueryをMemory write / keep / summarize / deleteにいつから利用できるか。

StreamAgentはAgent利用という意味では非常に近い。一方で今回の候補設定は、Queryを最初から既知としてExternal Memoryのwrite / keep / deleteを最初のchunkからQuery-awareにし、Sequential Loader側でfuture accessを強制する点を比較軸として明示できる可能性がある。

## 未確認・注意

- 21件すべてについてcode-levelのreader / sampler / future-aware preprocessingまで監査したわけではない。今回の表はMTG用の一次スクリーニング。
- `Online` とした手法でも、benchmark別のoffline evaluation pathが併存する場合がある。
- 動画長は代表設定であり、同一benchmark・同一sampling rateでの公平な比較ではない。
- Agent判定は論文中の明示的構成を優先した保守的な分類。

## 2026-09-11 13:34 JST: 残り17モデルの論文図・読み方をMTG Notionへ同期

先に詳細化した StreamingVLM / StreamForest / StreamMem / StreamAgent を除く17件について、各論文の代表Figureを確認し、現在のMTG Notionページ末尾に **論文図 + 図の読み方 + 今回の研究に対する要点** を追記した。

- MTG Notion: https://app.notion.com/p/3d777f89f3cd80dab6c5f6efc924e337
- 対象: CogStream / ProAssist / Flash-VStream / LiveVLM / StreamFormer / LiveCC / ViSpeak / LION-FS / STREAMMIND / STREAMCHAT (2501.13468) / DisPider / StreamChat (2412.08646) / MMDuet / VideoLLaMB / VideoLLM-MoD / VideoLLM-online / VideoStreaming
- 図はarXiv論文HTMLに含まれるFigure画像をNotionへ取り込み、AI生成の再構成図には置き換えていない。

### 図から見える大分類

17件は、中心機構だけを見ると次の4群に整理しやすい。

1. **Memory圧縮・検索系**: CogStream / Flash-VStream / LiveVLM / STREAMCHAT / VideoLLaMB / VideoStreaming
2. **選択的計算・効率化系**: LION-FS / STREAMMIND / VideoLLM-MoD / DisPider
3. **Streaming interaction・発話タイミング系**: ProAssist / ViSpeak / StreamChat / MMDuet / VideoLLM-online / LiveCC
4. **Causal representation backbone系**: StreamFormer

### 今回の研究へ特に効く比較

- **LiveVLM / VideoStreaming**: stream中のmemory write時には実Queryを使わず、Query到着後のread / retrievalでQuery-awareになる。`q=t0` からwriteをQuery-awareにする今回の案との対照が明確。
- **CogStream**: Query-aware compressionを行うため今回の案に近いが、stream中に到着するcurrent questionを軸とする設計で、最初から固定Queryを保持する設定とは分けて監査する必要がある。
- **STREAMCHAT / VideoLLaMB**: short/long-term、tree/recurrent memoryなどExternal Memory設計の比較対象として重要。
- **STREAMMIND / LION-FS / DisPider**: Memory内容そのものより「いつ重い推論を起動するか」「perceptionとreactionをどう分離するか」のAgent/system設計として参考になる。
- **StreamChat / MMDuet / VideoLLM-online**: Query後もstreamが進む・任意timestampで対話する設定が中心で、今回の`future chunkへのaccess contract`とQuery timingを混同しない。

### 注意

- MMDuetなど、論文の中心貢献が新規network blockではなくinteraction formatにあるものは、専用のarchitecture box図ではなく論文の中心概念Figureを採用した。
- StreamChat (2412.08646) はArchitecture Figure 3も存在するが、NotionではまずStreamingの差が最も分かるFigure 2を採用し、Cross-Attention / V-FFN / Parallel 3D-RoPEのarchitecture説明を本文で補った。
- これは図ベースの方法理解であり、17件すべてのcode-level causality / sampler / preprocessing監査を完了したことを意味しない。
