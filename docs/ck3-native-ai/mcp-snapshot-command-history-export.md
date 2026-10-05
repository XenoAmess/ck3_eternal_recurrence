# MCP snapshot 的有限默认导出与完整历史 opt-in

2026-10-06 的最小修复将 registered `ck3_take_snapshot` 的
`include_native_command_history` 默认值改为 `false`。空参数调用现在复用已有有限
export；需要完整历史时明确传 `true`。该默认修改为 **static-ready，当前冻结
g78 尚未采用**；既有显式 `false` 查询的 production-live primitive 证据继续见下文。

2026-10-02，Robert 的冻结档有 4,031 条 command history；该数组的紧凑 UTF-8 JSON 为 48,711,631 bytes。现有 `ck3_take_snapshot` 经 `GameplayBridgeService.snapshot()` 调用 native driver 的完整 public snapshot，历史会被 deepcopy；MCP 2.0 同时生成 text content 与 structured content。因此状态绑定读取也会承担整份历史的复制与序列化。

已保留的 SDK RED 是 `m7-robert/paused-intent-19a0e945-v4/first-paused-02/error-traceback.txt`：`ck3_take_snapshot` 的 `tools/call` 在 90 秒后报 `MCPError: Request 'tools/call' timed out`。这是可观察的 SDK 阻点；没有对应 `OverflowError`，也没有证明固定 stdio buffer 上限。不要把这次 timeout 改写为另一种异常。

此前同 owner 的有限内部读取 workaround 已在 `m7-robert/actual-v16-multidomain-01/capture-01/result.json` GREEN，actor 29829/date 53220000；它走 registered 查询，snapshot 绑定使用内部 semantic frame。后续真正 public stdio SDK 的有限快照验收见下文，两份证据分别保留。

现有 MCP tool 新增可选参数：

```json
{"name":"ck3_take_snapshot","arguments":{"include_native_command_history":false}}
```

省略该参数或传 `false` 时，native driver 复用 `take_internal_semantic_snapshot()`，保留原 public snapshot 的 semantic 与 rollback 字段，返回 `native_command_history: []`，并添加：

```json
{"native_command_history_export":{"mode":"omitted","total_count":4031,"included_count":0}}
```

`total_count` 从当前 driver 拥有的历史数组读取，4,031 只是本次冻结档的实测值。
完整历史仍可显式请求：

```json
{"name":"ck3_take_snapshot","arguments":{"include_native_command_history":true}}
```

完整历史、持久化与规划器均继续使用原有来源。service/native driver 的直接调用默认值
保持原合同；本次只修改 MCP tool 的参数默认值。其他没有原生历史导出接口的 backend
继续返回原 snapshot。

2026-10-02 曾仅跑一次直接受影响的方法链检查：实际 registered `ck3_take_snapshot` → service → native producer；fixture 读取冻结真实 semantic frame 与 4,031 条 archived rows。有限导出没有 deepcopy 历史，所有原 snapshot 字段保留；当时默认导出保留完整历史和原字段结构。结果为 1/1 GREEN，2.284 秒。该检查没有 client、pipe、游戏启动或 state 写入。本次默认值修复只做语法与 diff 检查，不重读该巨大历史、不重跑旧检查，也不把历史结果记为新默认值的实机验收。

## R0047 的真实完整历史延迟与最小修复

2026-10-06 Asia/Shanghai（下表保留 UTC），Root 的同一 Robert 普通战役
R0047/v73/g78 通过 held stdio client session88374 运行。670 的实际 normal save
保留 h9519/raw53286000/5903 个正常游戏日；Robert 活着、CK3 暂停。随后误把
[`671-post-peace-fresh-snapshot.json`](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-requests/671-post-peace-fresh-snapshot.json)
排入队列，其原文为 `{"tool":"ck3_take_snapshot","arguments":{}}`，在旧 g78 默认下
选择完整历史。21:39Z 排队，至 21:44:48Z 尚无 response/DONE；stderr 为空。
这是已观察到的长耗时，尚未证明 deadlock、protocol rejection 或固定消息上限。

| UTC / 证据来源 | client74252 CPU 秒 / RSS bytes | server119352 CPU 秒 / RSS bytes |
|---|---|---|
| 21:42:58 / Root 已保存的已知进程树 | 131.3 / 478380032 | — |
| 21:43:42 / Root 已保存的已知进程树 | 168.8 / 864243712 | 621.6 / 4157931520 |
| 21:44:48.268774 / 同一已知进程树的只读核对 | 219.65625 / 754900992 | 621.578125 / 4157931520 |

最后一分钟 client CPU 增加约 50.86 秒，server CPU/RSS 保持同量级；CK3 PID69432
RSS 为9971019776，仍在原进程中。这些进程值只证明 CPU/内存活动，不是读取游戏状态。

源码路径闭合了这次实际耗时的来源：

1. `ck3_take_snapshot()` 旧默认 `true` 经 service/native producer 调用
   `_history_snapshot()`，对全部 `_command_history` 做 deepcopy。
