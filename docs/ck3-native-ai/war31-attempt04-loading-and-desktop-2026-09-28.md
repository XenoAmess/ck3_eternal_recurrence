# WAR31 attempt-04：加载窗口与桌面证据

2026-09-27 的 `D:/ck3-research-artifacts/war31-live-20260927/attempt-04` 从已核对的 R0197 save/driver 与 R0221 原始 DLL/injector 重新准备，显式 `xar_off` 的 no-launch preflight 为 READY。派生 driver SHA-256 `754B9B1F86C3F165A6ED14967822A4A2E643816693DC9DA0A81E5DF1B10A51F5`；preflight 报告 SHA-256 `F3617B841A564AB49501F5BF8B55CD2558D8537CCC174ED994F3D88B3E333DE1`。这份尝试的准备状态与之前失败的 attempt-03 分开保留。

原 R0197 检查点在 CK3 PID 14216 启动，原生会话报告的冷启动 save SHA-256 仍为 `1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A`。MCP 的两个独立首次只读快照请求都返回 `native game state is not available yet`，原始响应分别保留在 `live-mcp-controller/before-snapshot.json` 与 `live-mcp-controller-02/before-snapshot.json`。此时没有 WAR31 同帧读回、硬件附加或投降。CK3 的隔离 `debug.log` 后续在 15:51 UTC 出现游戏 GUI 日志，`game.log` 在 15:50 UTC 写入；因此更符合加载时间超过早期只读查询时机。到 15:57 UTC 本机再次检查时 CK3、injector 和 operator 进程均已不存在。没有把启动成功或只读工具响应误写成动作成功；跨 attempt 的 `war31-one-shot-submission-reservation.json` 仍不存在。

这次还暴露桌面截图新鲜度问题：加载期多张原始截图呈现同一画面与停滞时钟，不能仅凭截图生成时间认定实时。此后按 [Steam 新鲜帧门禁](steam-offline-frame-freshness.md)使用窗口位移，外置 `attempt-04/desktop-recovery-02` 的回执为 `fresh_frame_needs_offline_visual_review`，图像 SHA-256 `205FBB91AFD1DC4415CF6F6D62CA84166946178879973E65F85C74FA466142E7`；人工查看该次新图左下确有“离线模式”。该恢复未重启 ToDesk、未改变 Steam 模式、未启动 CK3。

新 `attempt-05` 另从原件准备、预检、冻结采样输入。其第一次、第二次 Steam 窗口位移虽然证明桌面截图响应，却只得到全黑客户端，不能当作离线证据。在确认无 CK3、injector、录制进程且持有屏幕租约后，Steam 客户端受控关闭并以 `-offline` 重启；通过本地 `steam://open/library` 唤出库窗口。`attempt-05/desktop-recovery-03` 的新鲜帧 SHA-256 `94107235DB9A6D227B10A8171A223FA097868045EA6574A725EC760627A18E2A`，人工查看左下明确显示“离线模式”。这才作为 attempt-05 实机启动前的 Steam 离线画面证据。受管会话改用较长时限，地图未就绪期间只做可归档的只读轮询。
