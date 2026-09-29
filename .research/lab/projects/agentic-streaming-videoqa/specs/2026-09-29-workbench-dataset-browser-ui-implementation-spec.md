---
date: 2026-09-29
project: agentic-streaming-videoqa
status: implemented
topic: workbench-dataset-browser-ui-implementation
source: 2026-09-25 MTG, 2026-09-29 brainstorm, current user instructions
last_updated: 2026-09-29
scope: LongVideoBench browser UI; Video-MME research only
git_strategy: integrate previous phase to main, create phase branch, merge Step branches into phase
---

# LongVideoQA Workbench: データセット・動画ブラウザの実装計画

## 0. Authorityと状態

本書は2026-09-29のユーザー決定によりapprovedとなった実装契約である。前フェーズのcommit整理とmainへの非破壊的統合を今回の新branch作成より先に行い、その後にStep 1〜7を実装する。過去の壁打ち中のEgo4Dカード例、右側動画preview案より、今回のユーザー指示を優先する。必須検証が完了したらstatusをimplementedとする。文書承認とコード実装は、dependency・翻訳モデルのdownload/install、GPU run、dataset download、push、PR、今回phaseのmain統合を許可しない。

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

サムネイルはlazy。原動画がブラウザ適合ならRangeで要求時配信し、合わなければ要求時だけ冒頭6秒・最大480p・無音のclipを生成・キャッシュする。同時再生・変換は原則1本、preview cache上限は512MiBとする。必要な動画だけをon-demandで処理し、全尺変換や全件先行probe/thumbnailはしない。hover解除・画面移動で停止、古い非同期結果が新しい選択を上書きしない。失敗時はposter。取得済みLongVideoBenchの代表2本はH.264/720pであり、実装後の短時間測定でこの設定を変更する必要が生じた場合は、測定値と理由を先に示す。

星/最近使用/任意別名/ユーザー作成フォルダは、実動画を動かさない単一ユーザー向け論理collectionとしてSQLiteへ保持する。DB pathは設定可能とし、既定は`$XDG_DATA_HOME/longvideoqa-workbench/library.sqlite3`、`XDG_DATA_HOME`未設定時は`~/.local/share/longvideoqa-workbench/library.sqlite3`とする。一時directory、repository、run artifact配下には置かない。複数フォルダ所属可、フォルダ削除は元動画/run非削除。datasetと正式ID/内部キーで他datasetへの誤紐付けを防ぐ。run artifact、media cache、user DBを別管理し、DB fileのcopyによる停止中backup手順を文書化する。

日本語訳はArgos Translate 1.11.0と英語→日本語モデルを用いるローカルCPU text-only処理とし、右パネルの翻訳アイコンクリック時だけ質問と選択肢を翻訳する。外部serviceへ本文を送信しない。原文切替、選択肢ラベル/順序保持、原文digestとtranslator versionによるcacheを実装し、元annotation、答え、Agentへ渡す原文を変更しない。Argos本体または英日モデルが未導入なら利用不可理由を画面へ表示する。dependencyとモデルのdownload/installは別の明示許可まで行わない。Argos 1.11.0はPyPI metadata上でPython 3対応の`py3-none-any` wheelと`Python >=3.5`を宣言しており現行Python 3.12の導入候補にできるが、実runtime互換性は別許可後のinstall smokeで確定する。

## 6. 保存・復元・中止

browser reload/back/forwardは選択値/検索条件を復元し、既存runはGETで閲覧するだけ。表示操作でPOSTや次turnを二重実行しない。どの画面からもホームに戻れる。単なる画面離脱とrun cancelは別操作・明示確認。browser backはturnのundoではない。中止要求後は新しいturnを開始せず、進行中のモデル呼出しを強制終了せずに現在のturnが安全に終了した時点でreader等を解放し、旧run artifactをcancelledとして保持する。

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

## 8. readinessと解決済みGate

