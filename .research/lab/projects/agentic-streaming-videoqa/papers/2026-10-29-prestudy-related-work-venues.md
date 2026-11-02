---
date: 2026-10-29
project: agentic-streaming-videoqa
topic: prestudy-related-work-venues
tags: [related-work, midterm-slides, prestudy, question-aware, streaming-videoqa, venue-check]
---

# 関連研究２「質問に備える（予習）」：引用の会議と URL

## 位置づけ

- 中間発表スライド「関連研究２：質問に備える（予習）」の引用を、「トップ会議の版を優先し、なければ arXiv」の方針で確かめ直した。
- 「予習」＝実際の質問を知らないまま、来そうな質問の傾向を使って、何を見て何を残すかを決めること。
- 会議は、arXiv の abs ページのコメント欄・Journal-ref 欄と、会議の公式ページ（ACL Anthology、ICLR のポスターページ）で確かめたものだけを書いた。確かめられないものは「arXiv」とした。1本あたり検索1〜2回の範囲で調べたので、見落としはありうる。
- 仕組みの一言は、2026-10-26 のメモ（[question-aware の整理](2026-10-26-query-agnostic-question-aware-related-work.md)）と今回の検索結果の要旨から書いた。本文は今回読んでいない。

## 結論

- 今の7本のうち、トップ会議の本会議に採択と確かめられたのは **Video Streaming Thinking（ECCV 2026）だけ**。arXiv のコメント欄に「Accepted by ECCV 2026」とある。ECCV の公式ページ（ECVA）は検索で見つからなかったので、URL は arXiv の abs ページにした。
- 残りの6本（StreamMem、SAVEMem、Imprint、SVMemAgent、EGSD、TaskMem）は、arXiv のコメント欄・Journal-ref 欄に会議の記載がなく、検索でも会議の版は見つからなかった。
- 差し替え・追加でトップ会議の候補になるのは、参考メモにある **InfiniPot（EMNLP 2024）** と **Episodic Memory Reader（ACL 2019）**。どちらも動画ではない（テキスト、またはテキストと動画QA）が、考え方の源流として置ける。
- 3「過去に来た質問に合わせる」は、トップ会議の論文が見つからなかった。TaskMem（arXiv）のままにする。

## 推薦の表

| 分類 | 論文名 | 引用形式 | URL | 会議の確認の状況 | 一言の仕組み |
|---|---|---|---|---|---|
| 1 代わりの質問を入れる | InfiniPot: Infinite Context Processing on Memory-Constrained LLMs | [Kim+, EMNLP2024] | https://aclanthology.org/2024.emnlp-main.897/ | EMNLP 2024 本会議（ACL Anthology 2024.emnlp-main.897 を検索結果で確認） | 汎用の要約指示（Catalyst Prompt）を一時的に付け、その注意でどの KV を残すかを決める。テキストの LLM が対象 |
| 1 代わりの質問を入れる | StreamMem: Query-Agnostic KV Cache Memory for Streaming Video Understanding | [Yang+, arXiv2025] | https://arxiv.org/abs/2508.15717 | arXiv（v1 のみ。コメント欄は「15 pages, 3 figures」で会議の記載なし。過去メモの CVPR 2026 Workshop も今回の検索では見つからず） | 汎用の質問トークン（チャットの定型トークン）との注意で、残す KV を選び、決まった大きさに保つ |
| 1 代わりの質問を入れる | Imprint: Online Memory Compression for Long-Horizon Egocentric QA | [Das+, arXiv2026] | https://arxiv.org/abs/2607.00696 | arXiv（コメント欄・Journal-ref 欄なし） | 人手で作った meta-question をキャプションの指示に入れ、答えさせずに書き方を導く。本研究にいちばん近い |
| 2 学習で備える | Video Streaming Thinking: VideoLLMs Can Watch and Think Simultaneously | [Guan+, ECCV2026] | https://arxiv.org/abs/2603.12262 | ECCV 2026（arXiv v2 のコメント欄「Accepted by ECCV 2026」で確認。ECVA の公式ページは検索で見つからず） | 質問が来る前に流れてくるクリップについて考えを書き、最終回答の報酬（RL）でその書き方を学ぶ |
| 2 学習で備える | Episodic Memory Reader: Learning What to Remember for Question Answering from Streaming Data | [Han+, ACL2019] | https://aclanthology.org/P19-1434/ | ACL 2019 本会議（ACL Anthology P19-1434 を検索結果で確認） | 記憶が一杯になったらどれを置き換えるかを、後で来る質問の正答率を報酬にして RL で学ぶ。bAbI・TriviaQA・TVQA で評価 |
| 2 学習で備える | SVMemAgent: A Streaming Video Memory Agent for Query-Agnostic Online Frame Selection | [Ko+, arXiv2026] | https://arxiv.org/abs/2609.18540 | arXiv（コメント欄・Journal-ref 欄なし。過去メモの ECCV 2026 Workshop は本会議ではない。今回は再確認していない） | 多様な QA から作った報酬で、毎秒のフレームを捨てるか記憶の枠と入れ替えるかを学ぶ。質問は見ない |
| 3 過去に来た質問に合わせる | Task-Focused Memorization for Multimodal Agents（TaskMem） | [Zou+, arXiv2026] | https://arxiv.org/abs/2605.31075 | arXiv（コメント欄・Journal-ref 欄なし） | 配備後、直近に来たタスク（質問）から報酬を作り、記憶ポリシーが書く内容をそちらへ寄せる |
| 3 過去に来た質問に合わせる（任意の2本目） | FOLIO: Focused Semantic Memory for Streaming Video Understanding | [Fan+, arXiv2026] | https://arxiv.org/abs/2607.13298 | arXiv（コメント欄「28 pages, 5 figures」で会議の記載なし） | 映像の変化と過去のターンの質問から focus score を作り、記録の細かさを変える |