2. 本机 SDK `mcp/server/mcpserver/utilities/func_metadata.py::convert_result`
   同时构造 JSON text content 和 structured content。server stdio writer 将整个
   CallToolResult 序列化成一行 JSON，再在行末加 newline。
3. 本机 SDK `mcp/client/stdio.py::stdout_reader` 每次收到 chunk 执行
   `lines = (buffer + chunk).split("\n")`，再取未完成行作为新 buffer。
   在最后 newline 到来前，已有整行被逐块重新复制与扫描；固定大小 chunk 下工作量
   随消息长度近似 O(n²)。完整行收齐后才 `_parse_line/validate_json`。
   这是源码支持、与实际 client CPU 增长一致的 framing 原因；未测量此次完整 wire 大小，
   不把 RSS 当成 payload bytes，也不能据此断言最后一次观察已进入 JSON parse 阶段。
4. 外置 `gameplay_mcp_client.py` 串行 `await session.call_tool()`，返回后才
   `model_dump(mode='json')`、带 indent 的 JSON 落盘并打印 DONE。它没有设置 request
   read timeout。`672` 的已有显式 `false` 请求及 `exit_client` 都要等 `671` 返回。

当前最小恢复是让同一 `671` 继续消费，保留原请求和延迟证据，再让已排队的
[`672-post-peace-snapshot-no-history.json`](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/gameplay-requests/672-post-peace-snapshot-no-history.json)
走已有有限读取。无需普通 close/reconnect；当前真实 CPU 进展不支持为此更换连接。
现有外置 client 没有独立的取消控制入口，不能用排队 `exit_client` 抢占这个 await。
若 Root 后来决定中止整个 client，stdio context 关闭会结束它拥有的 MCP server
进程并需真实重新连接；那是实际 runtime lifecycle 变化，不得伪造或沿用旧 generation
证明。本包没有执行该操作。

未来最小源码修复只将 tool 默认改为 false，避免普通空参数观测再次导出完整历史；
显式 true 保留原能力。正在运行的 g78/SDK、671 request 和 runtime generation
均不由此修改。源码与静态交付收据在
[`snapshot-default-omission-gbsnap`](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261006/snapshot-default-omission-gbsnap/ROOT-DELIVERY.json)；
本包增加0个游戏日、0个实机查询和0个新的 production-live primitive。

本包 artifact 根：`Z:/ck3_mod_rewrite/artifacts/g2-maintainer-2026-10-02/resume-12003/robert-sdk-history-export-01/`。`CHECK-RESULT.json` 是静态验证；`root_sdk_capture_finite.py` 是显式选择有限导出的 SDK capturer，原 helper 与历史 RED 保留。

## 真正 stdio SDK：production-live primitive

2026-10-02 的 `actual-stdio-01/result.json` 为 GREEN，实际 CLI 使用 `production-source-dd4772c0`、`--driver native-headless --transport stdio`。公开 Python commit 为 `dd4772c02b8183b9e7c5efe72fe01649e4f67be1`；native 仍使用 v16 DLL `83a811d717b836f589f76c91fc03f205235aac70bb72c50842258d701468a6ff`。本次保留原受管环境，MCP attach 的 Python source identity 与已加载 native binary identity 分别记录。

`003-ck3_take_snapshot.json` 的真实请求为 `include_native_command_history:false`；MCP 回包 `isError:false`、`resultType:complete`，`native_command_history` 为空，导出元数据为 `mode:omitted,total_count:4041,included_count:0`。文件为 54,567 bytes；其 CallToolResult 的紧凑 UTF-8 JSON 为 45,467 bytes，semantic DTO 为 18,907 bytes。后两者是从保存的回包计算的序列化大小，不冒充含 JSON-RPC envelope 的逐字节 wire 大小。

semantic 身份为 PID 109676、CK3 1.20.0.3、EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`、`ck3_build_match:true`；actor 29829、episode `native-29829-2bc2d599f7f9`、date 53220000、paused/map_ready 均为 true，snapshot `native:20`、public revision 2、native revision 20。ordinary campaign / `xar_off` 与 `dynasty_continuity` goal 均保留。

`004-ck3_get_capabilities.json` 同样为真实 SDK 成功回包，transport_ready/snapshot/minimized_operation 为 true，`life-advance` 同时出现在 action 与 composite 列表。这个观测证明该 capability 已恢复发布；本包日期仍为 53220000，不证明 action 已执行或游戏已推进。

旧默认 full export 的 90 秒 `tools/call` timeout 保持 RED；本次显式选择有限 export 后，真实 SDK 可以读取相同当前 semantic 字段和实际历史总数。这是 public snapshot 查询 primitive 的实机闭合，不是全 G2 OODA、实际推进或完整 SDK 工具矩阵完成。实际 packet pins 与解析保存在 `ACTUAL-STDIO-ANALYSIS.json`。
