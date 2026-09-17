---
date: 2026-09-18
project: agentic-streaming-videoqa
source_todo: null
topic: ego4d-staged-download-strategy
status: exploratory
tags: [brainstorm, research, ego4d, dataset, streaming-videoqa]
---

# Ego4D段階的ダウンロード方針の壁打ち

## 出発点と問い

ユーザーの質問：「ベンチマーク用Clipとannotationsを全部取得すれば万事解決か。それともCanonical Videoが重要か」。容量を抑えながら、将来のStreaming VideoQA研究に必要な動画・正解データを確保したい。Notionの更新はしない会話である。

## 研究文脈（確認済み）

- プロジェクトREADME（2026-09-16更新）：Queryをt=0から既知、動画を時間順に処理しfuture chunkにアクセスしないchunk-level causal設定。現状EgoCrossの最小text-state Agentの短時間実データ検証までで、Ego4D評価やダウンロード成功の記録はない。
- 2026-09-11 MTG議事録：長期記憶の希釈を課題候補とし、multi-timescale memory等は未検証案。

## Evidence：Ego4D公式・CLIで確認したこと

1. [Start Here](https://ego4d-data.org/docs/start-here/)：Full scale動画約7 TB、benchmark clips約1 TB、annotations約2 GB（概算）。全量取得より、研究対象に合わせた部分集合を推奨。
2. [Videos](https://ego4d-data.org/docs/data/videos/)：canonical videoは収集動画断片を正規化・連結した連続動画。canonical clipsはcanonical videoからbenchmark用に切り出す。公式は両方の利用を推奨。clips, clips_540ssがあり、どちらも30 FPS。NLQ clipは平均約10分・最長20分、VQは平均6分・最長16分、MQは平均7.8分・最長8分。clip_とvideo_の時間・フレーム参照先は異なる。
3. [CLI](https://ego4d-data.org/docs/CLI/) および [現行CLIのconfig.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/config.py)：`--datasets annotations`、`clips`、`full_scale`、`video_540ss`、`--benchmarks`、`--video_uids`、`--video_uid_file`などがある。config.pyの`VERSION_DEFAULT`は`v2_1`。README・ウェブ文書の一部は古い版に言及するためバージョンを明示する。`--video_uids`は動画に適用し、annotationsを質問単位で絞るものではない。
4. [Annotation Schemas](https://ego4d-data.org/docs/data/annotations-schemas/)：`ego4d.json`にvideo_uid、duration_sec、scenarios、解像度、fps、split等。annotationのclip_uidとvideo_uid、video_/clip_時間を突き合わせる。`annotations`はCLI説明上「大半のbenchmarkの注釈」であり、EgoTracks等別配布データまで必ず網羅するとは言えない。

## Interpretation：取得方式と研究要件の対応

- **Clipのみで開始可能なケース**：benchmark規定のクリップ範囲内に質問・証拠が収まり、最初は数分〜20分の因果的逐次読み込み、タイムスタンプ整合、モデル/Memoryループの動作を評価する場合。既存ベンチマークのprotocolに近い検証に適する。
- **Canonical Videoが必要になるケース**：clip前後の文脈、clipをまたぐ長期記憶、20分を超える連続ストリーム、切り出し起点ではない動画全体のイベント履歴を研究対象とする場合。clipに含まれない時間区間はclipの全量を集めても自動的に復元できない。
- **どちらにも残る評価問題**：NLQは回答文章のGTではなく質問に対応する時間区間のGT。query t=0を想定する研究側設定、回答文GTの用意、未来アクセス禁止の実装条件は別途定める必要がある。
- 低解像度を重視するなら公式の`clips_540ss`（動画ページの記述）または`video_540ss`（canonical videoの低解像度版）を検討。ただし現行config.pyの標準DATASETS_VIDEOに`clips_540ss`が列挙されておらず、公式ページと実装に差がある。現行版で利用可能か`--list-datasets`/manifestを確認するまで確定扱いしない。bboxなど空間注釈は解像度に注意。

## 方針候補（未承認）

A. **段階取得・最有力の相談案**：`annotations`と`ego4d.json`を先に取得→関心benchmark（例EM/NLQ）のannotationから動画・clip UID、split、長さ、問いを確認→5〜10件程度を試験的に選定（件数は仮の目安）→必要なClipだけ取得→長期評価のために対応するCanonical Video数本を追加→実測容量・長さ・annotationの整合に基づき拡大。
B. **全Clip＋全annotations**：既存benchmark全体の開発には便利だがClipだけで約1 TB。全動画時間軸・clip外文脈が必要なら不足する可能性があり、初手としては容量削減の目的に反する。
C. **Canonical Video中心**：最長時間文脈が最初から研究の主評価軸なら合理的。ただし全量約7 TBは不要で、annotationから絞ったvideo UID単位で取得する。

## 棄却寄り・保留

- 全`full_scale`を最初から取得する案：容量とターゲット未確定のため当面非推奨。長時間評価の具体的対象が定まれば再検討。
- 全Clipを取得すれば全Ego4Dの全時刻・全annotationが再現できるとの前提：公式動画構造から支持されない。
- 特定のデータを採用決定したわけではない。現時点は探索。

## MTGで決めたい未解決事項

1. 最初の目的は短時間の動作検証か、20分超の長期記憶評価か。
2. GTはNLQのtemporal groundingで十分か、回答文を評価するVideoQAが必要か。
3. Clip時間をt=0としてよいか、canonical videoの先頭からの文脈が必要か。
4. 目標動画時間・総容量上限・解像度・サンプル数、train/val/test分割。
5. `clips_540ss`などの利用可否・S3アクセス・実ファイル容量は未確認。

## 次のアクション候補（TODO化していない）

- `annotations`とmetadataを取得し、対象benchmarkのUID・clip/video対応・durationとsplitを一覧にする。
- CLIの`--list-datasets`とmanifestで現行バージョンの配布物を確認する。
- 少数Clipとその親Canonical Videoについて、ファイルサイズ・時間軸・視覚品質・QA可能性を比較するpilotをMTGで相談する。

## 関連ファイル

- `.research/lab/projects/agentic-streaming-videoqa/README.md`
- `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`