2026-09-29のlocal監査とユーザー決定により、実装の意味を変えるblocking事項は解消した。翻訳はArgos Translate 1.11.0のローカルCPU英日モデル、永続DBは設定可能なrepo外XDG data領域の単一ユーザーSQLite、previewは冒頭6秒・最大480p・同時1本・512MiB、cancelは現在turnの安全な終了後に資源解放する契約とする。Argos dependency・英日モデルが未導入の状態は実装blockerではなく、利用不可状態を明示する受入ケースである。

現行local Workbenchはmain `41b5870`、前フェーズ先端`e0d1c70`、main上の未commitサムネイル修正2件、未追跡docs 3件を確認した。サムネイル修正2件は専用保全branchで該当fileだけをcommitし、未追跡docsは変更・stage・commitしない。保全branchと前フェーズ先端を順にlocal mainへ`--no-ff`統合し、競合時は既存サムネイル修正と`e0d1c70`のreader mode対応を両方保持する。Workbench 86件、sequential_loader 182件、compile、CLI helpは統合前のclean先端で成功している。

non-blockingはカードの細かな間隔・文言、実画面幅に合わせるbreakpoint、SQLiteのbusy timeout等で、既存styleと標準libraryに従う。原本ID規則、中央優先幅、明示run、非回帰の要件は省略不可。Argosの実install後runtime smoke、実動画での継続的なpreview性能測定、実GPU推論は別許可事項として未実施に残す。

## 9. 受入・Implementation Handoff

受入は、中央が左右より広いdataset/video画面、PC4列のcard内hover1本preview＋右QA、元ID非捏造、全索引search/sort後のpage、folder/星のrestart永続、翻訳原文切替、アイコン1クリックでrun設定へ、reload/back時の誤POSTなし、server restart後の別ID先頭再実行、既存LongVideoBench/reader/Agent/records/CLI/API/thumbnailの非回帰で判定する。

実装対象は、前フェーズをlocal mainへ検証済みで統合したclean基点から切るフェーズ親branchと、その子となるStep 1～7。**前フェーズ→local mainとStep→phaseの--no-ff mergeは今回指定のGit手順**。今回のphase→mainは完了レビューと別の明示承認が必要。Video-MME/Ego4D接続、download、実GPU、push/PR/remote反映は非許可。短時間fake unit/integration、compile、CLI help、loopback smokeの範囲で検証し、長時間runは別途許可を要する。

## 10. 実ブラウザ受入後のUI修正追補（2026-09-29）

### 10.1 状態・根拠と実行境界

本節は、ユーザーの実ブラウザ確認で見つかった問題と追加要求を受けた、完了済みStep 1～7の後続修正である。元の実装契約、micro commit、結果記録を消さず、追加工程をStep 8とする。スクリーンショットにはFake Browser DatasetとVideo-MMEだけが表示され、データセット画面の下に推論画面が続き、白・ベージュ基調になっていた。

対象コードはWorkbenchの`feat/workbench-dataset-browser-phase`（調査時HEAD: `f184dff5b0d64f18032e43e4df73364bf0aaebf5`）。`web/browser.js`は`hidden`を切り替えているが、`web/style.css`の`.workspace { display: grid; }`などの指定により非表示が上書きされる。LongVideoBenchが見えなかった事象は、先のFake用安全起動手順で`--data-root`を省略したことと区別する。実データ接続の不具合と決めつけない。

**Company同期注意:** GitHubの本specは現時点で`draft`だが、Codex報告ではローカルCompanyにStep 1～7の`implemented`更新と実装記録の未同期変更がある。ローカル変更を捨てたり、古いGitHub版で強制上書きしたりせず、本節を現地の実装記録と差分照合して両方保持する。元の承認/実装履歴の意味を変更しない。本追補の保存はコードやREADMEの変更完了を意味せず、実行は引き継ぎ先のengineering-taskのGateに従う。

作業前に最新branch/HEAD/worktree/dirty/適用指示を再確認する。既存Step 1～7のcommit/merge履歴とユーザー由来の未追跡docsは保全。今回の作業はphase上の受入修正であり、mainへの最終merge、push、PR、実Qwen/GPU、実動画previewの高負荷確認、データダウンロードは許可しない。

