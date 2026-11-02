---
date: 2026-10-29
project: agentic-streaming-videoqa
topic: online-memory-forms-related-work
tags: [related-work, midterm-slides, memory, streaming-videoqa, venue-check]
---

# 関連研究①「何を残すか」：引用論文の選び直し

## 位置づけ

- 中間発表スライド「関連研究①：何を残すか」の引用を、林さんの方針「トップ会議の版を優先し、なければ arXiv」で選び直した。
- 分類はスライドの4つ：①テキストを残す ②モデル内部の表現を残す（KVキャッシュ・視覚トークン）③フレームを残す ④モデルの重みに書き込む。
- 調べた範囲（2026-10-29、時間をかけない方針で範囲を縮めた）：
  - スライドの今の引用7本
  - [サーベイのまとめ](2026-10-15-streaming-video-understanding-survey.md) の (b)(c)(d) に挙がっている手法
  - 調査の途中で原文を確かめた数本（M3-Agent、OASIS、Vista、FluxMem、MEMO）
- 会議名は、会議の公式ページ（ポスターページ、CVF、PMLR、AAAI OJS）か arXiv のコメント欄で確かめたものだけを書いた。確かめられないものは「arXiv」または「未確認」とした。
- 「オンライン」は、未来を見ずに時間順に処理し、記憶を作るときに質問を見ないこと、とした。

## 1. 推薦の表

