---
date: 2026-09-12
project: agentic-streaming-videoqa
source_todo: null
topic: EgoCross を用いるAgent動画理解の試験的仕様の設計指針
status: exploratory
tags: [brainstorm, agentic-streaming-videoqa, egocross, streaming-videoqa, memory]
---

# EgoCross を用いるAgent動画理解の試験的仕様の設計指針

## 出発点

2026-09-11 MTGで、EgoCrossを候補データとして、フレームを1枚ずつ既存VLMへ入力し、
前時点までのtext Memoryを使って「何が起きているか」を逐次更新する最小プロトタイプを
作る方針が出た。本メモは、その**仕組みを理解するための試験**の設計指針であり、
研究手法・学習方式・正式な評価プロトコルを確定する仕様ではない。

## 中心となる問い

`Queryが動画開始時から既知`で、動画を未来を見ずに順次観測するとき、
外部のtext Memoryを介して、各時点の観測を後続時点へどのように引き渡せるか。

この試験で最初に確認したいのは最終QA精度ではなく、次の三点である。

1. future frameを参照せずに、観測・Memory更新・最終回答のループが成立するか。
2. 各時点の出力を見れば、Memoryに何が追加・維持・失われたかを追跡できるか。
3. Queryを与えることが、Memoryを質問に関連する出来事へ寄せる実感につながるか。

## 採用候補: 最小の観測・記憶ループ

研究条件は、既存の整理どおり **query-known, frame-level observational prototype,
compute-incremental streaming VideoQA** とする。ただし、EgoCrossのreaderが一度に
動画全体をdecodeする実装である場合は、試験の主張を安全に
`sequentially processed frames` に留め、strictなframe-level streamingとは呼ばない。

```text
q = question known at t=0
M_0 = empty, or a fixed initial statement
for frame f_t in chronological order:
    o_t = VLM(q, M_{t-1}, f_t)              # current observation
    M_t = update_text_memory(q, M_{t-1}, o_t)
answer = VLM(q, M_T)                         # after the final observed frame only
```

### 入力アクセスの契約

- フレームはtimestamp昇順に一度だけ処理する。
- 時刻`t`の推論で渡してよい画像は`f_t`のみ。`f_{t+1...}`、全動画由来の要約、
  future-awareなサンプリングindexは入力に含めない。
- Queryは`t=0`から利用してよい。ただし、Queryで未来フレームを検索・seekしない。
- 前フレームのraw画像・VLM内部KVは初期試験では保持しない。保持する状態は外部text Memoryと
  保存済みログのみとし、挙動とコストを可視化する。
- フレーム間隔、最大フレーム数、resizeなどの観測条件はrunごとにログ化する。

この契約は、後でchunk単位の実験へ拡張するときも、`f_t`を`chunk_t`へ置換すれば保てる。

### VLMへの役割分離

一回の自由な長文生成に「観測」と「Memory編集」を混ぜない。最小構成でも、少なくとも
次の二つを論理的に分ける。

- **観測**: current frameから見えている事実を短く列挙する。見えない過去を推測して補わない。
- **Memory更新**: `previous memory + current observation + query`から、質問に関係する
  持続的な事実を短く更新する。

同一VLM・同一呼び出しで実装してもよいが、promptと出力フィールドを分離する。
これにより、誤認識がframe由来かMemory編集由来かを後で切り分けられる。

## Memoryの設計指針

### まずは構造化text Memoryにする

自由形式の長い要約だけでは、古い情報が消えた理由を追えない。初期Memoryは以下のような
小さな構造を推奨する。MarkdownまたはJSON Linesのいずれでもよいが、1 run内では固定する。

```text
time_range: [start, end]
entities: 人・物・場所と識別上の手掛かり
events: 時刻付きの観測済み行動・状態変化
query_relevance: 質問への関係と根拠
uncertainties: 見えていない点、曖昧な同一性
```

- 観測事実と推測を混ぜない。予測は必要になってから別フィールドにする。
- entityはIDを安易に確定しない。連続フレームで同一人物・物体と判断できない場合は
  `person_A?`のように不確実性を残す。
- Memoryの長さ上限を初回から置く。上限超過時は古い全文を単に捨てず、
  「維持した事実 / 圧縮した事実 / 捨てた事実」をログへ残す。
- `重要`の判断は、まず質問との関連と後続行動の解釈に必要か、の二軸に限定する。
  予兆Memoryやmulti-timescale Memoryは本試験の対象外とする。

### 更新操作を明示する

更新結果には少なくとも `ADD / UPDATE / KEEP / DROP / UNKNOWN` を付ける。
Agentのactionを強く主張するためではなく、Memory更新を監査可能にするためである。

- `ADD`: 新しく観測された関連事実を記録する。
- `UPDATE`: 同じentity/eventの状態を時刻付きで更新する。
- `KEEP`: 現frameでは再確認のみで、既存記録を維持する。
- `DROP`: 上限のため除外した記録と理由を残す。
- `UNKNOWN`: 解釈に必要だが、映像だけでは確定できない点を明記する。

## 保存すべき最小ログ

各frameに対して、少なくとも以下をJSONL等の追記形式で保存する。

