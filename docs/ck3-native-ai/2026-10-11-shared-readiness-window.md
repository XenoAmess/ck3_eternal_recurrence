# 共享验收的就绪窗口与终态回执

R52 的完整存档绑定在公共 readiness timeout 之后 1.582638 秒完成，hold 更晚；原客户端没有落盘自己的计时起点，无法精确对齐它与 host 的独立 900 秒窗口。[原场次](../li-yu-dao/2026-10-11-i4-r52-readiness-timeout.md)保持失败。

`CaseClient.wait_hold` 现在为每次 single-use case 创建 `readiness-window.json` 和 `readiness-window-result.json`，记录实际 UTC/monotonic 起点、原预算字段和值、monotonic 截止、观测时刻、elapsed、host phase、restore finished 与原 hold estimate，并绑定 run/screen/state/frozen argv/runtime manifest。UTC 截止只作估计，资格比较使用原 monotonic 截止。

预算仍从原 wait_hold 起点计时；原 `initial_plan_original_business is True` 分支继续使用原 timeout，其余使用 readiness_timeout。没有新增等待、续期或重放。guard/保留句柄之后的最终资格观测若已达到截止，记录 TIMEOUT 并抛出原超时，不返回 READY。ERROR/中断也先保留终态回执，再交原失败处理；回执只创建一次，不能覆盖旧窗口。

实际验证：7 项新边界检查，加 2 项直接受影响的既有合同检查均通过。后两项仅补齐 synthetic runtime/binding 字段和计时读取，不重跑其他矩阵；失败启动仍先保留真实句柄再拒绝业务，business budget 仍只接受 literal true。新 7 项已接入原静态 CI 的共享验收步骤。[实际回执与源码 LF pins](acceptance/2026-10-11-shared-readiness-window/INDEX.actual.json)。最初 Git patch check 因 CRLF context 拒绝，未应用；后继按精确源码 SHA 和单一归一化 hunk 采用。缺少测试文件的初次命令 exit2 原件保留，该次未执行测试。

本包仅 STATIC_ONLY；没有启动 CK3、改变既有冻结 Source11/O11 或重验 R52。下一新场还须精确 runtime 选择、新案例、容量及 public 准入；仅公共调用方改动不自动要求新导出或 native 构建。冷载耗时原因、统一 host/client 权威 deadline 和同轮观察批量提交仍待独立施工，本次不授速度改善或 I4 通过信用。
