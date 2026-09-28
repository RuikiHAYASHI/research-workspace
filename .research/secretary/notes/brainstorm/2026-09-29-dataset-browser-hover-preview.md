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


## 2026-09-29 01:56 JST 追記: 4列サムネイル内ホバー再生・全画面の状態復元

### ユーザーからの追加希望（前段案を更新）

- 画面1のデータセット名・説明カードは維持する。
- 画面2の動画一覧は左側の縦リストではなく、PCで横4列・縦方向に並ぶサムネイルカードのグリッドへ変更する。各カードは動画アイコン/代表サムネイル・video ID・長さ等を持つ。
- カーソルをカード画像に合わせたとき、**そのカード画像の内部だけ**動画冒頭の無音previewに切り替える。別のカードへの移動で前カードを停止して通常サムネイルへ戻す。右側の常設動画preview欄を前提にしない。
- クリックは対象動画の詳細・QA選択へ進む確定操作。右側の詳細欄は、残す場合でも動画再生と重複させず、クリック後の詳細画面または選択概要に位置付け直す。選択後の詳細表示形式は未決。
- すべての段階（dataset選択、動画一覧、動画詳細/質問選択、実行設定、run中/結果）で、ブラウザreload・戻る/進む後に不整合やエラーを起こさず、妥当な直前状態に戻ることを重要要件とする。

### UI候補（探索）

```text
Dataset cards (name + description + availability)
      ↓
Video browser: [search/filter] + 4-column thumbnail card grid
  [poster + ID] [poster + ID] [poster + ID] [poster + ID]
  [poster + ID] [poster + ID] [poster + ID] [poster + ID]
       hover => only target card swaps poster to muted preview
       click => video detail / linked questions
      ↓
Question selection => run settings => existing turn-based run/results
```

- 画面幅に応じて4→2→1列、カード比率16:9、全カードには画像の遅延読込を適用。
- 一覧は索引からページング/追加取得する。動画全件デコードも動画全件に対するvideo elementの即時loadも行わない。
- previewはhover滞留後（仮目安200〜300ms）に開始、`muted`/`playsInline`/`preload=none`、必要なら短尺・低解像度clip cache。再生は原則同時1本、hover解除/画面離脱/画面非表示ではpauseしsourceを解放。古い非同期結果が新しいhover先を書き換えないようAbortControllerまたは要求世代番号でガード。
- タッチやキーボードでhoverできない利用者にも、カードfocus・選択・再生操作を用意する。画像のloading/error時はposterを保持し、一覧全体をエラーにしない。
- video cardクリックはプレビュー操作ではなく選択行為。前方decodeの研究用readerやQwen runを起動しない。

### 再読込・戻る/進むのための状態所有（提案、未実装）

| 種別 | 正本/復元手段 | 戻る/リロード時 |
| --- | --- | --- |
| dataset ID、video ID、question ID、検索、フィルタ、ページ | URL/path/query（IDを検査） | URLから復元。戻る/進むは履歴の表示変更であり、Agentを起動しない。 |
| 未実行のrun設定/prompt変更 | URLへ秘密情報を載せない。必要ならブラウザのdraft保存＋dataset/question整合確認 | 確認画面の編集を復元可能にするが、実行済みrunへ勝手に反映しない。 |
| hover対象、短尺動画の再生位置 | 一時UI state | リロード後はサムネイルから再開。autoplayを再起動しない。 |
| run_id・確定したsettings・各turn・結果・状態 | サーバ側artifact/安定ID。URLにrun_idを含める | GETで既存記録を再構成。ページreloadや戻るだけでPOSTしない。 |
| 実行中reader/model/session | サーバ側プロセス管理 | 同一server lifetimeのブラウザreloadでは既存runへ再接続。server restartでは状況を判定し、予期しない自動再実行をしない。 |
| 実行時の選択frame thumbnail | 現行approved契約はserver session内のみ | server存続時は表示可能。server restart後は非永続と明示、文字結果/metadataを表示。画像の再生成・永続化を要求するなら別途仕様判断。 |

- 選択済み動画の欠損、まだ取得されていないファイル、索引更新、未知のdataset/video/question IDは、クラッシュせず説明付きempty/error stateと前画面へ戻る導線を提供する。
- ダブルクリックや複数タブからのrun作成・次turn実行には、processing lockとrequest idempotency検討が必要。既存runを再取得するGETと新規POSTを混同しない。
- ブラウザreloadとサーバ再起動、任意の前ターン表示とreader sessionを戻すことは別。現在のapproved仕様では過去turn閲覧はread-onlyで、進行は最新位置からの次turnだけ。ブラウザbackで処理済みturnがundoされるわけではない。
- 前回実装メモにはbrowserの複数run間サムネイル黒化対策があり、run別URL/cache identifierの回帰を保持する。

### 評価軸・失敗条件・次に決めること

