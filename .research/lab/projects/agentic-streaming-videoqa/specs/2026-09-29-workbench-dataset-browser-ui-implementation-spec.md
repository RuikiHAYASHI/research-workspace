---
date: 2026-09-29
project: agentic-streaming-videoqa
status: draft
topic: workbench-dataset-browser-ui-implementation
source: 2026-09-25 MTG, 2026-09-29 brainstorm, current user instructions
last_updated: 2026-09-29
scope: LongVideoBench browser UI; Video-MME research only
git_strategy: integrate previous phase to main, create phase branch, merge Step branches into phase
---

# LongVideoQA Workbench: データセット・動画ブラウザの実装計画

## 0. Authorityと状態

本書は実装計画のdraftであり、文書更新そのものは研究コード変更・branch作成・commit・download・GPU runの実行ではない。後続のCodexに渡すユーザーの実装指示とresearch-spec/engineering-taskのGateに従い、blocking項目を解消してから作業する。現在のユーザー指示により、前フェーズのcommit整理とmainへの非破壊的統合を今回の新branch作成より先に行う手順を本書に追加する。過去の壁打ち中のEgo4Dカード例、右側動画preview案より、今回のユーザー指示を優先する。承認時にstatusをapproved、必須検証が完了したらimplementedとする。

参照: .research/secretary/notes/brainstorm/2026-09-29-dataset-browser-hover-preview.md、meetings/2026-09-25-mtg.md、specs/2026-09-25-sequential-loader-workbench-refactor-implementation-spec.md、specs/2026-09-25-workbench-target-stream-and-hierarchical-memory-spec.md。

目的は、データセット選択→動画探索→原文QA選択→既存のターン型推論への入口を改善し、同じ動画を探し直せる研究用UIにすること。現行のYAML recipe、英語prompt、sequential_loader公開API、前方因果的読取、1 window/turn、Agent、run別artifact、既存CLI/APIを保持する。

## 1. 対象と対象外

今回の実装対象は、登録済みLongVideoBench向けの共通dataset catalog、動画索引・検索・動画長filter/sort、サムネイルとhover preview、左サイドバー・星・最近使用・フォルダ・別名、右QAパネルと表示用翻訳、推論画面への直接移動、reload/back/restartの安定化、およびテスト。

今回の実装対象外は、初代Video-MMEの動画取得・展開・dataset adapter/reader追加・実推論、Video-MME-v2、Ego4DのWorkbench接続、字幕/音声の推論入力、動画の意味検索/自動命名、全件動画decode、現行推論システムの全面改修、実Qwen/GPU/長時間評価、無承認の外部翻訳送信。Video-MMEは第3節でread-only調査と後続接続方法だけを記録する。取得・接続済みと偽ってカードを有効化しない。

## 2. 現行実装の基点と保全

Companyの2026-09-25 implemented仕様は、src/longvideoqa_workbench/配下の config/ core/ dataset/ reader/ sampling/ model/ agent/ records/ interfaces/ web/ の責務分離、configs/のYAML、prompts/en、既存run/turn API、frame thumbnailのserver session-only契約を記録している。一方、GitHubで直接取得できるWorkbench remoteはfeat/step-10-qwen-preflight、7544cd869d4bb9a1d05e64c932922304210b0e02（9/24旧フラット版）のみ。Companyに記録された9/25 localのfeat/step-11-initial-qwen-run / 7957b66およびfeat/final-answer-evidence-trace / e0d1c70の現物、dirty、worktreeはGitHubから未確認。旧remoteを現行の代わりに使わない。今回のGit操作対象は**研究コードWorkbenchリポジトリのlocal main**であり、Companyのresearch-workspace@mainへの本spec保存とは別。研究コードremoteには9/29確認時点でmain branchをGitHub経由で直接確認できず、local mainの存在・HEAD・追跡関係も実装前の監査対象とする。

Codexは着手前にCompany main、現local tree、AGENTS/CLAUDE、branch/HEAD、status、既存未追跡文書・dirty、sequential_loaderの公開API、config、dataset、reader、interfaces、web、records、testsをread-only監査し、基点となるclean commitを記録する。ユーザーの未commit/未追跡作業をstage/commit/上書きしない。矛盾があれば作業を止め、根拠と選択肢を報告する。sequential_loader自体の変更が必要なら別の承認Gateを通す。

