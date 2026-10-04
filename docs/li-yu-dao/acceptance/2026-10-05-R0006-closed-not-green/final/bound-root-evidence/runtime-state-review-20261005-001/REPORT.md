# R6 runtime state review 20261005-001

审查时间：2026-10-04T18:38:26.496709+00:00（UTC）。只读检查现存进程和文件，仅新写本外置报告目录；没有调用 CK3 native 接口、桌面输入、启动或停止游戏/keeper/queue、任务总线 mutation、Git 或读取 auth secrets。

## 当前结论

- 旧 queue 与 lease keeper 不可继续使用。psutil 当前相关 Python 进程仅本次审查自身；不存在 `screen_lease_entry_r0006.py`、`persistent_native_mcp_queue.py serve`、`r6nativequeue` runner 或 `ck3_native_profile_mcp.py` 服务进程。
- CK3 PID 12500 的实际 create_time 仍为 1791115363.105566，argv 指向 live-attempt-006/userdir。`status=running` 是 OS 进程状态，不证明游戏模拟在运行或暂停。HWND 2491650 只在原 guard snapshot 中留存，本次没有重新做桌面/窗口取证。
- 屏幕记录只剩 `ck3-lyd-live-007-20261004` 一条 `running + ck3-screen:acquired`，序号 2808，最后更新 2026-10-04T17:19:00.588608+00:00。审查时已过 4765.908 秒，超过现行 600 秒合同，因此它是未释放的过期记录，不能视为新鲜独占。全量 task snapshots 没有其他 screen claim；events 没有该任务在此序号后的事件。直接文件读取不是加锁 CAS 授权。
- keeper 末次 OWNED_CAS 回执为 sequence 2808（2026-10-04T17:19:00.588608Z），末次 poll 为 17:19:44.311441Z；FINAL.json、ROOT_STOP_REQUIRED.json、STOP.request 均不存在。缺少 FINAL 不证明进程仍活着。
- SDK client READY 与 consumer-session 都是旧会话 `87d9d3a0b22e477a8e9192b42a4aa4e2`。实际 profile SHA-256 仍精确等于 `74601f97464a5faeb14312c4e2fa7458153c36fd7c2d5349a37ef852ec1db661`，guard 目标也仍为原 PID/create_time，但当前没有 SDK client/stdio server 进程，不能声称已连接当前 PID。
- 指定 Python313 的 installed metadata 实测 `mcp=2.0.0`、`mcp-types=2.0.0`；未确认“native SDK 2.2.0”的版本来源，不据此制造版本或连接结论。
- queue 共 45 个 request、45 个 response，未完成 request ID：[]。最后保存的 response 为 `0045-0044-i2-detach-source-yes-save.response.json`；旧存储回执与 driver-state 只是历史状态，不证明当前暂停或当前连接。
- general task `ck3-li-yu-dao-implementation-20261004` 仍为 running、序号 2701，最后更新 2026-10-04T11:58:24.412093+00:00；本审查不更新其业务状态。

## 现行正常释放命令与边界

以下均未执行。CLI 的 `--help` 返回 0，source/installed SHA 相同：`B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE`。

1. 当前 keeper 和 queue 进程已经缺席，不能再靠旧 session ID 向它们发送 STOP 或 close。若后续另建了活跃 client，会话正常关闭是创建一份唯一的 `ck3.lyd.mcp-request.v1` / `operation=close` JSON，再使用实际现行 `enqueue --queue --request`。工具没有 `close` CLI 子命令。活跃 keeper 使用自身 output 下的 `STOP.request` 协议，待 FINAL 与实际退出后再释放；工具没有 `stop` CLI 子命令。旧 output 和旧 queue 不可复用或重放。

2. CK3 仍实际运行。现有 11 个 native tools 与 live_control_r0006 没有 quit CLI，不能虚构“正常退出”命令。Root 在当前授权下正常退出游戏时仍须取当前 GUI 证据并遵守焦点/布局/坐标合同，核对原 PID/create_time 已退出并保存证据；本审查没有退出游戏。

3. 对当前未变的过期 screen claim，现行原生 CLI 支持下面的 CAS 释放。执行前须重新读当前序号和 CLI bytes；若记录变化必须停止复核。过期释放会得到 waiting、清空 resources，并写 `business_status=unresolved_red`，不会写成 done。

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe C:/workspace/ck3_eternal_recurrence/tools/codex_task_bus.py --bus-dir C:/workspace/.codex-task-bus --expected-cli-sha256 B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE release-screen-cas --task ck3-lyd-live-007-20261004 --expected-sequence 2808 --summary R0006-expired-own-screen-claim-released-unresolved
```

4. general task 应按实际完成程度记录 waiting 或最终 done；仅完成本状态审查不能标记 implementation 完成。实际可用 status 命令见 `release-commands.json`，其正常 `status` 路径可能执行现行 Git identity 查询，本审查没有运行。

详细证据见 `processes.json`、`bus-summary.json`、`keeper-ledger-summary.json`、`queue-summary.json`、`profile-summary.json`、`hashes.json`、`cli-help.json`、`source-excerpts.json`。释放操作只能由根代理按当时现场与授权执行。
