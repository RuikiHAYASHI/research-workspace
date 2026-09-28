---
date: 2026-09-18
project: agentic-streaming-videoqa
type: meeting-materials
topic: egocross-agent
status: draft
target_meeting: 2026-09-18
notion_url: null
notion_export: null
tags: [meeting-materials, research, egocross, agent, streaming-videoqa]
---

# 2026-09-18 MTG資料: EgoCross Agentの現状と次の検証方針

## 0. 今日のMTGで先生に相談したいこと

1. 現在のEgoCross text-state Agentを、まずは**因果的な状態更新を観察・診断するベースライン**として扱う方針でよいか。現段階では最終QA・正解率を扱わない。
2. 次の優先順位を、(A) traceの因果性・可読性を整える、(B) 少数のEgoCross画像列で質的に読む、(C) 最終QAを含む定量評価へ進む、の順に置いてよいか。
3. 研究上の主問いを、当面は「逐次text memoryで古い根拠がどう失われるか」に置くか。それとも「次の観測をどう制御するか」を先に扱うか。

## 1. 現時点の結論

- **確認できたこと:** 現在画像だけから観測文を生成し、前frameまでのtext stateと今回の観測文だけから状態を更新する最小Agentは、実Qwenで短時間動作した。
- **まだ示せていないこと:** このAgentがVideoQAに有効であること、最終回答が正しいこと、長い時系列で記憶が保たれること、Agent actionが意味的に適切であることは未検証である。
- **当面の見立て:** いま価値が高いのは、状態遷移を読み取れる形にして失敗を露出させること。その上で、memory保持または観測制御のどちらを研究差分として評価するかを決めることである。

## 2. 背景と今回の対象範囲

前回MTGでは、Queryを動画開始時から既知とし、未来frameを見ないchunk-level causalな入力から始めることを確認した。また、Agent系先行研究との差分は単なる「Agentの導入」では作れず、Memoryの保持・観測方法・計算資源などの軸で検討する方針となった。

今回のEgoCross Agentは、そのための最小実装である。各時点で過去raw画像やfuture frameを再入力せず、text stateだけを受け渡す。

```text
current image
  -> Qwen3-VL observation
  -> policy(previous text state, current observation)
  -> validated action + deterministic reducer
  -> next bounded text state
```

- state: `scene_summary`、open event、`watch_next`、`uncertainties`
- action: `ADD` / `UPDATE` / `KEEP` / `FLAG_UNCERTAIN` / `CLOSE_EVENT`
- trace: 各frameの観測、state前後、policy生出力、parse済みdecision、処理時間をJSONLへ保存

最終回答の選択、正解率、全957問への実行、学習はこの実装範囲に含めていない。

## 3. Evidence: 確認できた根拠・現状

| 項目 | 確認できたこと | 限界 |
| --- | --- | --- |
| 実装経路 | current-image-only観測とtext-only state更新を分離し、actionをReducerでstateへ反映する経路を実装した。 | Agent方策・state設計の意味的妥当性は未評価。 |
| 自動検証 | unit / CLI / fake-model integrationで31件のtest成功を記録した。 | 実Qwenの品質や長時間運用を保証しない。 |
| 実Qwen 1 frame | record ID 224で`FLAG_UNCERTAIN`を返し、空stateにuncertaintyを追加した。 | 1 frameでは時系列的な記憶更新を判断できない。 |
| 実Qwen 5 frame | record ID 1で5行のtraceを保存し、全行で`error: null`。frame 0は`ADD`、frame 1--4は`UPDATE`だった。 | 5 action全種の出現、actionの適切さ、最終QAはいずれも未評価。 |
| EgoCross評価データ | standard manifestは957問・10,748画像参照で、画像列を因果順に入力できる。 | このmanifestには正解ラベルがなく、これ単体ではaccuracyを計算できない。 |

### traceを読んで見えた課題

5-frame traceの探索では、`watch_next`が一般的な文になり、次frameで何を確かめるべきかの具体性が低い例があった。また、event claimが質問の対象時間を含んでいても、実際に観測済みの根拠範囲と区別して表示されていない。

これは性能低下を定量的に示す結果ではない。一方で、現状のJSONLだけでは「画像変化に応じたstate更新か」「未到着の映像について断定していないか」を人が点検しにくい、というデバッグ上のEvidenceである。

### viewer・少数runの計画上の位置付け

- 既存traceをread-onlyで表示し、画像・観測・action・state diffをframe単位で追うviewerのdelivery planがある。
- 表示用の新規traceでは、eventのframe provenanceをモデル出力に任せず、Reducerがcurrent `frame_index`から決定的に付与する案になっている。
- Agent実行からviewer起動までを一つのCLIにまとめ、ID 712 / 478 / 823（計21 frame）を同じbrowserで読む案もある。

これらは資料作成時点ではいずれも**計画書上のdraft**であり、viewer実装完了・GPU実行完了のEvidenceではない。GPU runは別途の実行許可が必要である。

## 4. Interpretation: 現時点での解釈

