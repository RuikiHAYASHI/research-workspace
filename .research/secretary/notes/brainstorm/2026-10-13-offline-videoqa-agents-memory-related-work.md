---
date: 2026-10-13
project: agentic-streaming-videoqa
source_todo: null
topic: オフラインVideoQA Agent 6本からのEvent Memory調査再評価
status: exploratory
tags: [brainstorm, literature-review, agent, event-memory, offline-online]
---

# Agent系VideoQA 6本のEvent Memory / Anticipationとの関係（2026-10-13）

## 調査の問い
ユーザーが挙げたVideoAgent2、VideoMultiAgents、VideoDeepResearch、LVAgent、AVUA、OmAgentの6本が、直近MTGの「重要イベントをSummaryとは別に保持」「将来何を記憶すべきかの予習」に寄与するか。

## 確認した結果（今回の関連度）
| 論文 | 主たる用途 | 関連度と限界 |
|---|---|---|
| [VideoMultiAgents](https://arxiv.org/abs/2504.20091) | Vision/Text/Graphの専門AgentとOrganizerでVQA。Graph Analysis Agentは短区間のscene graphを構築し、次chunk時に前chunkのgraphを参照 | 高：関係・動作の構造化とchunk間継承。ただしoffline full-video QA、Agentがonline event save/dropを判断する方式ではない |
| [OmAgent](https://arxiv.org/abs/2406.16620) | 前処理でscene segmentation、event-rich captionsとtimestampをmemory/DB保存、AgentがRewinderなどを選択 | 高：イベント保存とvisual evidence再取得。ただし動画全体の事前処理＋rewind可能なoffline方式 |
| [AVUA](https://arxiv.org/abs/2410.20252) | 質問に基づくframe sampling planとself-reflective feedback | 中：観測制御に転用可能だが未来質問の予測ではなく、時点tまでしか見ないオンライン保証は確認できない |
| [VideoAgent2](https://arxiv.org/abs/2504.04471) | 全segment caption→全体summary→answer assessment→uncertainty guided plan-adjust-CoT/tool calling | 中：記憶不足に気づき追加観測する制御、confidence利用。イベントのonline追加記憶には未対応 |
| [VideoDeepResearch / VideoExplorer](https://arxiv.org/abs/2506.10821) | planner+temporal grounding+on-demand perception | 中：何を見るか/どこを見るかの反復計画。初版名VideoDeepResearch、現arXiv v6(2025-11-01)ではVideoExplorerに改題。ICLR2025発表との表記は確認できない（初稿2025-06）。 |
| [LVAgent](https://arxiv.org/abs/2503.10200) | エージェントチーム選出・重要segment retrieval・議論・Reflection | 低：回答時の協調が中心で、イベントの保存設計は主眼でない |

## 6本から辿った重要な先行研究
- **[VideoAgent: A Memory-augmented Multimodal Agent for Video Understanding](https://arxiv.org/abs/2403.11481) (ECCV2024 / Fan et al.)**: Memory構築フェーズで2秒クリップごとにevent caption + visual/text embeddingsを追記するTemporal Memoryと、object tracking/re-ID + SQLのObject Memoryを構築。その後にAgentがmemoryへ各種tool queriesを発行してQA。これは「イベント保存＋Agent QA」の強い先行例。ただしmemoryは動画から先に構築され、Agentが未来を見ずに保存・削除の意思決定する方式ではない。Method §2.2–2.4, Algorithm 1–2。
- 同名の **[VideoAgent: Long-form Video Understanding with Large Language Model as Agent](https://arxiv.org/abs/2403.10517) (ECCV2024 / Wang et al.)** は別論文。前者と混同しない。
- **[VideoINSTA](https://arxiv.org/abs/2409.20365) (Findings EMNLP2024)**: event-based temporal reasoning、content-based spatial reasoning、self-reflective information sufficiency評価。Event Memoryとの違いを確認する追加候補。

## 現段階の解釈（未検証のアイデア）
- 「イベントを別メモに残す」自体は先行例がある。新規性の候補は、オンラインでの因果制約、Agentによる保持/棄却/改稿意思決定、保存容量・遅延・テキスト劣化の定量評価などの組み合わせにありうるが、いずれも実証・網羅検索前に新規とは断定できない。
- AVUA/VideoAgent2の「何を次に観測するか」を決めるPlannerは、未知の将来質問を予想するMTGの予習Agentとは直接同じではない。自研究ではQuery=t0既知を前提としており、未来質問予測との問題設定差に留意。

## Evidence境界
原論文arXiv HTML（OmAgent、VideoMultiAgents、VideoAgent2、Fan et al.VideoAgent、VideoExplorer）を優先して確認。AVUA/LVAgentは主にAbstractとMethod概要で評価。公開codeを網羅監査していないため「本文記載なし＝絶対にできない」とは断定しない。 

## 次の調査候補
Fan et al.VideoAgent (ECCV24)のTemporal/Object Memory、OmAgentのScene Event保存、VideoMultiAgentsのScene Graph生成を比較し、「onlineにする際の障害」と「保存意思決定がどの段階にあるか」を調べる。動画のオンライン性そのものの先行研究はStreamForest等と突き合わせる。
