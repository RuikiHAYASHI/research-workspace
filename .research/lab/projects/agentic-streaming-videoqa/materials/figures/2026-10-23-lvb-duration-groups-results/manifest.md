# Figure Manifest

## Source

- Material: ../../2026-10-23-lvb-duration-groups-results-mtg-materials.md
- Source data: Workbenchリポジトリ `2026_10_hayashi_pre_study_agent_system_workbench` の `outputs/2026-10-22_23-39-02/v6g/*/answers-a3.jsonl`（入力 `none` と `records`）
- 作図スクリプト: このセッションの一時スクリプト（matplotlib）。数値は資料の第4.4・4.5節の表と同じ。

## Figures

| file | type | purpose | source | note |
|---|---|---|---|---|
| 01-accuracy-by-group.png | experiment（MTG用） | グループ別に、記録なし→記録ありの正答率と95%信頼区間（Wilson）を示す | answers-a3.jsonl | 点線はチャンス |
| 02-accuracy-by-category.png | experiment（MTG用） | カテゴリ別（4グループ合計）の記録の効果を示す | answers-a3.jsonl | O3Oだけ低下 |
