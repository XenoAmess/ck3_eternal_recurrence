# MCP snapshot 的可选原生历史导出

2026-10-02，Robert 的冻结档有 4,031 条 command history；该数组的紧凑 UTF-8 JSON 为 48,711,631 bytes。现有 `ck3_take_snapshot` 经 `GameplayBridgeService.snapshot()` 调用 native driver 的完整 public snapshot，历史会被 deepcopy；MCP 2.0 同时生成 text content 与 structured content。因此状态绑定读取也会承担整份历史的复制与序列化。

已保留的 SDK RED 是 `m7-robert/paused-intent-19a0e945-v4/first-paused-02/error-traceback.txt`：`ck3_take_snapshot` 的 `tools/call` 在 90 秒后报 `MCPError: Request 'tools/call' timed out`。这是可观察的 SDK 阻点；没有对应 `OverflowError`，也没有证明固定 stdio buffer 上限。不要把这次 timeout 改写为另一种异常。

此前同 owner 的有限内部读取 workaround 已在 `m7-robert/actual-v16-multidomain-01/capture-01/result.json` GREEN，actor 29829/date 53220000；它走 registered 查询，snapshot 绑定使用内部 semantic frame。后续真正 public stdio SDK 的有限快照验收见下文，两份证据分别保留。

现有 MCP tool 新增可选参数：

```json
{"name":"ck3_take_snapshot","arguments":{"include_native_command_history":false}}
```

省略该参数或传 `true`，继续返回完整历史和原有字段。传 `false` 时，native driver 复用 `take_internal_semantic_snapshot()`，保留原 public snapshot 的 semantic 与 rollback 字段，返回 `native_command_history: []`，并添加：

```json
{"native_command_history_export":{"mode":"omitted","total_count":4031,"included_count":0}}
```

`total_count` 从当前 driver 拥有的历史数组读取，4,031 只是本次冻结档的实测值。完整历史、持久化与规划器均继续使用原有来源。其他没有原生历史导出接口的 backend 继续返回原 snapshot。

仅跑一次直接受影响的方法链检查：实际 registered `ck3_take_snapshot` → service → native producer；fixture 读取冻结真实 semantic frame 与 4,031 条 archived rows。有限导出没有 deepcopy 历史，所有原 snapshot 字段保留；默认导出保留完整历史和原字段结构。结果为 1/1 GREEN，2.284 秒。该检查没有 client、pipe、游戏启动或 state 写入。

本包 artifact 根：`Z:/ck3_mod_rewrite/artifacts/g2-maintainer-2026-10-02/resume-12003/robert-sdk-history-export-01/`。`CHECK-RESULT.json` 是静态验证；`root_sdk_capture_finite.py` 是显式选择有限导出的 SDK capturer，原 helper 与历史 RED 保留。

## 真正 stdio SDK：production-live primitive

2026-10-02 的 `actual-stdio-01/result.json` 为 GREEN，实际 CLI 使用 `production-source-dd4772c0`、`--driver native-headless --transport stdio`。公开 Python commit 为 `dd4772c02b8183b9e7c5efe72fe01649e4f67be1`；native 仍使用 v16 DLL `83a811d717b836f589f76c91fc03f205235aac70bb72c50842258d701468a6ff`。本次保留原受管环境，MCP attach 的 Python source identity 与已加载 native binary identity 分别记录。

`003-ck3_take_snapshot.json` 的真实请求为 `include_native_command_history:false`；MCP 回包 `isError:false`、`resultType:complete`，`native_command_history` 为空，导出元数据为 `mode:omitted,total_count:4041,included_count:0`。文件为 54,567 bytes；其 CallToolResult 的紧凑 UTF-8 JSON 为 45,467 bytes，semantic DTO 为 18,907 bytes。后两者是从保存的回包计算的序列化大小，不冒充含 JSON-RPC envelope 的逐字节 wire 大小。

semantic 身份为 PID 109676、CK3 1.20.0.3、EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`、`ck3_build_match:true`；actor 29829、episode `native-29829-2bc2d599f7f9`、date 53220000、paused/map_ready 均为 true，snapshot `native:20`、public revision 2、native revision 20。ordinary campaign / `xar_off` 与 `dynasty_continuity` goal 均保留。

`004-ck3_get_capabilities.json` 同样为真实 SDK 成功回包，transport_ready/snapshot/minimized_operation 为 true，`life-advance` 同时出现在 action 与 composite 列表。这个观测证明该 capability 已恢复发布；本包日期仍为 53220000，不证明 action 已执行或游戏已推进。

旧默认 full export 的 90 秒 `tools/call` timeout 保持 RED；本次显式选择有限 export 后，真实 SDK 可以读取相同当前 semantic 字段和实际历史总数。这是 public snapshot 查询 primitive 的实机闭合，不是全 G2 OODA、实际推进或完整 SDK 工具矩阵完成。实际 packet pins 与解析保存在 `ACTUAL-STDIO-ANALYSIS.json`。
