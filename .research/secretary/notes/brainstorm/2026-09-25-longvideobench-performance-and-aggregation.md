---
date: 2026-09-25
project: agentic-streaming-videoqa
source_todo: null
topic: longvideobench-performance-and-aggregation
status: exploratory
tags: [brainstorm, longvideobench, performance, sequential-loader, prompt, aggregation]
---

# LongVideoBenchの性能・prompt・情報集約の切り分け

## 出発点

600秒・32フレーム設定で、decodeが長いように見えること、観測出力が`image 0`--`image 3`程度しか説明しないこと、情報集約の担当主体が不明確であることを確認する。

今回の範囲は既存artifact・実装の読取りと方針候補の整理であり、コード・prompt asset・設定・実験結果は変更しない。

## 確認できた事実

### 600秒・32フレームrun

- artifact: `2026_09_hayashi_longvideoqa_workbench/outputs/20260925T024737Z-8dbf9455`
- 設定: `window_seconds=600`、`frames_per_window=32`、`decoder_frames_per_sample=16`、Qwen3-VL-4B。
- window 0のtargetは0.00秒から581.25秒まで18.75秒間隔の32点で、実際に32 frameが選ばれている。window 1も同様に32 frameである。
- window 0はrun開始からturn完了まで約183秒、stage計測値はchunk understanding 30.13秒、evidence aggregation 6.84秒である。残り約146秒は、model load、sequential decode、RGB/Tensor化、window組立、thumbnail等の合算であり、現artifactだけではdecode単独の時間とは断定できない。
- 現行recordはstage全体の経過時間しか保存しないため、decodeと画像変換・model input preprocessを分離していない。

### sequential_loader経路

```text
PyAV forward decode (25 fps)
  -> every decoded frame: RGB ndarray化 -> CPU uint8 Tensor化
  -> 16 frameごとのTensor stack / DataLoader sample
  -> Workbenchがtimestamp gridで32 frameだけ選択
  -> Qwenへ選択frameだけ入力
```

- 600秒・25 fpsでは最初のwindowを返すまで約15,000 frameを前方向decodeする。
- strictなライブ/因果設定で、時刻600秒まで到達したことを確認するには原則その範囲を順方向にdecodeする必要がある。したがって「全25 fpsのcodec decode」自体はstrict streamingの定義から自然であり、`sequential_loader`へ接続したことだけが非効率とは言えない。
- ただし現public APIは、**VLMに採用しない約14,968 frameも**`frame.to_ndarray(rgb24)`、`torch.from_numpy`、permute、16枚ごとのstackを行う。このmaterializationは32点sampling目的には不要で、優先的な最適化候補である。
- offline LongVideoBench評価だけを目的にするなら、各target近傍へseekして32点だけ復号するsparse baselineは大幅に速い可能性がある。ただしkeyframe seekとfuture accessを使い得るため、strict forward streaming実験と同一の比較軸には置かない。

### promptと画像入力

- `Qwen3VLAdapter`はrequest.imagesの各画像につき1個の`{"type": "image"}`を作り、同じ順序の32枚をprocessorへ渡す。コード上の4枚上限・sliceは確認されなかった。
- 現chunk promptは「current windowのselected imagesを観察し、chronological eventsを説明する」とだけ指示する。画像番号・timestampの対応、全画像の網羅、出力schema、画像ごとの不確実性を要求していない。
- window 0の実出力は選択肢の4場面の照合として`image 0`--`image 3`だけを列挙し、256 token上限で文の途中で切れている。従って、32枚が入力されていない根拠ではなく、選択肢に誘導されたshortcutと無構造・短い出力契約が直接の原因候補である。

### 情報集約の実体

1 turnは同じQwen3-VL adapterを2回呼ぶ。

```text
selected frames + question + choices
  -> chunk_understanding (画像あり) -> current observation

previous evidence + current observation + question + choices
  -> evidence_aggregation (画像なし) -> updated evidence
```

