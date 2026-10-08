---
date: 2026-10-08
project: agentic-streaming-videoqa
source_todo: null
topic: server-migration-offline-priorities
status: exploratory
tags: [brainstorm, server-migration, paper, evaluation, baseline, workbench]
---

# サーバ移行中に進める優先事項

## 出発点

サーバ移行中で実環境の動作確認ができないため、GPU・実Qwen・LongVideoBench実行を伴わずに進められる作業を整理する。

ユーザーが既に把握している作業:

- 論文 / PowerPoint の「はじめに」「関連研究」の記述。
- Agentの出力を表形式で整理し、見やすくする。
- 3-Agentパイプライン図は完全版ではないが一旦区切る。

## GitHub上で確認できた現在地

- Companyの現行SSOTは `AGENTS.md` + `.research/` 構成。
- プロジェクトREADMEでは、実Qwen / 実LongVideoBenchでの品質・速度、3-Agent E2Eは未検証として残っている。
- 2026-10-07のbrainstormでは、サーバ復旧後のGateを Fake smoke -> 実Qwen固定1 QA canary -> 長め動画trace review -> 小規模baseline評価の順とする案が最有力。
- Workbench remote `main` は 2026-10-08確認時点で `5a4de708b1ac645fe17452420fc85ab9226dd53d`。
- remote `main` のREADMEは現在も Situation / Memory / Answer と旧artifact構成を説明しており、2026-10-07のSituation / Summary / Answer簡略化specの実装完了はGitHub remoteから直接確認できない。
- remoteには `refactor/workbench-runtime-workflow` branchは確認できず、サーバ側local worktreeやuncommitted / unpushed変更はGitHubからは確認不能。
- repositoryのdefault branchは `feat/step-10-qwen-preflight` のまま。
- `.env.example` の最新mainにはmachine固有の `LVB_ROOT` と `CUDA_VISIBLE_DEVICES=1` が入っており、2026-10-07 shell entrypoint specの「machine固有値をtracked exampleへ固定しない」という方針と不整合がある。

## サーバなしで進める追加候補

### 1. canary / trace review評価表を確定する

最優先。

実Qwenを回せるようになった直後に「動いた / 動かなかった」だけで終わらないよう、事前に失敗分類を固定する。

最低限:

- Situation: 主要動作、見落とし、hallucination、時系列誤り。
- Summary: 重要情報保持、新観測統合、誤上書き、情報消失、冗長化。
- Answer: summaryに根拠があるか、根拠があるのに選択を誤ったか。
- System: window数、各Agent latency、total runtime、summary長、error / OOM / max token。

標準はartifactだけで埋めるtrace表とし、判断できない行だけ動画へ戻る二段階方式にする。

### 2. 論文のMethod / Problem Settingを先に書く

「はじめに」「関連研究」だけでなく、現在ほぼ固定している最小baseline部分はサーバなしで文章化できる。

候補:

- Online / Streaming VideoQAのProblem Setting。
- causal制約（future windowへアクセスしない）。
- fixed-window逐次処理。
- Situation Agent。
- Summary Agent。
- EOF-only Answer Agent。
- Backendが保持するwindow metadata / prompt / generation / latency / artifact。
- 最小baselineではEarly Answer、dynamic window、multi-timescale memory等を扱わない境界。

実験結果を含む節は後回しにし、Method本文と図・表の用語を先に一致させる。

### 3. Agent I/O表と「研究者向けtrace表」を分けて作る

既知の「Agent出力を表形式でまとめる」は2種類に分ける。

1. 論文 / PowerPoint向けの設計表
   - Agent
   - 入力
   - 出力
   - 責務
   - 次段への受け渡し

2. 実験review向けのtrace表
   - Window
   - Situation
   - Situation判定
   - Summary
   - Summary判定
   - Answerへの影響
   - 備考

設計説明と評価記録を同じ表へ詰め込まない。

### 4. canary QA選定基準を決める

実際のquestion ID選択はサーバ復旧後でよいが、基準は先に固定できる。

- 複数windowをまたぐ情報統合が必要。
- Situation -> Summaryの累積が意味を持つ。
- 人間が正解理由を追いやすい。
- 最初は細かい文字読み・音声依存・専門知識依存を避ける。
- 極端に長すぎる動画は最初のcanaryでは避ける。

### 5. 実験章の骨組みとbaseline matrixを作る

数値は空欄のままでよい。

最低限の比較軸候補:

- 最小3-Agent baseline。
- window / frame sampling条件。
- EOF-only Answer。
- 将来候補としてEarly Answer / readiness、summary改善等。

先に「何を比較すれば研究上の主張になるか」を固定し、サーバ復旧後に実験を増やしすぎないようにする。

### 6. 関連研究を「研究上の位置付け表」まで落とす

