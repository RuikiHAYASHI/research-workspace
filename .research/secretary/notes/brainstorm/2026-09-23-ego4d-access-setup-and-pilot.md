---
date: 2026-09-23
project: agentic-streaming-videoqa
source_todo: null
topic: ego4d-access-setup-and-pilot
status: exploratory
tags: [brainstorm, research, ego4d, dataset, download, nas]
---

# Ego4Dアクセスキー取得後のセットアップ・pilot方針

## 出発点

Ego4Dライセンス承認後のAWS access ID / secret keyを受領した。大容量のfull_scale取得を開始する前に、認証、CLI、v2.1、保存先、manifest、少数動画の取得・再実行までを安全に確認したい。

関連:
- [UID・NASダウンロード運用](2026-09-18-ego4d-uid-nas-download-operations.md)
- [段階的ダウンロード方針](2026-09-18-ego4d-staged-download-strategy.md)

## 確認済みEvidence

- Ego4D公式Start Hereでは、承認後にAWS credentialsが発行され、アクセス資格は14日で期限切れになる。データはAWSから常時ストリーミング利用するのではなく、ローカル/共有ストレージへ取得する想定。
- 公式CLIは `pip install ego4d` で導入可能。
- 公式GitHub CLI READMEは、AWS CLIで `aws configure --profile ego4d` を実行し、Access Key ID / Secret Access Keyを入力、default regionは空欄にする手順を示す。
- 現行CLIは `--aws_profile_name`, `--version`, `--list-datasets`, `--video_uids`, `--video_uid_file` をサポートし、現行コードのdefault versionは `v2_1`。
- datasetごとにmanifest.csvを取得し、full_scaleでは各video metadataを保持する。
- CLIはダウンロード前にS3 object metadataを取得し、対象ファイルの合計容量を表示して確認を求める。確認画面で中止しても、その時点までにmetadata/manifestは保存される。
- 完了済み動画はversion/sizeチェックでスキップできるが、途中の1ファイルをバイト位置からresumeすることは保証されない。

## 推奨手順（未実行）

1. 実際にダウンロードするサーバー上でPython/AWS CLI/Ego4D CLIを確認。
2. `aws configure --profile ego4d` でnamed profileを作る。認証情報はGit・チャット・共有メモへ保存しない。
3. `ego4d --list-datasets --version v2_1 --aws_profile_name ego4d` で認証とv2.1アクセスを確認。
4. NASの最終保存先を確定し、書込権限・空き容量を確認。
5. まず `annotations` を取得し、`ego4d.json` とdataset manifestを得る。
6. `full_scale` を -y なしで起動し、容量見積りまで進めて確認プロンプトで中止する。これによりfull_scale manifestを先に確保する候補。
7. manifestから1〜3 UIDを選び、`--video_uids` または `--video_uid_file` でpilot取得。
8. 同じpilotを再実行し、取得済みスキップ、保存先、ログ、破損検出を確認。
9. pilot成功後にmanifestからUIDを自動抽出・重複除去し、件数または容量基準でbatchファイルを生成する。
10. full_scale → clips → 必要に応じて gaze / imu / video_540ss の順で拡大する。各datasetは1回のCLI実行につき1種類を基本とする。

## 認証情報とNAS運用

個人へ発行されたaccess keyを別人へ平文共有する運用は避ける。可能なら本人がNAS接続サーバーの自分のアカウントにprofileを設定して実行する。別の研究室メンバーが実行主体になる場合は、そのメンバー自身のライセンス/credential、または機関契約・サーバー運用ルールを確認する。

## 次に確認すること

- NASの実mount path / quota / 空き容量 / 書込権限
- サーバー上のPython・AWS CLI・ego4dバージョン
- access key受領日と失効予定
- `--list-datasets --version v2_1` の成功
- annotations取得とfull_scale manifest取得
- 1〜3動画pilotの再実行動作

このメモは探索段階であり、NAS上での実行、コード実装、TODO追加はまだ行っていない。

## 2026-09-23 追記：Windowsローカル/HDDでの1本pilot

### 制約更新

- ユーザー本人はNASへアクセスできない。
- まずWindows端末のローカルディスクまたは外付け/内蔵HDDへCanonical Videoを1本程度取得して、認証・CLI・保存・再実行を確認する。
- NAS本番取得は先輩側の環境で実施する可能性があり、先輩はMacBookを使用。

### Windows pilotの推奨順

