---
date: 2026-09-25
project: agentic-streaming-videoqa
status: implemented
topic: sequential-loader-target-frame-stream-and-layout
source: 2026-09-25-longvideobench-performance-and-aggregation-brainstorm
related_specs:
  - 2026-09-25-sequential-loader-workbench-refactor-implementation-spec.md
last_updated: 2026-09-25
implemented: 2026-09-25
---

# sequential_loader（連続動画ローダー）: 対象frame（フレーム）専用ストリームとディレクトリ構造の仕様

## 0. この仕様の状態

この文書は `draft`（下書き）である。実装、branch（作業枝）の作成、commit（変更記録）の作成、push（リモート反映）、評価run（実験実行）は許可しない。実装着手には、この文書を `approved`（承認済み）へ更新する明示承認が必要である。

## 1. 表記規約

- 本文中の英語用語は、初出に限らず、単独で表記するたびに直後へ `（日本語訳または説明）` を付ける。例: branch（作業枝）、commit（変更記録）、API（公開呼出し口）、target-only（対象frame専用）。
- コードブロック内の識別子、ファイルパス、設定キーは、実装時の正確性のため原表記を維持する。その意味は、直前または直後の本文で必ず説明する。
- `frame`（動画の一枚の画像）、`RGB`（赤・緑・青の画素形式）、`PTS`（表示時刻を表すタイムスタンプ）も本仕様では上記規約の対象とする。

## 2. 背景と問題定義

現行の `SequentialVideoReader`（連続動画読取器）は、デコードした各frame（フレーム）に対し `frame.to_ndarray("rgb24")`（RGB配列への変換）を行い、`torch.Tensor`（PyTorchの多次元配列）へ積み、`SequentialSample`（連続チャンク標本）として返す。600秒・32frame（フレーム）の時間格子サンプリングでは、最終的に使う32frame（フレーム）に対して、25fps（毎秒25frame）動画なら最大約15,000frame（フレーム）をRGB化する可能性がある。

一方で、既存の連続読取は時間順、前方のみ、欠損なしという契約を持つ。その契約を満たす `SequentialSample`（連続チャンク標本）に、飛び飛びの対象frame（フレーム）だけを詰めて返すことは、既存利用者に誤解を与える。このため、新機能は既存型を流用せず、別の公開ストリームとして追加する。

## 3. 目的

1. 動画を先頭から順方向にデコードし続けながら、採用された対象frame（フレーム）だけをRGB（赤・緑・青）配列へ変換する。
2. 既存の公開経路 `import sequential_loader as sl`（公開窓口からの読み込み）と、既存の全RGB（赤・緑・青）連続読取の挙動を変更しない。
3. 新旧の経路を明確に分離し、今後の拡張に耐えるパッケージ構造へ段階的に整理する。
4. 時刻単調性、資源解放、対象frame（フレーム）数、不要なRGB化の不在を自動テストで保証する。

## 4. 非目標

- `SequentialDataset`（連続データセット）を対象frame（フレーム）専用モードへ改造しない。
- ランダムseek（任意位置へのジャンプ）、逆向きデコード、複数動画の同時読取を追加しない。
- 映像の全frame（フレーム）を保存したキャッシュを追加しない。
- Workbench（ブラウザ実行環境）側のプロンプト、情報集約、画面表示の変更は、本仕様では扱わない。これらは関連する別仕様で扱う。
- 性能向上率を事前に主張しない。性能は実装後に同一動画・同一条件で測定する。

## 5. 現在の互換性基準

調査時点の連続動画ローダーリポジトリは `/mnt/HDD18TB/hayashi/sequential_loader`（連続動画ローダーのリポジトリ）である。基準branch（作業枝）は `feat/longvideobench-source-adapter`（LongVideoBench接続用の作業枝）、基準commit（変更記録）は `e44efbf`（LongVideoBench接続部を公開APIへ追加した変更記録）である。

