---
date: 2026-09-17
project: agentic-streaming-videoqa
source_todo: "2026-09-11 MTG: Agent系の未解決点・Memory・動的chunkを比較"
topic: streamagent-research-opportunities
status: exploratory
tags: [brainstorm, research, streaming-videoqa, memory, streamagent]
---

# StreamAgentの問題点から研究課題へ（2026-09-17・探索メモ）

## Authorityと対象

- 相談: 「この手法から研究に使えそうなこと、研究で解決できそうな問題はあるか」。方向性の探索であり、採用・spec化・実装許可ではない。
- 決定済みの研究条件: Queryは t=0 で既知、動画は到着順、future chunk非参照。chunk-level causalを許容（[9/11 MTG](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md)）。
- [9/15 approved spec](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-15-streaming-text-memory-spec.md)の範囲: 1 frameずつ `query + current frame + previous text memory -> new memory`、EOF後の最終回答、timestampと更新履歴保存。学習・KV-cache管理・動的chunk・専用Memory・Agentはscope外。実装完了・実測性能を証明するものではない。
- 参照したCompanyの一次調査: [9/16 related-work scout](2026-09-16-streaming-videoqa-related-work-scout.md)。概要中心の調査であり、先行研究の新規性を確定していない。
- StreamAgent原論文（v4、2026-04-29）: https://arxiv.org/html/2508.01875 。3.1節は逐次要約による初期詳細の不可避な消失を明記。3.2節はKVを累積・CPU退避し質問時に選択的検索。Limitationsは曖昧な場面での回答時期判断、ストリーミング学習データ不足、冗長映像の計算負荷を挙げる。
- GitHub上での文献・spec調査のみ。研究コード実装、local worktree、実験結果、CPU容量上限は今回未監査。

## 中心となる研究の問い

同じ厳密な逐次入力・同一計算/記憶予算の下、質問が最初から分かっていることを利用して、**将来の回答に必要な証拠を残し、必要な箇所を適切な時間粒度で観察し、根拠が揃ってから答える**ことはできるか。まず誤答を記憶書き込み・検索・回答判定のどこで起こしたか切り分ける。

## 候補A: Query-awareな証拠保持と要約更新（現行baselineとの接続が比較的明確）

- 問題: `m_t=U(m_{t-1},C_t)` で古い一回限りの事実が上書き・希釈される。KVに残っていても検索・利用に失敗すれば救済されない。StreamAgentはこの詳細損失を明記。
- 仮説: 同じ最大テキストトークン数で、全文再要約のみより、Queryとの関連度・timestamp・事実単位の保護を用いたKEEP / UPDATE / COMPRESS（必要ならDELETE）により、古い答えの根拠が残りやすい。未来を予知していない事実だけを保存。
- 実験案: 承認済みの1-frame loopを比較の基準として、(a)元の逐次全文要約、(b)固定長のrecent+重要事実スロット、(c)質問条件付きの事実単位keep/updateの各案を**同一model、同一frame、同一budget**で比較。timestamp付き過去事実QA・途中で物体状態が変わるQAを設計し、必要な証拠があったprefixのみで評価する。
- 指標: QA accuracy / event or fact retention recall / contradiction rate / Memory tokens / latency。時刻別memory JSONLから「観測済み→保存された→更新で消えた」を追跡。
- 反例: 問いに沿って保護すると周辺文脈が消え、複数情報の統合が悪化する。保護基準に基づく誤保存、事実抽出エラー、Prompt長増もあり得る。
- 先例と差分未確認: QueryStream (ICLR 2026) はQuery-aware visual token pruningと応答制御 https://proceedings.iclr.cc/paper_files/paper/2026/hash/0b17d256cf1fe1cc084922a8c6b565b7-Abstract-Conference.html ; SelectStream は固定容量latent memoryへのwrite/consolidation/retrieval https://arxiv.org/abs/2606.16353 ; SAVEMemは意味的重要度・3階層Memory https://arxiv.org/abs/2605.07897 。「Query-aware Memoryが初」という主張は不可。Query既知×可読text fact×逐次更新×統一予算の組合せも全文/コード比較が必要。

## 候補B: Agentの行動空間を「観察位置」から「次の入力時間粒度」へ拡張

- 問題: StreamAgentの明示Toolは主にzoom/crop/trackingの空間行動。chunked prefillは同一clip内のvisual token分割であって次に取得する動画区間の秒数制御ではない。
- 仮説: 同じ処理コストで、細かい動作は短い次chunk、変化の少ない区間は長い次chunk、という因果的な切替が固定長より見落とし/レイテンシのバランスを改善し得る。
- 実験案: 一度に観測できるのは選択した次chunkまで。固定短/固定中/固定長と、過去のみから決める可変長を比較。取得chunk長、1秒あたりsampling frame数、イベント区切り、prefill token chunkは別パラメータとする。時間幅を短くするほど計算回数が増える対価を必ず数える。
- 指標: 重要イベント検出遅延、QA accuracy、per-frame/VLM call数、visual tokens、realized wall-clock latency。
- 反例: 短い閃光イベントは長chunkのframe samplingで失われる、長期間前の詳細を問うタスクはchunk長だけで解けない。
- 先例: VideoScaffold https://arxiv.org/abs/2512.22226 は予測駆動のイベント境界調整。EventMemAgent https://arxiv.org/abs/2602.15329 はイベント単位サンプリング。厳格な未来非参照でAgentが**次の入力長自体**を切替える先行例は要再調査、独自性未確定。

