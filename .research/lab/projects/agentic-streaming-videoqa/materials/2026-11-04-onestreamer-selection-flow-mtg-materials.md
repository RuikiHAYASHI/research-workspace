# OneStreamer を動かすことにした経緯（MTG 議事録用の下書き）

- 作成: 2026-11-04（林の説明の流れを、AI が調査メモの数字で補ってまとめた）。同日、本数・順位を比較表から数え直して直した
- 用途: 2026-11-06（金）の MTG の議事録に書く。11/04 の MTG は林の体調不良でなくなり、金曜に移った
- 根拠: [Streaming モデルの精度比較（2026-11-02）](../papers/2026-11-02-streaming-model-benchmark-comparison.md)、[再現の実行ログ](../experiments/2026-11-03-onestreamer-reproduction.md)

---

## 目的

- **メイン**: Streaming モデルの界隈で、強そうなモデルを探す
- **サブ**: Streaming のデータセット（ベンチマーク）は、どれが中心に使われているかを知る

## 調査で分かったこと

### ベンチマークは種類が多い

- 調べた 116 本は、すべてモデルを提案した論文（サーベイの Table 2 のモデル一覧などから選んだ）。ベンチマークだけを作って既存のモデルを比べた論文（OVO-Bench や StreamingBench の論文そのもの）は、選び方の時点で入れていない
- それでも、精度の表には 84 種類のベンチマークが出てくる。うち 52 種類は 1〜2 本しか使っていない
  - 23 種類は Streaming 用。多くは、モデルの論文が自分で作って一緒に出したベンチマークと思われる（例: Streamo と Streamo-Bench、StreamReady と ProReady-QA、LiveStar と OmniStar-RNG。名前から判断。原文での確認はまだ）
  - 29 種類はオフライン型の動画 QA（Video-MME などの仲間）で、論文ごとに選び方がばらばら
- ベンチマークを作り、その評価のためのモデルも一緒に出す論文もある（OVBench と VideoChat-Online、SVBench と StreamingChat、CogStream と CogReasoner など）

### よく使われるのは OVO-Bench と StreamingBench

調べた Streaming モデルの論文 116 本のうち、各ベンチマークで精度を報告している本数:

| ベンチマーク | 報告している論文 |
|---|---:|
| StreamingBench（どれかの区分） | 71 本（Real-Time は 68 本） |
| OVO-Bench（どれかの区分） | 67 本 |
| 両方 | 60 本 |
| （参考）次に多い Streaming 用のもの: RVS-Ego / RVS-Movie | 14 本 / 13 本 |
| （参考）OVBench / ODV-Bench / ProactiveVideoQA | 7 本 / 5 本 / 4 本 |

→ Streaming 用のベンチマークの中では、**OVO-Bench と StreamingBench の 2 つが事実上の共通の物差し**になっている。どちらかを報告しているのは 116 本中 78 本

- 但し書き
  - オフライン型の Video-MME も 51 本が報告していて、Streaming のモデルでもオフラインの性能を並べて示すことが多い
  - どちらも報告していない 38 本は、主に次の 3 種類: 2 つのベンチマークが出る前（2024 年ごろ）のモデル（VideoLLM-online・Flash-VStream など）、実況や対話など QA 以外のタスクのモデル、自前のベンチマークやオフライン型だけで評価したもの
  - OVO-Bench の Forward（先の出来事に答える問題）を報告しているのは 38 本だけ。Overall の定義も論文によって違う（Forward を入れない平均など）

### その 2 つで強く、記録をテキストで残すのが OneStreamer

- OneStreamer-4B（Qwen3-VL-4B を元にした 4B モデル）の、区分ごとの順位（116 本の報告値の中で）:

| 区分 | OneStreamer | 順位 | 上の手法 |
|---|---:|---:|---|
| StreamingBench Real-Time | 86.9 | **1 位** / 68 | — |
| StreamingBench のほかの区分（Omni-Source・Contextual・Proactive Output）・全体 | 報告なし | — | 論文が Real-Time だけを報告 |
| OVO-Bench Real-Time | 81.4 | 7 位 / 64 | WRWS 82.79 など 6 手法。差は 1.4 以内 |
| OVO-Bench Backward | 77.9 | **1 位** / 58 | — （HLD 99.5 が大きく効いている） |
| OVO-Bench Forward | 56.9 | 10 位 / 38 | Watch-Think-Interact 70.0 など 9 手法 |
| OVO-Bench Overall（公式の 3 区分平均にそろえた場合） | 72.07 | **2 位** / 38 | Watch-Think-Interact 73.43 |
| OVBench | 66.8 | 1 位 / 7 | — |
| ODV-Bench | 71.3 | 2 位 / 4 | VideoChat3 72.3 |

  （表に書かれた Overall の値のままだと 4 位 / 55 だが、上の SPARE 77.78・StreamScout-R 76.63 は Forward を入れない平均なので比べられない）
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