1. UI: 4列でIDが可読か、hoverしたカード以外の動画を取得しないか、戻る/進むの体験が自然か。
2. 資源: 初回一覧時間、サムネイル/preview初回準備時間、同時video再生数、NAS読取、preview clip生成・cache容量。Ego4D大量動画・不適合codecでも画面が詰まらないか。
3. 復元: dataset→動画→質問→runの各画面についてブラウザreload、browser back/forward、server restart、削除済み動画、失敗preview、処理中run、過去runをテスト。
4. 特に未決: click直後の詳細を専用画面とするかmodalとするか、previewの冒頭長・音声は原則無音、すべてのrun中にページ離脱してよいか/キャンセル確認が要るか、サーバ再起動後に選択frameを再生成するか。
5. 現段階は方針候補。research-spec、TODO、コードの自動変更はしない。


## 2026-09-29 02:03 JST 追記: 識別しやすい動画カード・時間フィルター・再起動後の再実行

### ユーザーの新たな方向性

1. サーバ再起動後、実行途中からの厳密なresumeは要求しない。対象動画・質問・設定を再選択または復元し、**動画先頭から新しいrunとして再実行する**のでよい。ただし「サーバ起動だけでGPU実行を自動開始」か「画面から再実行操作で開始」かは実装時に明確化が必要。現在の探索候補は誤操作・重複runを避けられる後者。既存artifactは旧run IDで保持し、新run IDを別に作り、旧runへ勝手に追記しない。
2. video IDは人間が識別するには不十分。カード上で見つけ直しやすい表示を設け、特定動画での繰返し動作確認を容易にする。
3. 一覧のフィルター・並べ替え、とくに動画長の昇順・降順を設ける。

### UIの有力候補

- PCで4列のposter card、hover中はそのカードだけ無音冒頭preview。各カードは「サムネイル、利用者が登録した任意の別名（なければ説明/質問文の冒頭など既存metadataから得られる表示）、動画長、関連質問数、コピー可能な正式video ID、取得状態」を持つ。情報量が過密になる場合はIDを二行目の小さい文字にし、全文は詳細・コピー操作で確認できる。
- 動画タイトルがannotationに存在するとは仮定しない。人間が付ける任意alias（例: 研究確認用A）、お気に入り、最近使用した対象、直接URL、過去runから同じ動画へ移動、を検討する。aliasと正規video_idを別フィールドに保持し、元データや評価IDは変更しない。
- 長尺VideoQAで同一videoに複数questionがある場合、一覧は動画単位で一つのカードへgroup化し、クリック後に質問一覧を出す。別名・お気に入りはvideo単位、実行履歴は(dataset, video, question, config, run_id)単位で管理。
- datasetによってEgo4D full_scaleとclipsが混在する場合はasset type/splitを識別子と表示に含め、同名stemを誤結合しない。
- 画面上部の操作候補: ID/別名/質問文による検索、動画長範囲（全件、短尺、中尺、長尺またはmin/max）、取得済みのみ、質問ありのみ、お気に入りのみ、並べ替え [動画長:短→長／長→短、ID順、最近使用]。検索・sort・filterはURL queryに表現してreload/back後に復元する。
- 時間は秒の数値で索引し、表示は mm:ss / hh:mm:ss。duration不明は末尾、同じdurationはstable IDでtie-break。データセット付属durationと実ファイル計測値が異なる場合は出所を明示する。
- 初期30〜50件のページング/追加読込は維持するが、検索・filter・sortはbackendの**全索引へ適用してから**page sliceを返す。現在画面にある50件だけをsortする誤実装を避ける。index作成時にannotation/manifestのdurationを優先し、全動画をdecodeしない。
- 既存AVA BrowserのSQLite indexing、GET videosのLIMIT/OFFSET、ファイル差分更新は参考。ユーザーの動画識別ニーズとQA紐付けはWorkbench側で定義。

### リロード・サーバ再起動の境界（先の探索案を具体化）

- 単純なbrowser reload/back/forward: run_idが生存していればGETだけで既存runへ戻り、POSTによる重複runを作らない。dataset/video/question/filter/sort/pageはURL由来で復元。
- サーバ再起動: active reader/model sessionは失われる。実行中だった旧runを新runと混同せず、中断として区別し、旧artifactを閲覧可能にする。保存済み対象とsettingsから新runとして**動画先頭から再実行**する。サーバ起動だけでGPUを自動占有する挙動は未決。新runを起こす場合はUIに「先頭から再実行」を明示し、二重POST防止。
- 完了したrunの記録は再起動後も履歴として残し、閲覧目的のGETで勝手に再実行しない。実行中だったrunを再実行する場合も旧ID上書きは禁止。thumbnailの旧runは現在のserver session-only契約に従う。
- IDからの直接URL、alias、お気に入り、最近使用はrestart後に失われない保存先が必要。未実装・未承認なので保存schemaはspec段階で決定。

### 反例・評価条件・未決

- 質問文から作る表示ラベルは問いの要約であって動画内容の真の題名とは限らない。LLMによる自動タイトル作成は余計なGPU負荷/未来映像使用の問題があるため初期scopeから外す。
- サムネイル1枚では類似動画を区別しにくいのでalias、正式IDコピー、質問文、最近使用/お気に入りの複数経路を確保する。動画内の複数サムネイル生成は後続候補。
- ページ跨ぎでduration sortが正しいか、未知durationの位置、同一durationで順序が安定するか、長さfilterとデータ取得有無、表示されたvideoにquestionが正しくgroup化されるか検証する。
- 動画未取得・別名の重複・同一stemのfull_scale/clip・索引更新・古い直接URL・restart後の旧run表示・新runの重複実行をテスト対象にする。
- 次の大きな選択は「別名をどこへ保存するか」「再起動後に自動runか、再実行ボタンか」「動画の詳細を専用画面にするか」。いずれも未確定探索。research-spec/TODO/コードは自動変更しない。