1. Windows用AWS CLI v2を導入し、PowerShellで `aws --version` を確認。
2. `aws configure --profile ego4d` でcredentialを保存。Access Key / Secret KeyはGitやチャットへ貼らない。region/outputはEgo4D公式READMEどおり空欄でよい。
3. Python仮想環境を用意し `pip install ego4d`。PowerShellで `ego4d --help` を確認。
4. `ego4d --list-datasets --version v2_1 --aws_profile_name ego4d` で資格確認。
5. 保存先を例 `D:\ego4d_test` として作成。空き容量を確認。
6. `full_scale` をUID指定なし・`-y`なしで開始し、manifest取得と容量見積りまで進め、確認で `n` を入力して全量DLは止める。
7. `D:\ego4d_test\v2\full_scale\manifest.csv` の実列を確認し、1件の `video_uid` を選ぶ。
8. `--video_uids <UID>` で1本のみ取得。CLIの容量見積りがローカル空き容量に対して大きい場合は `n` で止め別UIDを試す。
9. 同じコマンドを再実行し、取得済みファイルがスキップされることを確認。
10. pilot成功後に、Mac/NAS側では同じEgo4D CLI引数を使い、OS差は主にAWS CLI導入方法と保存パスだけに限定する。

### 注意

- Windows PowerShellのパスは引用符で囲む。
- v2_1を指定しても現行CLIのdataset保存ディレクトリはmajor版の `v2` になる。
- アクセス資格の14日失効に注意。
- pilotだけならannotations約2GBを先に落とす必要はない。目的が「動画1本のアクセス確認」であればfull_scale manifest取得→1 UID取得で十分。

## 2026-09-23 追記：本番バッチ方式とBenchmark Clips

### バッチ方式の現在の方向性

- 50 UID固定分割は簡単だが、動画ごとの容量差によりバッチの所要時間が大きく揺れる。
- 本番候補は、manifestをSSOTとして全UIDを読み、S3 object metadataのcontent_lengthを取得して `size_bytes` inventoryを作り、合計容量が目標値に近くなるよう自動分割する方式。
- pilotで実測転送速度を得た後、例えば「6〜12時間程度で終わる容量」を1バッチ目標にする。容量ベースにすると再起動・監視の区切りが安定する。
- batch_000.txt等は人が編集せず、plannerが自動生成する。runnerは各batchを `--video_uid_file` で公式CLIへ順番に渡し、ログと完了状態を残す。
- 完了判定はプロセス終了だけでなく、CLIの既存ファイル検証・manifest.ver・ローカルファイルサイズ等を使う。失敗UIDだけ再投入できる構成を候補とする。
- バッチファイルを残す価値は、再実行、監査、残件把握、別OS（Windows/Mac）への引き継ぎが容易になる点にある。

### Benchmark Clipsの整理

- 公式の `clips` datasetは各benchmark向けに切り出されたCanonical Clipsで、full_scaleとは別ファイル。
- 研究室共通データとして既存benchmark再現も視野に入れるなら、`full_scale`に加えて`clips`と`annotations`を保存する候補は維持する。
- ただし `--benchmarks EM/FHO/...` でfull_scaleの一部を別途ダウンロードする必要はない。full_scale全量を取得するなら、そのbenchmark subsetは既に含まれる。
- 現在のStreaming VideoQA研究だけを最小コストで進める場合は、まずfull_scale＋必要annotationsで開始し、benchmark再現時にclipsを追加する段階取得も可能。

この項目も探索案であり、バッチツール実装・全量DL・clips全量DLの決定ではない。


## 2026-09-23 21:03 追記：Windows pilot → 容量ベースbatch → Mac/NAS本番の具体フロー

### フェーズA: Windowsでfull_scale manifest取得

- PowerShellではPATH問題を避けるため `python -m ego4d.cli.cli` 形式に統一する。
- `--version v2_1 --datasets full_scale` をUID未指定・`-y`なしで実行する。
- CLIがmanifestを保存し、S3 object metadataから全対象の容量見積りを出した時点で `n` を入力して全量downloadを止める。
- 現行CLIではv2_1指定時のdataset保存先は `<output>/v2/full_scale/` となる。

### フェーズB: 1動画pilot

- `manifest.csv` を読み、実際のUID列を確認して1件を選ぶ。
- `--video_uids <UID>` で1本だけ対象にし、CLIの事前容量見積りを確認して許容可能なら取得する。
- 取得前後の時刻と実ファイル容量から実測転送速度を算出する。
- 同じコマンドを再実行し、完了済みファイルが既存file/version/sizeチェックでスキップされることを確認する。
- pilotの結果として「平均MB/s」「1本の代表サイズ」「再実行挙動」を残す。