単なる文章だけでなく、各手法について次を整理する。

- streaming / onlineか。
- future accessの有無。
- questionが開始前から既知か。
- current observationとpast memoryをどう分けるか。
- Memory表現: text / feature / KV等。
- Answer timing: EOF-only / early / readiness。
- 現在の3-Agent baselineとの違い。

これはIntroduction / Related Work / Novelty議論を同じ比較軸で接続するために使う。

### 7. GitHub上だけでできる整合性整理

研究実験とは別に、remoteだけで確認できる不整合を整理しておく価値がある。

- `.env.example` からmachine固有path / GPU番号を外す。
- repository default branchが古い `feat/step-10-qwen-preflight` のままかを運用上確認する。
- runtime refactorがlocal onlyなら、サーバ復旧後にlocal worktree / commit / push状態を確認し、Companyの実装済み認識とremoteを同期する。
- READMEのSituation / Memory / Answer記述は、実際にSummary版実装がremoteへ反映された後に更新する。

## 推奨順序

サーバ移行中:

1. canary / trace review評価表。
2. Agent I/O表。
3. 論文Method / Problem Setting。
4. Related Workの比較軸表。
5. canary QA選定基準。
6. 実験章骨組み / baseline matrix。
7. GitHub remoteの軽い整合性整理。

サーバ復旧後:

1. local worktree / remote同期状態の確認。
2. `./scripts/workbench.sh verify`。
3. `./scripts/workbench.sh preflight`。
4. 固定1 QAで実Qwen E2E canary。
5. 事前に作ったtrace表でreview。
6. 1本の長め動画。
7. 小規模baseline評価。

## 現時点の結論

サーバ移行中は、新しい機能追加よりも「論文に書ける設計の固定」と「復旧直後にEvidenceを取れる評価設計」を優先する。

特に、Introduction / Related Workに加えてMethod / Problem Settingと評価表まで先に作っておくと、サーバ復旧後は実験結果を流し込む作業へ直結する。


## 2026-10-08 02:45 JST 追記: Agent traceの確認形式

Agentの実行結果を人間が確認するための出力形式は、Markdown表を採用する。

目的は現時点では正誤評価ではなく、1本の動画について各windowで

- Situation Agentが何を出力したか。
- Summary Agentが何を出力したか。
- EOF時にAnswer Agentが何を出力したか。

を時系列で見やすく確認すること。

確認用の基本形:

| Window | Situation Agent | Summary Agent | Answer Agent |
|---:|---|---|---|
| 1 | ... | ... | — |
| 2 | ... | ... | — |
| 3 | ... | ... | — |
| EOF | — | — | ... |

Workbench内部の機械可読な実行記録はJSON / JSONLのまま保持してよいが、人間が確認しNotionやMTG資料へ持ち込むためのprojectionはMarkdown表とする。

現段階では正誤判定、failure category、複数動画の一括比較は含めない。


## 2026-10-08 02:45 JST 追記: Markdown trace specへ昇格

Agent出力をMarkdown表として保存する方針を、次のdraft specへ昇格した。

- `.research/lab/projects/agentic-streaming-videoqa/specs/2026-10-08-workbench-agent-trace-markdown-spec.md`

以後、実装契約の詳細は上記specを参照する。


## 2026-10-08 15:24 JST 追記: Run artifact簡略化と画像保存方針

現行Record v2の確認を踏まえ、Run artifactは今後さらに単純化する方向を有力とする。

現在の合意:

- 人間確認用Markdownには、現時点では画像列を直接埋め込まない。
- sampled frame / thumbnail自体は、server session内だけでなくRun artifactとして永続保存する方向とする。
- MarkdownはSituation / Summary / 最終回答等のテキスト確認を中心にする。
- 正解ラベルはAgent推論入力へ混ぜない。
- Answer完了後または評価用経路でDataset annotationから正解を取得し、予測との正誤判定を保存する方向とする。
- Run全体の機械可読記録は、現在の6ファイル構成より単純な単一JSONへ統合する案を有力候補とする。
- Answerだけを別fileへ分離する必要性は低く、Run全体結果の上位fieldとして保存する案を有力候補とする。
- Run directory名は timestamp + random hash より、人間が読める日時ベースを優先する案が有力。

有力なartifactイメージ:

```text
<OUTPUT_ROOT>/
└── <human-readable timestamp>/
    ├── result.json
    ├── trace.md
    └── frames/
        └── sampled-frame-thumbnails...
```

この時点では実装specの更新・コード変更は行わない。既存の `2026-10-08-workbench-agent-trace-markdown-spec.md` は、画像埋め込みを行わない点は維持できるが、Record構成やAnswer保存位置について今回の方向性と不一致が生じているため、実装前にrefreshが必要。
