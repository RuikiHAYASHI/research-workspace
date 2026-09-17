---
date: 2026-09-18
project: agentic-streaming-videoqa
source_todo: null
topic: egocross-demo-video-selection
status: exploratory
tags: [brainstorm, research, egocross, agent, visualization, sample-selection]
---

# EgoCross Agent表示用動画の候補選定

## 出発点

EgoCross Observation Prototypeのブラウザ表示では、初見者に「現在画像 → 観測文 → Agent action → text state」の流れを読ませたい。そのため、1 frameのsmokeや長い動画ではなく、約10 frameの画像列を4本程度、`--agent`で最後まで処理した結果を用意する。

今回の目的はAgentの性能・正解率の評価ではない。複数domainで、画像の変化と状態更新を質的に読む表示例を選ぶことである。

## 読み込んだ文脈とEvidence

- READMEと2026-09-11 MTG: current imageだけを観測し、previous text stateだけを次stepへ渡す最小Agentを先に理解・検証する。final QA、accuracy、全件実行は未実施。
- 2026-09-16の短時間実行: ID 1の5 frame agent runでは、frame 0が`ADD`、frame 1〜4が`UPDATE`であり、経路の動作は確認済み。ただし、actionの多様性・質は未評価。
- 既存の`2026-09-16-egocross-sample-selection.md`は、質的review向けに5 domain・40 frame（ID 1, 190, 367, 467, 712）を提案済み。本メモはそれを置き換えず、**ブラウザで見せる短い4本**に絞る選定である。
- local standard manifestを確認した結果、957 record、5 domainがある。8〜12 frameのrecord数は、CholecTrack20 51、ENIGMA 45、EgoPet 30、EgoSurgery 45、ExtrameSportFPV 181である。
- 提案候補の全画像はローカルdataset rootに存在することを確認した。先頭・中盤・終端画像も目視し、各候補に場面・対象・視点の変化があることを確認した。

## 選定基準

1. **長さ**: 8〜12 frameを優先する。10前後なら画面のframe navigatorで全frameを無理なく読める。
2. **domain多様性**: 医療、作業机、動物の視点、FPVスポーツを1本ずつ選び、同じAgent表示の汎用性を確認する。
3. **質問と変化**: 固定物体だけでなく、行為開始・相互作用・行為列を含める。Agentがeventを追加・更新・不確実性として扱う余地を持つ。
4. **表示の理解しやすさ**: 初見者が対象や視点の違いを画像から把握できること。
5. **再現可能性**: manifestのrecord ID、全画像path、既存の相対timestamp規則で実行できること。

## 有力な4本（医療映像を含む構成）

合計39 frameである。`--agent`ではframeごとに観測callとtext-only policy callを行うため、これは39の状態遷移を読む質的表示セットになる。

| 優先 | record ID | domain | frame数 | 質問形式 | 表示例としての狙い |
| --- | ---: | --- | ---: | --- | --- |
| 1 | 14 | CholecTrack20 | 10 | action temporal localization | 腹腔鏡映像で、bipolarによる凝固開始を問う。器具と術野の変化を時系列で追う例。VID06であり、現行実装の0.5 FPS規則と整合する。 |
| 2 | 545 | ENIGMA | 10 | dominant held-object identification | 電子機器・計測器のある机上作業。静かな作業環境から、手と電動ドライバーが前景になる変化が見える。 |
| 3 | 203 | EgoPet | 11 | interaction temporal localization | 猫の視点で別の猫との相互作用開始を問う。動物の移動・接近に対するevent更新を読む例。 |
| 4 | 823 | ExtrameSportFPV | 8 | action sequence identification | FPVスポーツの一人称視点。移動と姿勢が大きく変わるため、手術・机上作業と異なる高速視点の例になる。 |

### 質問文

- **ID 14**: main surgeon right handがbipolarでcystic plateの凝固を始めるおおよその時刻。
- **ID 545**: operator left handが主に扱っている道具（battery / battery connector / board / electric screwdriver）。
- **ID 203**: 猫が別の猫と初めて相互作用する時刻範囲。
- **ID 823**: 0〜20秒に行われる行為列。

ここで質問・選択肢は観測とpolicyへ渡す文脈であり、現行Agentは選択肢を回答・採点しない。画面では「質問が何を重要とみなすか」を理解する補助として扱い、Agent stateを最終回答のように表示しない。

### 視覚的確認

- ID 14は腹腔鏡の術野と複数器具の相対位置が変わる。
- ID 545は電子機器の机全体から、手に持たれた赤色の電動工具へ視点・対象が移る。
- ID 203は猫の視点で、別の猫の近接・周囲の床面・家具が時系列で変わる。
- ID 823は草地のFPV視点で、前方風景から身体・装備が見える動的な視点へ変わる。