### フェーズC: 全UID inventory

- `full_scale/manifest.csv` をSSOTとして全video UIDを抽出し、重複除去する。
- benchmark単位には物理分割しない。同一canonical videoが複数benchmarkで使われる可能性があるため、video UID単位で一度だけ取得する。
- 各UIDのS3 object `content_length` を取得し、`video_uid,size_bytes` inventoryを生成する。
- 空UID fileをCLIへ渡さないことをrunner側で必須チェックにする。

### フェーズD: 容量ベースbatch

- 50 UID固定ではなく、pilotの実測速度と運用上の監視頻度からtarget GBを決める。
- 例: pilotが40 Mbps程度なら約18 GB/h。8時間batchを狙うならおよそ140 GBを目標にする。ただし実際の本番回線で再測定して決める。
- plannerはinventoryを読み、各batchの合計容量がtargetに近づくよう `batch_000.txt`, `batch_001.txt` ... を自動生成する。
- batch fileは1行1 UID、headerなし。人手編集を前提にしない。

### フェーズE: 公式CLIで順次取得

- 自作runnerは動画を直接HTTP/S3 downloadせず、各batchに対して公式CLIを `--video_uid_file` 付きで呼ぶ。
- datasetは1 CLI invocationにつき1種類を基本とする。
- batchごとに開始時刻、終了時刻、対象UID数、期待容量、exit status、ログを残す。
- 完了済み動画は公式CLIの既存file/version/sizeチェックに委ね、失敗UIDだけ再投入できるようにする。

### フェーズF: Mac/NAS本番

- Windows pilotで確立した引数はMacでも共通で、差分はPython/AWS CLI導入とoutput path。
- Mac/NAS上でまず1 batchだけcanary実行し、NAS書込権限・実測速度・既存file skipを再確認してから残batchへ進む。
- 本番のbatch target GBはWindowsの回線速度ではなくMac/NAS側canaryの実測値で再計算する。

### Benchmark Clips

- `full_scale`はcanonical video、`clips`はbenchmark用canonical clipで別dataset・別UID体系。
- full_scaleの物理管理はbenchmark別にせずvideo UIDで一意管理する。
- clipsは既存benchmark reproductionが必要になった段階で別途clip UID単位で取得する候補。
- 研究室共通archiveとしてはfull_scale + annotations + clipsを保持する価値があるが、現在のStreaming VideoQAの最小取得順はfull_scaleを優先し、clipsは後段でもよい。

このフローは運用設計の探索段階であり、planner/runnerのコード実装やMac/NAS本番実行はまだ未着手。


## 2026-09-23 追記：ローカルCodex開発と先輩へのhandoff方針

### 現在の方向性

- ユーザー本人はWindowsローカルでpilotと運用ツール開発を行う。
- downloader本体は公式Ego4D CLIに任せ、自作部分はmanifest処理、S3 size inventory、容量ベースbatch、runner、verification、run summaryに限定する。
- ローカルGit repositoryでCodexに実装・修正・テストを担当させ、変更履歴をGit commitとrun summaryで残す。
- 大容量動画、AWS credential、Secret Access Key、生のcredential fileはrepositoryへ入れない。
- raw download logは肥大化しやすいため原則gitignoreし、追跡対象にはrunごとの要約（日時、dataset、batch、UID数、予定容量、実容量、所要時間、成功/失敗UID、CLI/Python version等）を残す。
- Windowsでpilotとdry-run相当を通した後、先輩へrepositoryとREADMEを渡し、Mac/NAS側で小さいcanaryを再実行してから本番batchへ進む。
- Mac/NAS側ではoutput pathと環境導入だけを差し替え、batch generationとrunnerのインターフェースはWindowsと共通にする。

### サーバ権限について

- 現行AWS公式Linux installerはcurrent-user installをサポートし、既定では `$HOME/.local/share/aws-cli` と `$HOME/.local/bin` を使うため、sudoは必須ではない。
- ただし研究室サーバ側の外部通信、curl/unzip利用、PATH、software installation policyは別途確認が必要。
- NAS本番環境でuser-space installが可能なら、先輩側でAWS CLI / Python venv / ego4d CLIをユーザー領域へ導入する選択肢がある。

### handoff時にREADMEへ必要な項目

