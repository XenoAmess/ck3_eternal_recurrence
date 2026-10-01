# CK3 1.20.0.2 完整 Doctrine 注册表私有只读 query

该 domain query 包装 [已加载 registry provider](religion_doctrine12002_catalogue.md)，把当前玩家、日期与全 loaded Doctrine 定义列表送入标准 bridge transport。它不读取当前 popup choices，不触发 lazy DB 初始化，也不把注册表条目当作最终合法选项。

```mermaid
flowchart LR
    A[private readonly selector] --> B[actual TrySubmit main-thread mailbox]
    B --> C[paused application-main owning pump]
    C --> D[QueryMailboxEnvelope: published full snapshot]
    D --> E[actual current core + loaded catalogue provider]
    E --> F[Finish same owner frame]
    F --> G[actual Wait / Reclaim]
    G --> H[protocol1 complete command_result]
    H -. central CMake/named slot/Python registry .-> I[MCP readonly query]
    I -. root live paused sample .-> J[production-live primitive]
```

Exact EXE 与注册表 ABI 复用 provider 专题：CK3 1.20.0.2 Crozier，EXE SHA `AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。query 接线约定如下：

| 项目 | 值 |
| --- | --- |
| compile flag（中央默认 OFF） | `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1` |
| selector | `query-player-religion-doctrine-catalogue-v1` |
| domain_key | `player_religion_doctrine_catalogue_v1` |
| backend_id | `ck3-1.20.0.2-native-player-religion-doctrine-catalogue-v1` |
| new named executor permit | `permitted_executor_religion_doctrine_catalogue12002` |
| inner DTO key | `result.player_religion_doctrine_catalogue` |
| MCP tool（Python owner） | `ck3_query_player_religion_doctrine_catalogue_v1` |

owned header/source 为 `religion_doctrine12002_catalogue_mailbox.hpp/.cpp`。函数为 `IsPlayerReligionDoctrineCataloguePrivateStep12002`、`ExecutePlayerReligionDoctrineCatalogueMailbox12002`、`HandlePlayerReligionDoctrineCataloguePrivate12002`，domain runtime `RunPlayerReligionDoctrineCatalogueMailbox12002` 由真实 handler 与离线 native fixture 共同使用。

请求只有可选 `expected_snapshot_revision`（别名 `expected_revision`）；读取 scope 永远是原生 core 的当前 played actor。发布 revision 与 main-thread capture epoch 不混用；实际 owner frame 漂移时不返回成功 packet。原生 registry 缺失但 owner frame 稳定时可返回有原因的 typed unavailable，`catalogue_complete=false`。

响应完整外层为 `type=command_result`、`protocol_version=1`、对应 `request_id`、`ok=true`，`result` 含 `accepted=true`、`private_build=true`、`read_only=true`、`advertised=false`、exact game_version/EXE SHA、domain/backend、published snapshot_revision/date_raw 和 actual catalogue DTO。`ok` 表示完整查询响应，不意味着任何宗教动作已执行。

## 实际验证与边界

[组件 fixture](../../ck3_autonomous_player/native_bridge/src/religion_doctrine12002_catalogue_mailbox_test.cpp) 与 [runner](../../research/religion_doctrine12002_catalogue_mailbox_tests.py) 直接链接实际 core、provider/copier、QueryMailboxEnvelope、主线程 mailbox、protocol 与本 domain runtime/serializer。新增路径 MSVC `/O2 /W4 /WX` **一次通过 23 项检查**：真实 worker TrySubmit，fixture owner 真实 ObserveMainThreadPumpAndDrainV1，随后 Wait/Reclaim；完整 packet 的 `protocol_version=1`、revision/epoch、当前 scope、mod stable key 和 typed unavailable 由 Python 直接解析验证。

实际产出 **3 份完整 C++ command_result**：`loaded-catalogue`、`known-empty`、`database-unavailable`。fixture native对象在自己的进程内，adapter unwrapping 是已知 bare native adapter identity shim，没有替换或声称验证 WorkerAdapter 的实际 unwrapping。此次使用已有 **offline primary executor permit**；中央将新增 `permitted_executor_religion_doctrine_catalogue12002` 并单独验证薄路由。当前包不宣称其 named permit/中央 DLL/Python SDK 已完成。

artifact 为 `Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/catalogue/mailbox/result.json`；完整 build/test/executable、source 与 wire SHA 留在同目录。三份原始 packet **逐字节**冻结到 `research/religion_doctrine12002_catalogue_packets/`，sidecar manifest 绑定 actual C++ output SHA 与生产 source；Python SDK/CI owner 可直接消费实际生产 packet，不补 mock metadata 遮盖 transport 不兼容。

状态为 **`static-ready` domain runtime/mailbox/protocol packet**，没有 fixture-live 或 production-live artifact。中央默认 OFF compile flag / named permit / CMake / selector、Python SDK 与 root 真实 paused 采样仍是各自独立边界。本 query 没有修改任何共享 CMake/bridge/worker/Python 文件，也没有操作 CK3、Steam 或 UI；没有重复旧 ABI span、旧 `/Od` 或旧矩阵。