### 10.2 必須修正・受入条件

1. **画面切り替え:** 初回は`#browser-view`のみ表示し`#inference-view`を完全に非表示とする。推論タブと「推論へ」では逆に切り替え、データセットへ戻したときは推論画面が下に残らない。共通CSSの`[hidden] { display: none !important; }`などでCSSのgrid/flexとの競合を修正する。初回、タブ、reload、back、forward、エラー時を実表示で確認する。画面移動だけでrun/turn POSTを行わない。CSS文字列だけのテストでは受入不可。
2. **LongVideoBenchの表示:** `--data-root longvideobench=...`を指定して起動した場合はLongVideoBenchのdatasetカード・動画数・QA数・取得状態を表示し、Fakeだけの確認用起動と区別する。既存データルートの`lvb_val.json`と`videos/`の存在・権限・注釈形式をread-onlyで確認する。Fakeは「テスト用」と明示し、実登録データを見つけやすくする。登録失敗を成功表示にしない。Video-MMEは接続準備中のみ。全件decode、動画preview、GPU処理は登録確認で行わない。
3. **黒を主役にしたデザイン:** 全体背景`#0B0E12`、panel`#151A21`、raised`#1D242D`、主要文字`#F4F6F8`、補助文字`#A9B3BD`、境界`#303944`、落ち着いた緑アクセントを基準とする（読みやすさ優先で調整可）。`color-scheme: dark`に対応し、背景だけでなくカード、右QA、推論設定、実行履歴、ボタン、input/select/textarea、status、hover/focus/disabled/error/loadingまで一貫させる。既存CSSの白背景直書きを残さない。巨大な見出し・上余白を縮め、中央優先の3列と十分な幅での動画4列、狭幅折畳みを維持する。
4. **既存契約を守る:** 元ID、質問選択、YAML/英語prompt、sequential_loader公開API、reader/Agent、1 window/turn、run/artifactを変更しない。タブ/閲覧/検索/翻訳は推論を開始しない。

### 10.3 README・利用手順の更新を必須成果物にする

Workbenchコード側のルート`README.md`と`docs/dataset-browser.md`を実装と一緒に更新する。READMEの目立つ位置に、実装確認に使う正しい**phase worktree/HEAD、Python仮想環境、実際のimport元、旧サーバーと衝突しないポート**を示す。次の2経路を混同しないコマンドで明示する。

- **Fakeだけの安全なUI確認:** `--data-root`なし。GPU不可視、既存環境のみ使用、独立した小さなDB/cache/output、既存サーバーと別ポート。レイアウト・タブ・右QA・テーマを確認する。
- **LongVideoBench登録確認:** `--data-root longvideobench=/mnt/HDD18TB/hayashi/data/LongVideoBench`あり。`lvb_val.json`と`videos/`を確認し、データセットカード/件数/状態を確認する。軽い注釈読取・動画存在確認が生じるため共有サーバー利用状況を確認してから行う。動画一覧のposter取得やhoverはffmpeg/ディスク読取・cache書込を発生させ得るので、別途許可なく自動実行しない。

README/docに`PYTHONPATH="$PWD/src..."`または同等の手段で旧editable installとの取り違えを防ぐimport元の確認、`python -m longvideoqa_workbench serve`による確実な起動、`CUDA_VISIBLE_DEVICES=""`、SSHポートフォワーディング、正しいブラウザURL、終了時のCtrl+C、トラブルシュートを含める。仮想環境が未確認なら存在を検証してから使う。新たなpip installやモデル重み取得を勝手に行わない。

**サーバーを起動するだけではQwen3-VLの重みをロードしない**ことと、「最初のターンを実行」を押すとモデル使用に進むことを明示する。DB、media cache、run outputの保存先を分離し、共有ディスク負荷・既存起動サーバーへの影響を記載する。`docs/dataset-browser.md`の内容をREADMEから直接参照できるようにし、旧画面につながる曖昧な説明を残さない。

