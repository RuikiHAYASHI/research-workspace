---
date: 2026-10-27
project: agentic-streaming-videoqa
tags: [related-work, pre-study, query-agnostic, implementation-candidates, public-code]
---

# 質問を知らずに質問を意識して記録する手法のうち、実装してみるべきもの

## 目的

[10/26 MTG](../meetings/2026-10-26-mtg.md) で、AIに作らせたコードではなく、論文の公開コードを元に組み直すことにした。そこで、[10/26 の整理](2026-10-26-query-agnostic-question-aware-related-work.md) に挙げた「Streaming で、質問を知らずに質問を意識して記録する手法」と、その周りの手法について、実際に動かせるかを調べた。

見たこと：公開コードがあるか（中身が空でないか）、重みが公開されているか、ベースのモデル、16GB 級の GPU（今のサーバーは RTX A4000 16GB ×3）で推論できるか、記録がテキストか、LongVideoBench（LVB）の結果、今の「記録 → 集約 → 回答」に組み込めるか。

## 確認の度合い

- 2026-10-27、AI（サブエージェント4つ）が arXiv の本文、GitHub のファイル一覧と README、Hugging Face を見て調べた。林はまだ原文もコードも見ていない。
- 「16GB で動くか」「組み込みやすさ」は AI の見積もりで、動かしてはいない。
- GitHub API の回数制限に当たり、一部のリポジトリは README しか見ていない。

## 結論

1. **最初に動かすのは VST（Video Streaming Thinking）**。この話題（質問の傾向を学習でつかみ、テキストで書き起こす）の手法のうち、コードと重みがそろっているのは VST だけ。VST-3B なら 16GB で推論できそう。教授と話した「学習ベースで質問の傾向をつかみテキストで書き起こす研究を実装してみる」にそのまま当たる。EGSD（コードなし）は VST の上に作られているので、VST を動かしておけば EGSD との比較にもつながる。
2. **次に CapRL-Video-4B**。ストリーミングの手法ではないが、「テキストだけで答えるモデルが、キャプションから多肢選択に答えられたか」を報酬にしてキャプションを学習している。今の回答 Agent はテキストだけで答えるので、目的がそのまま重なる。ベースが今と同じ Qwen3-VL-4B なので、記録 Agent のモデルを差し替えるだけで比べられる。
3. **質問を意識しない比較相手として OneStreamer-4B**（同じ Qwen3-VL-4B、テキストの記録、重みあり）。
4. ほかは、コードがない、重すぎる、記録がテキストでない、のどれかに当たるので、関連研究として引用するか、考え方だけ取り入れる。

## 候補の一覧

### 質問を意識して記録する手法

