---
date: 2026-10-13
project: agentic-streaming-videoqa
source_todo: null
topic: Awesome Streaming Video Understanding掲載論文のEvent Memory関連度仕分け
status: exploratory
tags: [brainstorm, research, literature-review, event-memory, streaming]
---

# Awesome Streaming Video Understanding：Event Memory調査の一次仕分け

## 対象・目的

- 元の一覧: https://github.com/Yang011013/Awesome-Streaming-Video-Understanding
- 2026-10-13時点main READMEのModels欄21本を調査。Datasets/Benchmarksの重複掲載は数えない。
- 目的はオンライン動画処理で重要イベントを記憶に残す研究の優先調査。
- 事前の固定テンプレート採用ではなく、今回の一次絞り込みに限る分類。

## 判定区分

- 最優先: Agent自身が逐次オンラインで重要イベントの保存可否を決定。
- 高: オンラインのevent-structured memoryを保持（Agent不要）。
- 中: オンラインの非イベント特化memory（KV/visual featuresなど）を保存・圧縮。
- 参考: オフライン動画からイベントを抽出・記憶するAgent。
- 周辺: 上記4種の定義には直接合致しないが、オンライン動画理解に関係する掲載モデル。

最優先と参考については、今回のModels欄から明確な該当を確認できなかった。これは当該研究が存在しないことを意味しない。

## 全21本の一次仕分け

