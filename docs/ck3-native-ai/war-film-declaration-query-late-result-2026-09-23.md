# R0004 宣战候选查询超时与按原请求收取

2026-09-23。本包修复 Python 等待与结果缓存，不改变 CK3 原生宣战选择、native DLL 或已冻结的 [CASE-R 取材方案](war-film-robert-mcp-shot-runbook-2026-09-23.md)。新增接口的当前证据层次是离线协议夹具；R0004 的临时同 driver 恢复另有实机证据，不能替代新增接口的 live 验收。

## 故障与已取得的实证

R0004 的 `006-declarable.json` 调用 `ck3_query_declarable_wars(expected_revision=6)` 后，Python 报 `native command_result timed out for gameplay step query-declarable-wars`。随后的 `007-after-declaration-read.json` 仍能读取同一暂停现场；普通 snapshot 没有执行新的候选查询，也没有把迟到结果自动写进公开候选缓存。

原始材料都保留在外置目录 `D:/workspace/ck3_war_film_research_20260923/capture-live-live-r4c/`：

- `interactive-requests-responses/006-declarable.json`、`007-after-declaration-read.json` 与 `mcp-calls.jsonl` 保留原 RED。
- `late-declaration-cache-readonly-r1.json` 在同一 capture Python driver 中找到原请求 `step-199-52e31f1268cd` 的迟到 `command_result`：`ok=true`、`status=available`、`query_sequence=1`。它证明结果后来存在，不提供精确的原生计算耗时或回包到达时刻。
- `late-declaration-reconcile-r1.json` 记录协调者的一次性 Python 缓存恢复；未重新向 native 提交该查询。恢复前后比对原 snapshot、public/native revision、episode、日期、玩家、bridge PID 和连接 generation。
- `interactive-requests-responses/008-after-reconcile.json` 从官方 MCP snapshot 读回 9 条候选。`009-assessment-one.json`、`010-assessment-two.json` 是之后独立的正式 `war_entry` 查询，`011-case-end-snapshot.json` 保留同帧末次读回。

这次恢复只附加了任务自身的 capture Python，未附加 CK3。它没有把 `006` 改写成成功，也没有证明本包新增的收取工具已在游戏中调用。

## 原因与最小修复

`NativeHeadlessGameplayDriver` 原本为宣战候选枚举使用通用的 10 秒 `command_timeout_seconds`。该枚举在 native worker 中读取候选；Python 超时不是 native 取消。`NativeProtocolState` 继续按 `request_id` 保存 `command_result`，而公开 `declarable_wars` 缓存只在原调用成功返回后发布。因此同一进程可能同时存在“原调用 RED”和“原请求已经有成功结果”，普通 `take_snapshot` 不能补走被超时打断的发布步骤。

本包仅修改 [native_driver.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py)、[service.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py) 与 [mcp_server.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)：

1. 构造参数 `declarable_wars_timeout_seconds` 默认 120 秒，仅用于 `query-declarable-wars`。通用命令默认仍为 10 秒。120 秒是有限的工程预算，不是本次已测延迟或性能保证。
2. 此查询超时后保留 `request_id`、原绑定、预算和 `pending` 状态；错误文本与 `driver.diagnostics().pending_declaration_query` 可读取这些信息。存在该待收取请求时，重复发起候选查询被拒绝，避免用重发掩盖原请求。
3. 新增 Python/MCP 收取入口，只读取同一 driver 已保存的那个请求；调用 native 发送次数为零。正常及时结果与迟到结果复用同一个归一化和缓存发布方法。
4. 发布仍要求暂停，且原始与当前的 snapshot ID、public/native revision、episode、日期、玩家 ID、bridge PID、连接 generation、map-ready、paused 全部相同。native 回包本身没有独立的上述完整绑定，因此不能仅凭回包 ID 将旧结果挂到新现场。

## 正式调用合同

先从超时错误取得原 `request_id`，随后读取 `ck3_take_snapshot` 的最新 **public** `revision`，调用：

```text
ck3_collect_declarable_wars_result_v1(
    request_id=<超时错误中的原请求 ID>,
    expected_revision=<本次 ck3_take_snapshot.revision>
)
```

返回 schema 为 `ck3-declarable-war-result-collection-v1`，包含原/当前绑定、`native_resubmitted=false` 和 `cache_restored`：

| status | 含义与后续 |
| --- | --- |
| `pending` | 同帧但尚无结果。保持现场，稍后按同一个请求 ID 再收取；不重新查询。 |
| `available` | 原结果通过归一化与同帧绑定检查，已恢复 Python 公开候选缓存。附原 `native_result_frame` 与 `declaration_result`，随后可用 snapshot 读回。 |
| `stale` | 当前现场与原绑定不同或已不暂停，不采纳旧候选；若结果已经存在则一并返回供保留。原 pending 记录结束。 |
| `native-rejected` | 收到原请求的 `ok != true` 回包，保留回包，结束 pending，不恢复候选缓存。 |

错误请求 ID 或错误 public revision 不消费回包。畸形结果仍报错，精确回包留在原 pending 记录中供诊断，不写入候选缓存。收取成功不重写原失败的 `native_command_history`；收取调用本身是独立证据。

该入口是 Python transport/cache 的补收能力，不是新的 native capability。记录只属于发起请求的同一 driver，不是跨 Python 重启的持久队列，也不为旧版本 driver 自动补造丢失的原绑定。R0004 已完成的一次性恢复无需重发或重复观测。

## 聚焦验证与边界

[专属测试](../../ck3_autonomous_player/tests/unit/test_declarable_query_collection.py) 通过 fake endpoint 构造确定性的“超时 → 迟到回包 → 原请求收取”，检查发送次数始终为一、原失败历史保持、正常结果缓存兼容，并覆盖换帧/玩家/日期/PID/generation、错误请求、错误 public revision、原生拒绝与坏回包。官方 MCP `Client` 的离线测试穿过新 tool、service 和 driver。

同时运行既有 `test_native_declaration_query_expands_and_starts_war` 与 `test_native_declaration_query_expires_on_next_snapshot`。这两项使用离线夹具，不启动游戏。验证收据目录为 `D:/workspace/ck3_war_film_research_20260923/declaration-query-collection-python-r1/`；结果以其中 `test-result.json` 和原始 stdout/stderr 为准。

实际结果：**11 tests PASS**（9 项专属测试加 2 项既有回归），退出码 0。解释器为本 worktree 的 `tools/.venv/Scripts/python.exe`，Python 3.14.7、MCP 2.0.0；未安装或修改依赖。在 `ck3_autonomous_player/tests/unit/` 下等价复现命令为：

```text
../../../tools/.venv/Scripts/python.exe -m unittest -v test_declarable_query_collection test_native_bridge_driver.NativeHeadlessGameplayDriverTests.test_native_declaration_query_expands_and_starts_war test_native_bridge_driver.NativeHeadlessGameplayDriverTests.test_native_declaration_query_expires_on_next_snapshot
```

收据保存实际 argv、cwd、解释器 probe、起止时刻以及三个生产 Python 文件和专属测试的 SHA-256。原始 stderr 中的 asyncio 慢任务诊断没有导致测试失败，不代表任何 CK3 耗时观测。

本包没有运行、重启、附加或注入 CK3，没有修改存档、原生研究结论或 CASE-R 计划。`open_kaishek` 对本问题为 `not-applicable`：故障位于 Python transport 等待与缓存发布，不是其 Paradox 脚本运行时子集。下次真实查询如果再次超时，可在同一暂停绑定下使用该正式入口并保存独立 MCP 回执，届时才能增加其 live 状态。
