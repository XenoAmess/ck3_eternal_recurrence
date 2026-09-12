# R493/R494 Stage 10 原版强制退休来源 RED（2026-09-12）

## 结论

R493 完成前台预热并终止后，R494 是唯一 gameplay 实例。R494 使用修复后产品树和 v6 source receipt，通过 loader、native、exact mount 与 material-error 门；在从 `date_raw=53154120` 前进至 `53156232` 的第 88 个游戏日遇到原版 `ep3_interactions_events.0630`。事件精确身份全部匹配，自动玩家保持暂停，没有选择唯一按钮，并返回 `SCENARIO_INVALID / scenario-invalid-product-precondition`。

这是 Stage 10 来源场景失效 RED，不是 B1 exact-roster 修复复发。R494 在失效前完成 29 次进度观测，日志出现 7 次 `performance season published`，修复前同类 final-callback compaction failure 只出现 1 次；但原版事件会移除玩家经理的 governor position 并改变验收依赖的 roster，所以 `.120` 产品结果只能记为 `NOT_EVALUATED`，不能据此宣称 B1 GREEN 或 RED。该来源永久退出 120 日 Stage 10 用途，不得原位 retry、扩大期限或自动点击事件绕过。

P1 保持 **`8/9 = 88.9%`**，唯一未完成项仍是玩家可见 `zg361mg.120`。P2 最终宣传视频继续 `LOCKED`。

## exact-build 原版定义与调用链

- 游戏版本：CK3 `1.19.0.6`。
- `ck3.exe` SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- 事件定义：`Crusader Kings III/game/events/dlc/ep3/ep3_interactions_events.txt:4469`，文件 SHA-256 `B36D7898D6F60983CD3EA359C768925EFE26DB6E9A0734D99A4C614EDE8AB1C4`。
- 调用方：`Crusader Kings III/game/common/character_interactions/06_ep3_interactions.txt:6512` 的强制 governor resignation 接受路径触发 `.0630`；文件 SHA-256 `00BEA6E5C880BAB47B0F7DB55BE3D17156547787F6887E5AB22C2DC184A43CC0`。
- `.0630` 只有一个 authored/enabled option。该 option 内部对 `scope:recipient` 执行 `governor_resignation_title_transfer_effect = yes`；它不是已经完成变更后的无副作用确认按钮。
- R494 事件上下文：instance `19`，actor `36354`，recipient/root/player `29037`，`option_count=1`，三类备用 character scope 不可用，`hook` 与 treasury-cost typed scope 均匹配既有 exact-build 合同；19 项 identity check 全部为 `true`，`selection_attempted=false`。

通用原版事件记录 `records_embedded_b.py` 已在本轮之前把该事件定义为 `scenario-invalidating-fail-closed`，reason code 为 `governor_resignation_title_transfer_breaks_manager_roster`。因此本轮没有新增事件处理代码：现有最小、可复用、安全合同已经生效。修改它去选择按钮会直接破坏 `stable_player_manager_governor_position_and_direct_vassal_roster`，属于错误修复。

## 实机证据

运行目录：

`Z:\ck3_mod_rewrite\_runtime\p1-stage10-player-publication-r493-r494-0b38d65-20260912`

| artifact | SHA-256 | 结果 |
|---|---|---|
| `activation.json` | `A90671228A34F528F383876F056FD61D5E7ABC36B8BC2354A505FF85A0CABB20` | v6、修复后产品树、唯一 handoff/run/cleanup 请求 |
| `live-artifacts/01_loader_native_readiness.json` | `8E078245F104D78491CBB5FA31D8DC6D358235F74A94E534E3BF06C197EBDD9F` | GREEN |
| `live-artifacts/03_loader_gate.json` | `375A4864270772B76C8E78B8D330A3E61D0609A8D9A064070F4DE93ED583BD33` | GREEN |
| `live-artifacts/stage10/stage10-player-subject.json` | `8AE3638D8EDB90F09DDA3AB1DDE6A970BE6445342471912847F1B3F4743C8084` | direct scenario-invalid result |
| `live-artifacts/stage10-player-subject-red.json` | `41FFAE51B7972B64FC78C83AA452D8D74483D46D196DF989C5D76EF5F6739D1D` | managed RED，158,679 bytes |
| `live-state/profile/logs/debug.log` | `AE20D196C080C667DB9B11DECE30D48BA8FCD83E8F7E7594DC8D0DBAD0F8555B` | 7 次 publication、1 次 compaction failure |
| `live-artifacts/09_phase2_native_session_cleanup.json` | `3A1264A49AA55AA6C25D2745E2F6DF9103DFDD2E96BF1771192ACC71F4EAA759` | canonical cleanup GREEN |
| `live-artifacts/stage10-player-subject-managed-cleanup.json` | `9FD5B57DE2C7495245FFE865853B56F3628A0960D36DD536CBA971A9ABA60487` | managed cleanup GREEN |

正式 handoff、run 与 cleanup request ID 分别为 `r493-r494-stage10-handoff-1`、`r493-r494-stage10-run-1`、`r493-r494-stage10-cleanup-1`；job ID 为 `febd3707-a4c0-4ef4-884b-4e295b66c785`。当前轮次 R494 PID `56280` 已终止，旧轮次 R493 PID `133252` 已终止；CK3、受管作业、Operator MCP 和端口 `12443` 均为零。

## 最小验证与下一来源

只重放与本事件有关的两个确定性测试：

```powershell
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -m pytest ck3_autonomous_player/tests/unit/test_zhongguo_promotion_source_progress_v1.py::test_product_path_stops_before_scenario_invalidating_interrupt ck3_autonomous_player/tests/unit/test_zhongguo_promotion_source_progress_v1.py::test_product_path_rejects_interrupt_identity_drift_before_action
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe -O -m pytest ck3_autonomous_player/tests/unit/test_zhongguo_promotion_source_progress_v1.py::test_product_path_stops_before_scenario_invalidating_interrupt ck3_autonomous_player/tests/unit/test_zhongguo_promotion_source_progress_v1.py::test_product_path_rejects_interrupt_identity_drift_before_action
```

normal/optimized 各 `2/2` GREEN。没有运行全量测试，也没有为这个事件启动额外 CK3。

下一步先离线扫描同一冻结世界中其他 active B1 manager，要求新的玩家经理在 exact tuple、天朝/governor 拓扑和单玩家身份上成立，并排除已知会在 120 日内移除该玩家官职的来源。只有离线准入和现有 exact-build 证据能证明候选值得启动时，才执行新的原生玩家切换与 checkpoint 捕获；新的 `.120` 尝试仍只允许一次有界运行。

本轮没有修改公共 MCP schema、DLL、游戏文件、加载顺序或 open_kaishek 接口。原版事件合同本身已经是可复用通用资产，因此无需新增一次性脚本或兼容层补丁。