## 候補C: Memory保存量と検索失敗の分離・容量制御

- 問題: StreamAgentのGPU→CPU offloadはGPUピーク容量を緩和するが、全過去KVを残すならCPU側は累積する。Selective Recallで必要な履歴を見逃す可能性もある（設計上の懸念で頻度は未計測）。
- 仮説: 有界の視覚Memory予算内で、textにある時刻・Entity・重要事実を索引として使い、古い特徴のkeep/evictと検索の双方を協調させると、同等budgetで回答根拠の保持が改善し得る。
- 実験案: (a)容量無制限の保存上限参考、(b)FIFO/均一サンプリング、(c)質問条件付きのkeepとretrieve、(d)理想検索Oracleを比較。まずどの段階で正解証拠が欠落したか分析してから実装範囲を決める。
- 指標: QA accuracy、証拠frame recall@budget、CPU/GPU peak GiB、CPU↔GPU転送bytes、retrieval latency。
- 反例: Queryが既知でも後でしか関連性が判明しない手掛かりを早期削除してしまう。Oracleの過去映像参照は実システムと区別。
- 先例: MuKV (CVPR 2026) https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_MuKV_Multi-Grained_KV_Cache_Compression_for_Long_Streaming_Video_Question-Answering_CVPR_2026_paper.html ; SelectStream, SAVEMemも圧縮・取得を研究済み。単なるKV圧縮・CPUへの退避は差分にならない。現行approved specはKVを対象外としているため実装コスト高。

## 候補D: 回答可能性判定を「Evidence確認」と結びつける

- 問題: 予測計画が正しいとは限らず、根拠が揃う前の早期回答や不必要な待機がある。著者は複雑な状況の回答時期予測を限界として明記。
- 仮説: Agentの自由文判定だけでなく、質問から必要な証拠チェックリスト（entity/action/time）を作り、各条件を観測済みtimestamp・memory factへ結びつけて回答するか決めれば早期回答が減る可能性。
- 実験案: heuristic/no gate、LLM judge、根拠条件付きgateを同一観測streamで比較。十分な証拠の出現時刻を人手または厳密ラベルで定義し、観測prefixのみで応答。回答しないまま終了するfailureも測る。
- 指標: premature answer rate、回答正確性、追加待機秒数、未回答率、planning model call数。
- 反例: 証拠チェックが厳しすぎると回答を永遠に延期。必要条件の抽出自体が誤る。QueryStreamのresponse scheduling、R3-Streamingのreadiness判定 https://arxiv.org/abs/2605.17921 と重複要確認。

## 現時点の収束（方向性の提案、未採用）

- **まず候補Aの失敗事例診断を始点にする案**: approved specのJSONLログと直結し、KVの実装なしで「どの時刻にどの事実が失われたか」を検証できる。ただし実装済み/実験済みと推定しない。結果が出なければ仮説は支持されない。
- **独立した第二軸として候補B**: MTGの次chunk長案と合致するが、入力時間幅とfps/処理待ち時間を分離した対照実験が必要。
- **C/Dは切り分け分析か後段候補**: Cは新規性先例とKV実装負担、Dは応答時刻の明確な正解定義が障壁。
- 採用/棄却はユーザー未決。すべてstatus exploratory、spec作成・コード変更・TODO追加・GPU runなし。

## 次の判断とspec引き継ぎ候補

最初に決めるのは「解きたい失敗例は古い証拠消失か、短時間イベントの見落としか」。両方を同時変更せず、同一動画prefix・同一VLM・同一入力frame・同等Memory予算でBaselineを取る。最低限の比較対象/指標を決めた後、ユーザーがspec化を明示した場合にresearch-specへhandoffする。

未確認: GitHub上の研究コードの現在branch/commit・local worktreeの実装/dirty state、対応データセットと質問/必要証拠のラベル、実予算、各候補の同一設定での文献全文/実装比較、現在の本研究実験結果。これらを推測で補わない。

## 参照

- [Project README](../../../lab/projects/agentic-streaming-videoqa/README.md)
- [9/11 MTG](../../../lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md)
- [9/15 approved spec](../../../lab/projects/agentic-streaming-videoqa/specs/2026-09-15-streaming-text-memory-spec.md)
- [9/16 related-work scout](2026-09-16-streaming-videoqa-related-work-scout.md)
- [StreamAgent v4](https://arxiv.org/html/2508.01875)
