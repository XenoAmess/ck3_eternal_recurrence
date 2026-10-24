# 失败宿主继续使用原生正常退出通道

观察机器：`desktop-3fevhd2-1c74096080`。验证时间：2026-10-24 UTC；精确时间、源码 SHA、命令与日志见[机器可读回执](evidence/failed-host-normal-exit-2026-10-24.actual.json)。

R0001 的业务步骤因 `Actual independent progress scope absent` 失败后，宿主保留原场景并进入 hold。公共 `ck3_mod_acceptance_queue_control.py` 却只允许 `failure_shutdown=true` 的 `finish_hold`；该动作又要求原游戏已经退出并完成清理。于是合法的 `failure-exit-query-001`（`ck3_query_normal_exit_context_v1`、`args={}`、`fresh_revision=true`）在写入 controls 前被拒绝，形成退出次序阻断。原记录位于 `C:/ck3-dynastic-esotericism-20261024/common-runtime-a03/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0001/failure-evidence/FAILURE.actual.json`。当时后续 GUI 正常退出 0 的证据继续保留，不能改记为 typed 正常退出成功。

修复只维护既有共享路径：`normal_exit_host_terminal_v1.require_failed_host_normal_exit_plan_v1` 统一校验单条退出计划；公共 producer 与 `PlanClient.execute` 共同使用它。失败状态允许原有 context query、有限 request action 与 retained-process observe 三个工具，以及原有的失败结束 hold。正常退出工具继续经过原 `self.invoke`、MCP session、`GameplayBridgeService` 和 driver；没有新建服务、会话或游戏进程。实际 snapshot 可继续为省略 revision 的合法查询生成规范十进制 revision。

原 driver 的每个 action／原 PID 与进程创建时间的一次 claim、确认前原生 context 签名、原进程 retained handle、未知结果不可重放均保留。更换计划文件名、step ID、revision 或签名不能清除 claim。观察只读取已保留的原进程句柄；确认及观察结果继续使用完整 V2 回执，终态后不查询活体 snapshot。失败结束 hold 仍须等待独立的原 managed native-zero／thread-cleanup 证明。顶层错误、原失败步骤与 RED 不会被退出成功覆盖。

专用 CI step 已加入 `.github/workflows/rite-confirmation-sdk.yml`。本机在 C 盘隔离 Python 3.14 环境完整执行该 step 的七条命令，全部通过：两个生产模块 strict、真实宿主修改 AST 范围 strict，以及 29 个 unittest。新增五例经实际 queue CLI → 原 host hold/load/execute/invoke/call → 注册 MCP Client/server → 原 service → 原 normal-exit driver；原生 endpoint 和进程 API 均为明确的 synthetic fixture。覆盖实际 R0001 查询形状、prepare／confirm、pending observer、UNKNOWN 后新 ID／revision／签名重提被拒绝、原 handle 后续观察及失败清理收尾。

从修复前 Git HEAD 提取的原 producer／host 已真实重现拒绝并保留 RED；早期 10 秒测试 hold 过短、以及并发消费会改写 report 的夹具断言失败也保留。最终通过不追认这些失败。没有启动 CK3、修改 C 盘冻结 runtime 或取得新的实机资格；下一次产品 attempt 必须使用重新冻结的共享源码。

C 盘隔离验证目录闭场占用 327,964,655 B，获批子预算 512 MiB；容量、来源与 2026-10-31 用途复核时间写入回执。原始失败和当前可复核日志按通用存储策略复核，不以本记录要求永久保留派生目录。
