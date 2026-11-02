---
date: 2026-10-26
project: agentic-streaming-videoqa
tags: [related-work, pre-study, query-agnostic, proxy-query, streaming-memory]
---

# 「質問を知らない条件で、質問を意識する」先行研究の整理（予習の位置づけ）

## 目的

「予習」は私たちが使っている言葉で、論文の用語ではない。そこで、**実際の質問を知らないまま記録・保持・処理をするが、来そうな質問を意識してそれを変える**手法がどれだけあり、どう呼ばれているかを調べた（2026-10-26、AIによる検索。サブエージェント3つ：動画・視覚の分野、動画以外の分野、引用をたどる調査）。

## 確認の度合い

- 下の論文はすべて、arXiv API で ID と題名、第一著者が一致することを確かめた（2026-10-26）。
- 中身の記述は、サブエージェントが本文またはアブストラクトを読んだ報告である。林はまだ原文を読んでいない。スライドに載せる前に原文で確かめる。
- 発表先は、書いていなければ arXiv プレプリントのみ（採択先は未確認）。

## 結論

1. **設定の名前は定着している**：query-agnostic（多数）。ほかに post-hoc queries（Vista）、delayed query（ProtoKV）、questions unknown during construction（Video-EMem）。
2. **「予習」に当たる手法のカテゴリには、定まった名前がない**。確認したサーベイ（Agentic Video Understanding、Why Is Video Still So Expensive?、Watch, Remember, Reason）は、どれもこのカテゴリを独立に命名していない。近い言及は次の2つだけ。
   - StreamMem の関連研究：query-dependent と query-agnostic の中間に「task instructions or task-specific proxy prompts」を使う方法がある（InfiniPot、Corallo+）。
   - 効率化のサーベイ（Steunou+）：query-free と query-aware に二分しているだけ。
3. **ただし、手法そのものは多い**。特に 2026 年に、ストリーミング動画の記憶で、質問の分布を使うものが急に増えている。「予習とイベント記録を組み合わせたものはほとんどない」とは言えない状況。
4. 考え方の源流は古い。検索の分野の query association（2002）と doc2query（2019）、ストリーミングQAの Episodic Memory Reader（ACL 2019）がある。

## 分類：質問の代わりに何を使うか

### A. 代わりの質問をそのまま入れる（学習なし）

| 論文 | 質問の代わり | それで変えるもの | 論文中の呼び方 |
|---|---|---|---|
| StreamMem [Yang+, arXiv 2508.15717] | チャットの定型トークン | KV を何で残すか | proxy queries |
| InfiniPot [Kim+, EMNLP 2024]（テキスト） | 汎用の要約指示を一時的に付ける | KV の重要度 | Catalyst Prompt |
| SAVEMem [Wu+, arXiv 2605.07897] | 汎用の擬似質問5個（物体・数・行動・変化・配置）を固定のバンクにする | 刈り込み・長期記憶に何を残すか | pseudo-question bank, query-agnostic semantic prior |
| Imprint [Das & Roy, arXiv 2607.00696] | EgoLifeQA から**人手で**作った64個の meta-question | キャプションの書き方 | meta-questions, Query-Aware Captioning |
| Beyond RAG [Corallo+, arXiv 2503.04973]（テキスト） | タスク説明と few-shot 例 | KV 圧縮 | task-aware KV cache compression |
| DeltaStreamer [Sun+, arXiv 2610.19849] | 観察プロンプトに「将来の質問が頼る事実」として、数・OCR・位置などを必須にする | 質問前の観察記録 | （明示の名前なし。予期と読んだのはAIの解釈） |

### B. 質問の分布を学習で写し取る（推論時は質問を見ない）