次の既存公開要素は、名前、引数、戻り値、例外の意味を維持する。

- `sequential_loader`（連続動画ローダー）の公開窓口
- `SequentialVideoReader`（連続動画読取器）
- `SequentialDataset`（連続データセット）
- `SequentialSample`（連続チャンク標本）
- `build_frame_sampler`（frameサンプラー構築器）
- `build_single_video_frame_dataset`（単一動画frameデータセット構築器）
- `build_longvideobench_frame_dataset`（LongVideoBench用frameデータセット構築器）

既存の `src.*`（内部実装の名前空間）直接参照は公開契約ではない。ただし、リポジトリ内テスト、開発補助コード、文書を更新して、移動後に古い内部パスが残らないことを確認する。

## 6. 新しい公開契約

### 6.1 時間格子方針

`TimeGridSamplingPolicy`（時間格子サンプリング方針）を公開する。これは動画全体の長さを既知として、連続する時間window（時間窓）ごとに等間隔の目標時刻を生成する不変の設定値である。

```python
policy = sl.TimeGridSamplingPolicy(
    duration_seconds=1995.88,
    window_seconds=600.0,
    frames_per_window=32,
)
```

上記の `TimeGridSamplingPolicy`（時間格子サンプリング方針）は、長さ1,995.88秒の動画を600秒ずつの時間窓に分け、各窓で32個の目標時刻を作る例である。

検証規則は次のとおりとする。

- `duration_seconds`（動画長）は有限かつ0より大きい。
- `window_seconds`（時間窓長）は有限かつ0より大きい。
- `frames_per_window`（窓あたりframe数）は1以上の整数である。
- 最終窓は動画末尾までの短い窓として残す。切り捨てない。
- 窓内の目標時刻は、窓の開始を含み、終了を含まない等間隔点とする。最終窓でも実際の窓長を用いる。
- 目標時刻は動画範囲へ丸め、全体として非減少にする。

### 6.2 対象frame（フレーム）専用ストリーム

`target_frame_stream`（対象frame専用ストリーム）を公開する。入力動画を先頭から一度だけ読み、目標時刻を最初に満たす表示frame（フレーム）のみRGB（赤・緑・青）化して、窓単位で返す。

```python
with sl.target_frame_stream(source=source, policy=policy) as windows:
    for window in windows:
        consume(window)
```

ここで `source`（動画ソース）は既存の動画ソース情報、`windows`（窓列）は時間順の `SampledWindow`（採用済み窓）列、`consume`（利用処理）は呼出し側の処理を表す。

選択規則は既存の `time_grid_first_after_target`（各目標時刻以降で最初のframeを選ぶ規則）と同一にする。すなわち、各目標時刻に対し、`PTS`（表示時刻）がその目標以上となる最初のデコード済みframe（フレーム）を採用する。これにより、既存の時間格子選択と新モードの選択結果を比較可能にする。

### 6.3 戻り値の型

`SampledFrame`（採用済みframe）には最低限、以下を持たせる。

| 項目 | 意味 |
| --- | --- |
| `image_rgb`（RGB画像） | `numpy.ndarray`（NumPy配列）、形状 `[H, W, 3]`、`uint8`（8ビット符号なし整数）。採用frameだけが持つ。 |
| `frame_index`（frame番号） | デコーダーが報告する元動画内の順序番号。取得不能なコンテナでは `None`（未取得）を許容する。 |
| `timestamp_seconds`（実際の表示時刻） | 採用frameの `PTS`（表示時刻）を秒へ正規化した値。 |
| `target_timestamp_seconds`（目標時刻） | このframeを採用させた時間格子上の目標時刻。 |

`SampledWindow`（採用済み窓）には `window_index`（窓番号）、`start_seconds`（開始秒）、`end_seconds`（終了秒）、`target_timestamps_seconds`（目標時刻列）、`frames`（採用frame列）を持たせる。