## 3. 初代Video-MMEの調査（今回の接続実装には含まない）

### 配布内容と構成

- 公式: https://github.com/MME-Benchmarks/Video-MME 。配布先は旧 https://huggingface.co/datasets/lmms-lab/Video-MME から現 https://huggingface.co/datasets/lmms-eval/Video-MME へredirect。Video-MME-v2は別物。
- 900動画・計254時間・2700人手QA、各動画に基本3問。長さは11秒から約1時間。区分はshort（2分未満）、medium（4～15分）、long（30～60分）。公式READMEは744字幕ファイルとする。動画、字幕、音声の評価条件は別。
- 現HF treeは約101 GB。注釈はvideomme/test-00000-of-00001.parquet、字幕はsubtitle.zip、動画はvideos_chunked_01.zip～videos_chunked_20.zipの分割アーカイブ。実ファイル名・拡張子・対応は展開後のmanifestで検査する。配布revisionと取得ログを保存する。
- HF test（2700行）のschemaには video_id（例001）、videoID（元動画由来の別ID）、question_id（例001-1）、duration、domain、sub_category、url、task_type、question、options（4個）、answer がある。video_idとvideoIDは別の意味。question_idを行順から作り直さない。
- 特にdurationは「short/medium/long」の**カテゴリ文字列**であり秒数ではない。正確な長さ順sortには取得済み動画を必要時にprobeして数値秒を索引にキャッシュし、未知値は不明・末尾とする。区分から勝手に秒数を生成しない。
- answerは正解ラベルであり、閲覧パネルやAgent入力へ漏らさない。配布元URL切れ、動画未取得、subtitle欠損、重複ID、annotationと実動画の対応欠損を区別する。
- 公式READMEは学術研究のみ、商用禁止、動画権利は各権利者、無承認の再配布等を制限する。研究室の取得・共有条件を導入時に確認し、動画・注釈・tokenをGitに含めない。

根拠:
https://github.com/MME-Benchmarks/Video-MME/blob/main/README.md
https://github.com/MME-Benchmarks/Video-MME/blob/main/evaluation/output_test_template.json
https://huggingface.co/datasets/lmms-eval/Video-MME
https://huggingface.co/datasets/lmms-eval/Video-MME/tree/main

### 後続接続の方針（今回は実装しない）

現行dataset/の責務に沿ってVideo-MME専用adapterを追加し、注釈から正式video_id、元videoID、question_id、原文、4選択肢、カテゴリ、元URL、実動画の相対locatorを区別して共通形式へ正規化する。正式video_idで3問をgroup化し、runは各正式question_idを独立に持つ。実動画のpathは取得後の照合表で解決し、動画IDからファイル名を推測しない。動画未取得でもbrowser上はmetadataを見せてrunを不可にできる契約が必要。数値durationはprobe由来と明示する。

初期の将来接続は映像のみの研究条件とし、字幕/音声は別設定・再現性条件。字幕を使うなら現在時刻より未来の字幕を前段Agentへ渡さない。公式benchmark条件と独自causal設定を混同しない。取得・ライセンス確認・reader互換性・実ファイルでのsmokeは別specおよび別承認にする。

## 4. 画面・操作契約

全画面で左サイドバー、**中央に比較的広い幅**、右詳細の3カラムを基本とする。PC案は grid-template-columns: clamp(208px,16vw,248px) minmax(0,1fr) clamp(304px,24vw,384px) または同等の配分。3等分は禁止。中央を主役とし、左右は固定気味、余り幅は中央に割り当てる。狭い画面で右はdrawer、左は折畳み、動画カードは4→2→1列。4列が可読な画面幅のときだけ4列にし、横スクロールで逃げない。

データセット画面: 中央の幅広領域にdataset名、説明、QA有無、動画/質問数、取得/欠損/index状態を示すカード。未集計を0と偽装しない。右欄はhover/選択で詳細、カード内「動画一覧へ」アイコンの1クリックで移動でき、右欄で再度確定する操作を強制しない。現在はLongVideoBenchを実状態に応じて表示、Video-MMEは準備中、Ego4Dは今回表示対象外。