## 外した・予備にした論文

| 論文 | 会議の確認の状況 | 扱い |
|---|---|---|
| SAVEMem [Wu+, arXiv2026] https://arxiv.org/abs/2605.07897 | arXiv（コメント欄・Journal-ref 欄なし） | 1 の予備。汎用の擬似質問5個のバンクで長期記憶に残すものを決める。1 は StreamMem と Imprint で足りるので外した |
| EGSD [Miao+, arXiv2026] https://arxiv.org/abs/2609.36803 | arXiv（v1〜v3、コメント欄・Journal-ref 欄なし） | 2 の予備。質問と正解を見られる教師が採点する自己蒸留。2 はトップ会議の2本と SVMemAgent で足りるので外した |
| CapRL [Xing+, ICLR2026] https://iclr.cc/virtual/2026/poster/10010207 | ICLR 2026 ポスター（ICLR のポスターページを検索結果で確認） | 2 の予備。キャプションだけで多肢選択に答えられた率を報酬にして、何を書くかを学ぶ。ただし画像のキャプションで、Streaming 動画ではない |
| MemLife [Xiong+] https://arxiv.org/abs/2609.40195 | arXiv（記載なし） | 2 の候補だが、トップ会議の版がないので外した |
| MemEvo [Liu+] https://arxiv.org/abs/2609.36581 | arXiv（記載なし） | 記憶の規則そのものを探索する。分類 2 の変形なので外した |
| H²-EMV [Bärmann+] https://arxiv.org/abs/2604.11306 | arXiv（記載なし） | 3 に近いがロボットの記憶。外した |

## スライドでの書き方の案

- 1：InfiniPot [Kim+, EMNLP2024]、StreamMem [Yang+, arXiv2025]、Imprint [Das+, arXiv2026]
- 2：Video Streaming Thinking [Guan+, ECCV2026]、Episodic Memory Reader [Han+, ACL2019]、SVMemAgent [Ko+, arXiv2026]
- 3：TaskMem [Zou+, arXiv2026]（必要なら FOLIO [Fan+, arXiv2026]）

## 残る確認

- Video Streaming Thinking の ECCV 2026 公式ページ（ECVA）。公開されたら URL を差し替える。
- StreamMem の CVPR 2026 Workshop、SVMemAgent の ECCV 2026 Workshop は、今回の検索では確かめられなかった（どちらにしても本会議ではない）。
- InfiniPot の Catalyst Prompt の説明は 2026-10-26 のメモによる。本文は今回読んでいない。

## 関連

- [question-aware の整理](2026-10-26-query-agnostic-question-aware-related-work.md)
- [関連研究①「何を残すか」の選び直し](2026-10-29-online-memory-forms-related-work.md)