| 優先度 | 論文 | 根拠／主要な記憶方式 | 確認の深さ |
|---|---|---|---|
| 高 | [StreamForest](https://arxiv.org/abs/2509.24871) | イベント境界からmeta-eventを作り、長期visual event treeに保存・統合。Agent判断でなく類似度・時差・merge履歴による規則制御。 | 原論文Method |
| 高（暫定） | [CogStream / CogReasoner](https://arxiv.org/abs/2506.10516) | フレームをイベントへ時空クラスタ化し、現在の質問への関連度で詳細保持/圧縮。全文を先読みしない厳密なincremental clusteringか未確認。 | 原論文Method／Appendix |
| 中 | [StreamingVLM](https://arxiv.org/abs/2510.09608) | attention sink・recent text・recent visualのKV cacheを有限予算で保持。 | Abstract |
| 中 | [StreamMem](https://arxiv.org/abs/2508.15717) | query-agnosticでvisual KV cacheを重要度評価して固定容量に圧縮。 | Abstract |
| 中 | [StreamAgent](https://arxiv.org/abs/2508.01875) | Agentによる未来予測・観測制御、長期記憶はKV cacheのCPU offload / selective recall。独立イベント台帳が中心ではない。 | 原論文Method |
| 中 | [Flash-VStream](https://arxiv.org/abs/2506.23825) | 低容量context memoryと高容量augmentation memoryで長期・詳細視覚情報を管理。 | Abstract |
| 中 | [LiveVLM](https://arxiv.org/abs/2505.15269) | Vision Sink Bucketingで視覚KVを整理し、query時にKV retrieval。 | Abstract |
| 中 | [STREAMMIND（2025 Event-Gated）](https://arxiv.org/abs/2503.06220) | perception tokensをmemoryへ逐次保存し、イベント検知でLLM実行。独立イベントメモを記録する方式ではない。 | 原論文Method |
| 中 | [STREAMCHAT（2025 ICLR）](https://arxiv.org/abs/2501.13468) | 階層的visual feature memoryを更新・圧縮し長時間対話に対応。 | Abstract |
| 中 | [VideoLLaMB](https://arxiv.org/abs/2409.01071) | SceneTilingとrecurrent memory bridges/temporal memory tokensで情報を継続伝播。 | Abstract |
| 中 | [Streaming Long Video Understanding（VideoStreaming）](https://arxiv.org/abs/2405.16009) | クリップ逐次encodingし前clipのmemoryを伝播、質問に関連したmemoryを選択。 | Abstract |
| 周辺 | [Proactive Assistant Dialogue Generation (IPS)](https://arxiv.org/abs/2506.05904) | オンライン一人称動画に基づく先回り発話。イベント長期Memory管理は中心でない。 | Abstract |
| 周辺 | [Streamformer](https://arxiv.org/abs/2504.20041) | causal temporal attentionによる動画表現の逐次学習。記憶の保存方策を主題としない。 | Abstract |
| 周辺 | [LiveCC](https://arxiv.org/abs/2504.16030) | video+ASRのstreaming trainingとリアルタイム実況。 | Abstract |
| 周辺 | [ViSpeak](https://arxiv.org/abs/2503.12769) | 視覚指示・ジェスチャーを認識して応答。 | Abstract |
| 周辺 | [LION-FS](https://arxiv.org/abs/2503.03663) | Fast pathで回答時機を決定、Slow pathでkeyframe featuresを補強。 | Abstract |
| 周辺 | [DisPider](https://arxiv.org/abs/2501.03218) | perception・decision・reactionの非同期化と応答契機判断。 | Abstract |
| 周辺 | [StreamChat（2024 CVPR系）](https://arxiv.org/abs/2412.08646) | decoding中の映像contextを更新し続ける対話設計。 | Abstract |
| 周辺 | [MMDuet](https://arxiv.org/abs/2411.17991) | 動画とテキストの交互進行に対応するstreaming interaction設計。 | Abstract |
| 周辺 | [VideoLLM-MoD](https://arxiv.org/abs/2408.16730) | vision tokenのlayer skipで計算削減。保存／イベント記憶でなく計算制御。 | Abstract |
| 周辺 | [VideoLLM-online](https://arxiv.org/abs/2406.11816) | 連続動画と応答の同期・学習・並列推論。Event Memory管理が主眼ではない。 | Abstract |

## 重要な区別

- StreamForestのmemory treeはevent単位だが、EventをAgentが自然言語で選んで保存するとは確認できない。inter-frame similarity/local-minimum segmentationとpenaltyでmergeする。
- CogStreamは質問ごとに関連イベント詳細を残すが、AppendixのK-means clusteringはクラスタ数を動画長に比例させており、完全なライブ逐次実行かどうか要コード検証。このため「高（暫定）」。
- STREAMMINDはEvent-Gated **LLM invocation**を行う一方、Memory自体はperception tokens。Event-Ledgerそのものの保存ではない。
- StreamAgentはAnticipation Agent + streaming KV long-term memoryとして重要だが、Event Memoryの保存可否判断とは異なる。
- 「Future framesに触れずにprefixを使う」ことと、「過去の状態を保持・更新し続ける」ことは別軸。各論文のcode/runtimeで要追加検証。
- 今回の研究のsummaryを逐次全面再生成する方式と異なり、visual KV / feature memoryの研究が多い。情報の劣化の種類を同一視しない。

## 次の読み順候補（非固定）

1. StreamForestのPersistent Event Memory Forestを精読し、独立イベント記憶・統合・情報損失を検討する。
2. CogStreamのevent clusteringとquestion-aware compressionを読み、オンライン性の実装面に疑問を持って監査する。
3. StreamAgentの長期KV retrievalと比較して、Agentが観測を選ぶことと記憶を選ぶことを区別する。
4. STREAMMINDのイベントgateが「Event Memory保存」と異なる理由を検証する。

### References

- https://arxiv.org/html/2509.24871v1
- https://arxiv.org/html/2506.10516v3
- https://arxiv.org/html/2503.06220v3
- https://arxiv.org/html/2508.01875v4

## 未確認

全21本の実装とevaluation harnessを監査したわけではない。特に周辺・中の分類はAbstractに基づく一次判定を含む。イベントが完全に存在しないと断定しない。


## 2026-10-14 追記：Memoryの表現形式についての訂正

前段の21件仕分けは **Event Memoryとの関連度** に基づくものであり、text/KV/featureの表現方式別の完全分類ではない。特にStreamAgentをKV Cache中心と表記したことで重要なテキストMemoryを見落としていた。

**原論文（https://arxiv.org/html/2508.01875、§3.1–3.2）に基づく確認:**
- StreamAgentは各video clipのvisual tokensをテキストcaption C_tへ変換し、テキスト状態 m_t = U(m_(t-1), C_t) を逐次更新する。原論文は m_t を明示的に text memory と記している。
- 累積テキスト化によって古いfine-grained detailsが失われることを原論文自体が認め、その補完として視覚KV Cacheを別に保持しselective recallする。従って **text + KVの併用** であり、KVだけの論文と分類してはならない。
- Event Ledgerを独立した文章/JSONレコードで保存することは、上記のテキストmemory更新とは別の設計である。

**MTGの要請（GitHub会議記録）:**
- 2026-09-11 MTGの原文に「今のここでの会話でのメモリはmarkdownとかのテキスト」「他のAgentのいうメモリもそんなことやっている？」とある。決定事項には「textual、KV cache、feature/vector等を区別して調査」と「text memory最小プロトタイプ」が明記されている。
- 2026-09-25 MTGには「気になるイベントをテキストとして残すAgent」と「時刻などを含むJSON設計」がある。これは自研究の設計方向であり、先行研究の調査をテキストに限定する指示ではない。
- ユーザー提示の直近MTG文字起こしでもSummaryをtextとして累積改稿し、重要イベントを別保存する案が出る。ただし形式やAgentの保存ポリシーの最終仕様はまだ決定していない。

**リスト外の直接的なテキスト記憶例:** ProVideLLM (ICCV 2025, https://arxiv.org/abs/2504.13915) はlong-term観測をverbalized text tokensへ圧縮しshort-term visual tokensと併用する。指定されたYang011013の2026-10月時点のModels 21本には掲載されていない。

今後の調査では **memory表現形式（text / KV / visual）** と **記憶更新・選択動作（append / rewrite / merge / retrieve / discard）** と **Agentの意思決定** を別々の性質として捉える。テキストSummaryが失う情報と視覚feature圧縮が失う情報は同じ問題ではない。