動画画面: 中央で16:9サムネイルの横4列グリッド。カードに元ID（あればコピー）、別名、duration、QA件数、取得状態、星、folder+、QA、推論へアイコン。hoverしたカード内で冒頭の無音previewを流し、右には該当動画の質問・選択肢・question IDを仮表示。動画clickで固定し、右欄へマウスを移動しても消えない。複数QAは右側で明示選択、未選択なら先頭を勝手に採用しない。QAなしはその旨を表示。

検索: 原本ID、別名、原本に存在するタイトル/説明、関連質問文。動画長短→長/長→短、指定範囲、取得済み、QAあり、星、最近使用の絞込を併用。索引全体に検索/filter/sortしてから30～50件程度ずつpage slice。duration不明は末尾、同値は安定内部キーでtie-break。検索時に全動画をdecodeしない。URLにはdataset/video/question/folder/query/filter/sort/pageを持たせる。

正式IDが提供されない場合、行番号やsort順から架空の正式IDを生成しない。「提供IDなし」と表示し、必要な内部キーはdataset登録・版・split・元相対locator等の実在参照から別に管理。原本ID、内部キー、ユーザー別名を混同せず、曖昧な紐付けを勝手に引き継がない。

カードのhover、翻訳、一覧検索、画面遷移は既存sequential_loaderやAgentのturnを進めない。「推論へ」はdataset/video/questionの選択を引き継いで設定画面へ1クリック移動するが、実際のrun/nextは明示操作のみ。キーボード/focus対応、loading/empty/error状態も実装する。

## 5. 分離すべき責務

dataset/にはデータセット固有annotation/locatorと共通catalogへの変換。reader/・sampling/・model/・agent/・records/は既存の推論契約を保護。interfaces/には一覧・検索・QA・media・library・翻訳・既存runのAPIを役割別に置く。web/は現行の静的asset構成を尊重する。新datasetを追加しても検索/preview/UI/runをコピーしない。server.py等の巨大化や全面的な再配置を避ける。

サムネイルはlazy。原動画がブラウザ適合ならRangeで要求時配信し、合わなければ要求時だけ数秒の低解像度clipを生成・キャッシュ。原則1本だけ再生し、生成同時数と容量に上限。全尺変換や全件先行probe/thumbnailはしない。hover解除・画面移動で停止、古い非同期結果が新しい選択を上書きしない。失敗時はposter。

星/最近使用/任意別名/ユーザー作成フォルダは、実動画を動かさない論理collectionとしてSQLite等のrepo外の永続領域に保持。複数フォルダ所属可、フォルダ削除は元動画/run非削除。datasetと正式ID/内部キーで他datasetへの誤紐付けを防ぐ。runのartifact、media cache、user DBを別管理する。

日本語訳は右パネルの質問文または翻訳アイコンクリック時のみ、質問と4選択肢をtext-onlyで翻訳する。原文切替、選択肢ラベル/順序保持、原文digestとtranslator versionによるcache。元annotation/答え/モデルに渡す原文を変更しない。翻訳provider/外部送信は第8節Gateで固定する。

## 6. 保存・復元・中止

browser reload/back/forwardは選択値/検索条件を復元し、既存runはGETで閲覧するだけ。表示操作でPOSTや次turnを二重実行しない。どの画面からもホームに戻れる。単なる画面離脱とrun cancelは別操作・明示確認。browser backはturnのundoではない。

server再起動でactive reader sessionが消えた場合、旧runのtext artifact・設定は閲覧用に保持し、旧runへの追記や厳密resumeはしない。「先頭から再実行」明示ボタンで別run_idを発行して最初から実行。server起動だけでGPU処理は始めない。旧thumbnailは現在のsession-only契約を維持。folder/星/最近使用/別名は同じ永続DBを再openして戻す。DB領域自体が削除された場合は復元不能と明示。欠損video/無効URL/多重クリック・競合を安全に表示・抑止する。

## 7. 前フェーズのmain統合 → 今回のフェーズbranch → Step別branch

