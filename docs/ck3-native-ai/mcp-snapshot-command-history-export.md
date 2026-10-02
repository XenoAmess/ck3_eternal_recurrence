# MCP snapshot 的可选原生历史导出

2026-10-02，Robert 的冻结档有 4,031 条 command history；该数组的紧凑 UTF-8 JSON 为 48,711,631 bytes。现有 `ck3_take_snapshot` 经 `GameplayBridgeService.snapshot()` 调用 native driver 的完整 public snapshot，历史会被 deepcopy；MCP 2.0 同时生成 text content 与 structured content。因此状态绑定读取也会承担整份历史的复制与序列化。

已保留的 SDK RED 是 `m7-robert/paused-intent-19a0e945-v4/first-paused-02/error-traceback.txt`：`ck3_take_snapshot` 的 `tools/call` 在 90 秒后报 `MCPError: Request 'tools/call' timed out`。这是可观察的 SDK 阻点；没有对应 `OverflowError`，也没有证明固定 stdio buffer 上限。不要把这次 timeout 改写为另一种异常。

现有同 owner 的有限内部读取 workaround 已在 `m7-robert/actual-v16-multidomain-01/capture-01/result.json` GREEN，actor 29829/date 53220000；它走 registered 查询，snapshot 绑定使用内部 semantic frame。这个结果不等于修改后的 public stdio SDK 已验收。

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

本包 artifact 根：`Z:/ck3_mod_rewrite/artifacts/g2-maintainer-2026-10-02/resume-12003/robert-sdk-history-export-01/`。`CHECK-RESULT.json` 是静态验证；`root_sdk_capture_finite.py` 是显式选择有限导出的 SDK capturer，原 helper 与历史 RED 保留。修改后的真实 stdio SDK 查询仍待 ROOT 用新冻结 Python runtime 执行。