1つのデコードframe（フレーム）が複数の等しい目標時刻を満たす場合、出力は目標時刻ごとに `SampledFrame`（採用済みframe）を返してよい。この場合もRGB（赤・緑・青）変換は元frameごとに最大一度とし、未採用frame（フレーム）をRGB化してはならない。

`target_frame_stream`（対象frame専用ストリーム）は、`SequentialSample`（連続チャンク標本）を返してはならない。連続性がないことを型名と文書で明示する。

### 6.4 資源と異常の契約

- 動画reader（読取器）はストリーム生成ごとに一度だけ開く。
- 正常終了、利用者側の早期終了、デコード例外、検証例外のすべてでreader（読取器）を閉じる。
- `PTS`（表示時刻）が減少した場合は、時刻の並びを推測して続行せず、動画識別子と直前・現在時刻を含む例外で停止する。
- 終端までに満たせない目標時刻があれば、満たせた目標時刻と未達目標時刻を明示する例外で停止する。短い最終窓を黙って捨てない。

## 7. デコード処理の設計

新モードは次の順序を守る。

1. `TimeGridSamplingPolicy`（時間格子サンプリング方針）から全窓の目標時刻を生成する。
2. PyAV（動画入出力ライブラリ）で動画を先頭から一回だけデコードする。
3. 各デコードframe（フレーム）では、RGB（赤・緑・青）配列化より先に `PTS`（表示時刻）だけを確認する。
4. そのframe（フレーム）が次の未充足目標を満たす時だけ、`to_ndarray("rgb24")`（RGB配列化）を呼ぶ。
5. 採用frame（フレーム）のメタデータと画像を該当窓へ追加し、全目標を満たしたらデコードを終了する。

これにより、デコードの前進自体は維持しつつ、RGB（赤・緑・青）化、配列確保、PyTorch変換、全frame（フレーム）のstack（積層）を対象frame（フレーム）に限定する。新モードでは `torch.Tensor`（PyTorchの多次元配列）、`DataLoader`（バッチ読取器）、連続チャンクのpadding（不足部分の埋め合わせ）を使わない。

## 8. ディレクトリ構造の目標

公開パッケージを標準的な `src`（ソース配置）形式へ寄せる。最終形の責務は次のとおりとする。

```text
src/sequential_loader/
├── __init__.py                 # 公開窓口
├── adapters/                   # 外部データセット接続
├── core/                       # 共通の型、検証、例外
├── decode/                     # PyAV読取と時刻正規化
├── streams/                    # 全RGB連続経路と対象frame専用経路
├── policies/                   # サンプリング方針
└── legacy/                     # 互換維持する既存実装
```

上記の英語ディレクトリ名は順に、公開窓口、外部データセット接続、共通基盤、デコード、ストリーム、方針、既存互換実装を表す。公開利用者は常に `sequential_loader`（連続動画ローダー）だけを読み込む。

## 9. 実装を承認後に行う段階

各Step（主要段階）は専用branch（作業枝）で行う。次のStep（主要段階）のbranch（作業枝）は、直前Step（主要段階）の全micro step（小段階）が検証済みである最終commit（変更記録）から作成する。各micro step（小段階）は、表に記した検証が通った直後に、表に記した一つのcommit（変更記録）だけを作成する。未検証の複数micro step（小段階）を一つのcommit（変更記録）へまとめてはならない。

### Step A1（主要段階）: 型と選択規則を追加する

branch（作業枝）は `feat/target-frame-core`（対象frame中核の作業枝）とする。基点は `e44efbf`（LongVideoBench接続部を公開APIへ追加した変更記録）である。全RGB（赤・緑・青）連続経路は変更しない。

