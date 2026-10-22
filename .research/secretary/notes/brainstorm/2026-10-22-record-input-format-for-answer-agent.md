---
date: 2026-10-22
project: agentic-streaming-videoqa
topic: 回答Agentに集約した記録をどの形（Markdown・表・JSONなど）で渡すか。後で正答率で比べる
status: idea
tags: [answer-agent, input-format, markdown, aggregation, longvideobench, later]
---

# 回答Agentへの記録の渡し方（Markdownで渡してよいか）

- 経緯（2026-10-22、林との話し合い）: 林「実際にClaudeやCodexに渡すプロンプトはMarkdown形式なので、モデルもMarkdownを案外理解できるのでは」。
- 林の希望: **後でやりたいので記録しておく**（回答Agentができた段階で行う）。
- 前提（2026-10-22時点の仕組み）: コードが読むのはJSONだけ（記録は `records/<動画>/result.json`、集約は `aggregations/stage_b/stage_b.json`）。`record.md` や `stage_*_<動画>.md` は人が見るための形で、コードは読み返さない。回答Agent（モデル）には、コードが `stage_b.json` から作った文字列を渡すことになる。その文字列の形はまだ決めていない。

## 話し合いで出たこと（AIの考え。根拠のない部分は推測）

Markdownで渡すのが合っていそうな理由:
- LLMは学習データでMarkdown（README・ドキュメント・チャットの出力）を大量に見ている。Qwen3-VLも見出し・箇条書きを理解できるはず（推測）。
- 記録Agent（Qwen3-VL-4B）は、すでに `- [F1-F3] EVENT: …` というMarkdownの箇条書きを、暴走なく書けている。
- JSONより短い。JSONは記号とキーの名前が毎行に付き、トークンが増える。小さいモデルほど、括弧の対応を追いながら読むのが苦手な印象がある（推測）。

気をつけたいこと:
- 表（`stage_b_<動画>.md` の第6節のような形）は、`|` と空の欄がトークンを食い、列が多いと小さいモデルが値と列を取り違えるおそれがある。1行1イベントの箇条書きの方が安全かもしれない。
- 同じ内容でも、プレーンテキスト・Markdown・JSON・YAMLで精度が変わるという報告がある（2024年ごろ、Microsoftの "Does Prompt Formatting Have Any Impact on LLM Performance?" など。**記憶にもとづく。原文は未確認**）。どの形が最良かはタスクとモデルによって違い、小さいモデルほど影響を受けやすい傾向があったはず（未確認）。
- 記録と質問の境目ははっきりさせる（Markdownの見出し、または `<record>…</record>` のようなタグ。AnthropicはClaudeにXMLのタグでの区切りを勧めている）。

分割統治の構成との相性:
- Markdownの見出しを時間の階層に使うと、「この範囲だけを担当のモデルに渡す」切り出しを、見出しの単位で機械的にできる。

```
## 00:00–05:00（要約）…
### 02:00–02:32
- [02:00.0–02:32.5] P05: woman in a beige turtleneck ... speaks in front of bookshelves
```

## 後でやること（実験の案）

- 回答Agentができたら、**同じ集約の結果**を2〜3通りの形で渡し、LongVideoBenchの正答率を比べる。
  - 候補: (a) 1行1イベントの箇条書き＋時間の見出し（第一候補）、(b) Markdownの表、(c) JSON。必要なら (d) XMLのタグで囲んだ形。
  - そろえるもの: 集約の結果、モデル、質問、回答のプロンプトの本文（渡す記録の部分だけを変える）。
  - 見るもの: 正答率、入力token数、回答の形式の誤り（Answer形式のvalidation失敗）、時間。
- モデルの再学習は要らないので、コストは小さい。論文で「なぜこの形で渡したか」を説明する根拠にもなる。
- 比べる前に、上の先行研究（プロンプトの形の影響）の原文を確認する。