**今回のユーザー指定Git方針:** 研究コードWorkbenchの現在のcommitを整理し、前フェーズの実装をlocal mainへ取り込んでから、今回の新しいフェーズbranchを作成する。さらにフェーズ内の各Stepにも別branchを作る。Git graphでmain・フェーズbranch・Step branchの三系統を追跡できる構成とする。**Step番号は今回の実装で1から**とし、前フェーズ統合の準備にはStep 0等の番号を付けない。

### 実装準備（Step番号外）: 前フェーズのcommit監査とmain統合

1. Company記録とlocal現物から、現在の作業branch、main、全worktree、HEAD、未commit/未追跡、既存Step/feature branchの親子関係、mainに未統合のcommit、remote追跡、保護ルールをread-onlyで一覧化。git log --graph --all --decorate、status、merge-base、branch包含関係とdiffを使い、実在するHEADとmerge対象を決める。Company文書に記録された旧SHAだけを根拠に自動選択しない。
2. 前フェーズの変更とユーザー由来のdirty/未追跡差分を分ける。未commitの前フェーズ関連作業があれば、変更意図が明確で承認対象に含まれるものだけ既存の適切な作業branch上で論理単位にcommitして整理する。無関係なユーザー変更・docsを勝手に編集、stage、破棄しない。git add .、reset --hard、clean、force、無断rebase/squash/cherry-pick、履歴書換えは行わない。区別不能なら停止して根拠を報告する。
3. 前フェーズの各既存Step commitとtests、既存Reader/Agent/UI/artifact回帰を確認。最新branchがすべての前フェーズ変更を包含しているか確認し、独立した未統合branchがあれば差分・統合順を説明する。重複取り込みやコードの欠落を起こさない。
4. local mainを確認し、前フェーズの検証済み先端を**git merge --no-ff**でmainへ取り込む。mainに並行変更があれば競合/非互換を監査し、明らかな衝突だけを解消・再検証。基点や競合が判断不能ならmainは変更せず停止する。既存履歴と元branchを残し、見た目のグラフのために不要な空commitや人工的な分岐を捏造しない。
5. 統合後mainで短時間の必須回帰（Workbench・sequential_loader関連test、compile、CLI help、許可されたfake smoke）を実施し、mainのmerge commit SHA、採用した前フェーズ先端SHA、結果、clean statusを記録する。失敗なら新フェーズを開始せず同じ統合の範囲で対処する。push、PR、remote mainへの反映は**別の明示指示がない限り行わない**。
6. mainへの統合完了・clean・検証成功後に限り、**今回のフェーズ親branch** feat/workbench-dataset-browser-phase をそのmain HEADから作成する。既存branch名と衝突する場合は勝手に上書きせず確認する。今回のStep 1はこのフェーズbranchから作る。

### 3系統のGitグラフと統合の方向

~~~text
前フェーズの開発branch ----（既存micro commits）----\
                                                  \
main               ------------------------------- M0 ------------------------------ Mfinal
                                                    \                                /
phase: feat/workbench-dataset-browser-phase          P--M1--M2--M3--M4--M5--M6--M7
                                                       \ / \ / \ / \ / \ / \ / \ /
step branches:                                        S1  S2  S3  S4  S5  S6  S7
~~~

M0は**前フェーズ→mainの統合commit**、Pはmainの統合済HEADから切るフェーズbranchの基点（branch作成自体はcommitを作らない）、S1～S7はStep別branch上の検証済みmicro commits、M1～M7はそれぞれStep branch→phase branchの**--no-ff merge commits**。Mfinalはフェーズ完了後に許可された場合だけphase→mainの統合commit。図は概念図で、実際のグラフ配置はGit UIや既存履歴に依存する。Pに飾りの空commitを作らない。mainは各Stepの途中で更新しない。**今回は「前フェーズのmain統合」は明示された手順だが、今回のフェーズの最終main統合は完了レビュー後の別の明示判断とする。**

### Step別branchとmicro commitの必須ルール