| micro step（小段階） | 変更内容 | commit（変更記録）の題名 | commit（変更記録）前の検証 |
| --- | --- | --- | --- |
| A1.1 | `TimeGridSamplingPolicy`（時間格子サンプリング方針）、`SampledFrame`（採用済みframe）、`SampledWindow`（採用済み窓）と、入力値・短い最終窓の検証を追加する。 | `時間格子方針と採用frame型を追加` | 方針の境界値、最終窓、型の単体テスト |
| A1.2 | `PTS`（表示時刻）に基づく最初の採用規則を実装し、時刻逆行と終端未達の例外を追加する。 | `対象frameの時刻選択を追加` | 合成動画での選択時刻一致、時刻逆行、終端未達の単体テスト |

### Step A2（主要段階）: 対象frame（フレーム）専用ストリームを追加する

branch（作業枝）は `feat/target-frame-stream`（対象frameストリームの作業枝）とする。基点はStep A1（主要段階）の最終commit（変更記録）である。

| micro step（小段階） | 変更内容 | commit（変更記録）の題名 | commit（変更記録）前の検証 |
| --- | --- | --- | --- |
| A2.1 | PyAV（動画入出力ライブラリ）の前方デコードに、未採用frame（フレーム）をRGB（赤・緑・青）化しない `target_frame_stream`（対象frame専用ストリーム）を接続する。 | `対象frame専用ストリームを追加` | 偽frame（フレーム）での採用順・窓順の単体テスト |
| A2.2 | reader（読取器）の正常終了、早期終了、例外時の一度だけのclose（解放）を保証する。 | `対象frameストリームの資源解放を保証` | 正常、早期終了、例外の各経路でのclose（解放）回数テスト |
| A2.3 | 採用元frame（フレーム）だけを高々一回RGB（赤・緑・青）化し、非採用frame（フレーム）をRGB化しないことを計測テスト化する。 | `不要なRGB変換を防ぐ検証を追加` | `to_ndarray`（RGB配列化）の呼出し回数テスト |

### Step A3（主要段階）: 公開窓口と後方互換を固定する

branch（作業枝）は `feat/target-frame-public-api`（対象frame公開APIの作業枝）とする。基点はStep A2（主要段階）の最終commit（変更記録）である。

| micro step（小段階） | 変更内容 | commit（変更記録）の題名 | commit（変更記録）前の検証 |
| --- | --- | --- | --- |
| A3.1 | `sequential_loader/__init__.py`（公開窓口）から新しい4要素を公開する。 | `対象frameストリームを公開する` | `import sequential_loader as sl`（公開窓口からの読込）だけで新規型・ストリームを使うテスト |
| A3.2 | 既存の公開型、全RGB（赤・緑・青）連続読取、LongVideoBench接続用経路の回帰を固定する。 | `既存の公開読取経路を回帰検証する` | 既存公開窓口テスト、既存全RGB読取テスト、LongVideoBench接続テスト |

### Step A4（主要段階）: 責務単位のパッケージ構造へ移行する

branch（作業枝）は `refactor/package-layout`（パッケージ構造整理の作業枝）とする。基点はStep A3（主要段階）の最終commit（変更記録）である。公開利用者の読み込みは常に `sequential_loader`（連続動画ローダー）に保つ。

| micro step（小段階） | 変更内容 | commit（変更記録）の題名 | commit（変更記録）前の検証 |
| --- | --- | --- | --- |
| A4.1 | 型・例外・方針を `src/sequential_loader/core`（共通基盤）と `src/sequential_loader/policies`（方針）へ移す。 | `型と方針を標準配置へ移す` | 公開窓口テストと方針・型の全単体テスト |
| A4.2 | デコードと二つのストリームを `src/sequential_loader/decode`（デコード）と `src/sequential_loader/streams`（ストリーム）へ移す。 | `デコードとストリームを標準配置へ移す` | 全RGB読取・対象frame読取・資源解放の全テスト |
| A4.3 | 外部データセット接続と既存実装を `adapters`（外部接続）と `legacy`（既存互換実装）へ移し、内部import（内部読み込み）とパッケージ設定を更新する。 | `外部接続と既存実装を標準配置へ移す` | 全テスト、パッケージからの公開読み込み、古い内部パスが本番コードにないことの検査 |