- 別プロセス・別モデル・別memory agentは存在しない。
- `evidence_aggregation` stageがtext-onlyで前turnのevidenceを置換更新する。次turnへ渡るのはこのupdated evidenceだけであり、過去画像・過去observation全体は渡らない。
- final answerも同一adapterのtext-only呼出しであり、final evidenceを入力にする。
- 現aggregation promptも全文を毎turnに再生成する制約がなく、`max_new_tokens=256`で途中切れ・古い根拠の消失・同じ回答文の反復が起こり得る。

## 仮説と候補

| 区分 | 方針 | 期待 / 注意点 |
| --- | --- | --- |
| 最優先の計測 | turnを`decode`, `target-only materialization`, `thumbnail`, `vision preprocess`, `vision generation`, `aggregation generation`へ分割計測する | 現在の「decodeが遅い」印象を確認できる。UI操作待ちと初回model loadも別計上する。 |
| 有力なstreaming高速化 | loader側に、前方向decodeは維持しつつtargetに達したframeだけRGB/Tensor化して返すtarget-sampling reader/iteratorを追加する | codec decode数は減らないが、約15,000回のRGB変換・Tensor化・stackを約32回へ減らせる。同一target timestamp・同一画像になる回帰testが必要。 |
| 比較用baseline | sparse seekで32 targetだけ読むoffline baselineを別recipe/明示ラベルで追加する | 実務上のLongVideoBench throughputの上限を測れるが、strict causal streamingの速度と混同しない。 |
| prompt改善 | chunk observationからchoicesを外すか弱め、`[index, timestamp, scene/event, relevance, confidence]`の全画像レコードを要求する | 選択肢先行のshortcutを避ける。32件を256 tokensで出すのは不十分なので、出力上限も同時に設計する。 |
| scalable観測 | 4--8画像のmicro-batchごとに短い構造化観測を作り、window内text aggregatorで32枚を統合する | 全画像coverageを検証しやすい。VLM call数が増えるため、単発32枚との精度・速度比較が必要。 |
| evidence改善 | fixed schemaのbounded evidence（確定event、時刻、根拠frame、未確定、answer-relevant state）へ更新する | evidence肥大と256-token truncationを防ぐ。回答をearly commitしない制約が必要。 |

## 収束と優先順位

### 採用候補

1. **計測を先に追加し、current full pathのどこが遅いか確定する。** 特にfirst windowの未説明約146秒をdecode、RGB/Tensor化、model loadへ分ける。
2. **strict streamingを維持するtarget-only materializationを最初の高速化候補にする。** `sequential_loader`を外すのでなく、public APIをtime-grid sampling用途に拡張する方向である。
3. **観測promptをcoverage-firstへ直し、回答選択はaggregation/final段階へ寄せる。** まず4/8/32枚で「全入力indexが出力に現れる率」と回答精度を測る。
4. **text evidenceのschema・最大長を明示する。** 情報集約を説明可能・比較可能な状態にする。

### 保留

- 32画像を一度のVLM呼出しで扱うか、micro-batchへ分割するか。coverage、accuracy、wall-clock、token量で決める。
- PyAV/FFmpegのhardware decode、decoder thread数、resize/max-pixelsの調整。まず計測でdecodeまたはvision preprocessが支配的と確定してから扱う。
- sparse seek baselineの採用。研究主張がonline/causalであるため、baselineの位置付けを明確にしてから追加する。

### 棄却寄り

- `decoder_frames_per_sample`だけを大きくして「decodeを減らす」とみなすこと。全frameのcodec decode・RGB/Tensor化は残り、chunkを大きくするとCPUメモリも増える。
- current promptのまま`frames_per_window`だけを増やすこと。32枚を使った根拠が出力に残らず、速度だけ悪化する可能性が高い。
- 現行の2段階を「別Agentが自律的に情報集約している」と解釈すること。同一Qwen adapterへの逐次的なtext-only再呼出しである。

## 次アクション候補

