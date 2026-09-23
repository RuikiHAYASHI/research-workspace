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