- **1 Step = 専用branch、1 micro step = 検証成功後の独立した1 commit**。micro専用branchは作らない。Step 1 branchはフェーズbranchの最新HEADから作成。Step nを完了したらStep branch上で末尾test/回帰とdiffを確認し、フェーズbranchへ git merge --no-ff で戻し、そのmerge commitを記録する。**Step n+1 branchはフェーズbranchのその最新merge commitから作る**。旧案の「Step branchから次Step branchを直接切る」方式は採用しない。
- Step branchからmainへ直接mergeしない。各Step branchをphaseへ戻さず次Stepに進まない。フェーズbranchで未検証の独自実装を増やさない。全Step終了後のmain反映はフェーズbranch一本から行う。
- 各microは実装→関連test→diff→commit。未検証の複数microをまとめない。Step末尾の失敗は同じStep branchでfix:/test: commitを作り、再検証後にphaseへ統合する。競合・想定外変更・他worktreeによる更新を確認したら古い内容で強制上書きしない。
- Git mergeの履歴を保持し、意図的なsquash/fast-forward/rebaseではなく、--no-ff mergeでフェーズとStepの境界を残す。ただしmainの保護設定や権限と競合する場合は迂回せず停止・報告する。
- commit表題は日本語の完結した文。本文は箇条書きにせず、一つの日本語段落で「対象・変更内容・理由・実施した検証と結果・既存への影響・次工程」を記す。未検証は理由と未実施を明記する。前フェーズ整理commitも同規約に準じる。
- データセット動画/注釈、モデル重み、credentials、outputs、SQLite/preview cacheをcommitしない。mainのmerge commitとフェーズ/Stepのbranch名・各SHA・test結果を毎回記録する。push/PR/remote mergeは別許可。

### Step 1: 現行基点の監査とdataset catalog
branch: feat/workbench-browser-catalog

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 1.1 | 現行Workbenchの責務と既存契約を記録する。 | local tree/dirty/API/テスト/基点記録。既存最小testとdiff確認。 |
| 1.2 | データセットと動画の共通閲覧形式を追加する。 | dataset/video/question/正式ID有無/duration出所/取得状態を正規化。fake fixture。 |
| 1.3 | 動画ごとの質問一覧を取得できるようにする。 | 同一動画3問、QAなし、欠損動画、ID非捏造、GT非露出test。 |

末尾: 全関連unit、compile、既存LVB run mock契約。Video-MME adapterは追加しない。

### Step 2: 軽量索引と検索API
branch: feat/workbench-browser-index-search

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 2.1 | 動画metadataの差分索引を追加する。 | annotation/manifest中心、必要時duration測定、未取得は不明、全件decodeしないtest。 |
| 2.2 | 動画検索と時間順の並べ替えを追加する。 | 全索引filter/sort後page、複合条件、不明duration、安定tie-break test。 |
| 2.3 | データセットとQAの閲覧APIを追加する。 | dataset/video/QA list/detail、未登録/欠損/無効selector/path traversal test。 |

末尾: fake多数件のpageと既存HTTP/CLI非回帰。

### Step 3: サムネイルとホバープレビュー
branch: feat/workbench-browser-media-preview

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 3.1 | 要求時のサムネイル配信を追加する。 | lazy cache、欠損placeholder、不正path、全件同期生成なしtest。 |
| 3.2 | 対象カードだけ動画をプレビューできるようにする。 | Range/codec、短尺clip fallback、同時数上限、cancel/cache test。 |
| 3.3 | プレビューの中断と失敗表示を整える。 | hover連打、先行response破棄、非対応/未取得fallback test。 |

末尾: 全尺事前変換なし、reader/Agent非起動、既存frame thumbnail非回帰。

### Step 4: 永続ライブラリ
branch: feat/workbench-browser-library

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 4.1 | 閲覧者の整理情報を永続保存する。 | DB schema/再open/ID別管理、artifact分離test。 |
| 4.2 | お気に入りと最近使った動画を管理する。 | 別名/星/recent/欠損/異dataset同ID test。 |
| 4.3 | フォルダで動画を整理できるようにする。 | 作成/改名/削除/複数所属、元動画/run非削除test。 |

末尾: DB配置/権限/バックアップ、全関連test。

### Step 5: 中央が広いdataset/video画面
branch: feat/workbench-browser-ui

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 5.1 | 中央を広く取る共通サイドバーを追加する。 | PC3列の幅比と狭幅折畳、focus/keyboard test。 |
| 5.2 | データセットカードから動画一覧へ直行できるようにする。 | 名称・説明・状態・右詳細、1クリック、Video-MME準備中test。 |
| 5.3 | 動画4列カードと右側QAパネルを追加する。 | card内preview、hover仮表示/click固定、複数QA/QAなしtest。 |
| 5.4 | 検索と整理操作を画面に接続する。 | 検索/sort/filter、星/folder、URL復元、文字安全表示test。 |

