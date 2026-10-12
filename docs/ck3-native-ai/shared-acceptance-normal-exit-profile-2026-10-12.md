# 受管验收的正常退出配置接点

2026-10-12：实际 Source19 host 未绑定已有的 `normal_exit_managed_profile`，既有正常退出 MCP 因而在 dispatch 前拒绝；同时 `PlanClient.execute` 会在终止工具完成后无条件读取新游戏快照。两项均阻碍《礼与道》下一次代表性实机收尾。本次只连接既有 source-inventory 协议并处理终止结果，没有新增 native/provider 能力。

`tools/ck3_mod_acceptance_normal_exit_profile.py` 从当次实际 public preparation 投影既有 profile 字段，核对 state/userdir、游戏版本与 EXE、所选 DLL/injector 和实际 runtime。它调用原 `build_normal_exit_source_inventory_v1.py` 和 verifier 生成该 userdir 的源清单；目标记录只表达静态来源绑定，不授启动权限。外置部署作者在 host 父进程启动前创建此配置，再经两个显式参数传给子 server。profile、target record、source inventory、runtime 和 helper 的精确 pins 随当次 artifact 保留；不得复用另一场的 profile。

生产 host 新增 `--normal-exit-managed-profile` 与 `--normal-exit-managed-profile-sha256`，默认关闭。绑定时核对实际 state、输出目录及既有 verifier，随后才赋给 driver。原 Source19 export 与 Native058 不改写；本机场次使用小 Python overlay，保留其原来源及派生补丁。

成功的 `ck3_request_normal_exit_v1`（仅 `confirm_desktop`）和 `ck3_observe_normal_exit_v1` 在返回对应真实 schema、action 且 `snapshot_after_required is False` 时保留完整 typed result，跳过额外 fresh，不生成虚假的 `after_snapshot`。prepare、普通工具、错误及不匹配结果仍走原处理。观察待定退出只观察原保留 HANDLE，不重放确认；MCP ACK 不能代替实际进程退出、原 HANDLE 的退出码、native/thread cleanup 或 public run 结果。

两项 profile 测试及三项直接执行回归分别实际通过，证据在 `C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-followup-storage-admission-20261012-032/normal-exit-profile-001/TEST.RESULT.actual.json` 与 `normal-exit-profile-002/TEST.RESULT.actual.json`。后者覆盖终止 request/observer 保留结果、普通或非终止工具仍 fresh、MCP 错误保留且不重放。默认 CI 运行完整模块。上述结果为 SOURCE_ONLY；尚未在后继真实场次取得正常退出资格。
