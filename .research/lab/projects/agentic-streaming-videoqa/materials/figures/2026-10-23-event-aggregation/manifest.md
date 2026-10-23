# Figure Manifest

## Source

- Material: ../../2026-10-23-event-aggregation-mtg-materials.md
- Source data: Workbenchリポジトリ `2026_10_hayashi_pre_study_agent_system_workbench` の `outputs/2026-10-22_23-39-02/`
  - 画像: `records/v6g/600/2026-10-23_02-05-04/records/BtaVRhoLpC0_0/frames/`（01）、`records/v6g/3600/2026-10-22_23-39-02-2/records/JDtVwz1R-kI_0/frames/`（02）
  - ID: `v6g/600/aggregations/stage_b/stage_b.json`、`v6g/3600/aggregations/stage_b/stage_b.json`
- 作り方: 記録Agentに渡した画像を横に並べ、時刻・段BのID・記録の呼び方（短縮）のラベルを付けた。赤枠は本文で注目する枚。

## Figures

| file | type | purpose | source | note |
|---|---|---|---|---|
| 01-news-person-ids.png | MTG用再構成図 | 成功例（woman / man でも同じID）と失敗例（2人目にIDなし） | `BtaVRhoLpC0_0` 10/45/65/80/120 s | 5秒に1枚 |
| 02-vlog-person-split.png | MTG用再構成図 | 失敗例（同じ人が多くのIDに分かれる） | `JDtVwz1R-kI_0` 50/90/160/230/290/400/760/1120 s | 10秒に1枚 |