| 分類 | 論文名 | 引用形式 | URL | 何を残すか | オンラインか | 上限 | 一言の仕組み | 確認の状況 |
|---|---|---|---|---|---|---|---|---|
| ①テキスト | Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory（M3-Agent） | [Long+, ICLR 2026] | https://arxiv.org/abs/2508.09736 | 出来事と知識の文（テキストのノード）を、顔・声のIDでつないだグラフ | はい。動画を区間ごとに時間順に処理する（学習データは30秒区間）。記憶づくりは質問と別に並行して動き、質問が来たら検索して答える | なし。ノードを足し続ける。同じ内容は重みを上げてまとめる | 区間ごとに文を書いてグラフに足し、質問時はエージェントが何度も検索する | 会議：ICLR 2026のポスターページで確認。仕組み：arXiv HTML 本文（前半）で確認 |
| ①テキスト | OASIS: On-Demand Hierarchical Event Memory for Streaming Video Reasoning | [Liang+, CVPR 2026] | https://arxiv.org/abs/2604.17052 | 出来事ごとのテキスト要約＋代表フレーム16枚（テキストとフレームの組） | はい。重ならない固定の窓で時間順に作る。記憶の整理は質問と無関係と明記。評価では質問時刻までの映像だけを使う | 一部あり。最上位の出来事が4個を超えると似た隣どうしをまとめる。全体のノード数の上限は書かれていない | 窓ごとにMLLMが要約を書き、出来事の木にまとめる。迷ったときだけ検索する | 会議：CVPR 2026のポスターページで確認。仕組み：arXiv HTML 本文で確認 |
| ①テキスト | Streaming VideoLLMs for Real-Time Procedural Video Understanding（ProVideLLM。arXiv版の題は "Memory-efficient Streaming VideoLLMs for …"） | [Chatterjee+, ICCV 2025] | https://arxiv.org/abs/2504.13915 | 古くなった視覚トークンを言葉（作業ステップの名前）に変えたテキスト＋直近の視覚トークン | 未来を見ないと明記（フレームごとに処理）。記憶の更新はフレームとモデル自身の出力だけで決まるが、質問を使わないとは明記されていない | あり。長期のテキスト5件、短期の視覚64フレーム。古い順に押し出す | 窓から押し出す視覚トークンを、デコーダがステップ名の文に変えて長期側へ移す | 会議：ICCV 2025（CVF Open Access と ICCV のポスターページを検索結果で確認。ページ本体は開いていない）。仕組み：arXiv HTML 本文で確認。料理など手順動画が対象 |
| ②内部表現（KV） | InfiniPot-V: Memory-Constrained KV Cache Compression for Streaming Video Understanding | [Kim+, NeurIPS 2025] | https://arxiv.org/abs/2506.15745 | KVキャッシュ | はい。質問を使わない（query-agnostic）と要旨に明記 | あり。利用者が決めた量に達すると圧縮する | 時間方向に冗長なトークンを消し、Valueの大きさで重要なトークンを残す | 会議：NeurIPS 2025のポスターページを検索結果で確認。仕組み：要旨のみ（本文は未読） |
| ②内部表現（視覚特徴） | Flash-VStream: Efficient Real-Time Understanding for Long Video Streams | [Zhang+, ICCV 2025] | https://arxiv.org/abs/2506.23825 | 視覚特徴。低解像度の特徴をまとめた60枠（各64トークン）＋代表フレームの高解像度特徴30枠（各256トークン） | はい。フレームが届くたびに更新。質問に依存しないと本文に明記 | あり。合計11,520トークン。ただし全フレームの高解像度特徴は別の保管場所（ディスクへ逃がせる）に溜まり続ける | 届いたフレームをk-meansで既存の枠にまとめ、大きいまとまりの代表フレームの詳しい特徴を別枠に残す | 会議：arXivのコメント欄「Accepted by ICCV 2025」で確認（CVFのページは未確認）。仕組み：arXiv HTML 本文で確認 |
| ③フレーム | Vista: Scene-Aware Optimization for Streaming Video Question Answering under Post-Hoc Queries | [Lu+, AAAI 2026] | https://arxiv.org/abs/2602.08448 | 場面ごとの全フレーム（原解像度、CPU側）＋場面ごとの小さなトークン（GPU側） | はい。質問の前に、見た目の似かたで場面に区切って圧縮する（「ストリーミング中は質問が分からない」と明記） | GPU側は質問ごとに上位k場面に抑える。CPU側のフレームの上限は書かれておらず、溜まり続ける | 質問が来たら場面トークンと照合し、上位k場面の原フレームを取り戻して答える | 会議：AAAI公式（OJS、40巻9号）を検索結果で確認。仕組み：arXiv HTML 本文で確認 |
| ③フレーム | SVMemAgent: A Streaming Video Memory Agent for Query-Agnostic Online Frame Selection | [Ko+, arXiv 2026] | https://arxiv.org/abs/2609.18540 | フレーム | はい。未来を見ず、質問なしで選ぶと要旨に明記 | あり（と読める）。毎時刻「記憶のどれかと入れ替える／捨てる」を決めるので枠の数は一定。具体的な枚数は要旨になく未確認 | 学習した方針（GRPO、多様なQAの報酬）が、残すフレームを入れ替える | 会議：arXivに記載なし。2026-10-14のメモでは ECCV 2026 Workshop（WearableAI）だが今回は未確認。トップ会議の本会議ではない |
| ④重み | video-SALMONN S: Memory-Enhanced Streaming Audio-Visual LLM | [Sun+, ICML 2026] | https://arxiv.org/abs/2510.11129 | モデルのパラメータ（推論しながら学習するテスト時学習、TTT） | 1 FPSで3時間超の動画を流して処理する（要旨）。質問を見ないかは今回は未確認 | 「同じメモリ予算」で比べると要旨にある。固定と明記された文は今回見ていない | 短期の表現を、推論中の勾配更新で重みに書き込み、長期の記憶にする | 会議：PMLR 306巻（第43回ICML、2026）と ICML 2026 のポスターページ（検索結果）で確認。仕組み：要旨のみ |
| ④重み | Memory as Weights: Internalizing Long-Term History for Streaming Videos（MaLoW） | [Liu+, arXiv 2026] | https://arxiv.org/abs/2610.22070 | 固定サイズのLoRA重み | ストリーミングで少しずつ更新し、過去の映像を見直さない。質問を使わないかは要旨に書かれていない | あり。LoRAの大きさは固定 | 再帰型のハイパーネットワークが、届いた映像を少しずつLoRA重みにまとめる | 会議：arXivに記載なし。トップ会議の版は見つからなかった |

### 分類ごとの結論

