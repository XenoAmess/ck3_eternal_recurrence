# CK3 1.20.0.2 当前玩家个人 Tenet 参数私有查询

状态：`static-ready`。实际 owner mailbox / handler / complete command-result 通路已通过一次新的 MSVC `/O2 /W4 /WX` 离线队列验证：30 项检查、五份真实完整响应。上游冻结 provider 的旧 17 项 main 未执行。未触碰本地 CK3，没有本包 live artifact。

冻结构建为 CK3 1.20.0.2 Crozier / Steam 25588574，EXE SHA-256 `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。宗教研究已由用户授权，本包不研究或执行战争、宗教动作或策略。

| 接线项 | 约定 |
| --- | --- |
| selector | `query-player-religion-personal-parameters-v1` |
| domain key | `player_religion_personal_parameters_v1` |
| backend | `ck3-1.20.0.2-native-player-religion-personal-parameters-v1` |
| 默认 OFF 编译开关 | `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_PERSONAL_PARAMETERS_PRIVATE_QUERY_V1` |
| 中央 named permit | `permitted_executor_religion_personal_parameters12002`，由中央 owner 登记 |
| private SDK/MCP 名称 | `ck3_query_player_religion_personal_parameters_v1` |
| source header/runtime | `religion_doctrine12002_personal_parameters_mailbox.hpp/.cpp` |

namespace 为 `xar::ck3_12002`。接入点是 `IsPlayerReligionPersonalParametersPrivateStep12002`、`ExecutePlayerReligionPersonalParametersMailbox12002` 与 `HandlePlayerReligionPersonalParametersPrivate12002`。context 使用现有 `QueryMailboxEnvelope`、宗教 bindings、`PersonalParameterBindings parameter_bindings` 与 `PersonalParameterContext observation`。

请求读取 actual played scope，没有 actor / target selector。`expected_snapshot_revision` / `expected_revision` 是可选 aliases；提供时必须非零且匹配 published revision，同时提供时须相同。顶层响应为 `type=command_result`、`protocol_version=1`、原 request_id、`ok=true`，`result` 包含 accepted、step、status、private/read-only/advertised、构建信息、domain/backend、published revision / date，以及实际 `player_religion_personal_parameters` DTO。

该 DTO 的 `source=character_personal_tenets`，与当前 Rite / Faith main Rite 参数集合分开。它发布原生 supported key 集合及个人 Tenet 条件的最终 bool：支持的 key 在完整观测集合中缺失时为 false；没有 Character extension 或有 extension 但没有 owned Tenet 时，也可观测到全部 false。数据库不可用或读取漂移时输出 typed unavailable，不能冒充 known false。`supported_keys_complete` / `personal_parameters_complete` 标明实际完整性，`personal_tenet_keys` 保留个人定义来源。

owner pump epoch 保存在 DTO 的 `capture_epoch`，与 published revision 分开。native read 失败但 owner snapshot 稳定时，保留当次 owner 的 played actor/date/epoch 与真实 unavailable reason；owner frame 漂移不返回成功 packet。

```mermaid
flowchart LR
    Q[Private worker request] --> S[Actual TrySubmit]
    S --> P[Paused owning-thread pump and drain]
    P --> E[Enter published frame]
    E --> R[Actual Character personal parameters provider]
    R --> F[Finish owner snapshot]
    F --> W[Actual Wait and Reclaim]
    W --> J[Complete command_result]
    J -. root integration .-> M[Private readonly MCP]
    M -. paused artifact required .-> L[Production-live primitive]
```

验证使用冻结的个人参数 memory/callback helpers，与真实 `TrySubmitMainThreadQueryV1 → ObserveMainThreadPumpAndDrainV1 → WaitForMainThreadQueryV1 → ReclaimMainThreadQueryV1` 及 C++ serializer。夹具只登记既有 primary permit；部署的独立 named permit 由中央 owner 接线。GameAdapter 仅供应 fixture owner frame，没有替换 WorkerAdapter 的生产实现。

[五份完整响应](../../research/religion_doctrine12002_personal_parameters_mailbox_wire_fixtures.json)覆盖个人 Tenet 参数 true 与 supported-but-missing false、无 extension、空个人列表、`parameter_registry_unavailable` 与 `state_changed`。前面三份完整 registry 状态为 `observed`；后面两份为 `unavailable`，保留同次 owner epoch/date/played identity，完整性字段为 false。此 fixture 的 Character 没有 Rite/Faith getter bindings，个人参数观测不依赖 Rite cache。

验证 receipt：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-doctrines\personal-parameters\mailbox\results\result.json`，SHA-256 `8764256287563d127a3cb56671e009f68c7de0b342b3daecf645b2c7f1f5d939`。六文件交付清单：`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-doctrines\personal-parameters\personal-parameters-mailbox-delivery-result.json`。上游八文件冻结 manifest SHA-256 `bf5bafc634f0227610e34470fc9572e2e38b664621c895de1ff9a9022f83d72e`；本包引用其既有证据，不重复 producer 验证。

下一步是中央/Python 接线与 root 主导的实机 paused snapshot。离线证据只证明完整查询通路可构建和执行，不宣称自动宗教动作或完整 OODA。
