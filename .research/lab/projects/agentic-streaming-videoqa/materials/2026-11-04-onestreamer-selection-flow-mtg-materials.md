# OneStreamer を動かすことにした経緯（MTG 議事録用の下書き）

- 作成: 2026-11-04（林の説明の流れを、AI が調査メモの数字で補ってまとめた）
- 用途: 2026-11-06（金）の MTG の議事録に書く。11/04 の MTG は林の体調不良でなくなり、金曜に移った
- 根拠: [Streaming モデルの精度比較（2026-11-02）](../papers/2026-11-02-streaming-model-benchmark-comparison.md)、[再現の実行ログ](../experiments/2026-11-03-onestreamer-reproduction.md)

---

## 目的

- **メイン**: Streaming モデルの界隈で、強そうなモデルを探す
- **サブ**: Streaming のデータセット（ベンチマーク）は、どれが中心に使われているかを知る

## 調査で分かったこと

### ベンチマークは種類が多い

- ベンチマークやデータセットを作ること自体が目的の論文が多い。サーベイ（Yang et al. 2026）の Table 3 だけでも、Streaming 向けのベンチマーク・データセットが 26 件ある
- ただし、モデルの論文が実際に精度を比べるのに使うベンチマークは、一部に偏っている

### よく使われるのは OVO-Bench と StreamingBench

調べた Streaming モデルの論文 116 本のうち、各ベンチマークで精度を報告している本数:

| ベンチマーク | 報告している論文 |
|---|---:|
| StreamingBench（どれかの区分） | 71 本（Real-Time は 68 本） |
| OVO-Bench（どれかの区分） | 67 本 |
| 両方 | 60 本 |
| （参考）次に多い Streaming 用のもの: RVS-Ego / RVS-Movie | 14 本 / 13 本 |
| （参考）OVBench / ODV-Bench / ProactiveVideoQA | 7 本 / 5 本 / 4 本 |

→ Streaming の比較では、**OVO-Bench と StreamingBench の 2 つが事実上の共通の物差し**になっている

### その 2 つで強く、記録をテキストで残すのが OneStreamer

- OneStreamer-4B（Qwen3-VL-4B を元にした 4B モデル）の報告値は、StreamingBench Real-Time **86.9**（調べた中で最高）、OVO-Bench Overall **72.1**
- 同じ大きさの元のモデル Qwen3-VL-4B（StreamingBench Real-Time 81.8・OVO-Bench 58.8）から大きく上がっている
- 記憶の形は**テキスト**。映像を 1 秒ごとに見て、起きたことを文章の記録として残し、質問にはその記録と直近の 16 枚の画像で答える
- このプロジェクトはイベントをテキストで記録する方向なので、近い仕組みの強いモデルとして、まず動かしてみることにした

## そこでやっていること

- 論文の結果（Table 1）を、公式のコードと同じ設定で再現している（139 の GPU 4 枚）
- 今のところ: ODV-Bench は 71.36（論文 71.3）、OVO-Timing は平均 F1 42.9（論文 41.6）で、ほぼ論文どおり
- OVO-Bench・StreamingBench は、公式が評価に使う注釈ファイルが公開されていないので、元のベンチマークの公開注釈から作り直して回している（11/04 時点で StreamingBench を実行中）

## 聞かれそうなこと（メモ）

- **OVO-Bench だけで見ると、OneStreamer が一番ではない**。Watch-Think-Interact が Overall 73.6 を報告していて、これも記録にテキストを使う。OneStreamer を選んだのは、StreamingBench Real-Time が一番高いこと、論文で 8 つのベンチマークを評価していること、同じ大きさの元のモデルとの比較が載っていること、による
- 各論文の数字は自己申告で、評価の条件（フレーム数・Overall の定義など）がそろっていない
