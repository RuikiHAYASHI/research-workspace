---
date: 2026-11-06
project: agentic-streaming-videoqa
topic: StreamingBench のまとめ — 全体の構成、OneStreamer が Real-Time だけを使う理由（推測）、再現の結果
tags: [streamingbench, onestreamer, benchmark, reproduction]
---

# StreamingBench のまとめ

- ベンチマーク: Lin et al., "StreamingBench: Assessing the Gap for MLLMs to Achieve Streaming Video Understanding"（arXiv:2411.03628、OneStreamer の文献 [12] では ICASSP 2026）
- 見たもの: HF の配布（`mjuicem/StreamingBench@48872fa`）の README と 6 つの CSV、GitHub の `questions_real.json`（`THUNLP-MT/StreamingBench@8929923`）、OneStreamer の論文（表1・表2・表9・表17・表18・付録 D）と公式コード、再現の予測（`merged-recon2-3-4-predictions.jsonl`）
- StreamingBench の論文本体はまだ読んでいない。区分の説明は HF の README と CSV から書いた
- 書いた人: AI（Claude）、林の依頼（2026-11-06「次は StreamingBench をまとめたい。Real-Time だけの理由も気になる」）
- 記号: [論文] OneStreamer の原文、[データ] 配布の注釈を見て数えたこと、[実験] 再現で機械が出した値、[AI] AI の考え（未検証）

## 1. StreamingBench は全体で何を測るか

[データ] 動画 900 本・質問 4,500 問。1 本の動画に、時刻の違う質問が 5 つずつ付く。質問の時刻までの映像を見て答える 4 択がほとんど。HF の README は、評価の観点を次の 3 つとしている。

| 区分 | 何を聞くか | タスク（問題数） | 問題の例（訳） | 答えの手がかりがある時点（`temporal_clue_type`） |
|---|---|---|---|---|
| **Real-Time Visual Understanding**（2,500 問・500 本） | 質問の時刻の映像の理解 | 物体・属性・動作・文字・空間・数え上げ・出来事・因果・次の展開・直前の要約の 10 タスク | 「緑の標識に書いてある通りの名前は？」 | **今 84%**（2,093）・過去 16%（407） |
| **Omni-Source Understanding**（1,000 問・200 本） | 映像と**音声**を合わせた理解 | Emotion Recognition（感情）・Scene Understanding（場面の描写）・Source Discrimination（誰が言ったか）・Multimodal Alignment（発言と場面の対応）各 250 | 「今『Oh my God』と言ったのは誰？」「男性が『Thank you』と言った場面はどれ？」 | 今 25%・過去 75% |
| **Contextual Understanding**（1,000 問・200 本） | 長い文脈の理解 | Misleading Context Recognition 250・Anomaly Context Understanding 250（今起きた異常は何か）・Sequential Question Answering 250（前の質問を受けた連続質問）・**Proactive Output** 250（条件が来たら自分から出力） | SQA:「前の質問の人は今、誰とやりとりしている？」/ PO:「太陽の真ん中に 20 が出たら『20』と出力して」 | MCR・ACU・SQA は**過去 100%**。PO は**未来 100%** |

- `temporal_clue_type` は配布の注釈の欄で、答えの手がかりが質問の時刻より前（Prior）、質問の時刻（Concurrent）、質問の時刻より後（Subsequent）のどれにあるかを表す。[AI] 名前から読んだ意味で、StreamingBench の論文での定義は未確認
- 全 18 タスクの点の公式な総合は「Overall」。全問の正答率と思われるが、計算のしかたは未確認

## 2. なぜ OneStreamer は Real-Time だけを使うのか

**[論文] OneStreamer の論文には理由が書かれていない。** 表1 の列名も「StreamingBench Real-Time」で、付録 D にも理由の説明はない。公式コードも Real-Time の 1 ジョブしか用意していない（`run_script/recipes.py` の `streamingbench` は `memory` の設定だけ）。以下は [AI] の推測と、その裏付けになる事実。

### 理由の候補

