---
date: 2026-09-18
project: agentic-streaming-videoqa
source_todo: null
topic: EgoCross Agent traceの結果可読性
status: exploratory
tags: [brainstorm, research, egocross, agent, visualization]
---

# EgoCross Agent traceを分かりやすく読むための壁打ち

## 出発点

`2026_09_hayashi_egocross_observation/outputs/20260917T034823Z_1_60ee3a84/` に、record 1を5 frameまで `--agent` で処理したJSONL traceがある。現在の一行一frameのJSONは再現性には有用だが、画像・観測・方策・memory更新の関係を人が時系列で読むには負荷が高い。目的は評価指標の追加ではなく、最小Agentが各時点で何を見て何をmemoryへ残したかを検証しやすくすることである。

## 読み込んだ文脈とEvidence

- プロジェクトREADME: current-image-only観測とprevious text stateのみを用いる最小Agentは実装・短時間実データ検証済み。最終QA・accuracy・全件実行は未実施。
- 2026-09-11 MTG: 最初はGUIなし・Pythonの最小構成で、timestampとVLM出力を保存し、memoryの感覚を掴む方針だった。
- 実行run: record 1は「0.00s〜10.00sに見えた手術器具の種類数」を問う問題（選択肢4/3/1/2）。Agent runは5 frames、Qwen3-VL-4B-Instruct、`agent-text-state-v1`。
- trace: frame 0で器具2種類のeventを`ADD`し、frame 1〜4では`UPDATE`を選択。stateは一つのeventと、frame 1以降の`watch_next`で構成される。
- trace上の観察: `watch_next`は"what to check in a later current frame"と一般的であり、次frameの確認点として役立たない。eventのclaimは質問の時間範囲（0.00s〜10.00s）を含むが、各時点で得た視覚的根拠の範囲と区別して表示されていない。

## 中心となる問い

Agentの生JSONを保持しつつ、因果順の入力画像、今回の観測、前stateからの変更、現在のactive memoryを一目で追える形にするには、どの閲覧表現が適切か。

## 発散した候補

### A. 画像付き「Agent trace report」をJSONLから派生生成する

runごとに閲覧専用のMarkdownまたは静的HTMLを生成する。元の`frames.jsonl`は正本として変更しない。

- 冒頭: run ID、質問、選択肢、モデル、frame数、causalityの境界（現在画像のみ／過去画像は未再入力）。
- 時系列: `時刻・サムネイル・現在観測・action・state差分・現在の追跡event・次に確認する点・confidence` を1 frameずつ並べる。
- 末尾: final active memory、event履歴、各action件数、警告一覧を置く。
- `state_before`と`state_after`全体を毎回繰り返さず、`+ event`、`~ evidence更新`、`- event close`の差分だけを主表示にする。生JSONは折りたたみ・リンク先に置く。

### B. 接触シート（contact sheet）＋状態遷移タイムライン

全frameの縮小画像を時間順に横並びにし、各画像の下へ`ADD/UPDATE/KEEP/...`と短い根拠を載せる。別段にeventの開始・更新・終了を線で表示する。

- 映像変化とAgentの更新頻度が対応しているかを素早く点検できる。
- 少数frameのsmoke runやMTGで特に有効。
- 長い動画では間引き・横スクロール・重要eventだけのフィルタが必要。

### C. 「Agentが何をしたか」の集約カードを追加する

frame表の前後に、質問に関係する現在の結論ではなく、**根拠の収集状況**を示すカードを置く。

- 観測済みの根拠: eventごとに最初・最後のevidence frameと要約。
- 未解決点: active `watch_next` / uncertainty。
- coverage: 観測済みの時刻範囲だけを表示（問題文の対象時間範囲とは別にする）。
- final answerは未実装であることを明示し、state traceを回答のように誤読させない。

### D. Agent出力の品質警告を可視化する

表示だけでなく、traceを読む際に次の機械的なwarningを出す。