- supported OS / tested OS
- Python / ego4d CLI / AWS CLI versions
- credential setup（secret値そのものは含めない）
- manifest取得
- pilot
- inventory生成
- batch生成
- canary run
- full run
- rerun/resume時の挙動
- logs / run summaryの場所
- data directoryがgitignoreされていること
- 失敗時の再実行方法

この方針は探索段階であり、新規utility repositoryの作成・実装はまだ行っていない。


## 2026-09-23 追記：LinuxサーバとNASの配置方針

- 本番では「コードをNAS上に置く」必要はなく、Linuxサーバのユーザーhome等へutility repositoryをcloneし、Ego4D CLIのoutputだけNAS mount pathへ向ける構成を基本候補とする。
- 例: code = `~/ego4d-downloader`, data = `/mnt/nas/.../ego4d`。
- NAS上にrepositoryをcloneすることも技術的には可能だが、実行権限、ファイルI/O、共有領域の運用を考えるとcodeとdataを分離する方が単純。
- LinuxのAWS CLI v2はAWS公式install scriptでcurrent-user installが可能。現行公式手順は `curl -fsSL https://awscli.amazonaws.com/v2/install.sh | bash` で、既定では `$HOME/.local/share/aws-cli` と `$HOME/.local/bin` を使うためsudoは必須ではない。
- handoff READMEにはLinux/macOSのAWS CLI公式URLと最小コマンドを記載し、環境固有のNAS mount pathは先輩側で設定する。
- 本番credentialをrepositoryへ置かず、実行者のAWS profileを使う。個人credentialの平文共有は避ける。


## 2026-09-23 追記：Ego4D downloader utility repoをCodexへ実装委譲する方針

- ユーザーがLinuxサーバ上で新規utility repositoryを作成し、そのrepository内でCodexに実装を依頼する。
- Codexは実装前にresearch-workspaceの現行Company文脈、`.agents/skills/research-spec/SKILL.md`、`.agents/skills/engineering-task/SKILL.md`、agentic-streaming-videoqaのREADME、関連brainstorm/specを読む。
- 最初に新規repositoryの`specs/`へimplementation specを作成し、目的、scope、CLI、credential境界、log/run summary、Windows/Linux/macOS、local/server pilot、batch/inventory/verification、success criteriaを固定する。
- 既存Companyの実例に合わせ、Stepごとにbranchを作り、Step内のmicro stepは同じbranchへ個別commitする。Step末尾のtestが通る前に次branchへ進まない。
- commit本文の粒度・形式は既存specを調査して合わせる。branch名・commit数・タイミングをプロンプト側で固定せず、既存mdから運用を復元してspecへ明記する。
- 今回のCodex依頼ではbranch作成とscope内commitを明示許可するが、push/PRは別指示があるまで行わない。
- 実動画の大容量downloadは実装作業の一部として自動開始しない。短いmanifest取得、dry-run相当、1 UID canary/pilotなど、ユーザーがサーバ上で明示的に実行できるtest pathを整備する。
- AWS credential、Secret Access Key、credential file、動画本体、大容量raw logをGitへ含めない。


## 2026-09-24 追記：Ego4D downloader repository監査

対象:
- `RuikiHAYASHI/2026_09_hayashi_ego4d_downloader`
- GitHub上のmain: `99577c292da2af4e68f9a8a3f8b867de20d1f8f7`
- GitHub default branch: `feat/step-06-local-pilot-docs` (`5fa7fa567bcdd040f265b540c35f33ab2da327c1`)

### 確認済み事実

- repositoryのdefault branchがmainではなく`feat/step-06-local-pilot-docs`になっている。
- mainはそのfeature branchをmergeした後、Linux setup README commitを追加しており、default branchより2 commit先にいる。
- approved spec `specs/2026-09-23-ego4d-v2-1-downloader-implementation-spec.md` は初期scopeをfull_scaleのみとし、clips、動画/annotation download等を対象外としている。
- commit `5fa7fa5` で、clips、annotations、visualization、features、narrations向けの機能が一括追加され、7 fileが大きく変更された。test fileはこのcommitで変更されていない。
- 現在の `ego4d_downloader/cli.py` は `from .direct import DIRECT_DATASET_PRESETS, fetch_narrations, run_direct_download` をimportする。
- mainおよびdefault branchの`ego4d_downloader/`一覧には`direct.py`が存在しない。したがって現在のpackage entrypointはimport時に失敗する可能性が高い。
- READMEは`features` presetが複数feature datasetをまとめて取得すると記載するが、その実装元となる`direct.py`はGitHub上で確認できない。
- 初期specでは容量ベースbatchが主要契約だったが、最新NAS helperの既定経路は50 UID固定batchへ変更されている。容量ベース実装自体は残っているがhandoffの主経路ではない。
- latest expansion commitは既存の「1 Step = 1 branch / 1 micro Step = 1 commit / Step末尾test」運用と整合していない。

