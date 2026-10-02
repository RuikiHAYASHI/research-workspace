---
project: agentic-streaming-videoqa
status: active
summary: Workbenchのデータセット・動画・QA選択UIを試作。Agent実行は未確認で、入出力・Prompt・永続化・推論設定の整理を優先中。
created: 2026-09-10
last_updated: 2026-10-02
---

# エージェント型オンラインストリーミングVideoQAの研究

## 概要

YouTubeなどのライブ配信を想定し、動画を先頭から逐次的に読み込みながらVideo Question Answeringを行う仕組みを構築する。問題文を事前に与え、VLMが各時点の映像を認識した結果をメモリとして蓄積する。別のLLMによる要約や「次に何に注目すべきか」の予測を利用し、過去の情報を引き継いで回答するエージェント型の処理を検討する。

本研究でいう「オンライン」は、モデルの勾配更新を行うオンライン学習ではなく、オンライン動画ストリームを逐次処理することを指す。

## 現在の状況

2026-08-28のMTGで、逐次読み込み・VLM出力の保存・LLMによる要約・注目対象の助言から成る最小構成を優先する方針を整理した。高速化は後続課題とする。

2026-09-04のMTGで、研究コードから分離した逐次動画ローダーを整備する方針を確認した。取得順出力とバッファによるタイムスタンプ順出力を扱い、先行研究では未来情報を遮断した実際の逐次入力の有無と実装方法を調査する。

2026-09-11のMTGで、Queryを動画開始時から既知とし、future chunkへアクセスしないchunk-level causal設定から始めてよいことを確認した。Awesome Streaming Video Understandingの調査を踏まえ、次はStreamAgentを含むAgent系手法をより広く調べ、既存手法ができていること・できていないこと、Memoryの表現（text / KV / feature等）を整理する。並行して、1 frameずつVLMへ入力し、previous text memoryをcurrent frameと合わせて更新する最小Pythonプロトタイプを作る。動的chunk長、multi-timescale memory、重要イベント用Memory、長めのanticipationは現時点では未検証の研究候補として扱う。

2026-09-16に、`2026_09_hayashi_egocross_observation`の`feat/step-07-agent-reproducibility`で最小text-state Agentを実装した。各frameではQwen3-VLが現在画像一枚だけから観測文を作り、同じモデルのtext-only方策が前stateと観測文から`ADD`・`UPDATE`・`KEEP`・`FLAG_UNCERTAIN`・`CLOSE_EVENT`を選ぶ。決定的Reducerがbounded stateへ反映し、state前後と生出力をJSONLに保存する。ID 224の1 frameとID 1の5 frameを実Qwenで確認し、最終QA・正解率・全件実行は未実施である。

2026-09-18のMTGで、既存の実行済みtrace viewerを、操作時にAgent実行・プロンプト変更を試せる最小デモへ発展させる方針を確認した。並行して、長尺動画を逐次ロードし、区間ごとのQwen出力を保存・集約して最終回答へつなぐ2--3段階の最小Streaming VideoQAを試作する。初期構成はPythonの同期的な逐次処理を優先し、サーバ連携やノード接続UIは後続候補とする。

2026-09-25に、`sequential_loader` 公開APIでLongVideoBenchを先頭からEOFまで前方向decodeし、YAML recipeの可変区間・画像上限、英語prompt、3段階Agent、artifact、ローカル画面を接続するリファクタリングを完了した。Workbench統合ブランチは `refactor/sequential-loader-workbench`（`a4d6aa5`）、ローダー側は `feat/longvideobench-source-adapter`（`e44efbf`）。生成動画と擬似モデルの短時間検証は完了し、実LongVideoBench・実Qwenでの速度と精度は未検証である。

2026-09-25に、ローダーへ対象frameだけをRGB化する前方ストリームを追加し、Workbenchへ読取モード、全frame構造化観測、追記型観測・イベント台帳、可変長物語、上限超過時だけの章圧縮、根拠参照付き最終回答を実装した。ローダー182件、Workbench 86件の短時間テストと、両リポジトリを接続した生成動画確認に成功した。実LongVideoBench・実Qwenでの精度と速度は未検証である。

2026-09-25のMTGで、Ego4Dの基本データセットを整理しつつ`full_scale`動画を取得する方針を確認した。Workbenchは、対象動画・質問・メタデータを確認できる入口、分かりやすい時刻・設定表示、リロード時の安定性を改善する。研究コードでは、状況理解・情報集約・最終回答の3段階Agentの責務と編集点を明示し、重要イベントを保存するJSON形式とpromptを設計する。

2026-09-30に、承認済みspecに基づきWorkbenchのvideo_clip入力、窓単位Situation観測、根拠付きMemory記録、EOF Answer、read-only履歴表示を実装し、Workbenchの`main`（`2b5f830`）へfast-forward統合・GitHubへpushした。Fake・短い合成動画・Firefoxを含む181件の短時間テストが成功した。実Qwen/GPU・LongVideoBench実データでの品質と速度は未検証である。詳細は同日付のWorkbench Agent mode spec第14節に記録した。

2026-10-02のMTGで、データセット・動画・QA選択画面（プレビュー、お気に入り、検索を含む）を試作した一方、推論画面とAgentのエンドツーエンド動作は未確認であることを整理した。フォルダとプレビューキャッシュの実行間永続化、推論設定の矛盾解消、Agentの入出力・JSON・Prompt・責務の可視化を優先する。Situation / Memory / Answer Agentのデータフローを図と具体例で説明し、結果表示とサムネイルを整える方針を確認した。

