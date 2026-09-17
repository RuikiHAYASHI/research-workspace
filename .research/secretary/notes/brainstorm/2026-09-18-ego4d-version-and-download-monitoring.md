---
date: 2026-09-18
project: agentic-streaming-videoqa
source_todo: null
topic: ego4d-version-and-download-monitoring
status: exploratory
tags: [brainstorm, ego4d, dataset-version, download-operations]
---

# Ego4Dのリリース版と低負担なダウンロード監視

## 問い

ユーザーはv1/v2/v2_1の違いと、UIDを手動指定せず適度な頻度で状況を確認できるNASでのダウンロード方式を知りたい。研究室共同利用、Canonical Video＋Clip＋Annotationsを検討。Notionの更新は不要。NASでの実行・コード実装は未依頼で未実施。

## 確認済みEvidence

- [公式更新履歴](https://ego4d-data.org/docs/updates/)：v2はFHOやNLQの注釈拡充（NLQ 17.3k→27k）、誤動画除外・注釈修正、PACO/EgoTracksなど。v2.1はGoal-Step注釈と、従来分割されていた210動画に関係するGrouped Videoを追加。バージョンはデータセットリリース／manifest・注釈の選択であり、動画の解像度種別やソフトウェア版とは異なる。
- [CLI config.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/config.py)：`VERSION_DEFAULT = 'v2_1'`。出力先の`out_version_dir`は`version.split('_')[0]`であり`v2_1`でも`v2`ディレクトリ。`--video_uid_file`、`--benchmarks`、`--datasets`をサポート。異なるv2/v2_1を同じoutput_directoryに混ぜない運用を推奨。
- [manifest.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/manifest.py)：manifestとmetadataの取得元S3キーに完全なバージョン文字列を利用する。`ego4d.json`はoutput_directory直下、datasetファイルはoutput_directory/v2/dataset/。
- [download.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/download.py)：取得済みファイルはS3 version_idとサイズ・`manifest.ver`により照合してスキップ。versionファイルは成功ダウンロード時に約15秒間隔で保存を試み、処理最後にも保存。ただし処理中の単一ファイルは再取得時削除して先頭から取得する。完全なバイト位置resume機能は確認できない。ダウンロードは内部スレッドプール8本。S3アクセス不可・ファイル破損はログを残すが終了コードだけでは完全な成功は証明できない。
- [cli.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/cli.py)：UID指定なしの`--datasets full_scale`で対象全動画を取得し、事前にファイルごとのS3 content_lengthを問い合わせ合計サイズを表示。確認後に実行。同一 dataset に限定することで現行コードの複数dataset管理変数使い回しへの懸念を回避する（後者は静的コード読解による懸念、NASで未検証）。
- [公式CLI説明](https://ego4d-data.org/docs/CLI/)の一部はv1や過去の容量を例示しており現行config.pyと差がある。実行するCLIの`ego4d --help`、リリースmanifest、`--list-datasets`で最終確認する。

## 方針候補の比較

A. **最も単純**：`tmux`でCLIの`--datasets full_scale --version v2_1`をUID指定なしで1 datasetずつ実行し、標準出力をログに残す。6〜12時間ごとに`tail`・完了済みUID/ファイル数・空き容量を確認。SSH切断には強いがNAS自体の停止時はジョブ再起動が必要。同一コマンド・出力先で再実行すれば正常にversion管理されている完了済みファイルはスキップ、途中ファイルは先頭から再取得。全件S3存在チェックや既存検査に時間がかかる可能性がある。大規模な全件実行前にpilotを推奨。

B. **推奨する堅牢な共同利用**：一度だけmanifestから全video_uidを自動抽出し、固定件数（まず数十本）で`split`する簡単なプランナーを用意。先輩は`for`ループでバッチを順次CLI実行し、各バッチ後にログ/ファイルサイズ照合して進捗保存・失敗UIDを次回対象とする。UIDを手書きする必要はない。サイズ別分割はHEAD結果でsize_bytesが取得できる場合に改善。件数は所要時間を保証しないためpilot後に調整。

C. タスク別`--benchmarks`だけで数日分をまとめて取得：UID手動指定不要だが各タスクの容量偏差・重複・非benchmark動画の取りこぼしと実行時間が大きい。共同基盤の全量収集向けにはA/Bの進捗管理を要する。

## 実行提案（未実行）

```bash
tmux new -s ego4d
mkdir -p /nas/ego4d/ops/logs
set -o pipefail
ego4d --version v2_1 --datasets full_scale --output_directory /nas/ego4d/releases/v2_1 --aws_profile_name ego4d 2>&1 | tee -a /nas/ego4d/ops/logs/full_scale.log
```

NASパスは説明用の仮置き、プロフィール名も先輩の実環境に合わせる。`--yes`なしならダウンロード前のサイズ見積りと確認が出る。別セッションから`tmux attach -t ego4d`や`tail -n 50 -f ...log`、`df -h`等で確認。`tmux`はNAS/サーバ再起動を乗り越えない。メタデータ・manifestを先に保管し、初回1〜3本を使って再実行・検証・実際の速度を測る。

## 研究上の判断・未決

- シンプルなAで開始するか、作業完了の区切りと失敗時の復旧単位を明確にしたBにするか。共同利用と数TB運用ではBが有力だが、最小工数ならAで始められる。
- NASのパス/容量/権限、シャットダウンポリシー、実回線速度、AWS認証期限・許諾は未確認。実際のmanifestとバージョン差分も現地未検証。
- バッチ単位を動画件数・サイズ・目標時間のどれにするかはpilotの実測で調整する。分割しなくても6〜12時間のログ確認は可能だが、区切り完了を記録するなら分割方式が便利。
- これは探索記録であり実装指示・大規模ダウンロード承認ではない。TODO/spec/コードは更新しない。
