---
date: 2026-09-18
project: agentic-streaming-videoqa
source_todo: null
topic: ego4d-uid-nas-download-operations
status: exploratory
tags: [brainstorm, research, ego4d, data-management, nas]
---

# Ego4D UID・容量管理とNASダウンロード運用の壁打ち

記録時刻: 2026-09-18 02:15 JST頃。関連する先行壁打ち: [段階的ダウンロード方針](2026-09-18-ego4d-staged-download-strategy.md)。ユーザーはNotionの更新を求めておらず、NAS上での実行もまだ依頼していない。

## 相談の出発点・中心の問い

- 研究室の共同利用を前提に、重複を避けて動画 UID で取得対象を管理したい。
- annotations を取得した段階で UID と動画ファイル容量が分かるか。
- NAS上のディレクトリをどう構成するか。
- NASアクセス権のある先輩に実行を任せ、自分でUID仕分けスクリプトを準備する分業がよいか。

## 確認済み Evidence

- [公式Metadata](https://ego4d-data.org/docs/data/metadata/) の`ego4d.json`スキーマは`video_uid`、`duration_sec`、`scenarios`、解像度/FPS、`s3_path`、`has_gaze`、`has_imu`、clipと親動画の対応等を記載。ファイルのバイト数の標準フィールドは示されていない。
- [公式CLI](https://ego4d-data.org/docs/CLI/) はdatasetごとに `manifest.csv` があると説明するが、size列の存在は文書から一律保証できない。現行[manifest.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/manifest.py)は`file_uid`/`video_uid`、`canonical_s3_location`/`s3_path`、benchmarksを用いる。UID一覧の正本は対象datasetのmanifestにする。UIDはclipならclip UID、full_scaleならvideo UIDなどデータ種別ごとに意味が異なる。
- 現行[cli.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/cli.py)はS3オブジェクトの`content_length`をダウンロード前に取得し、選択済みファイルの容量合計を表示して確認させる。容量別バッチ計画は、manifestにsizeがなければ権限を有する環境でS3オブジェクトメタデータ（HeadObject等）からsize_bytesを取得・保存する必要がある。CLI自体の確認画面でも各バッチの見積りが可能。現在NAS/AWSで実サイズの取得実績はない。
- 現行[config.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/config.py)は`--video_uid_file`、`--datasets`、`--version`をサポート。初期版は`v2_1`、出力ディレクトリ名はmajor版`v2`。現行[cli.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/cli.py)はmaster metadataを`output_directory/ego4d.json`に、各datasetを`output_directory/v2/<dataset>/`へ保存する。
- 現行[download.py](https://github.com/facebookresearch/Ego4d/blob/main/ego4d/cli/download.py)は既存ファイルのS3バージョンとサイズを確認してスキップするが、再取得対象では旧ファイルを削除して丸ごとダウンロード。断片的ダウンロードのバイト単位resumeは保証しない。manifest.verによる既存管理あり。
- 現行cli.pyは複数datasetを一回で要求した場合にも`version_entries`と`download_path`変数を最後のdatasetのものとして全体処理に渡す構造に見える。潜在的な整合性リスクがあるので運用提案として1回のCLI実行で1 datasetに限定する（未検証のコードリスクとして扱う）。CLIは破損をログ表示しても失敗終了コードを保証しないためログだけでなくmanifest対照とsize検証が必要。

## 比較した運用案

A. 先輩がすべて手動ダウンロード：着手は早いが、UID重複・容量見積り・進捗追跡・復旧が属人的になる。

B. ユーザーがS3 downloaderを自作：制御自由度はあるが、リトライ、認証、整合性確認、アップデート追従など保守範囲が広がる。

C. **候補**：ユーザーがメタデータとmanifestからUIDとバッチ計画を生成し、先輩が認証済みNAS環境で公式CLIを実行、取得後にmanifest・S3サイズ・破損チェックに照らして結果をCSV/JSONへ保存。先輩は初回にNASマウント・権限・認証・少数サンプルを確認。コード実装は本会話では未着手・未承認。

## ディレクトリ構成の探索案

実NASパス・容量・ACLは未確認。下記は例であり、データルートを`<NAS_ROOT>/ego4d/v2_1`としてCLIへ渡す。CLIにより `v2_1/v2/<dataset>/`が作られ、`ego4d.json`は`v2_1/ego4d.json`に置かれる。リリース違いを混在させない。

```
<NAS_ROOT>/ego4d/
  v2_1/                              # CLI --output_directory
    ego4d.json                       # CLIが保存
    v2/
      full_scale/                    # video_uid.mp4, manifest.csv, manifest.ver
      clips/                         # clip_uid.mp4 ...
      annotations/
      gaze/
      imu/
      video_540ss/                   # 任意
  ops/
    manifests/                       # リリース固定コピー・取得日時/sha等
    inventory/                       # UID, dataset, S3 path, bytes, status, benchmarkタグ等
    batches/full_scale/             # batch_000.txt etc（UIDのみ）
    batches/clips/
    logs/
    reports/
    README.md
```

同じvideo_uidが複数benchmarksに属しても、物理ファイルはdataset別に1つ、タスクラベルはinventory上で多対多管理。clip_uidとvideo_uidは混ぜない。`manifest.csv`と`manifest.ver`はCLI管理ファイルとして退避・上書き・移動しない。`ops`は研究室の書き込みACLに合わせて別領域に置く代案もある。

## 候補となる最小コード境界

1. Planner：`ego4d.json`＋各datasetのmanifestを入力、UIDの重複/対応/unknownを照合。file size列が存在すれば使い、なければsize_bytesを未取得と記録。サイズを推定だけで確定しない。
2. Size inventory：AWS閲覧権限のある先輩がS3 object metadataを用いてcontent_lengthを取得、UIDとサイズの表だけ返す。認証鍵をGitや共有ファイルに含めない。サイズ取得不可なら件数ベースの小分けで初回pilot、その後はCLIが表示する見積りを活用。
3. Batch planner：datasetごとに容量上限で分割し `batch_###.txt` と計画CSVを書き出す。ログや進捗CSVの検証と全UIDの集合一致（漏れ/重複なし）を行う。
4. Runner：先輩が公式`ego4d --version v2_1 --datasets full_scale --video_uid_file ... --output_directory ... --aws_profile_name ego4d`をdataset別・バッチ別に実行。tmux/systemdなどは現地運用とNASポリシーに合わせる。同一dataset/出力先に同時複数プロセスを起動しない。
5. Verifier：ダウンロード終了コードだけを信じずファイル存在、期待S3 bytes、成功率、失敗UIDを出力し再実行可能にする。`--bypass-existing`や`--skip-s3-checks`を常用しない。シンボリックリンクやファイルの勝手な移動で公式CLIのディレクトリ契約を壊さない。

## 未確認点・MTGで判断すること

- NASの実mount path、容量とreserve、quota、書込権限、長時間ジョブ許可、再起動条件、認証主体・Ego4Dライセンス上の共有可否。
- v2_1の実manifestの列名とsize列の有無、S3 HEADのアクセス、想定バッチ容量、並列度、件数、回線速度。
- full_scale＋clips全量取得か、一部の追加sensorも保存するか。実S3容量が未取得なので容量・所要時間は未確定。
- 初回1〜3本で版・ディレクトリ・resume・ログ・検証のpilotを行い、問題なければ拡大する案を相談する。

## 今回の現在地

- UID管理／自作planner＋公式CLI executorは最有力の相談案。保存構成は提案でありNAS環境では未確認・未承認。実装・ジョブ起動・NAS上での変更はしていない。
- 次の作業候補：計画ツールのread-onlyな入力／出力仕様を先輩と合意した後、研究実装のGateを通してコード化する。TODO・spec・研究コード変更はしていない。