1. 計測仕様を固め、1 turnの各境界時間・decode frame数・RGB materialized frame数・入力visual token/画像サイズ・出力token数をartifactへ保存する。
2. current path、strict target-only path、offline sparse pathを同一question・600秒・32 targetsで比較する小規模benchmarkを設計する。
3. coverage-first observationとbounded evidence schemaのprompt案を作り、既存の32枚artifactで目視比較できる評価基準を定める。

## Research Spec Handoff候補

- 目的: strict sequential LongVideoQAの因果性を維持しつつ、不要な全frame materializationを除き、frame coverageが検証可能な観測・evidence更新へ変更する。
- scope候補: timing artifact、sequential_loaderのtarget-only public reader、Workbench reader接続、prompt asset、structured stage output/evidence、tests、比較recipe。
- 成功基準候補: 同一target frame選択を保持、decode/materialization/modelを個別計測、観測出力が採用全frame indexを扱う、evidenceが最大長内で時系列根拠を保持、strict/offline baselineを区別する。
- 未決: 32枚単発かmicro-batchか、structured output format、evidence上限、sparse baselineを研究評価へ含めるか。


## 2026-09-25 追記: Workbench側だけでのRGB化削減と物語型集約

### `sequential_loader`を変更しない場合のRGB化

現行public APIでは、`SequentialVideoReader.read()`が全decoded frameに対して`frame.to_ndarray(format="rgb24")`、Tensor化、chunk stackを行ってからWorkbenchへ`SequentialSample`を返す。従って、公開APIをそのまま使う限りWorkbench側だけで「target frameだけをRGB化」することはできない。

- Workbenchの`_valid_frames()`でtime-grid選択後にHWC NumPyへ変換すれば、Workbench側の二重変換は採用frameだけにできる。ただしloader内部のRGB化・Tensor化は全frameで残る。
- Workbench内のPyAV forward readerがadapterから得たvideo pathを順方向decodeし、target到達frameだけRGB化すれば実現できる。codec decode数は残るが、RGB ndarray・Tensor・HWC NumPy化は32枚へ抑えられる。
- 後者はstrict forward decodeを維持するが、現行の「sequential_loader公開APIが唯一の動画読込経路」を変えるためspec化が必要である。責務上の本命はloaderへtarget-aware public readerを追加する案である。

独自readerでは、全frameのtimestampだけを順方向に確認し、time-grid targetに初めて達したframeだけへ`to_ndarray("rgb24")`を行う。timestamp jump時に一枚を複数targetへ対応付ける現行first-after-target規則と、選択metadata一致を回帰条件にする。

### 物語型evidenceの候補

純粋な追記型storyはwindow数に比例して増え、純粋な再要約は古い根拠を失う。このため二層stateが有力である。

```text
per-frame / micro-batch observations
  -> window evidence ledger（時刻・frame・出来事・確信度。追記型）
  -> rolling narrative（ledgerと前narrativeから作る、固定token上限の物語）
```

- evidence ledgerは`time span`, `frame index`, `scene/event`, `question relevance`, `confidence`を持つ根拠の正本である。artifactには全window分を保存し、次promptへは質問関連項目だけを渡す。
- rolling narrativeは前の物語と新windowの新規eventを時系列に接続した、長さ上限付きの可読な要約である。正解根拠の唯一の正本にはしない。
- final answerではnarrativeに加え、質問関連ledger行で選択肢を検証する。

LongVideoBenchの時系列順序問題では、scene labelと最初の出現時刻をledgerに残す必要がある。

### 今回のLongVideoBench設問

- 対象ID: `P9hDA0u6FO0_0`、動画長1995.88秒（約33分16秒）、Historyカテゴリ、`SSS` / `L2-Relation`、duration group 3600。
- Napoleonに関する四つの視覚的sceneが動画中に現れる正しい時間順を四択から選ぶ問題で、validation annotationの正解labelは候補1（0始まり）である。
- 一枚の物体認識ではなく、長尺内で複数sceneを発見し出現順を保持して比較するtemporal-relation問題である。
- LongVideoBench全体は最大1時間のvideoとsubtitleをinterleaveして使う英語multiple-choice VideoQA benchmarkである。現Workbenchはsubtitleを無効化しており、今回の実行は視覚のみの部分設定である。


