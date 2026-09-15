---
date: 2026-09-15
project: agentic-streaming-videoqa
source_todo: null
topic: streaming-text-memory-implementation-order
status: exploratory
tags: [brainstorm, research, implementation]
---

# Streaming Text Memory 実装順の壁打ち

## 読み込んだ文脈

- 承認済み実装spec: `2026-09-15-streaming-text-memory-spec.md`
- プロジェクトREADME: chunk-level causalな逐次VideoQAと最小text Memoryプロトタイプが現在の方針。
- 2026-09-11 MTG: futureを見ず、1 frameずつVLMと前時点のtext Memoryを用いる最小構成を優先。複雑なMemory設計は後続の研究候補。

## 中心の問い

未決のモデル・データセット詳細を固定せずに、Streaming causality、Memory継承、provenanceを検証できる最小実装をどの順で成立させるか。

## 採用候補: 実装順

1. **作業対象と既存契約の確認（Codex）**
   - 対象worktree、branch、HEAD、dirty state、局所指示を確認する。
   - `sequential_loader` のpublic APIと既存50Salads smokeが返す`SequentialSample`を読む。
   - 意図: 依存ライブラリの内部実装や既存smokeを壊さず、実データへ接続する境界を確定する。

2. **純粋な入出力契約を先に実装・unit test化（Codex）**
   - Memory更新prompt/inputとfinal answer inputを、画像・質問・frame metadata・previous/final memoryから構築する関数として分離する。
   - fake/stub VLMで、future情報を渡さないこと、final answerがfinal MemoryとQueryだけを使うことをテストする。
   - 意図: 実VLMやデータセットがなくても、研究上の因果制約を自動検証できるようにする。

3. **逐次推論loopとMemory状態遷移（Codex）**
   - `frames_per_chunk=1`の入力を順番に処理し、valid frameごとに1回だけVLMを呼ぶ。
   - `updated_memory`を次フレームの`previous_memory`へ引き継ぐ。
   - fake sequenceとfake modelで、呼出回数・順序・EOF・Memory連鎖をunit testする。
   - 意図: Streaming本体をモデル実ロードから独立して成立させる。

4. **artifact出力とCLIを接続（Codex）**
   - runごとの新規`outputs/`ディレクトリ、逐次JSONL、最終answer JSON、run metadataを実装する。
   - CLIに少なくともdataset root、question、model ID、50Saladsのsplit/sequence IDを用意する。
   - 意図: 再現性と後からのMemory解析を確保する。

5. **実VLMと実datasetによる短時間smoke（Codex + ユーザー）**
   - Codex: 利用可能なmodel/dataset rootで少数frameまたは短いsequenceを動かし、JSONLの逐次追記と最終answer保存を確認する。
   - ユーザー: datasetの研究serverへの配置、アクセス権、必要ならHugging Faceの規約同意・tokenを準備し、使用可能なrootを共有する。
   - 意図: 外部リソース依存の部分だけを最後に検証し、未利用なら明確に未検証とする。

6. **実装後の研究評価を別フェーズへ分離（ユーザー主導、Codex支援）**
   - Memoryの精度寄与、prompt、容量、multi-timescale化、重要イベントMemory、モデル比較を実験計画として決める。
   - 意図: 最小パイプラインの成立と研究仮説の検証を混同しない。

## 担当の整理

| 作業 | 主担当 | 補助 | 判断・境界 |
|---|---|---|---|
| local worktreeと既存APIの確認 | Codex | ユーザー | Codexはlocalのみ変更し、remoteへは書き込まない |
| コード、unit test、CLI、artifact保存 | Codex | ユーザー | spec内の最小範囲に限定 |
| データ移送、認証、token、権限 | ユーザー | Codex | credentialや別server操作はユーザー担当 |
| model/checkpoint、dataset変更、prompt研究方針の確定 | ユーザー | Codex | 未決事項をCodexが独自に固定しない |
| 短時間smoke | Codex | ユーザー | 利用可能な外部資源の範囲でのみ実施 |
| full benchmark・GPU長時間run・精度主張 | ユーザー | Codex | 別experiment/specで合意してから行う |
| commit / push / PR | ユーザー | Codex | 個別の明示指示がある場合のみ |

## 保留と注意点

- specは50Saladsの既存接続を最初の基盤とする。EgoCrossを入力datasetへ切替えるにはadapter・split・annotationの追加判断が必要。
- VLMの個別model ID、dtype、deviceはCLIで受け、特定値を研究判断として固定しない。
- JSONLはframeごとの更新直後に追記し、クラッシュ時にも途中経過を解析できるようにする。
- `sequential_loader`と既存`smoke_sequential_loader.py`は変更対象に含めない。

## 次にユーザーが決めること

1. この実装順で進めるか。
2. 実装を開始する際に使うlocal worktreeの場所。
3. 短時間smokeに使える50Salads dataset rootと、候補VLMへのアクセス可否。

## research-specへの引き継ぎ状況

実装scope、因果制約、artifact、検証条件は承認済みspecに揃っている。今回の壁打ちでは、その実施順と担当境界を補足した。実装へ移る場合は、対象local worktreeと外部resourceの利用可否を確認してから開始する。