- ①テキスト：トップ会議の論文が3本見つかった。いちばん近いのは **M3-Agent**（区間ごとに文を書いて溜め、質問は記憶だけで答える）。**OASIS** はテキストとフレームの組なので、「テキスト中心＋根拠のフレームも残す」例として出す。**ProVideLLM** は上限のあるテキスト記憶の例（ただし手順動画で、書くのはステップ名）。
  - 本研究にもっと近い arXiv の論文（Calì+ 2610.31284、Imprint 2607.00696、OneStreamer 2610.01762）は、どれも arXiv に会議の記載がない。スライドに残すなら「arXiv」と付けて補足に回す。
- ②内部表現：KV は **InfiniPot-V**、視覚特徴は **Flash-VStream**。どちらもトップ会議で、質問を使わず、上限ありの Streaming 型。今の引用の StreamMem（KV、質問を使わない圧縮）と役割が同じなのは InfiniPot-V。
- ③フレーム：トップ会議の本会議で、**上限のある**フレーム記憶の論文は今回の範囲では見つからなかった。トップ会議では **Vista**（AAAI 2026、全フレームを残して後で引く型）を、上限ありの例は **SVMemAgent**（arXiv）を推薦する。
- ④重み：トップ会議は **video-SALMONN S**（ICML 2026）が見つかった。2本目は今の **MaLoW**（arXiv）のまま。

## 2. 候補として見たが外したもの

| 論文 | 会議（確認の状況） | 外した理由 |
|---|---|---|
| StreamingVLM [Xu+, ICLR 2026] https://arxiv.org/abs/2510.09608 | ICLR 2026（ポスターページを検索結果で確認） | 長く残るのはモデルが書いた実況テキストだが、KVの形で持つ。①と②の中間なので外した。①の4本目の予備にはなる |
| ReKV [Di+, ICLR 2025] https://arxiv.org/abs/2503.00540 | ICLR 2025（ICLR論文集のPDF・ポスターページを検索結果で確認） | 全フレームのKVをRAMやディスクに溜め、質問に関係するKVだけを取り出す。上限なしの「全部残して後で引く」型。②の対比としては使える |
| StreamMem（今の引用） https://arxiv.org/abs/2508.15717 | 2026-10-14のメモでは CVPR 2026 Workshop（ICLR 2026は不採択）。今回は再確認していない | 本会議の版がない。役割が同じ InfiniPot-V（NeurIPS 2025）に置き換え |
| SAVEMem（今の引用） https://arxiv.org/abs/2605.07897 | arXivに記載なし | トップ会議の版がない。Flash-VStream に置き換え |
| Calì+（今の引用） https://arxiv.org/abs/2610.31284 「Retrieval-Augmented Online Textual Memory for Episodic Memory VQA」 | arXivに記載なし（2026-10-22投稿） | 本研究に近いがトップ会議の版がない。補足に回す |
| OneStreamer（今の引用） https://arxiv.org/abs/2610.01762 | arXivに記載なし | 同上 |
| Imprint（今の引用） https://arxiv.org/abs/2607.00696 | arXivに記載なし | 同上 |
| FluxMem [Xie+, CVPR 2026] https://arxiv.org/abs/2603.02096 | arXivのコメント欄「Accepted at CVPR 2026」 | 視覚トークンの圧縮。上限や質問を使わないかが要旨に書かれていない。②の予備 |
| MEMO [Li+] https://arxiv.org/abs/2609.38900 | arXivのコメント欄「ACM MM 2026」 | 区間ごとに高解像度の映像を別に残す（③に近い）。上限・オンラインかが要旨に書かれていない。指定のトップ会議の一覧にない |
| EventMemAgent https://arxiv.org/abs/2602.15329 | arXivに記載なし。過去メモでは「ECCV 2026」とする記載と、著者GitHubだけという記載が食い違う。今回も未確認 | 会議を確かめられない |
| StreamForest、StreamChat、VideoChat-Online、StreamKV、WeaveTime など、サーベイ (b)(c)(d) のほかの手法 | StreamForest：NeurIPS 2025、StreamChat：ICLR 2025（2026-10-14のメモ、今回は再確認なし）。StreamKV：AAAI 2026（検索結果の一覧の記載のみ）。WeaveTime：CVPR 2026（CVF Open Access にPDFがあるが開けなかった）。VideoChat-Online：未確認 | どれも②（視覚特徴・KV）に入る。②は推薦2本で足りるため、今回は詳しく見ていない |
| StreamingAssistant、TaYS、VST、TWW、OVG-HQ-Unify、HERMES、StreamingTOM、CacheFlow、rLiVS、Venus、V-Rex、LiveVLM | 未確認（LiveVLMは2026-10-14のメモで arXiv、本文に DAC '26 の記載） | 時間をかけない方針のため、会議の確認をしていない |