## マイルストーン

- [ ] 研究方針を整理する
- [x] 動画ストリームを逐次読み込む最小実装を作成する
- [ ] VideoQAデータセット候補を調査する
- [x] 逐次動画ローダーの取得順出力・バッファ付きタイムスタンプ順出力を実装する
- [x] 逐次動画ローダーの利用サンプルと説明を整備する
- [x] 先行研究の逐次入力方法を調査する
- [ ] Agent系Streaming Video Understanding / VideoQAの既存機能と未解決点を整理する
- [ ] Agent / Streaming VideoQAにおけるMemory表現をtext / KV / feature等に分類する
- [x] 1 frameずつVLMへ入力してtext Memoryを逐次更新する最小Pythonプロトタイプを作成する
- [ ] 動的chunk長・multi-timescale memory・重要イベント用Memory等の研究候補を既存研究と比較する

- [x] 操作時にAgentを実行し、プロンプト・区間長等を変更して結果を確認できる最小デモを試作する
- [x] 長尺動画を逐次ロードし、区間ごとのQwen出力を保存・集約して最終回答を出す2--3段階の最小Agentパイプラインを作る
- [x] `sequential_loader` のAdapterが意図するデザインパターンと一致しているかを確認する
- [ ] Ego4Dの取得対象・取得状況・用途をまとめた説明書を作る
- [ ] Workbenchでデータセット、動画、質問、メタデータを確認してから実行できる入口を整える
- [x] 状況理解・情報集約・最終回答のAgent責務と編集点を明示する
- [x] 重要イベントを保存するJSON形式と、各Agent用promptを設計する
- [ ] Qwen3-VLの複数frame入力とオーケストレーションの実装例を調査する
- [ ] Workbenchのデータセット・動画・QA選択UIを実行間も保持できるDB・永続化構成に整理する
- [ ] 推論設定の矛盾とエラーを解消し、3段階Agentのエンドツーエンド実行を確認する
- [ ] Situation / Memory / Answer Agentの責務・入出力・JSON形式・根拠データフローを図と具体例で整理する
- [ ] Promptの妥当性を検討し、結果表示・サムネイル・メモリ内容を確認できるUIを整える

## Workbench個人利用の起動・終了運用（2026-09-29ユーザー指示）

Workbenchは本人だけが必要時に利用するローカル開発用UIである。サーバーの常時起動・常駐化は不要。Codexを含む実装者は、通常の起動手順を**ターミナルの前面で `longvideoqa serve` 等を実行し、同じターミナルの `Ctrl+C` で終了できる方式**とする。終了後は通常のシェル入力へ戻ることを確認する。

`nohup`、末尾の`&`、systemd、tmux等によるバックグラウンド化・自動起動は、ユーザーがその都度明示希望した場合を除き提案・実装・READMEの標準手順に採用しない。SSHポートフォワーディングが必要なら別ターミナルを使い、既存の他人のプロセスは停止しない。VS Codeで`Ctrl+C`後に文字入力/表示が乱れる場合は、まずフォーカス・端末制御・TTY復元とサーバーの終了処理を原因別に切り分け、常駐化を代替解決にしない。

共有サーバーのストレージ/GPUを他者が利用中のときは、画面確認用起動と実モデルロード/動画preview等の高負荷処理を区別する。ユーザーが明示的に実行しない限りQwenのモデルロード・GPU run・自動モデル取得を開始しない。
## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-08-28 | MTGでエージェント型ストリーミングVideoQAの構成と初期実装順序を整理。 |
| 2026-09-04 | MTGで逐次動画ローダーの分離・機能方針と文献調査の基準を整理。 |
| 2026-09-10 | プロジェクト作成。オンラインストリーミングVideoQAの対象と境界を記録。 |
| 2026-09-11 | MTGでchunk-level causal設定を確認し、Agent/Memory差分調査と最小text Memoryプロトタイプを次段階に設定。 |
| 2026-09-16 | EgoCrossの現在画像観測とtext-only state更新を分けた最小Agentを実装し、短い実Qwen runでtraceを確認。 |
| 2026-09-18 | MTGで、操作可能なAgentデモと長尺動画を逐次処理する最小Streaming VideoQAの試作方針を確認。 |
| 2026-09-25 | sequential_loader接続、YAML recipe、英語prompt、可変window、3段階Agent、artifact、ローカル画面を統合し、短時間検証を完了。 |
| 2026-09-25 | 対象frame専用RGB変換、全frame観測台帳、可変長物語・章圧縮、最終回答の根拠追跡を実装し、短時間検証を完了。 |
| 2026-09-25 | MTGでEgo4Dの取得方針、Workbenchの入口・表示改善、3段階Agentの責務明示とイベントJSON設計を確認。 |
| 2026-09-29 | Workbenchの個人利用・前面起動・Ctrl+C終了の運用境界を明記。 |
| 2026-09-30 | video_clip、窓単位観測、根拠付き記憶、EOF回答と可読表示を実装し、Fake・短い合成動画・Firefoxを含む181件を確認。Workbench `main`へ統合・push。実Qwen評価は未実施。 |
| 2026-10-02 | データセット・動画・QA選択UIを試作。Agent実行は未確認のため、入出力・Prompt・設定・永続化・結果表示の整理を優先する方針を確認。 |