## 2026-09-29 JST 追記: データセット取り込み時のID原則・常設サイドバー・最初からやり直す操作

### 今後のデータセット取得・登録のルール（ユーザー指定）

- **配布元データに正式な video ID / question ID 等が存在しない場合、並び替え、配列位置、通し番号の付け直し等によって、正式IDがあるかのように捏造・補完しない。** 行番号は索引更新や並び替えで変化するため、恒久的なIDとして使用しない。
- 配布元が提供する識別子がある場合はその値をそのまま保持し、原本由来の識別子であることを分かるようにする。なければ UI では「提供IDなし」などと明示する。
- アプリ内部の参照に安定キーが必要な場合は、データセット登録名・split / asset type・配布元の相対パスなどの実在する参照情報を組み合わせて、**「アプリ内部キー」**として別フィールドで管理する。ハッシュを使う場合も元の参照情報との対応を保持する。これを配布元正式IDや評価用IDとして表示・使用しない。名前の衝突、ファイル移動・改名、同一動画の複数question等は明示的に検査し、曖昧なときは未確定として扱う。
- 正式IDも適切な安定参照もない場合、勝手に同一性を推定してお気に入りや履歴を別動画へ引き継がない。紐付け不能を表示し、dataset固有の取り込み契約を検討する。
- 動画一覧のソート・フィルターは表示順を変えるだけで、原本ID、内部キー、質問との紐付けや保存済みrunの参照を変更しない。この原則は今後追加するデータセット接続部すべてに適用する設計要件の候補とする。

### 左側の常設ナビゲーション

- ChatGPTの画面を参考に、画面左へ共通サイドバーを設ける。データセット一覧へ戻るホーム入口、独立した星アイコンの「お気に入り」、時計アイコンの「最近使った」、必要に応じたrun履歴を置く。
- 画面2の本体はPCで4列のサムネイルカードグリッド、hoverしたカード内のみ無音動画previewを行う。サイドバーはメイン領域に重ならないようにし、狭い画面では折りたたみ可能にする。
- 「お気に入り」はユーザーが明示的に星を付けた動画の一覧。「最近使った」は実際に選択/実行した動画のアクセス時刻に応じて更新する一覧。両者の意味とアイコンを分け、サイドバーから直接対象のdataset/videoページに移動できるようにする。
- alias、星、最近使用、選択済みdataset/videoは配布データと切り離したアプリ側のユーザー状態である。正式video IDを上書きしない。研究用run履歴・成果物とも別データモデルを使い、source pathなどの機密情報をURLへ露出しない。

### サーバ再起動後も保持するものと復元

- alias / お気に入り / 最近使った / 必要なUI設定は、サーバプロセスのメモリではなく、ローカル永続領域に保存すれば再起動を跨いで保持できる。初期候補は SQLite（例: ローカルの `var/workbench.sqlite3`、配置・バックアップ・権限は後続specで決定）とし、実データセットやGit追跡ファイルを直接変更しない。
- サーバ再起動時も同じ永続データ領域をマウント・参照することが条件。サーバの一時領域ごと削除されると消えるため、単にSQLiteを利用するだけで無条件に残ると主張しない。
- 保存キーは dataset登録名 + dataset内の安定参照（正式IDがないときは別扱いの内部キー）等。動画が削除・移動されても星や履歴を別の動画へ誤って付け替えず、「現在アクセスできない」と表示する。
- ブラウザreload/backはURLからdataset/video/question/search/sort/filterを復元。星や履歴はserverの永続DBから読み直す。

### 途中からホームに戻り、最初からやり直す操作

- サイドバーのホーム/「最初から選び直す」はdataset選択画面へ戻る常設入口。dataset一覧、動画グリッド、質問選択、実行設定、run中、最終回答画面のいずれからもアクセス可能。
- 実行前: 画面遷移のみでやり直し。以前の選択や検索条件をURL等で適切に保持し、戻る/進むでもクラッシュしない。
- 実行中: 「画面から離れる」と「現在のrunを中止してやり直す」を混同しない。利用者が明示的に中止を選んだ場合、進行中turnの終了/中断ルールに従ってreader/model資源を解放し、旧runをcancelled等の記録として保持。旧runへ新結果を追記しない。cancelとhome移動のUX、推論呼出し中に実際に即時停止できるかは実装契約で明確化する。
- 同じserverが生きている通常reload/backでは既存runを表示するだけで再POSTしない。サーバ再起動でactive sessionが失われた場合は、旧runを中断扱いにして旧artifactを保存し、保存済み対象・設定から新しいrun IDで**動画先頭から再実行**する。GPU処理の予期しない自動起動を避けるため、候補として「先頭から再実行」ボタンを用意する。これは厳密なresumeではない。
- 既存approvedな実行frame thumbnailのserver session-only契約と、ユーザー状態（お気に入り等）の永続化を混同しない。再実行による新しいframeサムネイルは新runへ紐付ける。