## 2026-09-25 追記: 可変長narrativeとtarget-only公開mode・構造整理

### 可変長narrative

rolling narrativeを常時固定長にする必要はない。推奨は「artifact上の根拠は無制限、modelに渡すnarrativeだけは可変長budget」である。

1. 各windowの全frame observationは時刻・frame index付きledgerとして永続保存する。
2. 近いwindowの新規eventはnarrativeへそのまま追記し、物語を自然に成長させる。
3. 次windowを加えるとprompt budgetを越えるときだけ、古い連続windowをchapterへ圧縮する。
4. chapter化時にも、質問関連eventの時刻・根拠frame・確信度をledgerから落とさない。
5. final answerは可読なnarrativeだけで決めず、質問・候補に関連するledger行を再投入して検証する。

従って、物語は`recent detailed scenes + older compressed chapters`からなるmulti-timescale memoryである。純粋な追記は長さが線形に増え、純粋な再要約はforgettingを起こすため、どちらも単独採用しない。

### target-only RGB modeの公開契約候補

既存経路は変更しない。

```python
import sequential_loader as sl

# Existing full-RGB chunk path: unchanged.
dataset = sl.SequentialDataset(
    sources=[source],
    reader=sl.SequentialVideoReader(),
    chunk_config=sl.FixedChunkConfig(frames_per_chunk=16),
)
```

これと別に、`SequentialSample`を返さないpublic modeを追加する。`SequentialSample`は連続した全RGB frameを契約にしているため、target-only modeを同型に偽装しない。

```python
policy = sl.TimeGridSamplingPolicy(
    window_seconds=600,
    frames_per_window=32,
    clock="decode" or "presentation",
)
with sl.target_frame_stream(source=source, policy=policy) as windows:
    for window in windows:
        # targetに初めて達したframeだけRGB ndarray化する
        # frame_index / actual timestamp / target timestampを返す
        consume(window)
```

このmodeはPyAVの順方向codec decodeを維持し、source順・frame index順・target first-after-target規則を保証する。一方、target以外はtimestamp/absolute indexを確認後に破棄し、RGB ndarray・Tensor stack・DataLoader sampleを作らない。時間gridはfuture visual contentでなく設定だけから決まるためcausalである。

public APIを増やすが、既存の`import sequential_loader as sl`、`SequentialDataset`、`SequentialVideoReader`、`SequentialSample`、Workbenchの既存接続は不変とする。target modeはnew public APIの利用時だけ選ばれる。

### ディレクトリ構造候補

最終形は標準src layoutへ寄せ、配布packageと実装packageを同じ`sequential_loader`にする。

```text
src/sequential_loader/
  __init__.py                 # stable public facade
  adapters/                   # LongVideoBench, 50Salads source discovery
  core/                       # SequenceSource, lifecycle, public contracts
  decode/                     # PyAV session, timestamp/clock policy
  streams/                    # full RGB chunk stream, target-frame stream
  policies/                   # fixed chunk, time-grid sampling
  legacy/                     # old 50Salads/EPIC learning path (not public)
tests/
examples/
docs/
```

`src/sequential_loader/__init__.py`だけを外部のstable入口にし、外部repositoryからの`import sequential_loader as sl`は変えない。旧`src.*` direct importは公開契約に含めず、legacyを削除・移動する前に内部debug・mainとの依存を別途監査する。

### 段階的な実装候補

1. target-only public modeだけを現行構造へ追加し、existing full-RGB pathとのtarget metadata一致・resource close・外部Workbench import互換をtestする。
2. Workbenchでnew modeをopt-in recipeとして接続し、existing recipeを変更せず速度・選択frame同一性を比較する。
3. behaviorが固まってからsrc layoutへ移行し、public facadeのcontract testと外部Workbench smokeを維持する。

mode追加と全ディレクトリ移動を同一変更に混ぜると、性能差・契約破壊の原因が切り分けられないため、実装は分離する。