## 重要な注意: 医療映像の扱い

ID 14には血液を伴う実際の手術映像が含まれる。研究室内でAgentの対象domainを示すには有用だが、初見者向けの一般的なデモや共有画面に適するかは別判断である。

- **医療映像を許容する場合**: 上の4 domain構成を採用する。domain多様性が最大になる。
- **医療映像を避ける場合**: ID 14を外し、EgoPet ID 190（9 frame、猫とplasticのinteraction temporal localization）を追加候補にする。この場合は4本・3 domainになり、医療domainの比較はできない。

医療domainを完全に外すかは、想定閲覧者と表示場所に依存する未決事項とする。

## 保留・棄却寄り候補

| record ID | domain | frame数 | 判断 |
| ---: | --- | ---: | --- |
| 65 | CholecTrack20 | 10 | 画像変化は明瞭だが、VID111は現行実装で1 FPS例外になる一方、質問選択肢は約20秒まで含む。表示上のtimestampを混乱させる可能性があり、ID 14を優先する。 |
| 190 | EgoPet | 9 | 医療映像を避ける代替として有力。既存の質的review候補でもあるが、ID 203とdomain・質問型が近いため、4 domain構成では採用しない。 |
| 540 | ENIGMA | 8 | electric screwdriverを取る時刻を問うため状態変化は見せやすいが、ID 545と同domainである。医療回避時の予備候補。 |
| 467 | ENIGMA | 15 | 既存seed setのprediction候補だが、今回の「約10 frame」条件を超える。 |
| 712 | ExtrameSportFPV | 5 | 既存seed setの短い高速視点候補だが、今回の全frame表示には短すぎる。 |

## 反例・失敗条件

- image列と質問が変化していても、現行Agentが`ADD`と`UPDATE`以外を選ぶ保証はない。5 actionをすべて見せることを今回の選定成功条件にしない。
- 4 runのAgent出力により、stateが定型的、`watch_next`が一般的、またはeventが質問対象と無関係になる可能性がある。これは失敗として隠さず、viewerのquality warning候補として記録する。
- 質問の対象時間と、traceが付ける相対timestampを混同しない。とくにFPS例外を持つrecordは、viewerで質問上の時間範囲と観測済みframe範囲を別表示にする必要がある。
- 39 frameでも、GPU推論は1 frameごとに観測とpolicyの2 callを含む。実行時間・GPU利用可能性は選定調査だけでは確定しない。

## 現在の方向性

表示用の第一候補は **ID 14, 545, 203, 823** とする。各recordを`--agent`で全frame処理し、4 domain・39 frameの閲覧用traceを作る。

ただしこれは探索上の有力候補であり、実行許可ではない。医療映像の扱いを決めた後、viewer実装specとは別に、対象record・output root・既存run上書き禁止・短時間runの範囲を確定してspec化する。

## 次にユーザーが決めること

1. 医療映像（ID 14）を4 domainデモに含めるか、ID 190へ差し替えるか。
2. viewerの実装を先に承認・完成させるか、4本のAgent runを先に作ってから画面を調整するか。
3. Agent run後に、質問・画像・observation・action・state diffのどの見方を人手で採点・比較するか。

## Research Spec Handoff（未承認）

- 対象プロジェクト: agentic-streaming-videoqa
- 元依頼: 初見者向け結果表示に使う、約10 frame・4本・複数domainのEgoCross Agent run候補を調査する。
- 読み込んだ文脈とEvidence: 最小text-state Agentの5-frame実行成功、957 record manifest、4候補の画像存在と先頭/中盤/終端の目視確認。
- 採用方向: 医療映像を許容するならID 14, 545, 203, 823（4 domain、39 frame）。
- 実験候補: 各recordの全frameを`--agent`で1 runずつ処理し、閲覧用traceを作る。
- 比較対象・評価指標: 正解率ではなく、frame順、actionとstate diff、未確実性、画像との対応を人手で読めるか。
- 対象外: final QA、accuracy、全957 record、学習、GPU長時間run、viewerからの実行。
- 保留・棄却案: 医療映像の公開可否。回避時はID 190を追加し4本・3 domainにする。
- 未決事項: 4本の最終採否、実行順、GPU利用時間、run後の質的レビュー規約。
- 関連: `notes/brainstorm/2026-09-16-egocross-sample-selection.md`、`notes/brainstorm/2026-09-18-egocross-agent-trace-readability.md`、`specs/2026-09-18-egocross-trace-viewer-implementation-spec.md`。