### 検証・未決事項

- IDなしdatasetの一覧ソート前後で同一動画キーが変わらないか、正式IDなし表示・質問との紐付け・類似/重複ファイル・移動・削除で誤結合しないか。
- お気に入り登録→サーバ再起動→再表示、最近使用順・aliasの永続性、別datasetへの誤紐付けなし。
- 全画面のホーム移動とbrowser back/forward/reload、run中のcancel後の資源解放、server restart後の旧run閲覧・新run先頭開始・二重起動防止。
- 未決: 最近使ったの更新契機（動画詳細を開く時点かrun開始時点か）、複数利用者利用時の保存単位、永続DBの配置/バックアップ、cancelがQwen生成中にどの時点で効くか、再起動後の再実行ボタンと自動実行の選択。
- 本記録は探索段階であり、dataset接続部・承認済みspec・コードを自動変更しない。新規dataset取込仕様を作る際は上の正式ID非捏造原則を受入条件へ引き継ぐ。


## 2026-09-29 追記: プロジェクト風フォルダ、右側質問パネル、動画検索とクリック翻訳

### 追加されたユーザー希望

- ChatGPTの「プロジェクト」のように、利用者が独自のフォルダ（研究用コレクション）を作成し、動画を整理できるようにする。
- 画面2で右側にも常設の領域を確保し、中央の動画カードへhoverすると、該当動画の質問文・選択肢・質問ID等を右側へ表示する。動画の冒頭previewは従前どおり**hover中カードの内部だけ**で流す。
- 動画検索機能を用意する。
- 質問文をクリックして日本語訳を表示できるようにする。原文との切替を可能にする。

### UIの有力構成（探索、先の「右側は不要」を更新）

```text
┌ 左・常設サイドバー ─┬ 中央・動画一覧（横4列のposter card） ┬ 右・QA詳細 ┐
│ ホーム／dataset       │ 検索・sort・duration filter          │ hover対象    │
│ ☆ お気に入り         │ [poster/hover preview] × 4列        │ question IDs │
│ ◷ 最近使った         │ 表示カードのみlazy load             │ 原文・選択肢 │
│ ▸ フォルダA           │ ID・alias・duration・star           │ 日本語訳切替 │
│ ▸ フォルダB ＋新規     │ クリックで動画/質問を確定            │ 実行対象選択 │
└──────────────────┴───────────────────────────┴────────────┘
```

- サイドバーはホーム、お気に入り、最近使った、ユーザー作成フォルダをアイコン・見出しで区分。フォルダの新規作成、改名、削除、動画の追加/除外を候補とし、名称はユーザー独自の表示情報であり原本のdataset名やvideo IDとは別。
- フォルダは物理ディレクトリを作って動画ファイルを移動する機能ではなく**永続DBに保持する論理コレクション**。データセットを横断して動画をグループ化でき、同じ動画を複数のフォルダへ登録可能とする候補。フォルダ削除で元動画・既存run・実データは消さずmembershipのみ解除。フォルダ内でaliasや説明の追加は拡張候補。
- 永続DB（例SQLite）にフォルダ、所属関係、星、最近使用、aliasを保存し、サーバ再起動を跨いで復元。同じ永続領域を保持していることが前提。正式ID欠損時のアプリ内部キーはdataset由来IDと明確に区別、sort順位由来の擬似正式IDは作らない。
- 右側パネルはhover時に高速なQA metadataを表示し、hoverが抜けたときは最後の選択対象を維持するかplaceholderへ戻すかを明確化する。操作案: hover中は仮表示、クリックで動画と対象questionを固定。右パネルへカーソルを移したときに内容が消えないようpinned stateを分ける。
- 一動画に質問が複数ある場合は右パネル上部に質問件数/質問切替。選択肢の順序・記号・原文、正式question IDがあるときはその値を保持。関連するQAがないdatasetは「この動画の質問データはありません」と明示して、架空のquestionを作らない。
- リストでのhover切替え連打時、前の動画の非同期取得結果や翻訳結果が別の動画の右パネルに表示されないようキャンセル/要求世代管理する。

### 動画検索と並べ替え

- 対象dataset、任意のフォルダ、全登録datasetの検索スコープをUIで明示。初期の中心は現在dataset内のvideo ID（あれば）、alias、原本のタイトル・説明（あれば）、動画に紐づいた質問文で検索できる方式。検索文字列・duration filter・取得済み・QAあり・sort条件を組み合わせる。
- 原本にないタイトルを推測で自動生成しない。「動画検索」は画像の内容認識検索を初期機能とするものではない。映像内容で検索するAI機能は別の計算負荷・因果境界を持つ後続候補。
- 検索/フィルター/sortはbackendの永続索引全体に対して適用し、結果をページングする。表示中50件だけをsortしない。入力debounce、サーバでindex参照、動画を検索のたびにdecodeしない。
- URLには検索・filter・sort・選択dataset/フォルダを反映し、戻る/進む/リロードで復元。特定動画へのリンク・folderリンクも安定識別子で復元。

