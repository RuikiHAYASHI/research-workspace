---
date: 2026-09-16
project: agentic-streaming-videoqa
source_todo: "2026-09-11 MTG由来のAgent/Memory/chunk/予測の文献調査"
topic: literature-review-depth-guidance
status: exploratory
tags: [brainstorm, literature-review, streaming-videoqa]
---

# 9/11 MTG由来の文献調査：今回必要な深さの整理

## 相談の出発点

ユーザーの問い：「MTGの結果から，今回はどの程度深く調べる必要がありそう？」

9/11 MTGの明示事項は、Agent系研究を幅広く確認し、各手法でできていること・できていないことを説明し、Memoryの実体（text / KV / feature等）を区別し、不明な用語を自分の言葉に直すこと。動的chunk、複数時間幅のMemory、予兆Memory、計算資源切替は探索候補であり実装決定ではない。並行して最小text-memory Python実装を進める。9/15 approved specはこの最小実装を扱い、上記探索候補をscope外とする。

9/16の一次調査では、4領域（Agent、Memory、動的時間粒度、予測と計算切替）それぞれに関連論文があることと提案概要を確認したが、数式・同一評価条件・コード・future-accessの実装監査はしていない。

## 解釈・今回の提案

MTGで具体的な精読本数・時間数・深さが明文化されたわけではない。以下は会議の目的と一次調査の到達点からの実務上の提案。

- Level 1（完了済み）：関連研究の存在、目的、仕組みを抄録や概要で幅広くスクリーニング。
- Level 2（今回の到達目標）：直接比較する主要論文について、設定（Query timing、未来情報/過去rawへのアクセス）、Memoryの表現・write/update/delete、Agentの入力・action、できること、未対応または未確認のことを論文本文・中心図で確かめて説明できるようにする。
- Level 3（原則後続）：すべての数式、詳細な学習条件、網羅的な実験値比較、全コード監査。Level 2の結論を左右する箇所（未来情報の利用、実際のwrite/keep/deleteなど）に限って今回も必要な部分だけ確認する。

## 調査対象の絞り方（未承認候補）

- 中心比較：StreamAgent（Agent actionとText/KV Memory）、QueryStreamとSelectStream（Query-awareな保持/削除/書込）。この3本はQuery timing、memory write時のQuery利用、具体的な操作で差分を監査する候補。
- Memory設計の補助比較：StreamForest、EventMemAgent、必要に応じLatentStream。短長時間幅やイベント保存がtext memoryの古い事実の希釈問題とどう異なるか確認する候補。
- 動的制御：VideoScaffold（イベント境界変更）、R3-Streaming（モデルrouting）は中心機構とStreaming条件のみをまず確認。全論文を同じ深さで読む必要はない。

## 完了基準の提案

直接比較する論文ごとに『対象タスク・Queryの時点／future可否／Memoryの実体と更新／Agent action／既存研究で実現済みのこと／本研究との差分候補／根拠と未確認事項』を自分の言葉で短く説明できること。本文未確認の機能は「ない」と断言せず「未確認」とする。論文名だけ、あるいは「AgentもMemoryも既にある」で止まらない。差分候補は新規性の確定とは区別する。

## 反例・制約・未決

同じ「Query-aware」でもQuery到着後のretrieveのみと、stream開始時からのwrite/deleteでは意味が異なる。可変イベント長と次入力chunk長の選択も違う。予測・Memoryの複雑化がQA精度を改善するとは未検証。重要な仕様差が概要に書かれていなければ本文やコードを局所的に確認する必要がある。

ユーザーが判断する論点：次回MTGで一番明確にしたい差分を「Query-awareなText Memory書込・削除」「古い情報の脱落」「動的chunk/計算制御」のいずれに置くか。現時点で研究方向は採択していない。

## 関連資料

- `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`
- `.research/lab/projects/agentic-streaming-videoqa/README.md`
- `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-15-streaming-text-memory-spec.md` (approved; scope is minimal prototype)
- `.research/secretary/notes/brainstorm/2026-09-16-streaming-videoqa-related-work-scout.md`

TODO自動追加・spec変更・研究コード変更なし。
