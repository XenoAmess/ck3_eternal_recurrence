# R0025 后记002：实际 Army / Route 构造递归；focused 修复通过，DLL/live 待验

本后记追加在首版 `REPORT.md`、`INDEX.json`、`raw-evidence.zip` 之后；首版原 bytes/SHA 全部保持。旧截止的“最终原因 NULL”是当时真实边界，本后记记录后来实际证据，不回写原包。加载源仍是 `720ef066ce5513875ca694201f7f70694988d81b`，不是已修复 DLL。

`COFF-BINDER-SYMBOLIZATION.actual.json` 把失败 DLL 的 RVA `0x547840` 定位到 `BindRouteImage12004`、`0x6c8030` 定位到 `BindArmyImage12004`；对应 COFF 与 DLL 的 804 / 4262 个非 relocation bytes 全部实际匹配。Route 的 reciprocal relocation 指向 Army，Army 的 reciprocal relocation 指向 Route。`FRAME-LOCATIONS.actual.json` 保存实际调用 `0x54799d → 0x6c8030` 与 `0x6c8e6c → 0x547840`，分别对应交替返回帧 `0x5479a2` / `0x6c8e71`；异常 RVA `0x71d8d7` 在 `__chkstk` 触页段。这些证据共同定位 **Army → Route → Army binding bundle 构造递归导致栈溢出**，发生在成功 pipe attach 之前。exception.txt 的 nearest-export `XarCk3BridgeStop` 并非实际函数调用证明；没有操作 factory 或业务事件。

最小生产修复把 Army 的 current-edge movement-rate callback 直接绑定到同一 `image_base + kCommanderCurrentEdgeMovementRateRva12004` typed leaf，解除 Army 再构造 Route 的回边。原 focused 回执 source base 为 `5d1b736f9279fd9f9e10d6623e2f1e3d1b01adb3`，新 army leaf 实际编译后与原 R25 unchanged route/dependency library 链接。完整 Army / Route constructors 实际 fixture exit **0**：两者 enabled、storage一致、current-edge speed同叶，zero base / wrong EXE继续拒绝；没有解引用或执行游戏函数。原 compile/link成功而 outer exit **1**，原因是实际 Defender `settings_failed`，原回执保留。

后续 final CMake target 显式链接 `xar_bridge_protocol`，匹配已经实际编译执行的 fixture libraries；production army / fixture source保持相同，没有新增 compile或 fixture runs。完整小 patch、原源码叶、stdio 与 source补充分别归档。**修复 runtime DLL 尚未构建，runtime PASS、新 cold qualification 均 NULL**；focused通过不能追认旧失败 attach，也不能作为实机修复通过。

ROOT 原 boundary CHECK 与 CREATE 均实际 exit **0**；CREATE finished `2026-10-07T20:14:37.477759Z`。原 `PREVIOUS-BOUNDARY.actual.json` 保留 `ROOT_REVIEWED_ACTUAL_CRASH_ENDED_RELEASED_RED_BOUNDARY`：helper原 HANDLE/exec退出0、无强制结束、fresh identity absence、screen released/vacant；game原 HANDLE未捕获，game exit code / typed normal exit / callback / autosave verified仍 NULL。最终 Steam离线审阅发生在 CAS释放之前，原 `final_offline_review_is_postrelease=false` 保持，不把它改写为释放后截图。

首版 exact720 CI 结论继续保持：Li Yu / Linear SUCCESS，Official Runner为独立 RMTM合同测试FAILURE。本后记没有查询新 CI、重跑 tests/build、操作 MAIN/Git/SDK/CK3/进程/屏幕/总线，未读复制 dump、binary或存档正文。B0 SAVE、当前87、formal、newT、C3、I4仍 NULL，whole mod **NOT_GREEN**；75%仍只表示工作量估计。

`INDEX002.json` 串联首版 pins和本后记原件；`cause-supplement-002/raw-evidence.zip` 保存新增原 bytes，原始frame文件的早期“cause not yet proven”状态也不改写。`cause-supplement-002/ARCHIVE-VALIDATION.actual.json` 记录必要解包核验。后续新 DLL / 新冷载结果另追加，不能预填。