### クリックによる日本語訳（表示機能、推論とは分離）

- 右欄の原文question/choicesをクリック、または隣接する「日本語訳」アイコンからon-demandで翻訳し、質問文だけでなく選択肢も対応した順序とラベルのまま表示する。元の英語と日本語をトグルでき、原文を常に確認できる。
- 翻訳は**UI閲覧専用**とし、配布元annotation、正解ラベル、研究runに使う元の質問/選択肢を書き換えない。翻訳内容をmodelに入力する実験をしたい場合は別設定とrun設定・再現性記録を要求する。
- 表示用translationは質問の安定参照+原文のdigest+翻訳器version等をcache keyとしてアプリ側に永続保存する候補。同じ質問を開くたびに無駄な再翻訳をしない。原文変更時はcache invalidation。翻訳が失敗しても英語原文は利用できる。
- 翻訳器は独立したtext-only処理または許可済みの外部翻訳APIを候補とし、使用するモデル・実行負荷・外部送信/データ利用条件は実装spec時に明示。既存のQwen動画推論中に予告なくGPUを占有しない。初期は利用者のクリック時だけ翻訳する。
- 翻訳が不完全・曖昧な可能性を考慮し、「機械翻訳」の表示と原文切替を残す。元ラベルA/B/Cや固有名詞、数字、時刻を崩さないことを評価する。
- QA metadataで質問を切り替えたりhover先を変えたりした場合は、翻訳の取得結果を別questionへ誤表示しない。正解ラベル/GTはUIに不用意に露出しない。

### 既存導線と衝突を避ける境界・検証

- フォルダ閲覧、検索、hover、翻訳は`sequential_loader`やQwenの実行ターンを進めない。画面上の未来動画プレビューは人間の探索操作と研究用causal inferenceを明確に分離する。
- dataset選択→動画hover→質問選択→設定→runの各段階、およびフォルダ・翻訳ON状態でreload/back/forwardを試験する。hover stateは揮発でもよいが、クリック確定したvideo/questionとfolder検索条件は再構成できること。
- サーバ再起動後はfolder・星・最近使用・alias・翻訳cacheを永続DBから取得。既存runの文字結果は別のartifactで保持。live reader sessionが失われたrunは新run IDで先頭から再実行する既存相談案を維持し、閲覧だけで勝手に実行しない。
- フォルダ内にdataset横断で同じvideo IDが存在しても誤結合しないこと、動画削除時はfolder項目を別動画へ付替えないこと、QAのない動画とIDのないデータを正常に表示できることを受入候補とする。
- 未決は、フォルダ所属を複数許すか（一旦許す案）、右欄hover解除の表示、翻訳の具体的エンジンと外部API利用可否、フォルダ共有の必要性、翻訳状態をreload後も維持するか。現時点はbrainstormのみで仕様/実装/TODOは未変更。


## 2026-09-29 追記: 入口となるデータセット選択画面のUI案

### 中心となる提案

ユーザー要望「データセット選択部分も案を載せる」を受け、最初の画面を左常設サイドバー／中央dataset card一覧／右dataset説明の3カラムとする。動画選択画面のレイアウトと操作体系を揃え、datasetカードを選択してから明示的に「動画一覧を見る」へ進む。正式なdataset名とユーザー定義の表示名を区別する。

```text
┌ 左・共通サイドバー ──┬ 中央・データセット一覧 ─────────┬ 右・選択中dataset詳細 ┐
│ ホーム/データセット     │ データセットを選ぶ + 検索           │ 名称・概要・用途        │
│ ☆ お気に入り          │ ┌ LongVideoBench ┐ ┌ Ego4D ┐     │ QA有無・課題形式        │
│ ◷ 最近使った          │ │説明・QAあり・状態│ │説明  │     │ split / 動画種別       │
│ ▸ 研究用フォルダ       │ │動画数・質問数   │ │取得状況│    │取得済/欠損/索引状態   │
│ ＋ フォルダ作成        │ └───────────────┘ └────────┘      │ [動画一覧を見る]        │
└───────────────────┴───────────────────────────────┴────────────────────┘
```