1. **分野の慣習で、比べる相手がそろうのが Real-Time だけ**
   - [データ] 林の比較表（[Streaming モデルの精度比較](2026-11-02-streaming-model-benchmark-comparison.md)、116 本）で StreamingBench の値を報告しているのは、Real-Time 68 本、Omni-Source 21 本、Contextual 20 本、Proactive Output 15 本、全体の Overall 19 本。Real-Time だけを報告しているのは 42 本
   - 表1 で比べている手法（VideoChat3・Mage-VL・JoyAI-VL-Interaction・AURA・MOSS-VL-Realtime・Qwen3-VL）の数値も Real-Time の列にある
2. **Omni-Source は音声が要り、Qwen3-VL-4B は音声を入力できない**
   - ただし、決定的な理由ではない。同じ表で、Qwen3-VL-8B ベースの AURA（62.0）・FOLIO（63.6）・SPARE（61.1）なども Omni-Source の値を出している（音声をどう入れたかは各論文で未確認）。また OneStreamer 自身も OmniMMI では音声の書き起こし（ASR）を入れて評価している（付録 D）
3. **Contextual は評価の手順が Real-Time と違う**
   - SQA は前の質問と答えを文脈に持たせる必要がある。Proactive Output は「いつ出力したか」を採点する。公式コードには、これらの手順がない
4. **[AI] 提案の強み（記憶）が試される区分を使っていない、とも読める**
   - Real-Time は 84% が「今の画面」に答えがある問題。記憶が効きそうな「過去」の問題が多いのは Contextual（100%）と Omni-Source（75%）のほう。未来の Proactive Output は、OneStreamer の能動的な応答の評価にも合いそうだが使っていない
   - 記憶を使わない基盤の Qwen3-VL-4B でも 81.8 が出ていて、記憶ありとなしの差も +0.6（表2）しかないのは、この問題の性質と合う
   - 単に手間や慣習の問題かもしれないし、点が良くなかったので載せなかったのかもしれない。どちらかは分からない。確かめるなら著者に聞くか、残りの区分を自分で回すしかない

### 説明するときの言い方（案）

> StreamingBench は Real-Time・Omni-Source・Contextual の 3 区分・18 タスクからなりますが、OneStreamer は Real-Time の 10 タスク 2,500 問だけを使っています。論文に理由は書かれていません。ただ、ストリーミングの論文の多くが Real-Time だけを報告していて、比べる相手がそろうのがここだからだと思います。注意点として、Real-Time は 8 割以上が「今の画面」に答えがある問題なので、OneStreamer の記憶の効果はあまり出ません。実際、記憶ありとなしの差は 0.6 点です。

## 3. OneStreamer での解かせ方

[論文] 付録 D と [実験] 公式コード（`local_runner.py`・`cache.py`）:

- 1 本の動画に付いた 5 問の時刻を区切りにして、**記憶づくりを動画ごとに 1 回だけ**流す（`load_or_create_shared_caption`）。各質問には、その時刻までにできた記憶を渡す。OVO-Bench は問題ごとに記憶を作り直すので、ここが違う
- 記憶づくりは 4fps・直近 128 枚（32 秒）を見て、1 秒ごとに `</Silence>`・`</Observe>`・`</Summary>` を出す（OVO-Bench と同じ設定）
- 回答は「記憶（最大 12,000 token）＋ 直近 16 枚（1fps、元の解像度）」で、選択肢の記号を 1 つ出す
- 指標は全問の正答率（マイクロ平均）。論文の表9 は「2,498 問の正答率」と書いているが、配布されているのは 2,500 問。どの 2 問を外したかは書かれていない

## 4. 結果

### 論文（表1・表9）

| 手法 | Size | ALL |
|---|---|---|
| OneStreamer | 4B | **86.9** |
| AURA | 8B | 83.2 |
| MOSS-VL-Realtime | 11B | 82.9 |
| JoyAI-VL-Interaction | 8B | 82.7 |
| Mage-VL | 4B | 82.1 |
| VideoChat3 | 4B | 81.9 |
| Qwen3-VL-4B（元のモデル） | 4B | 81.8 |

