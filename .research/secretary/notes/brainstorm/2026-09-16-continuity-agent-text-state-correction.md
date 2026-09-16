---
date: 2026-09-16
topic: egocross-continuity-agent-text-state-correction
status: exploratory
project: agentic-streaming-videoqa
supersedes: 2026-09-16-continuity-hypothesis-agent.md の前画像入力案
---

# Continuity Agentの過去画像入力を使わない修正

## 修正理由

直前画像を現在画像と一緒にVLMへ渡す案は、future frameを使わないため因果的ではある。しかし今回の基礎経路では、VLM観察の入力を`question + options + current frame + current frame metadata`に限定している。また研究上は、過去を保持する媒体をtext stateとして比較したい。過去のraw画像を再入力すると、この入力境界とMemory比較条件を崩す。

したがって、次段階のAgentは過去画像を保持・再入力しない。

## 修正後の因果状態遷移

```text
observation_t = VLM(question, options, current_frame_t)
action_t = Agent(question, state_{t-1}, observation_t)
state_t = Reducer(state_{t-1}, action_t, observation_t)
```

- `observation_t`の画像入力は常にcurrent frame一枚だけである。
- `state_{t-1}`はtextだけから成り、raw画像・画像embedding・未来情報を含まない。
- `state_t`は場面要約、event log、未確定仮説、`watch_next`を持つ。
- `watch_next`は「次frameで確認する対象」をtextで表す。次時刻のAgentはそれをcurrent observationと照合し、仮説を確定・更新・保留する。

## 行動

Agent policyは`ADD`、`UPDATE`、`KEEP`、`FLAG_UNCERTAIN`、`CLOSE_EVENT`から一つを選ぶ。

- `ADD`: 新たな事実または仮説をstateへ加える。
- `UPDATE`: 既存の場面要約、event、仮説を新しい観測で更新する。
- `KEEP`: current observationが既存stateを変えない。
- `FLAG_UNCERTAIN`: 判断できない仮説を根拠付きで保留する。
- `CLOSE_EVENT`: `watch_next`で追跡していた出来事を確定または否定して閉じる。

## Agentらしさと限界

Agentは前時刻に作った`watch_next`を次時刻の判断へ引き継ぎ、何を確認するかをtext stateとして制御する。過去画像を再入力しないため、VLMは毎時刻current image一枚しか見ない。一方で、frame選択、skip、再観察など以後の計算を変えるactionはまだ持たない。これらは別の研究判断と観測budgetが必要な将来拡張とする。

## 次のspecで固定すること

1. observation modelとagent policyを、同じQwenの別callにするか、一つのcurrent-image callでまとめるか。
2. text stateのJSON schemaと、各actionに対するdeterministic reducer規則。
3. state textの長さ上限と、上限到達時の更新規則。
4. fake model testと実Qwen smokeで記録するtrace schema。