- watch questionが空・定型的・eventと無関係。
- `UPDATE`なのにstate差分がない。
- evidenceの`last_evidence_frame`がcurrent frameと一致しない。
- stateのclaimが未観測の時間範囲や未来について断定している可能性。
- actionのreasonがcurrent observationの固有語を含まない。

これはモデルを自動的に修正するものではなく、traceを評価・デバッグするための明示的な印である。

### E. 観測と方策を質問に沿った小さなschemaへそろえる

自由文のままでは、frame間の比較とwatchの質が不安定になりやすい。質問形式ごとの構造化観測（例: countingなら`visible_types`, `new_type`, `occlusion`, `confidence`）を検討する。

- 長所: 比較・集約・QAへの接続が容易になる。
- 注意: question typeごとの設計と評価が必要であり、単なる可視化より研究上の変更範囲が大きい。

## 収束

### 最有力: A + B + Cを最小範囲で組み合わせる

まず、既存のagent JSONLから**画像付きの時系列レポート**を派生生成する。5 frame程度では画像を全て表示し、各frameではstate全体でなく差分を示す。最後に「このrunで確定したこと」ではなく、`final active memory`と「未解決／未評価」を明示する。

理由:

- Agentの因果的な処理順とmemory更新を直接点検できる。
- 正本のJSONL・モデル・promptを変えず、既存outputsに即適用できる。
- 後からAgent方策自体を改良する場合も、before/afterを同じレポート形式で比較できる。

### 同時に入れるべきもの: Dの警告

今回のtraceには定型的なwatchがあるため、見栄えを改善するだけではAgentが有用な次観測方針を作れているか判断しにくい。初版レポートに、少数のrule-based warningを添える価値が高い。

### 保留: Eの質問別schema

これはAgentの出力契約と研究上の比較対象を変える。可視化レポートを一度見て、どの自由文が比較不能かを確認してから決めるべきである。

## 比較・評価軸

- 人が質問、画像変化、action、memoryの更新理由を各frameで追えるか。
- 新規event・evidence更新・event close・uncertaintyがstate差分として識別できるか。
- 問題文の対象時間と、実際に観測済みの時間範囲を区別できるか。
- JSONL正本との対応（frame index、run ID、raw response）を失わないか。
- 長い動画でも同じ表現を縮約して閲覧できるか。

## 反例・注意点

- サムネイルを置くだけでは、memory更新の妥当性やfuture情報の混入は分からない。差分とwarningが必要。
- 色・アイコンだけでactionを示すと、色覚特性やMarkdown閲覧環境で情報を失う。action文字列も必ず併記する。
- 「final summary」を最終回答と混同しない。現実装は回答選択・accuracy評価の対象外である。
- 出力reportを研究結果の正本にはしない。入力、モデル出力、state遷移の正本はJSONLのままにする。

## Specへの引き継ぎ候補（未承認）

- 対象: `2026_09_hayashi_egocross_observation` の既存`outputs/<run-id>/frames.jsonl`。
- 目的: JSONLを変更せず、runごとの閲覧用trace reportを派生生成する。
- 最小scope候補: question/run metadata、全frameのサムネイル、観測、action、state diff、active memory、warning、元JSONLへの参照。
- 比較方法: 同一runについて、JSONLだけの場合とreportの場合で、各frameのactionとstate更新理由を追えるかを確認する。
- 未決事項: HTMLかMarkdownか、生成物の保存場所、長い動画の縮約ルール、warningの厳密な判定規則。

## 関連ファイル

- `.research/lab/projects/agentic-streaming-videoqa/README.md`
- `.research/lab/projects/agentic-streaming-videoqa/meetings/2026-09-11-mtg.md`
- `.research/lab/projects/agentic-streaming-videoqa/experiments/2026-09-15-egocross-qwen-local-investigation.md`
- `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation/outputs/20260917T034823Z_1_60ee3a84/frames.jsonl`
- `/mnt/HDD18TB/hayashi/2026_09_hayashi_egocross_observation/outputs/20260917T034823Z_1_60ee3a84/run_metadata.json`