末尾: desktopの中央が左右より広く、4列が可読、狭幅に破綻なし、既存turn画面非回帰。

### Step 6: 翻訳と安全な画面遷移
branch: feat/workbench-browser-navigation

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 6.1 | 質問文と選択肢の表示用翻訳を追加する。 | approved provider、原文トグル、4選択肢/cache/失敗、Agent原文不変test。 |
| 6.2 | 選択した質問から推論設定へ直行できるようにする。 | 1クリック、複数QA未選択ガード、遷移時POSTなし、URL test。 |
| 6.3 | 実行中のホーム移動と中止を分離する。 | leave/cancel、資源解放、旧run保持、重複POST防止test。 |
| 6.4 | 再起動後の先頭からの再実行を案内する。 | DB再open、旧text artifact、新run_id、旧thumbnail非永続、起動だけではrunなしtest。 |

末尾: fake turnの全関連test。翻訳provider Gateが未解決なら6.1は始めない。

### Step 7: 結合・回帰・文書
branch: test/workbench-browser-integration

| micro | commit表題 | 作業とcommit前検証 |
| --- | --- | --- |
| 7.1 | データセット選択から推論までを結合検証する。 | fake dataset、同動画3問、検索/整理/preview/訳/既存turn、ID非捏造・未来遮断test。 |
| 7.2 | リロードと再起動の回帰を検証する。 | 全画面back/forward/reload、DB、旧run、新run、欠損/競合test。 |
| 7.3 | 利用手順と保全条件を文書化する。 | 起動、DB/cache、UI、翻訳provider、Video-MME未接続、検証結果をREADME/docsに記載。 |

末尾: Workbench・sequential_loader全関連test、compileall、CLI help、fake API smoke、可能ならbrowser手動検証。未実施項目は未実施と記録。

## 8. approved前のblocking事項

1. 翻訳provider: ローカルtext-only翻訳器か、ユーザーが明示許可した外部APIか。無断の外部送信/GPU起動は禁止。依存、品質、翻訳キャッシュのversionと接続方法を固定する。
2. 現行local Workbenchのmain/開発branch/HEAD/worktree/dirtyとAPI構成、前フェーズの未統合commit、今回の統合対象・順序を確認する。旧remoteを最新版とみなさない。mainの保護設定、競合、未追跡の扱いが未解決なら統合しない。
3. 永続DBのrepo外配置、backup、単一ユーザーか複数利用者かの単位と権限。
4. preview実動画のcodec/Range/NAS負荷を代表動画で確認し、clip秒数、cache容量・並列数を確定。未許可ならfake契約のみ。
5. cancelがモデル呼出し中に即時かturn境界か。既存sessionとrun status契約に合わせる。

non-blockingはカードの細かな間隔/文言、実際の画面幅に合わせるbreakpointなどで、既存styleに従う。原本ID規則・中央優先幅・明示run・非回帰の要件は省略不可。

## 9. 受入・Implementation Handoff

受入は、中央が左右より広いdataset/video画面、PC4列のcard内hover1本preview＋右QA、元ID非捏造、全索引search/sort後のpage、folder/星のrestart永続、翻訳原文切替、アイコン1クリックでrun設定へ、reload/back時の誤POSTなし、server restart後の別ID先頭再実行、既存LongVideoBench/reader/Agent/records/CLI/API/thumbnailの非回帰で判定する。

実装対象は、前フェーズをlocal mainへ検証済みで統合したclean基点から切るフェーズ親branchと、その子となるStep 1～7。**前フェーズ→local mainとStep→phaseの--no-ff mergeは今回指定のGit手順**。今回のphase→mainは完了レビューと別の明示承認が必要。Video-MME/Ego4D接続、download、実GPU、push/PR/remote反映は非許可。短時間fake unit/integration、compile、CLI help、loopback smokeの範囲で検証し、長時間runは別途許可を要する。