1. 最小Agentは「過去画像を再読込せずに、観測とstateを因果順でつなぐ」ベースラインとして機能し始めている。
2. ただし、stateが存在することと、有用な記憶・計画ができていることは別である。定型的な`watch_next`や質問と無関係なeventは、改善すべき失敗Evidenceとして扱う必要がある。
3. 先行研究StreamAgentも逐次text memoryを持つため、text stateを更新するだけでは研究差分にならない。古い根拠の保持、または観測制御について、因果条件をそろえた比較・評価が必要になる。
4. その比較の前にtraceを読めるようにすることは、見栄えのためではなく、state更新の失敗・future情報の混入・根拠範囲の誤表示を検出するための基盤になる。

## 5. Ask: 判断していただきたいこと

### Ask 1 — 最初の到達点

「最終QAを解くAgent」ではなく、まず「画像、観測、action、memory更新の対応を監査できるAgent trace」を最初の到達点にしてよいか。

- 賛成の場合: provenanceを決定的にし、viewerで既存traceを読めるようにする。
- 異なる場合: QA用の正解ラベルの所在と、評価プロトコルを先に確定する必要がある。

### Ask 2 — 次に読むEgoCross例

少数の異なる画像列で質的レビューを始める場合、初期候補を ID 712 / 478 / 823（高速視点・机上作業を含む、計21 frame）とする案でよいか。

- 利点: 一つのmodel loadで複数recordを処理し、同一viewerで比較する導線を設計できる。
- 注意: これは質的なtrace確認であり、正答率比較ではない。実Qwen/GPU実行は承認後に限る。

### Ask 3 — 研究差分へ向けた最初の評価軸

次のどちらを先に小さく検証するかを決めたい。

| 候補 | 最初に問うこと | 必要になるもの |
| --- | --- | --- |
| A. Memory保持 | 早い時点の対象・数・行為順序が、何回の更新後にstateから失われるか。 | 根拠が既知の短い画像列、保持率／根拠frameの評価規約。 |
| B. 観測制御 | 質問に必要な変化に応じ、次の観測間隔・範囲を変えると何が改善するか。 | 観測間隔・遅延・計算量を固定した比較設定。 |

現時点ではAを先に扱うほうが、既存のtext-state traceを直接利用でき、失敗原因を切り分けやすいと考えている。これは提案であり、未検証である。

## 6. 今回言えること / まだ言えないこと

| 今回言えること | まだ言えないこと |
| --- | --- |
| current imageとprevious text stateだけを用いる最小Agent経路は、短時間の実Qwen runで動作した。 | AgentがEgoCrossの質問へ正しく答えられる。 |
| frameごとのstate前後と生出力を保存でき、因果順の検査対象を残せる。 | text memoryが長期情報を十分に保持する。 |
| traceの可読性とevent provenanceに、明示的に対処すべき課題が見えている。 | viewer案や複数record実行案が実装済み・有効である。 |
| EgoCrossの画像列を逐次入力する基盤はある。 | EgoCrossでの結果が実動画ストリーミング全般へ一般化できる。 |

## 7. 方針候補・比較

| 方針 | 直近の成果物 | 得られる判断 | 主な未解決点 |
| --- | --- | --- | --- |
| 1. trace基盤を先行 | deterministic provenance + read-only viewer | state更新を人が監査できるか。 | QA性能は分からない。 |
| 2. 少数traceの質的レビュー | 複数recordの短いAgent trace | domain・視点変化で失敗がどう現れるか。 | 代表性・定量性は低い。 |
| 3. Memory保持の小評価 | 同一質問でstate保持を測る比較プロトコル | text memoryの具体的な失敗を測れるか。 | 正解根拠・指標の設計が必要。 |
| 4. 最終QA評価を先行 | label付きデータとbaseline比較 | 回答性能を比較できる。 | 現manifestのlabel不足と、原因分析の難しさ。 |

提案する順序は **1 → 2 → 3 → 4** である。1と2で「何が壊れているか」を観察可能にしてからMemory設計を変え、最後に回答性能へ接続する。

## 8. MTG後に決まれば進める候補

- trace監査を最初のマイルストーンとするかを確定する。
- 初期の少数recordセットと、医療映像を含めるかどうかを確定する。
- Memory保持評価を採る場合、何を「残すべき根拠」と見なすかを決める。
- 最終QA評価へ進める場合、正解ラベルを持つデータソースと、future非参照条件を含む評価契約を調査・spec化する。

## 9. 図・生成物

新規の図は作成していない。MTGでは、既存5-frame traceを用い、各frameについて「現在画像 → observation → action → state diff」を1行ずつ読む例を示すと、上記の課題を最も短く共有できる。

## 10. 参照ファイル

- [プロジェクトREADME](../README.md)
- [2026-09-11 MTG議事録](../meetings/2026-09-11-mtg.md)
- [EgoCross text-state Agent 短時間実行ログ](../experiments/2026-09-16-egocross-agent-text-state-smoke.md)
- [EgoCrossとQwenのローカル調査](../experiments/2026-09-15-egocross-qwen-local-investigation.md)
- [EgoCross trace viewer delivery plan](../specs/2026-09-18-egocross-trace-viewer-delivery-plan-spec.md)
- [EgoCross Agent viewer launch plan](../specs/2026-09-18-egocross-agent-viewer-launch-plan-spec.md)
- [EgoCross Agent traceの結果可読性メモ](../../../../secretary/notes/brainstorm/2026-09-18-egocross-agent-trace-readability.md)
- [StreamAgent先行研究MTG資料](2026-09-17-streamagent-related-work-mtg-materials.md)