- 中央のカードはdatasetの名称、2〜3行の平易な説明、タスク種別（QAあり/動画閲覧/注釈の種類）、ローカルデータ取得状態、動画数、質問件数（存在する場合）を示す。件数はindex/manifestに裏付けがあるときだけ表示し、未集計・未知は「未集計」、未取得は「未取得」と分ける。現状の数値を固定表示しない。
- 右パネルはカードhover時に詳細を仮表示し、クリックで選択datasetを固定する。詳細は正式名称、説明、利用目的・研究上の位置づけ、動画/質問形式、利用可能なsplitやasset type、取得済数と欠損、索引日時、必要に応じて保存先の安全な表示名を示し、CTA「動画一覧を見る」へ進む。右欄へカーソルを移動しても選択表示が消えない。カーソルだけで動画の全件スキャンは開始しない。
- LongVideoBenchは動画に複数のquestionが紐づくQA datasetとして、Ego4Dは`full_scale`と`clips`のasset type、annotation taskを分けて表示する。Ego4D全動画にVideoQA questionが付くような表示・仮定はしない。dataset選択後に必要ならsplit/asset typeを選ぶ軽いフィルターを用意し、動画一覧へ渡す。
- 左の星・最近使った・フォルダはdataset画面にも共通表示し、動画直リンクは対応datasetの動画一覧/詳細を開く。folderはアプリ側の論理コレクションで、dataset本体の物理ファイル配置を変更しない。
- dataset検索は登録済み名称、説明、別名等の軽量metadataに対して行う。全動画の探索・decode・preview生成は選択画面ではしない。画面起動時は登録済catalog/索引の集計だけを取得し、必要なindex更新は明示操作またはbackground処理とする。
- データセットの利用可能性を明示: 登録済みか、動画あり/一部のみ/未取得か、注釈ありか、index作成中か、質問選択・実行が可能か。欠損ファイルに遭遇しても一覧自体は表示し、詳細に理由・更新操作を設ける。
- 原本IDとアプリ内のdataset registration key、利用者別名は混同しない。正式IDが提供されないdatasetで並び順由来の擬似正式IDを作らない既存要望を適用する。
- 選択dataset/split/asset type/検索をURLに保持し、戻る・進む・reloadで復元。サーバ再起動でもユーザー作成フォルダ/別名/お気に入り等は永続DBから復元。選択datasetが削除済みの場合は空状態とホーム導線を出す。
- 画面遷移は `dataset cardを選択→右で確認→動画一覧を見る→4列グリッド＋hover preview＋右QAパネル→質問選択→設定/実行`。お気に入りや最近使った動画、フォルダからの直接移動時はdataset画面の再選択を強制しない。
- 初期実装では宣言済みdataset catalogに限り表示し、全ストレージを起動ごとに再帰走査しない。負荷・欠損/遅延を測る。

### 誤解・未決・検証

- 「dataset」と「登録された物理data root」「split」「Ego4D full_scale/clips」「利用者フォルダ」は別概念。カードの粒度は原則dataset単位、split/asset typeは右詳細から絞る候補。異なる正式datasetを1カードへ無断統合しない。
- 同一datasetの複数登録rootや版に対応する場合は選択可能な登録元/版を明示して異なるデータを混ぜない。
- UI初回表示のレイテンシ、metadata未集計・index作成中・一部取得・QAなし・不正なdataset URL・reload/back/forwardを検証。
- 現時点は探索UI案であり、登録カタログAPIや新規asset取込等の実装許可ではない。README、approved spec、実コード、TODOを変更しない。


## 2026-09-29 追記: 今回はEgo4Dを使わず、次のdataset候補は初代Video-MME／各画面へのワンクリック遷移

### ユーザーによる今回のscope修正（以前のEgo4Dカード例を上書きする最新方針）

- **今回のWorkbenchの実使用対象にはEgo4Dを入れない。** 9/25 MTGのEgo4Dダウンロード・研究室保管作業と今回のWorkbench実装対象は別。Ego4Dの登録、UIでの有効表示、推論adapter接続やQAの準備を今回の前提にしない。既取得データの削除、取得停止、将来の不採用を意味しない。
- 現行接続先LongVideoBenchにもう一つVideoQA datasetを加えたい意向であり、**追加取得候補は初代Video-MME**。まだダウンロード済みとも採用・adapter実装済みともみなさない。配布元の動画・注釈・利用条件・サイズ/構成を確認した後に取得計画とdataset adapterの対象scopeを別途定める。
- 以前に示したデータセット選択画面のEgo4Dカードは今回の実使用画面例から除外し、LongVideoBench＋Video-MME（未取得/準備中）に修正する。未取得のVideo-MMEを即実行可能なように表示しない。
- 正式な配布元IDがない場合に並び順等から架空IDを作らない、原本metadataとユーザー別名/内部キーを区別する既存ルールはVideo-MMEにも適用する。

### Video-MME公式資料で確認済みの前提

- 初代Video-MMEの公式READMEでは900 videos、2,700 human-annotated QA、動画長11秒〜約1時間で短・中・長尺を含む。公式評価では動画、字幕、音声の入力条件を扱う。READMEに学術研究用途限定および無断配布等の制限が明記されている。
- 公式: https://github.com/MME-Benchmarks/Video-MME 。Video-MME-v2 https://github.com/MME-Benchmarks/Video-MME-v2 は**別物**であり、800 videos、3,200 QA等のv2構成を今回の初代Video-MMEへ流用しない。
- 初期接続候補は既存LongestVideoBenchと同様に元の質問・選択肢を維持し、映像のみでの逐次処理を基準にする案。字幕/音声の扱いはbenchmark条件と因果境界を確認して別途選ぶ。動画ごとに複数questionを持つこと、question IDやvideo keyの実際のフィールド形を配布schemaから確認し、推測で正規IDを作らない。
- 現時点では取得コマンド、実ファイル位置、ローカル取得成否、adapter実装状態を確認していない。downloadやGPU runは実施していない。

### ワンクリック導線（動画と推論を含む）

