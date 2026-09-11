---
project: agentic-streaming-videoqa
status: active
summary: Queryをt=0から既知とするchunk-level streamingを前提に、Agent/Memoryの差分調査と最小text Memoryプロトタイプを進める。
created: 2026-09-10
last_updated: 2026-09-11
---

# エージェント型オンラインストリーミングVideoQAの研究

## 概要

YouTubeなどのライブ配信を想定し、動画を先頭から逐次的に読み込みながらVideo Question Answeringを行う仕組みを構築する。問題文を事前に与え、VLMが各時点の映像を認識した結果をメモリとして蓄積する。別のLLMによる要約や「次に何に注目すべきか」の予測を利用し、過去の情報を引き継いで回答するエージェント型の処理を検討する。

本研究でいう「オンライン」は、モデルの勾配更新を行うオンライン学習ではなく、オンライン動画ストリームを逐次処理することを指す。

## 現在の状況

2026-08-28のMTGで、逐次読み込み・VLM出力の保存・LLMによる要約・注目対象の助言から成る最小構成を優先する方針を整理した。高速化は後続課題とする。

2026-09-04のMTGで、研究コードから分離した逐次動画ローダーを整備する方針を確認した。取得順出力とバッファによるタイムスタンプ順出力を扱い、先行研究では未来情報を遮断した実際の逐次入力の有無と実装方法を調査する。

2026-09-11のMTGで、Queryを動画開始時から既知とし、future chunkへアクセスしないchunk-level causal設定から始めてよいことを確認した。Awesome Streaming Video Understandingの調査を踏まえ、次はStreamAgentを含むAgent系手法をより広く調べ、既存手法ができていること・できていないこと、Memoryの表現（text / KV / feature等）を整理する。並行して、1 frameずつVLMへ入力し、previous text memoryをcurrent frameと合わせて更新する最小Pythonプロトタイプを作る。動的chunk長、multi-timescale memory、重要イベント用Memory、長めのanticipationは現時点では未検証の研究候補として扱う。

## マイルストーン

- [ ] 研究方針を整理する
- [ ] 動画ストリームを逐次読み込む最小実装を作成する
- [ ] VideoQAデータセット候補を調査する
- [x] 逐次動画ローダーの取得順出力・バッファ付きタイムスタンプ順出力を実装する
- [ ] 逐次動画ローダーの利用サンプルと説明を整備する
- [x] 先行研究の逐次入力方法を調査する
- [ ] Agent系Streaming Video Understanding / VideoQAの既存機能と未解決点を整理する
- [ ] Agent / Streaming VideoQAにおけるMemory表現をtext / KV / feature等に分類する
- [ ] 1 frameずつVLMへ入力してtext Memoryを逐次更新する最小Pythonプロトタイプを作成する
- [ ] 動的chunk長・multi-timescale memory・重要イベント用Memory等の研究候補を既存研究と比較する

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-08-28 | MTGでエージェント型ストリーミングVideoQAの構成と初期実装順序を整理。 |
| 2026-09-04 | MTGで逐次動画ローダーの分離・機能方針と文献調査の基準を整理。 |
| 2026-09-10 | プロジェクト作成。オンラインストリーミングVideoQAの対象と境界を記録。 |
| 2026-09-11 | MTGでchunk-level causal設定を確認し、Agent/Memory差分調査と最小text Memoryプロトタイプを次段階に設定。 |
