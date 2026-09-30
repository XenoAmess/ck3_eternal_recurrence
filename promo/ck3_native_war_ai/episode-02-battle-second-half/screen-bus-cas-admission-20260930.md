# 第二期受管画面任务总线 CAS 准入

状态：**代码与无害夹具候选；权威总线仍为旧 CLI，旧 XQOL screen 记录未审计退役，录制器仅证明根进程退出，实机 STOP。** 已从 #730 精确移植独立静审的 injector Job helper，但视频接线尚需独审；它不能替代 FFmpeg 录制器的进程树清场证明。当前 screen-gated native bridge 入口仍在总线、FFmpeg、watchdog、CK3 或 injector 子进程前硬拒绝。本文不证明已领取画面、Steam 离线、CK3 启动或成片。

每个 live attempt 必须先由画面所有者用已安装且与当前 checkout `tools/codex_task_bus.py` **逐字节相同**的受审 CAS CLI，在权威 `D:/workspace/.codex-task-bus` 注册全新的独占 `ck3-screen:acquired` task。旧未释放 screen 记录、第二 owner、stale/unsafe、安装与源码 SHA 不同，均停止；不能用旧 `status done` 或裸 `heartbeat` 清掉旧记录。保存注册返回的 `task.last_sequence`、task ID、CLI SHA、完整 stdout/stderr 和退出码。要有当次直接审阅的新鲜 Steam“离线模式”原图及 receipt，并遵守项目实机门禁。

`capture_session.py --capture` 新增三个必填参数：

```text
--screen-task-id <本次全新且已注册的 task ID>
--screen-expected-sequence <注册回执中的 task.last_sequence>
--screen-cli-sha256 <受审源码与安装副本共同的 64 位大写 SHA-256>
```

这些参数也必须加入 d06/d11 的 live argv；no-launch argv 不需要。新的捕获入口在受管启动前核对源码与安装 CLI 字节，读取唯一、未过期、同 checkout/HEAD、**当前工作树 clean** 的 screen owner，执行带预期序号的 CAS heartbeat，再独立读取总线任务状态。watchdog、CK3 每次启动（包括预热、正式载入与热重启），以及可选 debug FFmpeg 的 Popen 均在 keeper 锁内再次 CAS；注入器整段执行持锁，返回后在恢复 CK3 主线程前再取得一次 CAS 门。注入器 Job 回执须精确绑定 argv、PID/创建时间/程序字节、stdout/stderr、零退出码及两次空 Job 进程清单；未知字段、输出溢出与读取错误均 RED。每次尝试在隔离 `state/injector-attempts/<launch-nonce>/` 中 create-only 保全 argv、原始 stdout/stderr、完整 Job report、helper error 与 SHA 索引；任何写入失败阻止恢复 CK3 主线程并保留不安全标记。失租后请求受管会话停止，可选录制器目前仅 terminate/kill、wait 根进程，不能据此证明其子孙进程清零，因此本版本继续在最初启动前硬拒绝受管原生桥接会话。它在 CK3 运行期间每 180 秒续租；任一冲突或读回不一致则保存 RED 日志并请求受管会话停止。输出保存在本次新 `ck3-output/screen-lease-admission.json`、`screen-lease-journal.jsonl` 和 `screen-bus-commands/` 的逐次 argv、原始 stdout/stderr、退出码。不得为同一 task 同时运行独立续租脚本。

`renew_screen_lease.py` 仅续租任务总线，**自身无法停止 CK3、录制器或 worker，现有 live runbook 不得单独使用它作为安全门禁**。它的新参数为 `--task`、`--expected-sequence`、`--expected-cli-sha256`、`--journal`；旧 `--bus-script` 与裸 `heartbeat` 命令作废。只有外层 supervisor 已证明能在其非零退出时立即停止并清空进程树的其他会话，才可按另行审定的合同使用。CAS 失败立即停止并保留 RED journal，不再重试三次后声称仍持有租约。每次续租后，下次预期序号取当次回执 `lease.sequence`。CK3、录制器及 worker 全部退出且清场证据审阅后，画面所有者再用最新序号执行总线 `release-screen-cas`；启动前或清场未证实不能释放。

此变更改变 `capture_session.py` 的 SHA 和 checkout HEAD；旧 d11 无启动 seal 不再适用，后续须在同一最终 HEAD 重新生成和封存无启动 attempt。现有旧 CLI 与旧 XQOL screen 记录未解决前，即使通过其他静态测试，所有 `--capture` 仍应在启动前 RED/STOP。