- 左サイドバーのホーム、dataset、お気に入り、最近使用、フォルダは**アイコンまたは項目を1回クリックして目的の一覧/詳細へ直行**する。繰り返し同じ選択画面を踏ませない。戻る・reload・direct URLが成立する状態管理を維持。
- 画面1のdatasetカードはhover/選択で右説明を表示し、カード上の「動画一覧へ」アイコンを**1クリック**するとそのdatasetの動画ブラウザへ遷移する。「カード選択→右パネルで再度確認→ボタン」の余分な手順を強制しない。カード選択による右説明表示も残す。
- 画面2の動画カードは画像hoverで内部preview、同時に右欄で質問/選択肢の仮表示。カード上に別の操作アイコンを設け、☆お気に入り、フォルダ追加、質問表示、▶推論設定へ、を独立させる。preview clickと推論実行開始を混同しない。
- 「▶推論設定へ」アイコンからは、クリック済みの動画・質問・dataset contextを持って推論設定/既存turn UIの入口へ**1クリックで移動**。questionが1件だけならそれを引継ぎ、複数あるのに未選択なら右側QAパネルの質問選択へフォーカスする等して、先頭の問を黙って採用しない。右パネルで質問を選んだ後はその問の「▶推論へ」アイコンが1クリック遷移。
- 遷移のクリックではdataset index全件decodeもQwen runも開始しない。重い実推論の開始は既存の明示「実行」操作とし、reload/backや右パネルhoverだけでGPUが回らない設計候補。
- 推論画面にもホーム、動画へ戻る、最近使用、実行履歴へのナビゲーションを配置し、どの段階でも最初から選び直せる。run途中の「閲覧画面から離れる」と「runをcancelする」は別操作。
- Video-MMEが未取得/準備中なら動画一覧/推論への操作は誤動作させず状態と必要な手順を示す。

### 画面例（現在の採用候補ではなく、探索UI）

```text
[左: ホーム / ☆ / 最近 / フォルダ]
[中央: Dataset cards]
  LongVideoBench  [一覧へ ↗]  ローカル登録の状態に従う
  Video-MME       [準備中]   次の取得候補／未取得扱い
[右: dataset概要・取得/QA/索引状態]

datasetアイコンを1クリック
    ↓
[中央: videoカード 4列＋検索/動画長sort]
  [poster, ☆, folder+, QA, ▶推論設定へ]
[右: hover中の動画の原文質問・選択肢・日本語訳切替、question切替と▶推論へ]
    ↓
[選択したdataset/video/questionを引き継いだ推論設定画面]
    ↓ 明示操作でrun作成・次turn
[既存turn推論UI]
```

### 追加の確認観点・保留

- Video-MMEの取得手順・license、元annotation ID、メディア/字幕の配置、実映像ファイルの一部欠損、同一動画3問のgrouping、動画長フィルターの出所を取得前に確認する。
- dataset選択カードで動画一覧アイコンを1クリック、右QAからrun画面1クリック、sidebar/direct URLからの遷移、戻る/進む/reloadで対象dataset/video/questionを失わないことを検証する。アイコンのhit area/キーボード操作/説明を確保。
- この追記はbrainstormとして方向性を記録するもので、既存承認済spec、TODO、研究コード、データダウンロードには着手しない。今後Video-MMEの採用・取得・接続を仕様化する際はcurrent Company skill/Gateに従う。


## 2026-09-29 追記: 現在の責務別ディレクトリ構成を維持してデータセットを増やす

### ユーザーの意図・採用方向

- 現在のWorkbenchの責務別ディレクトリ構成は評価されており、今回のブラウザ追加と今後のデータセット増加のために既存構造を壊さない。
- Datasetを増やすたびに、増えるPythonファイルは主としてそのdataset固有の取り込み・注釈対応処理に限定する。LongVideoBenchに加えて初代Video-MMEを接続する場合、共通UI/Agent/reader/run処理をコピペしてdatasetごとの実装へ分岐させない。
- 機能・責務に沿った配置を維持する。必要な新しい単位は既存の適切なパッケージ配下へ追加し、明確に独立した責務が肥大化した場合に限り新たな小パッケージを検討する。フラットmodule構成への後退、大規模なrename・一括移動、暫定互換wrapperの乱立を避ける。
- 「今回の実使用はLongVideoBenchと追加取得候補Video-MME、Ego4Dは今回対象外」という最新ユーザーscopeを維持する。

### 調査時のEvidenceと限界

- 2026-09-25 implemented Company spec `specs/2026-09-25-sequential-loader-workbench-refactor-implementation-spec.md` は `src/longvideoqa_workbench/` の `config/`, `core/`, `dataset/`, `reader/`, `sampling/`, `model/`, `agent/`, `records/`, `interfaces/`, `web/` という責務分離を現行構成として記録している。YAML、prompts/en、sequential_loader公開API、1 window/turn、artifact契約等を保護する。
- GitHubのWorkbench remoteで直接閲覧できるのは `feat/step-10-qwen-preflight` の `7544cd869d4bb9a1d05e64c932922304210b0e02`（9/24）の旧フラット構成のみで、ここでは `adapters/base.py` と `registry.py` にdataset/model registry、`adapters/longvideobench.py` にLVB固有annotation、`contracts.py` に共通QuestionSampleが存在する。local9/25実装済みとするCompanyの新構成はGitHubから実ファイルを直接確認できない。**実装直前に対象local worktreeの現行ツリーと差分を確認し、旧remoteの場所へ機械的に追加しない。**
- 旧LVB実装の `get_question(question_id)` は注釈と実動画パス存在を同時に検査する。大量動画のcatalog表示は「注釈がある」ことと「動画がローカル取得済み」を区別できるように責務を分ける候補で、既存推論用validationを弱めない。
- 既存Company specは `sequential_loader` の公開APIから前方向読取する実行契約を定める。新Video-MMEの元動画形式を確認せずに既存LVB loaderを使えると仮定しない。必要な追加公開source adapterは別の責務・Gateで扱う。

