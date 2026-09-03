# CK3 正式启动链恢复记录（2026-09-03）

## 当前结论

截至 2026-09-03 上午，CK3 本体和正式 Steam 安装没有被昨天的项目改动破坏。已在同一台机器、同一构建上完成无 Mod/无 bridge 的受控启动：窗口显示完整 CK3 主菜单，日志出现 `Frontend`，退出码为 `0`，进程树清理成功。

目前真正需要修的是“自动化启动链的判定和输入条件”，不能把 runner 的 RED 直接等同于游戏没有打开。

## 固定基线

| 项目 | 值 |
|---|---|
| CK3 安装 | `Z:\SteamLibrary\steamapps\common\Crusader Kings III` |
| EXE | `binaries\ck3.exe` |
| 游戏版本 | 1.19.0.6 / Steam buildid 23530548 |
| EXE SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| 正式桥接 A/B | `_runtime\formal-ab-oldbridge-20260903`、`_runtime\formal-ab-current-buildoff-20260903` |

## 已复现实证

1. `formal-baseline-launch-2026-09-03.md` 对应的无 Mod/无 bridge 基线达到 Frontend，正常关闭。
2. `formal-ab-oldbridge-20260903\report.json` 与 `formal-ab-current-buildoff-20260903\report.json` 都记录 Frontend、截图、WM_CLOSE、退出码 0 和 cleanup proven。
3. `manual-profile-current-skeleton-20260903` 的实时截图是完整主菜单；该次报告虽写成 `early_exit`，但其 `debug.log` 随后写入：`End loading of history`、`Setting idler 'Frontend'`、`Total startup duration`。这是观察器的假阴性，不是 CK3 未启动。
4. 昨晚一次运行在 CK3 已完成 bridge hello 后约 18 ms 被协议抓屏门禁主动停止；`4f1ab5a` 已加入瞬态重试并推送。
5. 之前正式 runner 还出现过错误游戏路径、Debug CRT/不匹配 DLL+injector、精简 profile 和旧存档续载参数。`63cf0ba`、`1d53683` 已加入 Steam 路径解析、桥接来源约束和 frontend-first 启动 plumbing；`11856da` 已要求正式 Phase2 显式提供完整 settings 与同目录 warm shader cache，缺失时在创建 CK3 前返回 typed RED。

## 本次受控验证边界

受控实例使用：正式 Steam EXE、冻结 Phase2 product+fixture、同目录 Release DLL/injector、完整已知 profile 和 warm shader cache；不载入旧存档、不执行 gameplay、不执行购买/商店动作。日志/窗口/bridge 证据和 WM_CLOSE 清理分开记录，不把窗口可见误写成完整 gameplay 通过。

## 尚未宣称的内容

- 这份记录不把 `native readiness`、Phase2 seed 或视频素材当作已完成。
- 当前 Phase2 seed contract 仍为 `blocked_seed_generation_required`；视频实机素材仍为 `0/8`。
- Release bridge bundle 的离线 CTest 仍有冻结合同/路径类失败，因此 manifest 保持 `built_skip_tests`，不能称为 tests-green。

## 11:20–11:30 正式 product+fixture 试跑

这轮使用了上表中的 Steam EXE、同目录 Release bridge/injector、完整 pinned profile、warm shader cache 和当前 product+fixture。CK3 在 11:20:03 创建进程，窗口在 11:22 截图中显示完整中文主菜单且 `Responding=True`；日志在 11:20:58 完成原版 881 个 on_action。到十分钟上限仍没有 `End loading of history`、`Frontend` 或 bridge-ready receipt，随后只对该精确窗口发送 WM_CLOSE/Alt+F4 并确认进程与 injector 消失。独立收尾记录见 `_runtime/formal-phase2-product-fixture-release-20260903-rerun/artifacts/close-evidence-20260903.txt`。

因此本轮结论是：**CK3 窗口/主菜单启动 GREEN；当前 279-file broad Phase2 projection 的正式 Frontend/native readiness 仍 RED/未闭合**，不能把它写成完整 gameplay 通过。

随后进行的 `product-no-scoreboard` 无 bridge 对照也在 880 个 on_action 后长时间停留，说明 scoreboard 暴涨是重要负载，但不是唯一阻塞；离线分组与精确旧版 51-file 基线见 `scoreboard-load-bisect-2026-09-03.md`，canonical 产品树尚未回退。

## 11:37–11:50 旧核心 + 当前 Release bridge 复核

为区分“CK3/桥接链故障”和“当前 broad 内容投影负载”，在不改 canonical 产品树的隔离旧核心（精确 51-file product）上，接入当前 matching Release DLL/injector 做了一次正式 Steam 受控启动：`_runtime/formal-phase2-legacy51-currentbridge-20260903`。该轮仅观察启动和桥接心跳，不载入存档、不执行 gameplay、不触碰商店或购买。

结果为 GREEN：日志在 03:50:04 UTC 到达 `Setting idler 'Frontend'` 与 `End loading of history`，窗口标题为 `Crusader Kings III`，收到 bridge hello；随后发送 WM_CLOSE，退出码为 `0`，`cleanup_proven=true`，CK3/injector/watchdog 进程树和控制文件均清理完毕。该证据证明当前 Release bridge 与正式 Steam 启动链本身可用；尚不能外推到当前 279-file broad Phase2 的 native readiness 或 gameplay。

## 下一步

1. 对当前 279-file broad Phase2 按离线分组（workforce、phase3、career、feedback、credit 等）逐组缩小长加载来源；每次最多一轮 CK3 启动。
2. 合入 observer 的 Frontend fallback（日志三标记 + 精确 CK3 窗口响应校验），避免再次把已显示主菜单判为超时。
3. 使用 `11856da` 的正式 Phase2 profile gate；没有显式 pinned settings 与完整 warm shader cache 时返回 typed RED，不再用精简 profile 假装可录制。
4. 仅在 broad Phase2 启动链和 seed 证据 GREEN 后，继续实机素材和两版视频制作。