### 10.4 追加Step 8のブランチ・micro commit計画

Step 1～7は改番しない。親branch`feat/workbench-dataset-browser-phase`の最新clean HEADから専用branch`fix/workbench-browser-acceptance-ui`を作る（同名branchがあれば事前照合）。各microを実装→最小関連テスト→diff確認→独立commitとし、末尾検証成功後に`git merge --no-ff`でStep 8 branchをphaseへ戻す。mainへはmergeしない。

| micro | commit表題案 | 変更と検証 |
| --- | --- | --- |
| 8.1 | 画面タブの非表示制御を修正する。 | hiddenとCSS gridの競合、初回/切替/reload/back/forward、誤POSTなし。実ブラウザで非選択画面の非表示を確認。 |
| 8.2 | Workbenchの画面を黒基調のテーマに統一する。 | CSS変数と白背景直書き、全画面、入力、QA、状態表示、アクセシビリティ、3列/4列/狭幅の確認。 |
| 8.3 | 実データとFakeを区別して表示する。 | 登録あり/なし/無効パスのcatalog、LongVideoBenchカードと件数、Fake表示、Video-MME準備中を検証。実動画の高負荷操作はしない。 |
| 8.4 | READMEに新UIの安全な起動手順を記載する。 | ルートREADMEとdocs/dataset-browser.mdを更新し、2種類の起動、import元、別ポート、SSH、ディスク/モデル境界を現行CLIと照合。 |
| 8.5 | 実ブラウザ受入と既存機能を回帰確認する。 | 全関連テスト、compileall、CLI help、fake API、diff/dirty、実表示を確認。不可ならユーザー確認用の手順と未実施理由を報告。 |

### 10.5 main統合前のユーザー確認Gate

**Step 8が完了し、検証済み修正をphase branchへ統合した段階で、ユーザーへ新UIの実行手順を必ず提示し、実ブラウザ確認を待つ。** 少なくとも正しいbranch/worktree/HEAD、Python import元、Fake用とLongVideoBench登録用の起動コマンド、SSHトンネルとブラウザURL、不要なモデルロード/previewを避ける操作、テスト結果、未検証事項を示す。画面スクリーンショットは実際に取得できた場合のみ提示する。

ユーザーがLongVideoBenchカード、画面の相互非表示、黒基調、中央幅とQAを実際に確認し、問題があれば同じphaseで追加修正・再検証する。**ユーザーから明示的な最終承認を得るまでphase→local mainのmergeを行わない。** 過去の統合許可を今回の修正後へ自動流用しない。push/PR/remote反映、GPU、実動画preview負荷測定は別の許可とする。

## 11. 実装結果（Step 1〜7、2026-09-29）

readiness Gateで確定したArgos Translate 1.11.0、repo外SQLite、6秒・最大480p・同時1本・512 MiBのpreview、turn境界cancelを実装した。LongVideoBench browser、検索、4列card、右QA、星、recent、別名、folder、表示用翻訳、URL復元、既存推論への導線、旧run閲覧と別ID再実行までをphase branch `feat/workbench-dataset-browser-phase` に統合した。phase HEADは `f184dff5b0d64f18032e43e4df73364bf0aaebf5` で、local mainへの最終統合は未実施である。

前フェーズの保全commitは `17b2bba`、保全branch→mainは `d73d423`、前フェーズ `e0d1c70`→mainの統合commitは `d8863065adb04be08d99661b0acd1b672e9163b8`。元main worktreeの未追跡 `docs/file-relationships.md`、`docs/file-responsibilities.md`、`docs/processing-flow.md` は変更・stage・commitしていない。

