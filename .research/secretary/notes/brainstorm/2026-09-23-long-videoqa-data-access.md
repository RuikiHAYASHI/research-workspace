---
date: 2026-09-23
project: agentic-streaming-videoqa
source_todo: "LongVideoBench / MLVUを別サーバの助教ディレクトリから利用する方法の検討"
topic: long-videoqa-data-access
status: exploratory
tags: [brainstorm, research, dataset, reproducibility, access]
---

# 長尺VideoQAデータの利用方法

## 結論

助教の管理するデータを無断でコピーしない。助教またはデータ管理者から、研究利用・読み取り専用参照・必要なら複製の許可を得たうえで、まず共有ディレクトリを読み取り専用で参照することを第一候補とする。

共有参照が安定しない、公式取得元・版・完全性を確認できない、または実行時の読み込み性能が不足する場合は、公式配布元から自分で取得する。助教のコピーを自分の領域へ複製するのは、公式版と照合済みで、管理者が複製を明示許可し、共有参照では目的を満たせない場合に限る。

## 判断基準

| 方法 | 採用条件 | 利点 | 注意点 |
| --- | --- | --- | --- |
| 共有ディレクトリをread-only参照 | 管理者許可、安定したmount、公式版・版情報が確認できる | 容量と転送を節約し、研究室内で同じデータ版を使える | データ削除・移動、I/O競合、別サーバへの接続可否を確認する |
| 公式配布元から自己取得 | 共有参照が不安定、版不明、管理上の独立性が必要 | 取得手順と版を自分のrunに対応づけられる | download容量・時間、ライセンス同意、保存容量が必要 |
| 助教のコピーを複製 | 管理者が明示許可し、hashまたはmanifestで公式版と照合できる | 転送が公式downloadより速い場合がある | 非公式な前処理済み版や混在artifactを持ち込まない。Git管理しない |

## 必須の確認事項

1. 助教へ、対象dataset名・想定用途・read-only参照または複製の希望を伝え、許可を得る。
2. 公式取得元、dataset version / release、license、manifestまたはchecksumを確認する。
3. data rootは新規リポジトリ外のユーザー管理データ領域に置き、Gitへ追加しない。
4. run metadataには、dataset名、取得方法（shared-read-only / official-download / approved-copy）、version、manifest hash、video/question IDを残す。個人ディレクトリの絶対pathは公開用artifactに含めない。
5. LongVideoBenchで字幕を使う場合は、時刻整列済みの過去字幕だけを入力し、未来字幕を渡さない。

## 根拠

LongVideoBenchの公式repositoryはCC-BY-NC-SA 4.0・非商用利用を指定し、公式取得手順と動画・字幕を提供する。MLVUもCC-BY-NC-SA 4.0かつ研究目的のみの利用を指定し、raw videoの権利が配布者にないことを明記している。したがって、研究室内の所在だけでは利用権限・再配布可否・版の保証にならない。

## 次に確認すること

- 助教のデータがLongVideoBench / MLVUのどのreleaseで、元の公式ファイルから変更されていないか。
- 読み取り専用の共有参照を許可できるか。
- 新規実装repoから別サーバのデータ領域を安定して読む必要があるか、またはコピーが必要か。
