# R0244 本机 War4 同帧 v3 只读复测准备（2026-09-27）

这是对 [R0244 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-INPUT-R0244-20260927.json) 的**独立本机场景通路检查**。原请求是 War48、Army16777237 对 Army16777417、省份2640；本检查点是 War4、Army18 对 Army24、省份2638，绝不能将两者的结果互代。原 War48 存档、driver sidecar 和匹配 DLL 未在这台机器上找到；本尝试也不执行一跳移动、战斗或胜率验收。

## 冻结输入与本次状态

源清单 [`war-r0244-local-v3-source-manifest.json`](war-r0244-local-v3-source-manifest.json) SHA-256 `76D41D89165A305A2A4A9FFB3707E846BB35D439F22F58FC18386954FE34F13F`，锁定 CK3 EXE `2D00FF31…F83DB86`、058 原版静止检查点 `91CEE43C…BEDD592`、save 回执 `CBDC1F1B…71B`、同帧快照 `3F247A89…90A9`、063 曾使用的桥 DLL `7CCF1E7C…89CC3`、注入器 `C3110B4F…977B4`。回执记录 `pure-vanilla-enabled-mods-empty`、`xar_off`、raw date `53144520`；快照记录暂停状态、玩家角色29829、War4、可控静止 Army18 在2619、非撤退 Army24 在2638，以及完整敌军 ID 集合。预检同时逐文件重算上述 SHA，而不是只相信源清单。

`tools/war_r0244_local_v3_probe.py preflight` 已完成**无游戏**预检，产生新的外置目录 `D:/ck3-research-artifacts/war-r0244-local-v3-attempt-20260927-02/input-freeze.json`；其中 `live_status=NOT_STARTED`，保存源文件 SHA、采集脚本 SHA `0BB22F6E…5F45A6`、采样脚本 SHA、精确 capture/probe argv 和待满足门禁。目录内尚无 `ck3-output`、`ck3-state`、Steam 离线回执或实机查询回执。旧 attempt 063 已有独立同帧 v3 成功历史，但它的后续策略选择没有提交一跳移动；本记录不把旧证据说成新采集。

## 已准备的受管步骤

1. 由协调者取得独占 CK3/屏幕资源，确认新的 Steam 离线实时画面，并把经审阅的 `steam-offline-receipt.json` 放入**本次**外置 attempt；不得复用旧截图或旧回执。
2. 核对 `input-freeze.json` 的 `capture_argv` 后，在该计划的 `capture_cwd` 中单独执行受管 `capture_session.py --capture`。此步尚未执行；桥须报告 exact build match、同一 EXE SHA 和 `game.command.query-combat-simulation-inputs-v3-N`。失败时按受管流程清理进程并保留 RED 工件。
3. 待新 session 的 `interactive-requests` 和 `interactive-requests-responses` 出现后，单独执行计划里的 `probe_argv`。采样脚本只发 `ck3_take_snapshot`、`ck3_get_capabilities`、`ck3_execute_step` 的原生路线预览、全敌军路线接触查询、精确 v3 查询，再读一次快照；最后发 `finish`。不发送 `move-army`、`resume-map`、`plan_turn` 或其他游玩动作。每个响应的连接代次、native/public revision、snapshot ID、episode run ID 必须一致；日期仍为 `53144520` 且暂停，兵团、省份、路线及 v3 的 scenario/completeness 必须匹配。任何失败保存单独 RED 回执，不能写 GREEN。

只有在实际新 attempt 产生 `v3-read-only-result.json`、原始六项只读响应和受管 session clean-exit 报告后，才能记为“本机 War4 同帧 v3 查询通路成功”。它仍不证明原 War48 配对、模型胜率、移动提交或下回合决策。原请求的正式验收还须原 War48 存档/driver/DLL 的精确配对及动作、读回、下一回合与恢复回执。

无游戏检查：`tools/test_war_r0244_local_v3_probe.py` 在普通及 `-O` 下均为 `2 passed`；覆盖错误源 SHA、重复 attempt、暂停场景/待处理交互、四个同帧字段和 v3 scenario 拒绝。`preflight` 实际重算全部六个源 SHA 通过；未启动 CK3，也未从 OneDrive 下载任何文件。
