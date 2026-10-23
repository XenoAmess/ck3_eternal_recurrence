# R25：原生退出能力缺失导致的公共队列失败

`machine_id: desktop-3fevhd2-1c74096080`；离线复核时间：`2026-10-23T17:41:16Z`。机器身份来自本次 `tools/ck3_live_run_id.py machine`。场次为 `desktop-3fevhd2-1c74096080--superman-qiang--R0025`，本次修复没有启动游戏、修改冻结 host / native 或改写原回执。

证据：`C:/ck3-superman-validation-20261023/runs/desktop-3fevhd2-1c74096080--superman-qiang--R0025/native-report.json`（SHA-256 `ff36b985f21658598950e85fd72f8bfa12215b46c36041c5a24bb09c4c8dd898`）；同目录 `frozen-argv.json`（SHA-256 `f21964cb765c17ebd1699b39e89d11aa42ee8e57f928d3dc53f22e16df04668f`）。所选 DLL 为 `C:/w/e04date32a01/build-a01/xar_ck3_bridge.dll`，回执身份 SHA-256 为 `062b2ae3639c230d2ca4552d5de67c9536605b1fbda2045c040d3fd6f25ca746`。

R25 的 MCP metadata 注册了 `ck3_query_normal_exit_context_v1` 和 `ck3_request_normal_exit_v1`，但 `capabilities.bridge_capabilities` 及其 `diagnostics.hello.capabilities` 均未包含精确能力 `normal-exit-map-v1`。`17:23:34.152801Z` 投递后的查询于 `17:23:34.494797Z` 返回 `native normal-exit-map-v1 capability is unavailable (default OFF)`；异常从 `registration_host.py` 的 `hold → execute → invoke → call` 传播。最终原生报告 `exit_reason=stop`，shutdown 记录 `ck3_exit_code=1`、Job 中进程数由 1 清至 0，`cleanup_proven=true`；共享报告在 `17:23:37.884022Z` 结束并保留 `status=RED`。这些只证明清场完成，不是正常退出或业务验收通过。

能力名称来源已与 R25 冻结文件逐项核对，当前读取字节一致：`normal_exit_contract_v1.py:17` 定义无前缀的 `normal-exit-map-v1`（SHA-256 `269290c707c5ed575bb6bfe001b918b2b64e33dd07c1e29fda160742e4151c9f`）；`normal_exit_map_driver_v1.py:34–37` 从实际 `bridge_capabilities` 检查它（SHA-256 `3c2add3cf7017acdbb7b4cdbf6034865082400f81be8464aae6c08a9e7402db9`）。这两份文件位于冻结 `agent_source_root` 的 `ck3_autonomous_player/src/xar_autoplayer/bridge/`。

公共队列现在在 `validate_steps` 核对已绑定报告中的 native hello、连接 pipe / PID / generation 和能力镜像，缺失、错误类型、来源不一致或未支持时，在写入 once ledger、发布计划、调用 host 之前拒绝。精确范围只有原生退出 query/request；`ck3_observe_normal_exit_v1` 的保留 OS 句柄观察无需 native 能力，继续可用。注册表和 `action_steps` 不能代替原生 hello。

离线回归覆盖 query 与四种 request 动作的拒绝与成功投递、拒绝前无 claim / publish / host 调用、OS 观察放行、错误字段与 bool / float 身份、JSON 往返；历史 R25 完整回执只读重验也得到同一投递前拒绝，原文件 SHA 未改变。CI 增加队列已注解函数的 mypy 检查，并固定 `types-jsonschema==4.26.0.20261006`。R25 永久保留 **RED / cleanup-only**，后续新场次另行验收。