| 手法 | コード | 重み | ベース | 記録 | 質問の傾向の入れ方 | LVB | 16GB で推論 | 判断 |
|---|---|---|---|---|---|---|---|---|
| **VST** [Guan+, ECCV 2026, arXiv 2603.12262] | ○ [1ranGuan/VST](https://github.com/1ranGuan/VST)（SFT・RL・データ生成・評価、Apache-2.0） | ○ VST-3B / 7B / 32B | Qwen2.5-VL | テキスト（質問前の思考） | 最終回答の報酬（RL） | 58.0（7B）、54.1（3B）。ただし下の注意 | 3B は可（見積もり） | **最初に動かす** |
| **CapRL / CapRL++** [Xing+, ICLR 2026, arXiv 2509.22647 / 2606.09393] | ○ [InternLM/CapRL](https://github.com/InternLM/CapRL)（学習・QA データ作り・評価） | ○ **CapRL-Video-4B**（Qwen3-VL-4B から） | Qwen3-VL-4B | テキスト（時刻付きキャプション） | テキストだけの LLM が多肢選択に答えられた率を報酬にする | なし | 可（見積もり） | **2番目** |
| PReM [Zhong+, arXiv 2609.23601] | ○ [siruzhong/PReM](https://github.com/siruzhong/PReM)（LVB の読み込みあり、MIT） | × 自分で学習が要る | Qwen2.5-VL-3B ほか | 潜在ベクトル | 答えの損失で書き込み器を学習 | streaming で 3B 54.75 → 56.54 | 推論は可、学習は 8×A100 | 余力があれば |
| DeltaStreamer [Sun+, arXiv 2610.19849] | ○ [BBBBchan/DeltaStreamer](https://github.com/BBBBchan/DeltaStreamer)（CC BY-NC） | 不要（学習なし） | Qwen3.6-27B ＋ SAM2.1 ＋ Whisper | テキスト（階層） | 観察のプロンプトに「将来の質問が頼る事実」を書く | なし | × 27B、1fps で毎フレーム呼ぶ | プロンプトだけ借りる |
| SAVEMem [Wu+, arXiv 2605.07897] | ○ [wuhang03/savemem](https://github.com/wuhang03/savemem) | 不要 | Qwen2.5-VL-3B / 7B | 視覚トークン | 汎用の擬似質問5個 | なし | 3B は可 | 低い（下の注意） |
| TaskMem [Zou+, arXiv 2605.31075] | △ 推論と前半の学習のみ。質問を意識する後半（DPO）のコードなし | △ 前半のみ | Qwen3-VL-30B-A3B | テキスト | 最近来た質問で DPO | なし | × 約60GB、Gemini・GPT の API も要る | 動かさない |
| Imprint [Das & Roy, arXiv 2607.00696] | × | — | EgoGPT-7B | テキスト | meta-question をプロンプトに入れる | なし | — | 今の実装とほぼ同じ。プロンプトだけ再現できる |
| EGSD [Miao+, arXiv 2609.36803] | × | — | Qwen2.5-VL-7B / Qwen3-VL-8B | テキスト | 回答の報酬＋教師＋実体の網羅 | 60.9 / 61.1 | — | 関連研究（VST の発展） |
| MemLife [Xiong+, arXiv 2609.40195] | × | — | Qwen3.5-9B | テキスト（30秒ごと） | QA は報酬を作るときだけ使う | なし | — | 関連研究（設定が一番近い） |
| SVMemAgent / MemEvo / StreamMem / FOLIO | × | — | — | フレーム / フレーム＋テキスト / KV / テキスト | — | SVMemAgent のみあり | — | 関連研究 |
| Episodic Memory Reader [Han+, ACL 2019] | △ 古い（Python 3.6、ライセンスなし） | × | — | 符号化した記憶 | 後の質問の正答率で RL | — | — | 設定の源流として引用 |

### 質問を意識しないが、比較相手になるもの（公開コードあり）

| 手法 | コード・重み | ベース | 記録 | 備考 |
|---|---|---|---|---|
| **OneStreamer** [Zeng+, arXiv 2610.01762] | ○ [MCG-NJU/OneStreamer](https://github.com/MCG-NJU/OneStreamer)（推論・評価のみ）、OneStreamer-4B | Qwen3-VL-4B | 時刻付きテキスト（局所のキャプションとイベントの要約） | 回答時 約10GB。LVB なし |
| EventMemAgent [Wen+, ECCV 2026, arXiv 2602.15329] | ○ [lingcco/EventMemAgent](https://github.com/lingcco/EventMemAgent)、8B の重みあり | 記録は Qwen3-VL-4B（固定）、方策は Qwen3-VL-8B | イベントのキャプション＋変化のログ | 記録の部分は今の記録 Agent とほぼ同じ形 |
| Deep Video Discovery [Zhang+, NeurIPS 2025, arXiv 2505.18079] | ○ [microsoft/DeepVideoDiscovery](https://github.com/microsoft/DeepVideoDiscovery) | GPT-4.1 / o3（API） | クリップのキャプション＋人物の台帳 | LVB val 71.6。回答時に生のフレームも見る |
| EgoLife / EgoRAG [Yang+, CVPR 2025] | ○ [EvolvingLMMs-Lab/EgoLife](https://github.com/EvolvingLMMs-Lab/EgoLife) | EgoGPT-7B、回答は API | 30秒ごとのキャプション＋要約 | Imprint の土台。今の記録を JSON で入れて検索・回答に使える |

## 注意点

- **VST の LVB 58.0 は、質問を後から与える条件の結果ではない**。公式の LVB の評価スクリプトは `stream_think_times=1` で、思考の回数が0になり、動画全体（最大384枚）を質問と一緒に入れている。論文自身も LVB を「オフラインのベンチマーク」と呼んでいる。
- VST は Streaming の設定でも、答えるときに最後の区間の動画を見る。区間の数や画像の縮小は動画全体の長さから決めている（少しだけ未来を見ている）。
- VST のベースは Qwen2.5-VL で、今の記録 Agent（Qwen3-VL-4B）とは違う。比べるときはこの差が混ざる。
- MemLife の論文では、VST を記録の書き手にすると EgoLifeQA で 33.6%（検索の再現率 3.4%）と低かった。
- CapRL の学習に使う多肢選択は、そのクリップの中だけで答えられる質問。LVB には区間をまたぐ質問がある。キャプションは1クリップ約2,000トークンまで許すので、長い動画では記録が多くなりすぎる。データは CC BY-NC。
- SAVEMem の擬似質問は、文の埋め込みではなく単語ごとの埋め込みとの類似度に使われていて（コードで確認）、動画全体を一度に入れる「疑似 Streaming」である（論文が認めている）。
- ここに挙げた手法は、どれも「質問の傾向を入れない」条件との正答率の比較を、そのままの形では出していない。近いのは TaskMem（プロンプトに例の質問を入れる vs 学習）、VST（学習前の Qwen を同じ枠で動かす vs 学習後）、StreamMem（本当の質問 68.1 / 汎用の文 66.7 / 定型トークン 66.9、MLVU）。
- 学習（RL）をやり直すのは、どの手法も 8〜32枚の 80GB GPU を使っているので、今の環境では難しい。動かすのは公開された重みでの推論にする。

## 動かし方の案（AIの考え。林の判断待ち）

### 1. VST-3B を、質問を後から与える条件で動かす

- 今の LVB の4つの動画長グループ（208問）で、区間ごとに VST-3B の思考（質問なし）を書かせ、それを記録として保存する。
- 回答は、最後の区間の動画を渡さず、思考のテキストだけで答える。VST 自身に答えさせる場合と、今の回答 Agent に答えさせる場合の両方を見る。
- 比べるもの：
  - 学習前の Qwen2.5-VL-3B を、同じ VST の枠（同じプロンプト）で動かしたもの（質問の傾向を学習していない対照。論文の比較と同じ形）
  - 今の記録 v6g / v6g-lvb（Qwen3-VL-4B）
  - 参考に、公式の設定（動画全体＋質問）
- ここで見たいこと：学習で質問の傾向を入れた書き手は、どんな記録を書くのか。今の記録と比べて何が増えて何が抜けるのか。LVB の質問に答えられない記録はどんなものか。

### 2. CapRL-Video-4B を記録 Agent に差し替える

- 同じ区間（20秒・8枚）で、記録 Agent のモデルだけを Qwen3-VL-4B から CapRL-Video-4B に替え、集約と回答はそのままにする。ベースが同じなので、差は学習の効果だけになる。
- 記録の長さが増えたときに、集約と回答がどうなるかも見る。

### 3. 余力があれば

- OneStreamer-4B の記録を、今の回答 Agent に渡して比べる（質問を意識しない、学習済みのテキスト記録）。
- DeltaStreamer の観察プロンプト（7項目の報告と「将来の質問が頼る事実」の文言）を、今の記録 Agent のプロンプトの比較対象にする。
- PReM（LVB の読み込みあり）は、3B の学習が 16GB で回るかを先に確かめる必要がある。

### 動かす前に確認すること

- GPU は割り当ての中から、番号と時間の目安を決めてから使う。
- VST の推論コードは lmms-eval 用なので、区間ごとに思考を保存して止める部分は自分で書く必要がある。

## 関連

- [10/26 の全体の整理](2026-10-26-query-agnostic-question-aware-related-work.md)、[分岐1：学習で質問の傾向をつかむ](2026-10-26-learned-question-distribution-related-work.md)、[分岐2：クリップごとの QA と検索](2026-10-26-clip-qa-generation-retrieval-related-work.md)
- [10/26 MTG 議事録](../meetings/2026-10-26-mtg.md)
