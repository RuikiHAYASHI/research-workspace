---
date: 2026-09-16
project: agentic-streaming-videoqa
status: draft
topic: egocross-observation-agent-addendum
source: 2026-09-16-egocross-observation-prototype-plan-spec.md + 2026-09-11 MTG
last_updated: 2026-09-16
---

# EgoCross Observation Prototype: Agent拡張とcommit規約の追補

## 適用範囲

この追補は`2026-09-16-egocross-observation-prototype-plan-spec.md`のStep 5以降を置き換え、全Stepのcommit文章規約を補う。Step 1からStep 4の目的とmicro Stepは維持する。

## Agentとは何を追加することか

frameごとにモデルを呼ぶだけでは、状態をまたいだ意思決定がないため、Agentとは呼びにくい。最小のAgentには次の4要素が必要である。

1. **State**: 過去に確定・保留したtext Memoryと、その更新履歴。
2. **Observation**: current frameだけから生成された観測文。
3. **Action policy**: StateとObservationを基に、次のMemory操作を選ぶ方策。
4. **Reducer / trace**: 選んだactionを検証してStateへ反映し、更新根拠を再生可能に保存する処理。

固定順のEgoCross画像列では、次のframeを自由に選べない。そのため初期のAgentは、入力順序を変えるactive-perception agentではなく、Memory保持を制御するstate-management agentとする。

```text
observation_t = VLM(question, current_frame_t)
action_t = Agent(question, memory_{t-1}, observation_t)
memory_t = Reducer(memory_{t-1}, action_t, observation_t)
```

Agent actionは`ADD`、`UPDATE`、`KEEP`、`FLAG_UNCERTAIN`に限定する。`STOP`、frame skip、次chunk長、encoder切替は、観測budgetと公平な比較条件を別に定める必要があるため、今回のscope外とする。

## 改訂後のbranch系列

```text
main（空の開始点）
└── feat/step-01-foundation
    └── feat/step-02-manifest
        └── feat/step-03-image-trace
            └── feat/step-04-qwen-observation
                └── feat/step-05-agent-memory-controller
                    └── feat/step-06-reproducibility
```

各Step branchは、直前Stepの検証済みbranchから作る。micro Stepはbranchを増やさず、現在のStep branchへ個別commitする。Step末尾のtestが失敗した場合は次のbranchを作らない。

## 全micro Stepに適用するcommit文章規約

commit titleは既存計画のmicro Step名をそのまま使う。titleの後に、日本語で5〜6行の本文を必ず付ける。

```text
<type>: <micro Step title>

対象: このcommitが扱う機能またはファイル。
変更: 追加・変更した振る舞い。
理由: この変更が必要な研究上または実装上の理由。
検証: 実行したtest、または未実行の理由。
影響: 既存挙動・artifact・依存関係への影響。
次: 次のmicro Stepで確認または実装する内容。
```

`対象`から`次`までを本文の6行とする。検証前のcommitでは、`検証: 次のmicro StepまたはStep末尾で実行予定。`と明記する。outputs、dataset画像、model weight、credentialはcommitしない。

## Step 5: Agent Memory Controllerを追加する

### 目的

Step 4で得たframe-level observationを入力に、AgentがMemory操作を選び、検証可能なReducerがStateを更新する。観測、action、Memory before/after、根拠を同じframe traceへ保存する。

### Branch

`feat/step-05-agent-memory-controller`を`feat/step-04-qwen-observation`から作成する。

### Micro Step

1. `feat: add agent state and action contracts`
   - text Memory、operation enum、reason、uncertainty、observation referenceを表す構造化contractを追加する。
2. `feat: add deterministic memory reducer`
   - action schemaを検証し、previous Memoryとcurrent observationからnext Memoryを組み立てるReducerを追加する。
   - Reducerはモデルを呼ばず、同じ入力に対して同じ状態遷移を返す。
3. `feat: add qwen agent policy`
   - Qwenへ`question + previous memory + current observation`だけを渡し、1 actionを構造化出力させる。
   - current imageはStep 4のobservation生成時だけに渡し、policyには渡さない。
4. `feat: append agent decisions to trace`
   - action、reason、Memory before/after、validation結果、prompt version、model identifierをframeごとに保存する。
5. `test: cover causal agent state transitions`
   - fake observation modelとfake policyで、action順、Memory遷移、future入力の不在、invalid actionのfail-fast、replay可能性を検証する。

### Step末尾のtest

- fake model / fake policyによるunit・integration test。
- 実Qwen policyは、Step 4の実観測trace取得後、ID 224の1 frameだけで短時間確認する。
- 5-frame以上のAgent run、Memory品質評価、final QAはこのStepの自動検証に含めない。

### 完了条件

各frameについて、Observation、Agent action、Memory before/afterが因果順に追跡できる。入力traceを再生したとき、Reducerが同じMemory遷移を再現できる。

## Step 6: 再現性と実行手順を整える

### Branch

`feat/step-06-reproducibility`を`feat/step-05-agent-memory-controller`から作成する。

### Micro Step

1. `docs: document decode-only run`
2. `docs: document qwen observation and agent run`
3. `feat: add agent-aware run metadata manifest`
4. `test: verify reproducible agent trace metadata`

各commitは上記の日本語6行本文規約に従う。Step末尾ではrepository全体のunit test、compile/import check、decode-only smoke、利用可能な環境でのみ1-frameのQwen observation + agent smokeを実行する。

## Blocking / Non-blocking

### Blocking

- Step 5開始前に、Agent policyを観測モデルと同じQwenの別callで実行するか、別のtext-only modelで実行するかを確定する。初期案は同じQwenを別callで使い、観測とactionのprompt・traceを分離する。
- manifest由来の質問・選択肢をAgentへ固定で渡すことを確認する。初期案では外部`--question`で差し替えない。

### Non-blocking

- text Memoryの具体的なMarkdown/JSON表現は、Step 5.1のcontract内で最小の既存styleに合わせる。
- Qwen policyのdtype、device map、generation上限はCLI引数化し、研究比較の固定値にはしない。

## Active Agentへの将来拡張

次にどこを見るかをAgentが実際に選ぶためには、frame skip、次chunk長、再観測、停止など、以後の観測計算を変えるactionを導入する必要がある。その時点で、同一観測budgetのbaseline、停止時の評価、予測失敗時の振る舞いを別specで確定する。

## Approval Gate

この追補はdraftであり、branch作成・実装・commit・実Qwen runを許可しない。実装へ進む前に、Step 5を初期repository計画へ含めること、Agent policyを同じQwenの別callとして始めること、commit本文6行規約を承認する必要がある。