### 推奨する機能ごとの責務境界（仮ファイル名、仕様ではない）

```text
configs/                 dataset/model登録、profile/recipe（既存配置維持）
prompts/en/              Agent向け原文prompt（既存維持）
src/longvideoqa_workbench/
  config/                登録済dataset root、profile/recipeの解決・検証
  core/                  共通のVideo/Question参照・契約・状態遷移
  dataset/               dataset固有annotation解析・ID/動画/質問対応
    base.py              共通dataset契約（既存に同等があれば再利用）
    registry.py          登録済dataset adapterの選択
    longvideobench.py    LVBだけの注釈schema/locator
    videomme.py          初代Video-MMEだけの注釈schema/locator
    catalog.py           共通表示用の正規化metadataへの変換・索引窓口
  reader/                推論用の前方向reader、loader公開API接続
  sampling/              共通frame/window採用規則
  model/                 Qwen等モデル接続
  agent/                 観測・集約・最終回答の既存pipeline
  records/               runの不変設定・turn・artifact保存
  interfaces/            server入口/API: dataset一覧、動画検索、QA詳細、
                         preview、個人設定/フォルダ、翻訳、run操作を分ける
  web/                   共通サイドバー、dataset browser、4列動画card、
                         QAパネル、run view（現在のasset方式を尊重）
tests/                   dataset別fixture/test＋共通catalog/API/UI/run回帰
```

- ファイル名は概念上の例。現行local treeを見てすでに存在するbase/registry等を再利用する。`catalog.py` の責務が増えた場合のみ `dataset/catalog/` 等の小パッケージ化を検討するが、最初から過剰に階層を増やさない。
- 永続的なuser folders/favorites/recents/alias/translation cacheは`records/`の研究run artifactと混同しない。既存の永続化責務を調査後、例えば`core/`内のlibrary service＋`interfaces/` API、または独立責務が十分大きい場合に限り`library/`等の新パッケージを追加し、SQLite等のDBは実動画やrepo source treeから分離する。フォルダは論理コレクションであって物理ファイル移動ではない。
- dataset adapterの共通出力はdataset登録キー/版/split、配布元正式video/question IDの有無、アプリ内部の安定参照、元の質問・選択肢、durationとその出所、相対動画locator、取得状態等を明確にする。**配布元IDが欠けている場合、行番号やソート順位で正式IDを捏造しない。** 表示用aliasも公式IDとは別。
- データセットごとの`list_videos`/QA列挙/解決と共通catalogの一覧・検索・duration filter・sort・ページングを切り分ける。推論用`get_question`/readerは厳密な存在検証を維持。hover previewは推論reader/Agent turnから分離する。
- route/handler追加により`interfaces/server.py`一ファイルが肥大化する場合は責務別helperを同パッケージ内へ切り出すが、既存API入口・URL契約は維持。web側も現在のフレームワーク非依存のstatic asset契約を保ち、必要時だけ機能別JS moduleにする。
- 翻訳はdataset adapterやAgent promptには入れず、質問原文と選択肢を表示用に翻訳する独立service。正解ラベルをUIへ漏らさず、モデルへの入力は元の注釈を維持する。

### 別案と棄却/保留

- datasetごとに独自の画面、検索、プレビュー、DB、run orchestrationを一式複製する案は棄却寄り。バグ修正やリロード安定性がdataset数倍に分岐するため。
- 共通`dataset.py`や`server.py`へ新datasetのif/elifと機能一式を集中させる案は棄却寄り。新dataset追加時の回帰範囲が全体に広がるため。
- 現行10パッケージの全面再編・別frontend framework導入は保留。既存の機能とtest構成を尊重し、必要最小限の拡張とする。

### 実装前の受入候補と未確認点

1. Video-MMEの追加が基本的に`dataset/`の新adapterと登録/config/fixtureの追加で済み、既存Agent・model・sampling・recordsのdataset固有分岐を増やさないこと。
2. LongVideoBench既存runとartifact schema、CLI・server API、前方読取・時間/画像選択、サムネイル、既存prompt挙動は非回帰。
3. 1動画複数QA、ID不在の表示と内部キーの区別、取得不足、フォルダのdataset横断参照、全索引へのsort/search、reload/restartがdataset間で共通に動作すること。
4. 実装対象worktreeの最新ディレクトリとdirty変更、実Video-MME annotation schemaと媒体形式、loader追加の必要性はGitHubから未確認。実装・コード書込み・run・spec作成は本brainstormでは行わない。