## 3. 「フレームを残す手法はオンライン／Streamingと言えるか」への答え

結論：**フレームを残すかどうかと、オンラインかどうかは別の問題**。フレームを残す手法にもオンラインのものはある。分かれ目は「残す量に上限があるか」。

- 時間順に処理し、記憶を作るときに質問を見ない、という意味では、推薦した2本はどちらもオンライン。
  - Vista：質問の前に、見た目の似かたで場面に区切る。本文に「ストリーミング中は質問が分からない」とある。
  - SVMemAgent：未来を見ず、質問なしでフレームを選ぶと要旨にある。
- 違うのは上限の決め方。
  - **上限あり（Streaming型）**：SVMemAgent は、毎時刻「記憶のどれかと入れ替えるか、新しいフレームを捨てるか」を学習した方針が決めるので、枠の数は一定（具体的な枚数は未確認）。②の Flash-VStream も、代表フレームの高解像度特徴を30枠に固定している。OASIS は出来事ごとにフレームを16枚に抑え、最上位の出来事が4個を超えるとまとめる。
  - **上限なし（全部残して後で引く型）**：Vista は全フレームを CPU（またはディスク）に溜め続け、質問が来たら上位k場面だけ取り戻す。GPU に載せる量は抑えられるが、保存する量は動画の長さに比例して増える。②の ReKV も同じ型。
- スライドでの言い方の案：「フレームを残す手法にも、未来を見ずに質問なしで作るものがある。ただし、全部残して後で引くもの（Vista）と、決まった枚数だけを入れ替えて残すもの（SVMemAgent）がある」。
- 注意（私たちの推論）：テキストの M3-Agent も上限がない。上限の有無は、フレームに限らずどの分類にもある問題として扱う方が正確。

## 4. 確認できなかった点

- ProVideLLM、M3-Agent が「記憶を作るときに質問を使わない」と明記しているか。M3-Agent は記憶づくりと質問への対応が別の処理と書かれているが、「質問を使わない」という文は見ていない。ProVideLLM は明記なし。
- M3-Agent の本文の後半（arXiv HTML の 100,000 文字目以降）は読んでいない。
- InfiniPot-V、video-SALMONN S、MaLoW は要旨しか読んでいない。上限の具体的な値、質問を使うかは本文で未確認。
- SVMemAgent のフレームの枚数（上限の値）と、ECCV 2026 Workshop の採択。
- ProVideLLM、Flash-VStream、EgoLife などの CVF Open Access のページは、取得が 403 で拒否されたため、本文ページを直接開いていない（ProVideLLM は検索結果に CVF の URL があり、Flash-VStream は arXiv のコメント欄で確認）。
- StreamMem の CVPR 2026 Workshop、StreamForest・StreamChat の会議は、2026-10-14 のメモの記載のままで今回は再確認していない。
- サーベイ (b)(c)(d) のうち、表2で「未確認」とした手法の会議。

## 関連文書

- [Streaming Video Understanding サーベイのまとめ](2026-10-15-streaming-video-understanding-survey.md)
- [Memory分類 2回目](../../../../secretary/notes/brainstorm/2026-10-14-memory-classification-round2.md)
- [Memory分類 1回目](../../../../secretary/notes/brainstorm/2026-10-14-memory-classification-round1.md)
