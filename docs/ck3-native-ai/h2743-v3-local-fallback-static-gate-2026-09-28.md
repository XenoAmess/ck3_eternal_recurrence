# H2743 v3 本机备用路线静态门复核

2026-09-28 12:43 UTC 只读复核：外置 `D:/ck3-research-artifacts/war31-h2743-20260928/local-readonly-v3-static-admission-02.json`，SHA-256 `DBB4BE3A97F1E7B118F009CDC1F905D6DC866AB948D0000E9056775467949366`。本轮**未领取屏幕、未采 Steam 画面、未运行 official no-launch/profile/rebind、未启动 CK3**。E2 录制占屏依上级协调仍成立；任务总线瞬时 `screen_owners=[]` 和进程查询无 CK3/OBS/ffmpeg 不能视作屏幕释放、Steam 离线或可抢占的证据。

本次 `--check-static` 对精确 H2743 save `A501…10E9`、driver `F314…B150`、family sidecar `12D7…5724`、原件 DLL `8C3A…8A5C`、只读候选 DLL `FD8B…1470`、injector `C89F…84FF`、CK3 EXE `2D00…DB86` 返回 GREEN，并静态调用分支 CLI 顶层、`native-session`、MCP 的 `--help`。完整 SHA 和步骤参见 [v3 运行单](h2743-dejure-readonly-live-v3-runbook-2026-09-28.md)。OneDrive `WAR/H2743-EXIT-READONLY-V3-20260928/` 还没有真正的 `RECEIVER-ACK.json` 或 `RESPONSE-READONLY-V3-*`；名为 `RECEIVER-ACK-CONTRACT.md` 的指导文件不能算 ACK。

首个外置静态检查 attempt 在解析安装的任务总线 `list` 输出时暴露老任务摘要含非 UTF-8 字节；严格 `subprocess.run(text=True, encoding="utf-8")` 的读取线程发生 `UnicodeDecodeError`。#448 v3 runner 原本对 `list` 与 `heartbeat` 使用同一模式，因此本轮将两处改为捕获原始 stdout bytes，再用 `utf-8-sig` / replacement 解析 JSON；任务 ID、资源名和控制键仍是 ASCII，JSON 结构损坏仍会拒绝。测试新增混合编码摘要样例；runner gate 测试普通 4/4、`-O` 4/4。此修复只防止非关键摘要字节使租约读取误 RED，不放宽独占 owner、heartbeat 或清理后的成功门。

正式排屏条件保持：先由 E2 负责人明确释放占用，再由 H2743 本任务取得唯一 `ck3-screen:acquired`；全新 attempt 运行 `--prepare-no-launch --attempt-name attempt-N-dejure-baseline-no-launch --task-id <任务ID>`；随后取得当前 Steam 位移画面并人工确认“离线模式”，填写与新截图绑定的 gate；最后才按 v3 运行单执行唯一 `query-defender-de-jure-exit-terms-v1-16777231` 双读。任何源哈希、同帧身份、租约或退出清理不符都保留 RED attempt。终战具体 title/vassal/F/资源 delta、停战与续战风险仍 unknown；不提交投降或其他动作。