| Step | branch | micro commits | phaseへのmerge commit |
| --- | --- | --- | --- |
| 1 | `feat/workbench-browser-catalog` | `2f30b48`, `af12ee2`, `f9c5f30` | `1756a60fc0d589b5a64840cf00c4103bdaa5fdc2` |
| 2 | `feat/workbench-browser-index-search` | `4fd4bfc`, `7e4ddcd`, `2cd36f0` | `6583dbb13b1fe80e39d69c3b8615ee0e675cbae1` |
| 3 | `feat/workbench-browser-media-preview` | `8bc4d2c`, `ad38058`, `4fffc9c` | `59696d8f3d1be797cc20390fae236183bb12f311` |
| 4 | `feat/workbench-browser-library` | `a794056`, `3f2a9a1`, `5af663c` | `1f560f47f8ab5298e9cd079440cc021024a7d188` |
| 5 | `feat/workbench-browser-ui` | `f95ed36`, `3e4ce47`, `7716b8c`, `2529fc3` | `357a094b711f46b1d0b428bd77cc4957e53bfd3d` |
| 6 | `feat/workbench-browser-navigation` | `dedee56`, `39ee84e`, `277804e`, `fdf7bb5` | `44f525d450532a2a779ac909c05dd5198d8d8c72` |
| 7 | `test/workbench-browser-integration` | `525bbf8`, `e013150`, `c43b64a`, `2e457ac`, `99cd9bf` | `f184dff5b0d64f18032e43e4df73364bf0aaebf5` |

最終GateはWorkbench `133 passed`、sequential_loader公開checkout `169 passed`、`python3 -m compileall -q src tests`、`longvideoqa --help`と各subcommand help、loopback fake API結合testが成功した。実装用phase worktreeはcleanで、mainは `d8863065adb04be08d99661b0acd1b672e9163b8` のまま保持した。

未実施はArgos本体・英日modelのdownload/installと実runtime smoke、実LongVideoBenchでの継続的preview性能測定、browser実機での手動視覚確認、実Qwen/GPU推論、Video-MME取得・接続、Ego4D接続、push、PR、remote反映、phase→main最終統合である。Node.jsが環境にないため`node --check`は実施せず、JavaScriptは静的契約test、asset配信test、loopback API testで検証した。


## 12. 実装結果（Step 8、2026-09-29）

受入修正branch `fix/workbench-browser-acceptance-ui` をStep 1〜7統合済みのphase HEAD `f184dff5b0d64f18032e43e4df73364bf0aaebf5`から作成し、5 micro commitを検証後に記録した。`baf1699`でhiddenとgridの競合、初回の未接続placeholder誤選択、推論viewの履歴復元を修正した。`0681b74`で指定paletteを用いた黒基調テーマ、compact header、中央優先3列、4列動画、狭幅折畳み、hover/focus/disabled/error/loadingを整えた。`72787ab`でFakeだけの起動とLongVideoBench登録起動を分離し、Fakeをテスト用と明示した。`e4aa963`でルートREADMEと`docs/dataset-browser.md`へ正しいworktree、Python/import元、2経路の完全な起動、別port、SSH、終了、負荷回避、旧画面切り分けを記録した。`311aba1`でloopback受入testを追加し、全回帰で見つかったactive JSONL末尾の部分読取raceを、未完結末尾だけ次pollまで除外する契約で修正した。

Step 8 branchはphaseへ`--no-ff`で統合し、merge commit兼更新後phase HEADは `06fa1e0681242cdded611f5e791e1c41b0146380` である。統合後のphaseでWorkbench `141 passed`、sequential_loader公開checkout `169 passed`、`python -m compileall -q src tests`、top-levelと`run`/`serve`/`qwen-preflight`のCLI help、Fake loopback APIを確認した。Firefox headless実表示では初回、tab、back、forward、reload、質問から推論への遷移で両画面が同時表示されず、1600pxで左右248/384pxに対して中央872px、動画4列、720pxで1列折畳み、指定dark paletteを確認した。実LongVideoBenchはdataset画面に留まり、動画753件、QA 1337件、`available`を表示し、run outputとpreview cacheが空であることを確認した。