### Step A5（主要段階）: 文書と利用例を固定する

branch（作業枝）は `docs/target-frame-stream`（対象frameストリーム文書の作業枝）とする。基点はStep A4（主要段階）の最終commit（変更記録）である。

| micro step（小段階） | 変更内容 | commit（変更記録）の題名 | commit（変更記録）前の検証 |
| --- | --- | --- | --- |
| A5.1 | README（利用説明）へ新旧経路の用途、利用例、資源解放規則を追記し、対象frame（フレーム）専用経路は不要frame（フレーム）のRGB化を避ける機能であると明記する。 | `対象frameストリームの利用方法を文書化` | 文書内の利用例に対する公開読み込みの短い検証 |

## 10. 受入条件

| 観点 | 合格条件 |
| --- | --- |
| 選択一致 | 同一の合成動画・同一の時間格子で、既存選択規則と新規ストリームの採用時刻が一致する。 |
| RGB化の限定 | 計測用の偽frame（フレーム）で、非採用frameの `to_ndarray`（RGB配列化）が0回である。採用元frameは高々1回である。 |
| 窓の完全性 | 通常窓と短い最終窓の目標時刻数・出力順・窓境界が方針どおりである。 |
| 時刻安全性 | `PTS`（表示時刻）の減少は明示的な例外となり、暗黙の並べ替えを行わない。 |
| 資源安全性 | 正常、例外、早期終了のすべてでreader（読取器）のclose（解放）が一度だけ実行される。 |
| 後方互換 | 既存の全RGB連続読取テストと公開窓口テストが全件通る。 |
| 構造 | リポジトリ内の本番コードが古い内部パスを参照せず、責務別の配置と文書が一致する。 |

## 11. 性能評価の計画

実装後、同一の動画、同一の `duration_seconds`（動画長）、600秒、32frame（フレーム）、同一の動画reader（読取器）条件で、少なくとも次を記録する。

- 総壁時計時間
- デコードframe数
- RGB（赤・緑・青）変換回数
- CPU（中央処理装置）メモリの最大値
- GPU（画像処理装置）へ転送した画像数

評価では、新モードがデコードしたframe数ではなく、RGB化したframe数を減らす設計であることを分けて報告する。デコード時間が支配的なら、性能差が小さいという結果も有効な結論として残す。

## 12. 実装前の確認事項

1. PyAV（動画入出力ライブラリ）が対象コンテナで安定した秒単位 `PTS`（表示時刻）を返すこと。
2. `frame_index`（frame番号）を取得できない動画に対する `None`（未取得）許容が、下流の表示・記録に支障ないこと。
3. 実装時点で基準branch（作業枝）と基準commit（変更記録）が変わっていれば、差分を読んで本仕様との整合を再確認すること。
4. 性能評価の前に、Workbench（ブラウザ実行環境）側の対象frame専用接続仕様が承認済みであること。

## 13. 実装結果

- 実装前tag（復元用の印）: `pre-target-frame-implementation-20260925`（対象frame実装前の固定位置、`e44efbf1daa38451da7fdc75fb34dcb285b7df36`）。
- 最終branch（作業枝）: `docs/target-frame-stream`（対象frameストリーム文書の作業枝）。
- 最終commit（変更記録）: `76badb1`（対象frameストリームの利用方法を文書化）。
- micro step（小段階）ごとのcommit（変更記録）: `ab47689`、`8371325`、`efffd6e`、`af2fdbb`、`2e84780`、`cfb5bd2`、`0931eb9`、`baedd85`、`8c4ff19`、`e6da1f2`、`76badb1`。
- 検証: 単体・統合テスト182件成功、差分形式検査成功、Workbench（ブラウザ実行環境）との実動画を使った短い接続確認成功。
- 未実施: 600秒・32frame（フレーム）の実LongVideoBench・実Qwen性能評価、長時間run（実験実行）。