### 解釈

現在の主問題は機能数ではなく、Authorityとintegrationの崩れである。full_scale-only approved specの外側へ複数dataset機能を一括追加したため、実装契約、test coverage、README、Git branch状態が同期していない。

### 復旧候補

1. default branchをmainへ戻し、clone/通常閲覧の正本を明確にする。
2. 実downloadを一旦停止し、mainで`python -m ego4d_downloader --help`とunit testを確認する。
3. 欠落している`direct.py`について、local-only未commitなのか、誤ってcommit漏れしたのかをサーバworktreeで確認する。
4. clips/direct datasets/narrations/fixed-count batchを新しいspecまたはaddendumへ昇格し、現在のapproved specとの差分を明示する。
5. 新scopeをStep単位へ分解し、direct datasetごとのofficial CLI契約とtestを追加してから再実装する。
6. featuresは複数datasetを一括でofficial CLIへ渡さず、現行Ego4D CLIのdataset一覧とmulti-dataset挙動を確認した上で、必要ならdatasetごとに1 invocationへ分ける。
7. full_scale/clipsの物理downloadはUID単位管理を維持し、capacity-basedとfixed-countのどちらを本番正本にするかをspecで再決定する。

この監査ではdownloader repository自体へのcode変更、branch変更、default branch変更、download実行は行っていない。


## 2026-09-24 22:18 追記：video経路を凍結し、残datasetを公式CLIで独立取得する方針

### 現在確認できている状態

- ユーザーの実サーバ環境ではannotationsの実ファイル一式が `v2/annotations/` に存在する。
- ユーザー申告によりclipsも取得済みであることを確認済みとして扱う。
- `.ego4d-downloader/` にはfull_scale / clipsのUID batch、manifest、run log、report、stateが生成済みであり、video系の運用経路は既に独立した作業単位として成立している。
- 貼付treeでは `v2/viz/` はdirectoryのみでfileが見えないため、visualizationの取得完了は別途確認が必要。

### 公式CLI上の重要な境界

- `--video_uids` / `--video_uid_file` はofficial CLIのvideo dataset向けfilterである。
- official CLI sourceは、要求datasetがすべてnon-videoの場合、video_uids指定はignoredと明示する。
- 現行`DATASETS_VIDEO`は `full_scale`, `clips`, `components/videos`, `video_540ss`。
- よってfeatures、annotations、viz、imu、gaze、3d等を既存UID textで直接filterする設計にはしない。
- 今回の目的が「取得可能なものをできるだけ保存」であるため、non-video datasetはdataset全体をofficial CLIで1 datasetずつ取得する方が単純で安全。

### 推奨する二経路

1. Video queue:
   - full_scale / clips（必要なら後でvideo_540ss）
   - 既存のUID batch runnerを維持する。
   - 既存batchを変更せずrerunする。

2. Dataset queue:
   - non-video dataset名を1行1datasetでtextへ列挙する。
   - 各datasetについて `python -m ego4d.cli.cli --datasets <dataset>` を1 invocationずつ実行する。
   - multi-dataset 1 invocationは避ける。現行official CLIではdataset loop後のversion bookkeepingが最後のdatasetの値を再利用する実装になっているため、dataset単位実行を安全側とする。
   - datasetごとにlog / success markerを残し、失敗時は同じofficial commandをrerunする。

### features

- official docsで現行featureとしてSlowFast、Omnivore video、Omnivore image、Omnivore video FP16が案内されている。
- featuresはcanonical videoから抽出されたprecomputed featuresであり、raw `components/videos`を保存していなくても利用できる。
- corrected current featuresを優先し、`*_deprecated`系は取得不要。
- UID filterはofficial CLIではnon-video datasetに効かないため、全取得目的ならfeature datasetごとに丸ごと取得する。
- subsetだけ必要になった場合はmanifest subset + `--manifest-override-path`の検討余地はあるが、今回のfull archive目的では不要。

### components/videosを取らない場合の整理