未実施はユーザー自身のブラウザによる最終受入、実Qwenのmodel loadとGPU推論、実LongVideoBenchの動画一覧・thumbnail・hover preview性能確認、Argos本体と英日modelのinstall/runtime smoke、Video-MME/Ego4D接続、push、PR、remote反映、phase→local main最終統合である。ユーザーの画面確認と明示承認までphaseをmainへ統合しない。

## 13. ユーザー実画面レビュー後の画面状態・QA操作修正（Step 9案、2026-09-29）

### 13.1 根拠・状態・変更の境界

ユーザーがStep 8後の実LongVideoBench画面を確認し、黒基調の見栄えは改善した一方、質問が多い場合の選択、動画からデータセット一覧への帰還、ボタンの操作感を修正するよう依頼した。提示画像では動画にカーソルを置いた時点で右に長いQAが表示され、ホームへ戻った後も中央に「データセットを読み込んでいます…」が残り、タイトルがLongVideoBenchのまま、右側の前動画QAも残っている。

本節はStep 1～8の実装結果を取り消さない**追加受入修正のdraft**であり、既存frontmatterの`implemented`はStep 1～8の実装記録を指す。本節の未決Gateが解消して明示承認されるまでStep 9の実装可能な全契約とは扱わない。WorkbenchのCompany記録ではStep 8後のローカルphase HEADは`06fa1e0681242cdded611f5e791e1c41b0146380`。GitHubの研究コードremote phaseは確認時点では`f184dff5b0d64f18032e43e4df73364bf0aaebf5`で、Step 8後の現物は未push。古いremoteへ直接編集せず、Codexが最新ローカルworktreeのHEAD/dirty/適用指示/現コードを再監査してから変更する。画像からはUI症状を確認できるが、JSの具体的なrace原因は最新ローカルコードで検証する。

### 13.2 閲覧状態を独立させる

