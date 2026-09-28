---
date: 2026-09-29
project: agentic-streaming-videoqa
source_todo: "2026-09-25 MTG: Workbenchへデータセット選択、動画・質問・メタデータ表示、動画プレビューを追加する"
topic: dataset-browser-hover-preview
status: exploratory
tags: [brainstorm, research, workbench, dataset-browser, hover-preview]
---

# データセット選択・動画一覧・ホバープレビューの初期壁打ち（探索記録）

## 出発点・確認済み文脈

- 2026-09-25 MTGで、Workbenchはデータセット指定・動画一覧・動画プレビュー・質問とメタデータ確認を経て実行する導線を検討し、ava-browserを参考にすることを決定した。リロードエラー、動画内時刻と処理時間、区間秒数と入力frame数の区別も課題。
- ユーザーの現時点の希望は、画面1でデータセットの名称・説明を示して選択し、画面2で動画を選択する構成。画面2の右側に詳細欄を確保し、左側の動画にカーソルを合わせると動画の詳細情報と、開始時点からの軽い動画再生を示す。重さ次第でプレビュー方式は変えたい。
- 現行GitHub公開のWorkbench branch `feat/step-10-qwen-preflight`（`7544cd8`）では、既存UIはデータセット/登録データ/質問IDのフォームが中心。LongVideoBenchAdapterは注釈JSONを質問ID辞書として保持し、動画パスを検査する。動画一覧・プレビューの専用APIは確認できない。
- Company 2026-09-25 implemented仕様ではターン型実行と採用frameサムネイル、memory改修まで報告している。ただしGitHub上のWorkbenchの公開branchは9/24の内容で、9/25のローカルworktree実体・dirty状態はGitHubから確認できない。実装前に現作業ツリーを再監査する。
- ava-browserはSQLite索引、増分のファイルサイズ/mtime比較、`/api/videos`の`LIMIT/OFFSET`、要求時サムネイル、HTTP Range配信、必要時のブラウザ互換変換を持つ。ただし既存の動画全体変換をそのまま大量動画のhoverに流用しない。

## 中心の問い

数千規模の動画を扱うデータセット選択・動画選択UIで、最初の一覧表示とホバー時の動画プレビューを、逐次VideoQAの推論処理を妨げず軽く提供するにはどう分離するか。

## 候補と比較軸

### A. 一覧はメタデータのみ、メディアはオンデマンド（有力）

- dataset catalog（登録名、説明、QA有無、ローカル取得状態、索引状態）を軽量に表示。
- 選択後は、注釈/manifestからvideo ID、動画長、question件数等を抽出した索引をページ単位（初期30〜50件の目安）で返す。検索、絞り込み、取得済みのみ表示を検討。毎回全動画をdecodeしない。
- 映像の存在確認、取得状態更新は索引処理で行う。ffprobeやサムネイル作成は全件同期で画面遷移をブロックせず、必要時または後方処理でキャッシュ。Ego4Dの増分ダウンロードに対応。
- 左側一覧へカーソルを合わせた動画だけ右側にメタデータを表示。video ID切替え時は古い非同期レスポンスを破棄。クリックで選択を固定し、次の質問選択・設定へ進む。

### B. ホバー動画の方式

1. 直接再生可能な登録動画なら、hover安定後（例200〜300ms）だけ、ブラウザ互換動画の冒頭を`muted`/`playsInline`/`preload=none`で再生。サーバのRange対応とcodec適合が前提。全ファイルを先読みしない。
2. codec不適合・巨大なファイル・NAS負荷が問題なら、最初の数秒だけ縮小・低ビットレートへ変換したpreview clipをオンデマンド生成、ファイル識別子/mtime等に紐付けてcache。変換は並列上限を設け、初回遅延中は静止画を表示。
3. 最小案は静止画だけ。実測で動画化のコストが許容されない場合のfallbackとする。

一覧カード全件のautoplayや全尺動画の事前変換は、CPU/ストレージ/ネットワーク負荷が大きくなるため初期候補から外す。hover解除時はpause、選択を切替えたときは先行preview要求の反映を防ぐ。右欄へカーソルを動かしても選択が不意に消えないよう「hovered」と「selected/pinned」を分ける。

### C. UI構造の探索候補

- 画面1: データセットカード（名称、説明、QAの有無、ローカルデータ取得・索引状態）、選択。
- 画面2: 左は動画検索・絞込・ページングを持つ一覧、右は固定の詳細/preview欄。右欄にID、長さ、format/codec（必要時）、取得状態、質問件数、質問候補を表示。
- クリック後は動画に紐づく質問を選び、実行設定・既存ターン型Agent画面へ接続。質問がないEgo4D閲覧とQA付きデータを混同しない。
- hoverだけに依存せずクリック・キーボードでも詳細が開けるようにする。

## 境界・反例・未決

- 実行前のブラウザpreviewと研究用`sequential_loader`は別の読取経路。hoverはmodel/reader/turnを進めない。人間による事前動画閲覧は、盲検評価と混同しない。
- dataset metadataがあることと動画ファイルの存在は別。欠損・未取得・変換準備中・不適合は明示する。
- 全件索引はO(N)のファイル確認を要するが、全動画decodeや全件ffprobe/thumbnail生成は不要。NAS性能、動画codec、HTTPアクセスにより実測は変わる。
- 未決: 右側はhoverで詳細だけ更新か、短尺previewも再生するか。動画previewは直接再生優先か、短尺clip常用か。クリックで詳細を固定する操作。Ego4Dを閲覧だけで登録するか、QA接続を追加するか。preview cacheのサイズ・更新方針。
- リロード時にdataset/video/questionを復元することと、実行中のsession及びthumbnail復元は別契約。既存ターンUIの保存方針を変更せず検討。
- 既存ava-browserは索引やRange配信の参考になるが、フロントエンドの全面移植や同じ全尺transcode方式を前提にしない。

## 次アクション候補（未採用、TODO未追加）

1. 現行Workbench作業ツリー/9月25日以降の差分とdata adapter APIを確認し、browser catalog/動画一覧/詳細/previewの責務境界を整理。
2. 実動画1〜数本で、meta lookup、初回thumbnail、直接hover再生、5秒clip変換、NAS読み込みを分離計測する。
3. dataset catalog、動画一覧、右欄detail、質問選択の画面遷移・API shapeをresearch-specへ渡せる粒度にまとめる。

## 関連資料

- `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-25-mtg.md`
- `.research/lab/projects/agentic-streaming-videoqa/README.md`
- `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-25-sequential-loader-workbench-refactor-implementation-spec.md`
- `.research/lab/projects/agentic-streaming-videoqa/specs/2026-09-25-workbench-target-stream-and-hierarchical-memory-spec.md`
- `tamaki-lab/2026-08-21-ava-browser`: `app/indexer.py`, `app/main.py`, `app/media.py`
- `RuikiHAYASHI/2026_09_hayashi_longvideoqa_workbench`: GitHubで確認できる9/24版 `src/longvideoqa_workbench/server.py`, `adapters/longvideobench.py`, `web/app.js`