- `components/videos`約20TBはraw/unprocessed系の元video componentsであり、canonical `full_scale`、clips、annotations、featuresを使うための必須依存ではない。
- raw video componentsを保存しないことで失う主な能力は、元camera componentから独自に再処理・再エンコードする経路。
- processed IMU / gaze、3D annotations/scans、features等はraw video componentsがなくても独立取得候補。
- raw componentsのうち `components/imu`, `components/gaze`, `components/binaural_audio`, `components/burned_in_gaze`, `components/3rd_person_video` は`components/videos`とは別datasetとして公式docsにある。archive目的なら容量と必要性を見て追加可能。
- full annotations取得済みなのでNarrations Onlyを別途取得する必要はない（既に`narration.json`等が存在）。
- `video_540ss`はfull_scaleのdownscaled derivativeなので、full_scaleを保存するならsemantic contentとしては重複が大きい。特定baselineが540ssを要求しない限り優先度は低い。
- `annotations_540ss`は公式forumで別downloadをhostしない旨が案内されており、必要ならtransform notebook経由。
- visualizationは研究入力として必須ではないが約500MBなのでarchive目的なら取得候補。

### 次の実装候補

既存video codeを変更せず、独立した`dataset queue runner`を追加する。最初にofficial `--list-datasets --version v2_1`結果を保存し、そのavailable dataset名をSSOTとして、exclude listに`components/videos`、deprecated feature、既取得annotations/clipsを置く。各datasetは必ず1 invocationで実行し、実行前size estimate、log、success/failureをdataset単位で保存する。


## 2026-09-24 追記：Ego4D archive取得対象の現在判断

Notion「Ego4D ダウンロード手順」に、公式Start Here / CLI / Features / Unprocessed Data / Videos / Gaze / IMU、および現行 `facebookresearch/Ego4d@main` の `config.py` を突合した取得対象表を追記した。

現在の判断:
- 取得済み: `annotations`, `clips`, `ego4d.json`。
- 取得する: `full_scale`, `viz`, processed `imu` / `gaze`, 3D系、現行precomputed features、EgoTracks / PACO / benchmark artifacts / model checkpointsのうちv2.1で利用可能なもの。
- raw auxiliary componentsも、`components/imu`, `components/gaze`, `components/binaural_audio`, `components/burned_in_gaze`, `components/3rd_person_video` は容量に余裕がある限り取得する。
- 取得しない: `components/videos`（約20TB）、540ss系の重複派生物、deprecated feature、annotations取得済みのためNarrations Onlyの別取得。
- video UID filterはofficial CLIのvideo dataset（`full_scale`, `clips`, `components/videos`, `video_540ss`）向け。non-video datasetはdataset単位で1 invocationずつ取得する。
- `components/videos`を保存しなくても、processed IMU/gaze、precomputed features、3D、model checkpointsは独立して利用可能。raw IMU/gazeはraw video componentsなしだと利用価値が相対的に下がるが、archive候補としては残す。

実サーバtreeから、`full_scale`はmanifestのみ、`viz`はdirectoryのみで実file完了未確認と扱う。clipsはユーザー側で取得済み確認済み。


## 2026-09-24 23:31 追記：研究室共通Ego4D datasetの保存範囲を簡略化

Notion「Ego4D ダウンロード手順」に英語dataset名の日本語説明と、保存範囲をLevel分けした判断表を追記した。

現在の推奨正本:
- Level 1（中核）: ego4d.json, annotations, full_scale, clips, viz。保存する。
- Level 2（追加の実測sensor）: imu, gaze。保存する。
- Level 3（特定task専用）: 3d系, EgoTracks, PACO, fut_loc, social_test等。現在は保存しない。
- Level 4（precomputed features）: SlowFast / Omnivore系。現在は保存しない。特定baseline再現時に取得する。
- Level 5（model/checkpoint・推論結果）: av_models, lta_models, sta_models, vq2d_models, moments_models, nlq_models, vq2d_detections等。dataset本体ではないため保存しない。
- Level 6（raw components）: components/videosを含むraw component群。基本保存しない。processed canonical dataを優先する。
- 540ss系、deprecated features、Narrations Onlyは重複・旧版のため保存しない。

理由:
- Ego4D公式はCanonical Videoを主要な利用形態として位置づけている。
- IMUはcanonical video timestampsへ正規化されたprocessed CSV、gazeもprocessed CSVが提供され、raw componentsなしでも利用できる。
- precomputed featuresはcanonical videosから既存modelで抽出した派生物で、元データではない。
- raw dataは公式docsでも通常利用には推奨されず、特殊用途向け。

この整理により、研究室共通datasetの最終候補は ego4d.json + annotations + clips + full_scale + viz + imu + gaze とする。