- 状態は`dataset一覧`、`動画一覧・hover preview`、`動画選択済み・QA一覧`、`推論設定・run`を分け、画面ごとのタイトル、中央内容、右詳細、操作欄、URL、hover/selectionをそれぞれ一貫して制御する。
- 動画一覧でカードを**hover/focusしただけでは質問本文・選択肢を表示しない**。右側は動画のposter/previewを主役にし、表示中動画の基本情報のみ添える。既存カード内previewとの二重再生/二重decodeを避け、同時preview上限と失敗fallbackを維持する。動画カード本体を明示クリック/Enter等で選択した後、右側をその動画のQA一覧に切り替える。別のカードへのhoverだけで選択済みQAを不用意に上書きしない。
- QA一覧は1問ごとに「質問文＋選択肢」を**1つの操作可能なブロック**とし、ブロック全体のhoverとキーボードfocus時にネオン寄りの緑の輪郭・穏当なglowを表示。クリック/Enter/Spaceで**そのブロックの正しいquestion ID**を選ぶ。選択中・hover中・disabledの区別、文字/焦点コントラスト、`prefers-reduced-motion`を考慮する。翻訳・原文切替などブロック内の別ボタンは選択/遷移を誤発火させない。答えの正解ラベルは露出しない。
- **blocking未決:** QAブロック押下による「実行」は、(A)既存の`推論設定画面へ質問を引き継いで遷移するだけ、実際のrun/turnは別の明示操作、か、(B)直ちにrun/モデル呼出しを始める、かをユーザー確認する。明示決定がない間はBを実装/起動しない。BならGPU、run artifact、二重実行、キャンセル等の契約を別途確定する。
- 現在の動画カードには`★`、`名前`、`＋`、`QA`、`→`の5操作がある。カード本体のクリックでQA一覧を開くため`QA`を除く、残る4操作を`★／名前／＋／→`とする案は**ユーザー確認待ち**。`→`を残すなら質問未選択時は無効で理由を示し、QAブロック操作の決定と役割を重複させない。無断で4操作の別構成を決めない。

### 13.3 データセット画面へ帰還する際の状態・非同期修正

- 「データセット」タブ、左「データセット」、ホームから戻る操作では、遷移**直後に同期的に**`activeDataset`・動画選択・質問選択・フォルダ/検索の動画固有状態を解除し、タイトルを「データセット」、中央をdatasetカード/ロード状態、右側を未選択またはdataset概要に初期化する。前動画の質問やLongVideoBench見出しを残さない。必要な状態は明示URLを正本として復元し、ホームURLへdataset/video/question等を持ち越さない。
- 戻る直前に進行していた動画一覧/QA/翻訳/previewの応答が帰還後に到着しても、最新ページのDOM/stateを上書きさせない。画面遷移ごとのrequest revision/AbortController等で古い応答を破棄し、stop preview、remove source等の資源解放を行う。初期化/読み直しは`finally`や明示エラー状態を持ち、「読み込み中」のまま永続しない。失敗はエラー文と再試行導線を表示。
- データセット一覧を表示するだけで既存動画の一覧検索やサムネイル生成を始めない。可能なら取得済みcatalog summaryを再利用し、不必要な全件再計算を避ける。fake/実LongVideoBench、reload/back/forward、急速な往復、遅延応答、重複クリックでそれぞれ回帰検証する。
- UIフェーズ切替とブラウザ履歴操作ではrun/turn POSTしない。進行中runの画面離脱と明示cancelは従来どおり分ける。

### 13.4 ボタンのクリック感・操作応答

- すべての主要ボタンとQAブロックに`hover`、`focus-visible`、`active`（押下中の明確な背景/枠/影/わずかな沈み込み）、`selected`（持続する選択表示）、`pending`（処理中表示）、`disabled`の区別を与える。カーソル形状、テキスト、クリック可能範囲から操作対象を認識できるようにする。タブ、検索、星/フォルダ/名前、カード選択、QA選択で押下フィードバックの一貫性を検証する。
- 一時的な`:active`だけに頼らず、検索実行中や非同期保存中は読み込み/完了/失敗を表示し、連打による二重POST・二重操作を抑止する。誤解を招く「実行中」の表示は実際のrun状態と区別する。可能なら全操作はキーボードでも利用可能。ネオンのglowは文字可読性を損なわない強さとする。

### 13.5 実装計画と受入Gate

作業branchは最新の検証済み`feat/workbench-dataset-browser-phase`から切るStep 9専用branch（案: `fix/workbench-browser-interaction-state`）。Step 8の`06fa1e0`を含むことを確認する。`1 micro = 関連検証後1 commit`、Step末尾にphaseへ`--no-ff`で戻し、mainへは統合しない。最新ローカルworktreeがGitHub未同期であるため、GitHub上の古いbranchを基点に実装しない。

| micro | 変更・検証 |
| --- | --- |
| 9.1 | ホーム帰還時の同期的リセット、非同期応答破棄、URL/履歴の一致、loading終了/エラー/再試行。 |
| 9.2 | hoverは動画previewのみ、カード選択後にQA一覧、質問ブロック全体の操作と緑glow、原文/翻訳のイベント分離。 |
| 9.3 | 承認された4ボタン構成、QAクリック後の動作、タブ/カード/検索等の押下・選択・処理中フィードバック。 |
| 9.4 | fake UI/回帰、既存LongVideoBench状態の安全な確認、READMEとdocs/dataset-browser.mdの最新操作説明、ブラウザ実表示チェック。 |

受入は「hoverだけでは右QAが出ない」「カードclickで対応QAが出る」「QAブロックを狙って選択できる」「意図しないrun開始なし（A採用時）」「ホーム帰還で前動画と前QAが残らずロード完了/エラー表示へ遷移」「戻る・進む・連打時にも古い応答が侵入しない」「クリックした感覚が視覚的に明確」「ダークテーマ/中央広幅/4列維持」。LongVideoBench実動画の大量previewやGPU使用は引き続き別許可とし、ローカルphase→mainは**ユーザーが実画面を確認して明示承認するまで禁止**する。
