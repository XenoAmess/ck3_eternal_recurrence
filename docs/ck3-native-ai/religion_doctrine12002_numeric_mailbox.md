# CK3 1.20.0.2 当前玩家数值参数与原生最终值私有查询

状态：**static-ready**。本包将 [五项数值缓存](religion_doctrine12002_numeric.md) 与 [Faith 原生最终数值](religion_doctrine12002_numeric_final.md) 接入实际 owning-thread mailbox，并冻结六份实际完整 `command_result`。未触碰本地 CK3，没有本包 paused live artifact；宗教已由用户授权，未研究或执行战争、宗教动作或策略。

冻结构建：CK3 1.20.0.2 Crozier / Steam 25588574，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。两个 reader 的源码、ABI 与既有结果保持冻结。

| 接线项 | 约定 |
| --- | --- |
| selector | `query-player-religion-numeric-special-parameters-v1` |
| domain key | `player_religion_numeric_special_parameters_v1` |
| backend | `ck3-1.20.0.2-native-player-religion-numeric-special-parameters-v1` |
| 默认 OFF 编译开关 | `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_NUMERIC_SPECIAL_PARAMETERS_PRIVATE_QUERY_V1` |
| 中央 named permit | `permitted_executor_religion_numeric_special_parameters12002`，由中央 owner 登记 |
| private SDK/MCP 名称 | `ck3_query_player_religion_numeric_special_parameters_v1` |
| 原生接线源码 | `religion_doctrine12002_numeric_mailbox.hpp/.cpp` |

命名空间为 `xar::ck3_12002`。入口为 `IsPlayerReligionNumericSpecialParametersPrivateStep12002`、`ExecutePlayerReligionNumericSpecialParametersMailbox12002` 和 `HandlePlayerReligionNumericSpecialParametersPrivate12002`。context 包含实际 `QueryMailboxEnvelope`、宗教 bindings、`numeric_bindings` / `observation`、`final_bindings` / `final_observation`。中央构建需链接 `religion_doctrine12002_numeric.cpp`、`religion_doctrine12002_numeric_final.cpp` 与本包 runtime。

请求始终读取 actual played scope，没有 actor / target selector。`expected_snapshot_revision` / `expected_revision` 为可选 revision aliases；提供时必须非零且匹配 published revision，同时提供时必须相同。完整顶层为 `type=command_result`、`protocol_version=1`、原 request_id、`ok=true`；`result` 包含 accepted、step、status、private/read-only/advertised、构建信息、domain/backend、published revision / date，以及两个独立的实际 observation：

- `player_religion_numeric_special_parameters` 是五项缓存 DTO，保留 current Rite 与 Faith main Rite 的完整 ID 和不同数值。合法零值仍是 value，minimum 的原生 `-1` sentinel 是 unset；没有从任意 key 或 authored presence 推断零值。
- `faith_numeric_final` 是实际 final reader DTO，调用冻结原生 getter，携带原生 define、主 Rite adjustment 与最终 heresy threshold。`value_state` 为 `value`、`legal_absent_faith`、`legal_absent_main_rite` 或 `unavailable`。实际 native callback failure 输出真实 typed reason，数值字段为空；合法不存在保留其独立语义。

**外层 `status` 只由 primary 五项缓存的 available 决定。** 单独 final failure 不丢弃已观测缓存，允许 outer observed 与 final unavailable 同时出现。两个 observer 同时 available 时核对 pump epoch、date、played character 和完整 current Rite / Faith / main Rite IDs；其结果保存在同一次实际 owner capture 内。final 失败时保留当次 owner 的 actor/date/epoch。snapshot revision 与 owner pump epoch 各有用途，不混用。

```mermaid
flowchart LR
    Q[Private worker query] --> S[Actual TrySubmit]
    S --> P[Paused owner pump and drain]
    P --> E[Enter published frame]
    E --> C[Actual five-cache reader]
    C --> F[Actual native final reader]
    F --> I[Compare available scopes and epoch]
    I --> V[Finish owner snapshot]
    V --> R[Actual Wait and Reclaim]
    R --> J[Complete command_result with two DTOs]
    J -. root integration .-> M[Private MCP query]
    M -. paused artifact required .-> L[Production-live primitive]
```

## 离线验证与冻结产物

[新的组合 fixture](../../ck3_autonomous_player/native_bridge/src/religion_doctrine12002_numeric_mailbox_test.cpp) 使用冻结 numeric fixture 的内存对象，复用 frozen final fixture 的 `Threshold` / `native_define` helper 前缀。原 numeric 15 项 main、final 10 项 main 均未执行。真实 Worker thread submit → owner `ObserveMainThreadPumpAndDrainV1` → wait/reclaim，使用现有 primary fixture permit 和自有 TLS/state；未编辑中央 permit 或 `WorkerAdapter`。

[runner](../../research/religion_doctrine12002_numeric_mailbox_tests.py) 仅运行 MSVC `/O2 /W4 /WX`，最终组合 **31 项新通路检查 GREEN**，并解析六份实际 C++ 完整响应：current/main final 30 与 actor adjustment -5、native final zero、minimum unset、合法无 Faith、合法无 main Rite，以及 final callback failure 时保留五项缓存。final zero 来自实际 callback 返回，不是用 primary 缓存手拼的响应。

权威组合 receipt 在 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/numeric/mailbox/final-combined/result.json`；六份完整响应已原样冻结到 [可移植 wire fixtures](../../research/religion_doctrine12002_numeric_mailbox_wire_fixtures.json)，每例保留原始 C++ 输出文件 SHA-256 与完整 parsed command_result。

先前 cache-only query 的 `/O2` 39 项检查和六份 packet 保留于 `numeric/mailbox/final/`，manifest 将其标为 `superseded-cache-only`。新增原生 final reader 后只验证变化后的组合，未重新执行原 39 项，也未运行 `/Od`。本包没有 harness RED；已有两个 frozen reader 的验证与 native evidence 直接复用。

中央 CMake / selector / named permit / Worker 接线与 Python MCP 由各 owner 合并。下一项实机验收由 root 独占 paused CK3，验证实际主 Rite 与当前 Rite、合法零/不存在语义及原生最终 threshold。本包只交付观测通路，不宣称宗教动作或完整 OODA。
