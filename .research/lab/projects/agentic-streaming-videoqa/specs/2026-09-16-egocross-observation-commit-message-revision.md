---
date: 2026-09-16
project: agentic-streaming-videoqa
status: draft
topic: egocross-observation-commit-message-revision
source: 2026-09-16-egocross-observation-agent-addendum-plan.md
last_updated: 2026-09-16
---

# EgoCross Observation Prototype: commit本文規約の改訂

## 適用範囲

この文書は`2026-09-16-egocross-observation-agent-addendum-plan.md`のcommit本文規約を置き換える。branch、Step、micro Step、testの計画は変更しない。

## 改訂した規約

- commit titleは既存計画のmicro Step名をそのまま使う。
- titleの後に、日本語で5〜6行程度の本文を付ける。
- 本文を`対象`、`変更`、`理由`などの定型ラベルへ分けない。
- 各行で、どのファイル・機能に何を実装または変更したか、意図、確認結果、残る注意点を自然な文章として記録する。
- 未検証なら、その事実とStep末尾で確認する予定を本文に書く。
- outputs、dataset画像、model weight、credentialはcommitしない。

## 本文例

```text
feat: add manifest loader

`egocross_observation/manifest.py`にEgoCross manifestの読込処理を追加した。
指定IDのrecordだけを選び、JSONに記載されたframe pathの順序をそのまま保持する。
空の画像列と必須key不足は、読込時に明示的な例外として扱う。
このcommitでは画像decodeやQwenの呼び出しは追加していない。
合成manifestを使うunit testを加え、record選択と順序を確認した。
次のmicro Stepでdata root下の実画像path解決を実装する。
```

本文はこの文体・粒度を基準にし、各micro Stepの実際の変更内容に合わせて書き換える。
