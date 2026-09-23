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
