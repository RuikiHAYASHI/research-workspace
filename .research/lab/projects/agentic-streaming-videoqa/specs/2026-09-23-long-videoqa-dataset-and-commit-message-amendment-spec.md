---
date: 2026-09-23
project: agentic-streaming-videoqa
status: draft
topic: long-videoqa-dataset-and-commit-message-amendment
amends: 2026-09-23-new-repository-videoqa-system-implementation-spec.md
source: 2026-09-23 user-directed dataset task mismatch and commit-message prose revision
last_updated: 2026-09-23
---

# 長尺VideoQAデータセットとコミット本文に関する改訂

## 位置付け

本書は`2026-09-23-new-repository-videoqa-system-implementation-spec.md`のうち、初期データセット、データセット接続部、環境依存、Step 03、コミット本文規約を改訂する。その他の目的、共通の仕組み、実行設定、Step branch、小工程ごとのcommit、実行記録、ローカル画面の方針は維持する。

## 改訂理由

50Saladsは行動区間のアノテーションを主目的にしており、動画を逐次処理して質問へ回答する長尺VideoQAの初期対象としてはタスクが異なる。そのため、50Saladsと`sequential_loader`を初期データセット・必須環境依存から外す。

また、実際の長尺VideoQA benchmarkには、一つの動画へ複数の質問を対応づけるものがある。システムは「一動画に一質問」を仮定せず、`video_id`と`question_id`の組を独立した実行単位として扱う。

## 初期データセットの候補

### 第一候補: LongVideoBench

LongVideoBenchは最大一時間の動画を含み、時間的に離れた場面を結びつける選択式質問を対象にする。区間分割と区間情報の集約を操作する今回のシステムに最も合う。

公式配布物には動画と字幕がある。初版は**映像のみを既定**とする。字幕を有効にする場合は、各時点までに対応する字幕だけを入力し、未来時点の字幕を絶対に渡さない。字幕を全体まとめて入力する実装は採用しない。

### 第二候補: MLVU

MLVUは3分から2時間の動画と複数の長尺動画理解課題を含む。長さ・映像種別・問いの種類を広く確認する後続候補として有用である。一方、初期実装で扱う問題形式を絞る必要があるため、最初の接続先としてはLongVideoBenchより後に置く。

### 実装診断用の候補

- Video-MMEは11秒から一時間の動画と、動画あたり複数の人手質問を持つ。`video_id × question_id`の取り扱いを確認するのに有用だが、短・中尺も多く、長尺処理だけの主評価にはしない。
- EgoSchemaは約3分の動画と選択式質問で、短いend-to-end確認には扱いやすい。ただし長い区間の集約を検証する主データセットには短い。
- LVBenchは平均約4,101秒の非常に長い動画を持つ。計算量と取得・decodeの負担が大きいため、初回の接続先には採用しない。

## データセット接続部の改訂契約

共通入力を`VideoQuestion`とし、少なくとも以下を持つ。

- `video_id`: 動画を識別する値。
- `question_id`: 質問を識別する値。
- 質問文、選択肢、正解（配布され利用可能な場合のみ）。
- 動画の参照情報、動画の長さ（得られる場合）、字幕の参照情報（得られる場合）。

データセット接続部は、質問単位の`VideoQuestion`を列挙し、指定した`video_id × question_id`について、動画の先頭から順に画像列を返す。同一動画の複数質問は、それぞれ別runとして実行し、質問・選択肢・指示文展開結果・最終回答・実行記録を共有しない。動画ファイルを読み直すことは許容する。複数質問を一つのrunに同居させる最適化は対象外とする。

実行設定には、dataset名、split、`video_id`、`question_id`、質問文、選択肢、字幕を使うか、区間設定を保存する。最終回答段階には質問と選択肢を渡してよいが、正誤の自動集計はこの基盤の成功条件に含めない。

## 環境構築とStep 03の改訂

親specのStep 01では、50Saladsおよび`sequential_loader`を導入しない。Pythonの基本環境、テスト、画像処理、実モデル用の任意依存だけを整える。

親specのStep 03を次の内容で置き換える。

**ブランチ:** `feat/step-03-dataset-and-model-connectors`

| 小工程 | コミット表題 | 完了条件 |
| --- | --- | --- |
| 03.1 | `feat: add dataset and model connector registry` | 接続部の登録、能力情報、擬似データセット・擬似モデルを追加する |
| 03.2 | `feat: add video-question dataset contract` | `VideoQuestion`、一動画複数質問、質問ごとの独立runを扱う共通契約を追加する |
| 03.3 | `feat: add selected long-videoqa dataset connector` | 承認されたLongVideoBenchまたはMLVUの質問単位接続部を追加し、動画を先頭順に返す |
| 03.4 | `feat: add fixed-duration chunking` | 先読みせず、時刻範囲と採用画像情報を持つ区間を作る |
| 03.5 | `feat: add Qwen3-VL model connector` | Qwen3-VLを共通要求で呼び、画像あり/なしの出力とモデル情報を返す |
| 03.6 | `test: cover video-question and chunk boundaries` | 同一動画の複数質問が別runになること、順序、future遮断、画像上限、接続部の選択を擬似実装で確認する |

Step末尾では実モデル・実データを使わず、擬似接続部によるtestとcompileだけを行う。承認した実データセットのdownload、ライセンス同意、動画rootの設定、実モデルでの短時間runは別途明示許可を必要とする。

## コミット本文規約の改訂

コミット本文は、項目名を並べた箇条書きにしない。変更内容を一つの自然な日本語段落として書く。

各小工程の本文には、対象、変更、理由、検証、影響、次の作業を含める。ただし次のような文章として記述する。

```text
<対象>に対して<変更>を行った。<理由>のためである。<検証>を実行して<結果>を確認し、<影響>がないことを確認した。次は<次の小工程>を進める。
```

検証していない項目がある場合は、「<未検証項目>は本コミットの対象外であり、実行していない」と文章中に明記する。コミット表題、Step branch、小工程ごとの一commit、Step末尾test成功後にのみ次branchを作る規約は親specのまま維持する。

## Blocking事項

実装開始前に、初期実データセットをLongVideoBenchとMLVUのどちらにするかをユーザーが決める必要がある。選択により、接続部の入力形式、動画・字幕の取得方法、ライセンス、実データsmokeの手順が変わるためである。

推奨はLongVideoBenchである。採用時は、映像のみを初期条件として接続部・擬似testを実装し、字幕利用を後続の設定追加として分ける。

## 実装引き継ぎ

- 承認済み仕様: 親specと本改訂（現時点では双方draft）。
- 実装目的: 新規リポジトリで、質問単位の長尺VideoQAを設定変更可能に逐次処理する。
- 初期データセット: LongVideoBenchを推奨。ユーザー選択待ち。
- 維持条件: 50Saladsと`sequential_loader`を必須依存・初期接続部にしない。既存repoは変更しない。
- 追加成功条件: 同一動画の複数質問が独立runとなり、未来の画像・字幕を前段処理へ渡さない。
- 長時間実行の許可状態: 未許可。実データdownloadと実Qwen/GPU実行は別途明示指示を必要とする。