| 論文 | 学習の信号 | それで変えるもの | 論文中の呼び方 |
|---|---|---|---|
| Episodic Memory Reader [Han+, ACL 2019] | 後で来る質問への正答率（RL） | 記憶のどれを置き換えるか | learning what to remember |
| SVMemAgent [Ko+, arXiv 2609.18540] | 多様な QA から作った報酬（GRPO） | フレームを残すか捨てるか | query-agnostic prior, training query distribution, task-driven rewards |
| MemLife [Xiong+, arXiv 2609.40195] | 訓練 QA で報酬を作る（書き手は質問を見ない） | 一人称のテキスト記憶の内容 | question-independent writer |
| EGSD [Miao+, arXiv 2609.36803] | 質問と正解を見られる教師が採点する。質問への偏りを、イベントの網羅性で引き戻す | クリップごとの記憶文 | privileged information, invisible-question gap |
| Video Streaming Thinking [Guan+, arXiv 2603.12262] | 最終回答の報酬を、質問前の思考にも配る | 質問前に書くテキスト記憶 | query-ahead streaming think, pre-query reasoning |
| MemEvo [Liu+, arXiv 2609.36581] | NExT-GQA の正答確率を目的に、LLM が記憶プログラムを探索する | 記憶の規則そのもの | memory decisions made before future queries are known |
| CapRL [Xing+, arXiv 2509.22647] | キャプションだけで多肢選択に答えられた率（RL） | キャプションの内容 | utility |
| doc2query [Nogueira+, arXiv 1904.08375]（検索） | （クエリ、文書）の学習ペア | 索引に書き足す、来そうなクエリ | document expansion by query prediction |
| Mem-α [Wang+, arXiv 2509.25911]（LLMの記憶） | 後の QA 正答率（RL） | 記憶の書き方 | learning memory construction |
| QA rewards の要約 [Arumae & Liu, NAACL 2019] | QA 対を報酬にする | 質問を知らない要約 | question-answering rewards |

### C. 過去の質問からその場で合わせる

| 論文 | 使うもの | それで変えるもの | 論文中の呼び方 |
|---|---|---|---|
| TaskMem [Zou+, arXiv 2605.31075] | 直近の約10問を、来る質問の分布の代わりにする | 記憶ポリシーが書く内容（DPO） | task-focused memorization |
| H²-EMV [Bärmann+, arXiv 2604.11306] | 忘れたことを聞かれたときのフィードバックから、関連度のルールを学ぶ | 要約と忘却 | relevance rule learning |
| FOLIO [Fan+, arXiv 2607.13298] | 視覚の変化と過去ターンの質問から作る focus score | 記録の細かさ | dynamic focus state |
| SelectStream [Ge+, arXiv 2606.16353] | よく参照される記憶を優先する | まとめるときの優先度 | — |

### 対照：あえて予習しない立場

- **Video-EMem [Chen+, arXiv 2610.24537]**：記憶を書く側は QA を使わずに、原情報の網羅だけで改良する。QA は読む側にだけ使う。「質問に合わせた最適化は、見ていない質問の根拠を落とす」と述べる（過学習を示したわけではない、と本文で留保している）。**予習の正当性を議論するときの最大の比較相手。**
- 代わりの質問を置かない query-agnostic な手法：InfiniPot-V、ProtoKV、Vista、StreamScout、MERIT。
- StreamAgent は "anticipatory" を名乗るが、予測するのは質問が与えられた後の将来のイベント。未知の質問の予測ではない。

## 本研究への示唆（AIの考え。林・教授の判断待ち）

- 今の私たちの予習（LLM でタスクの傾向をまとめてプロンプトに入れる）は **A に当たり、Imprint にいちばん近い**。違いは、人手ではなく LLM で作る点だけ。
- 見つからなかったもの：
  - クリップごとに想定質問を生成して記録や索引にする（doc2query 型の動画版）
  - 予習で「どこを細かく見るか」（フレームレートやモデルの切り替え）を決めるもの。EgoTrigger [Paruchuri+, ISMAR 2025] は、記憶 QA の需要を動機に撮影のきっかけを選ぶ程度
- 予習の定義の案：「**実際の質問を知らない（query-agnostic）まま、来そうな質問の分布（タスクの事前知識）を使って、記録・保持・注視を制御すること**」。設定は query-agnostic、仕組みは proxy query / pseudo-question / meta-question の系譜として引用できる。

## 参照

- サブエージェントの作業ファイル（一時）：scratchpad/lit/（研究リポジトリの外）
- 関連：[Imprint の資料](../materials/2026-10-23-imprint-pre-study-prior-work-mtg-materials.md)、[サーベイのまとめ](2026-10-15-streaming-video-understanding-survey.md)
