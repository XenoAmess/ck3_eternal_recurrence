# R0025：首次 native 注入栈溢出 RED，运行占用已闭环

本轮加载源冻结于 `720ef066ce5513875ca694201f7f70694988d81b`；完整实机 ID 为 `bf-202609141645-5434332d4d--li-yu-dao--R0025`，execution `a18bad99-51be-48bc-9113-42318af64a13`，CK3 PID 19256。本报告保存实际失败与 operational closure，**whole mod NOT_GREEN**。75% 仅为此前工作量估计，不是通过率。

新 clean export 的 native 编译、五个 focused tests、source unchanged 与 exact private flags 均实际通过；SDK default21 / readonly23 / challenger24 / grant28 元数据实际取得。原构建 outer exit 1、Defender `settings_failed` 完整保留，不能标为全部构建门禁 GREEN。DLL、injector、EXE 和 runtime lib 的路径、大小与 SHA 来自原 `RESULT.json`，仅保留外置 refs。

实际冷载创建游戏并进入首次 attach。injector 本身 returncode 0、原子树已回收，但 native attach 失败，不能视为连接或快照验收成功。原崩溃目录为 `ck3_20261008_034235`，exception.txt 记录本地 `2026-10-08 03:42:37` 的 **C00000FD / EXCEPTION_STACK_OVERFLOW**，并有重复 DLL 栈帧。原异常把帧投影到 `XarCk3BridgeStop` 导出符号；这不能作为实际调用根因。最终 COFF/source 原因证明尚未并入此截止包，原因与修复验收保持 NULL，后续证据另加后记。

没有 B0 SAVE、存档正文扫描、当前 cold 的 87 protection 验收或业务回调；正式批准、newT、C3、I4 均 NULL。预备 checkpoint / capture / future-success author 的 source-only index 只表明准备，不能填补这些实际缺口。

截至原 closure summary 的 `2026-10-07T20:00:53.178263Z`，原 Client / keeper HANDLE wait 与原 Client / keeper / holder 执行均为 exit 0；crash reporter Cancel 回执、最后新鲜 Steam 离线原图审阅、identity absence、CAS release **3727** 与释放后任务列表均保存。CK3 原 HANDLE 未捕获，故 **game OS exit code、typed normal exit、autosave verified 均 NULL**；operational absence 不能替代 typed 正常退出 GREEN。最终离线审阅记录桌面时钟本地 03:54，审阅时间为 `2026-10-07T19:57:24.382103Z`。

同一 exact HEAD 的 [Li Yu CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37668163109) 与 [Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37668163129) 实际 SUCCESS；[Official Runner](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37668162860/job/112952663767) 实际 FAILURE。唯一失败为 `tools/test_reclaim_the_motherland_contract.py:579` 的 `test_phase_three_title_law_and_idempotent_save_migration`，期望 `add_title_law = single_heir_succession_law` 计数 2、实际 3（20 tests，failures=1、skipped=2）。此提交没有 RMTM changed path；未调查引入提交，未重跑 CI，也未把 Li Yu 的成功改写为总 CI 成功。

`INDEX.json` 逐项列实际来源、原 bytes/SHA 与 ZIP entry；`raw-evidence.zip` 按 SHA 去重保全原件。`critical-anchors/` 另保 failed attach、exception、closure summary 与 exact CI INDEX 四项原字节，解包核对见 `ARCHIVE-VALIDATION.actual.json`。135 MiB dump、游戏/构建二进制与存档正文永久留外置原位置，未读取或复制；截图仅保已有审阅与精确 PNG refs。原 RED、准备阶段错误、执行 argv/stdio 均保留，未覆盖任何旧 attempt。

本候选仅写外置文件；未写 MAIN、独立 Git 树或 HEAD，未操作 CK3、SDK、进程、Steam、屏幕或总线，未测试、构建、重播。后续必须取得实际原因修复、新 DLL 与新冷载结果才能获得相应 live credit。