- [論文] 記憶の効果（表2・表18）: 記憶なし（直近 16 枚だけ）86.3 → 記憶あり 86.9（+0.6）。Observe だけでも 86.9、Summary だけだと 86.6
- [論文] 記憶を書く学習（60K）を抜いたモデルでは、記憶なし 85.8 → 記憶あり 86.1（表17）

### 再現とタスク別の比べ方

[実験] 再現は **86.28**（2,500 問、注釈は GitHub の `questions_real.json` から作り直したもの。11/04 完了）。

| タスク | 問題数（再現） | 論文（表9） | 再現 | 差 |
|---|---|---|---|---|
| Object Perception（OP） | 367 | 90.7 | 91.0 | +0.3 |
| Causal Reasoning（CR） | 128 | 80.5 | 79.7 | −0.8 |
| Clips Summarize（CS） | 317 | 95.9 | 96.2 | +0.3 |
| Attribute Perception（ATP） | 306 | 93.1 | 91.8 | −1.3 |
| Event Understanding（EU） | 161 | 84.4 | 83.9 | −0.5 |
| Text-Rich Understanding（TR） | 321 | 94.1 | 94.4 | +0.3 |
| Prospective Reasoning（PR） | 108 | 87.0 | 87.0 | 0.0 |
| Spatial Understanding（SU） | 246 | 80.1 | 79.7 | −0.4 |
| Action Perception（ACP） | 353 | 85.3 | 85.3 | 0.0 |
| **Counting（CT）** | 193 | 61.7 | **54.9** | **−6.8** |
| **ALL** | 2,500 | 86.9 | **86.28** | −0.6 |

- [実験] ずれが大きいのは Counting だけ。Counting の −6.8 点 × 193 問 ÷ 2,500 問 ≒ −0.5 点で、ALL のずれ −0.6 のほとんどを Counting が説明する
- [実験] Counting は質問の時刻が遅いほど下がる（60 秒未満 80.9 → 300〜600 秒 35.7、再現ログ 11/04）。[データ] Counting 188 問のうち 179 問は手がかりが「今」とされているが、問題は「これまでに合計何回」を聞くものが多い。[AI] 「今」の画面だけでなく、それまでの回数を覚えておく必要がある問題で、記憶の書き方（同じ一文が何十回も繰り返される）の影響を受けやすいのかもしれない（未検証）
- [実験] 全体を質問の時刻で分けると、60 秒未満 89.5・60〜180 秒 90.4・180〜300 秒 82.0・300〜600 秒 84.9・600 秒以上 83.5
- [データ・実験] 手がかりの時点で分けると、「今」2,066 問で 86.6、「過去」395 問で 85.1（HF の CSV と照合できた 2,461 問）。過去の問題でも、それほど落ちない

### 再現の注釈についての注意

- [データ] HF の CSV と GitHub の JSON は、ほぼ同じ問題の集合。2,500 問のうち 2,439 問は動画・質問・時刻（±1 秒）まで一致した。時刻が違うのは 22 問（再現で動画の長さに合わせて止めた sample_132・sample_332 を含む）。質問文が少し違って照合できなかったのは 39 問
- [データ] タスクの名前が違う。GitHub は Object Recognition・Attribute Recognition・Action Recognition、HF と論文の表9 は Object Perception・Attribute Perception・Action Perception。名前以外にも、5 問はタスクの割り当てが違う。タスク別の比較には小さな影響がある
- [AI] 論文の表9 の 2,498 問は、HF の CSV（タスク名が表9 と同じ）から 2 問を外したものかもしれない。HF の CSV には、GitHub の時刻の書き間違い（sample_132 の `00:12450`）がなく、`00:12:20` になっている
- 次にできること（提案、未実施）: HF の CSV から注釈を作り直して回すと、論文の表9 とタスクの名前・時刻がそろう。また、作り直した同じ注釈で記憶なし（recent16）も回すと、記憶の効果（論文は +0.6）を再現の中で比べられる
- 林の判断（2026-11-06）: StreamingBench の記憶なし（recent16）は今は回さない