- `run_id`, `video_id`, `frame_index`, `timestamp`, `sampling_config`
- `query`, `input_memory_hash` または入力Memory本文
- `observation`, `memory_before`, `memory_after`, `memory_operations`
- VLM名・version・prompt version・generation parameters
- 処理時間、画像の参照先、エラーとretryの有無

同じrunで生成された最終回答にも、参照した最終Memoryと設定を紐付ける。画像そのものを
複製保存する必要はなく、原データ内の安定した参照先とframe番号で再現できればよい。

## 試験の比較順序

最初からAgentの有効性を結論づけない。失敗位置を切り分けられる順に比較する。

1. **Current frame only**: Queryと現frameのみ。Memoryなし。
2. **Append-only observation log**: 過去観測をそのまま連結し、長さ上限のみ適用。
3. **Query-aware text Memory**: 本試験の主条件。上記の構造化更新を行う。
4. **更新操作付きMemory**: `ADD / UPDATE / KEEP / DROP / UNKNOWN`を明示して更新する。

3と4が実質的に同一になりそうなら、初期試験では4のみでよい。一方、multi-timescale、
重要イベント専用Memory、anticipation、動的sampling、VLM内部KV操作、学習は比較要因を
増やしすぎるため保留とする。

## 成功・失敗をどう読むか

### 成功の最低条件

- 同じvideo・設定・seedで、入力順、各時点のMemory、最終回答を再現できる。
- ログからfuture frameを使用していないことを確認できる。
- 少数の代表動画で、人物・物体・行動の少なくとも一つについて、前の観測が次の時点の
  Memoryに正しく引き継がれている。
- 上限到達時に、Memory更新の根拠と失われた情報を確認できる。

### 失敗しても価値がある観測

- Memoryが早期に誤ったentity同定へ固定される。
- 要約更新で、質問に必要な古い出来事が希釈される。
- Queryに引っ張られ、画面にない出来事を幻覚する。
- 連続フレームの重複情報でMemoryが肥大する。

これらは、将来のentity tracking、event境界、multi-timescale Memory、重要イベントMemoryの
必要性を示すEvidenceになり得る。ただし、この試験だけで各拡張の有効性は結論づけない。

## 評価の扱い

EgoCrossで利用可能なアノテーションとQA形式は未確認のため、初期段階では定量的な
ベンチマーク主張を置かない。まずは短い代表動画を固定し、frameログと最終回答を人手で
読む**trace evaluation**を主にする。

アノテーションが利用可能になったら、少なくとも次を分離して評価する。

- 最終QAの正確さ。
- entity / eventの保持率（過去の正しい事実を失わないか）。
- hallucination率（未観測の事実を書かないか）。
- Memory token数・VLM呼び出し数・処理時間。
- 各方式が同じ観測フレーム列を使っているか。

## 採用候補・保留・棄却寄り

| 区分 | 内容 | 理由 |
|---|---|---|
| 採用候補 | Frozen VLM + external structured text Memory | 最小で監査しやすく、KV操作より原因分離が容易。 |
| 採用候補 | Query=t0、時系列一方向の入力アクセス | 既存の研究条件と整合し、query-aware選択も可能。 |
| 採用候補 | frameごとの追記ログとtrace evaluation | 試験の目的である「仕組みを理解する」を直接満たす。 |
| 保留 | fixed frame sampling間隔とMemory token budgetの値 | EgoCrossの動画長・解像度・VLM文脈長を確認してから決める。 |
| 保留 | append-onlyと要約Memoryの比較規模 | 利用可能なQA/アノテーションと初回traceで判断する。 |
| 保留 | multi-timescale / 重要イベントMemory / anticipation | 希釈・長期保持・観測選択の失敗Evidenceが出た後に切り出す。 |
| 棄却寄り（初期試験） | 学習、VLM内部KV圧縮、動的chunk・動的モデル切替 | 新たな要因が多く、text Memoryの挙動を理解する目的から外れる。 |

## 未解決事項

- EgoCrossの正式なデータ名・ライセンス・動画形式・アノテーション・QAの対応関係。
- 1 frameずつの処理が必要か、一定間隔samplingで十分か。
- 使用するVLMと、画像・text Memoryを同時入力できる最大コンテキスト。
- text Memoryの予算を文字数、token数、event数のどれで管理するか。
- 最終回答を動画終了後だけに出すか、各時点の暫定回答も保存するか。

## research-specへ引き継げる材料

- 目的: EgoCross上で、futureを見ない逐次観測と外部text Memory更新の成立・可観測性を確認する。
- scope: GUIなしのPython最小構成、frozen VLM、frame/時系列ログ、最終回答。学習・KV改造は除外する。
- 比較: current-only、append-only、query-aware structured Memoryを、同一frame列で比較する。
- 成功条件: 再現可能なtrace、因果的アクセスの監査、少数動画でのMemory引継ぎ確認。
- spec化前に必要: EgoCrossのデータ契約、利用VLM、sampling/budget、評価対象と回答形式の決定。

## 関連ファイル

- `.research/lab/projects/agentic-streaming-videoqa/README.md`
- `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`
- `.research/secretary/notes/brainstorm/2026-09-10-causal-granularity-query-pregiven.md`
- `.research/secretary/notes/brainstorm/2026-09-11-streamforest-streammem-streamagent-summary.md`
