# 1.20.0.2：一般宗教敌对等级只读 query/mailbox

2026-10-01；exact build、方向性 Faith／Rite getter 和主礼仪区别沿用
[已冻结 library](religion_doctrine12002_hostility.md)。本增量未改 library 的八文件首包，未重跑其旧夹具。
本包最高为独立 query/runtime **`static-ready`**，没有操作游戏／进程／pipe／界面，也没有战争研究。

## 请求与实际响应

selector：`query-player-religion-hostility-v1`。Payload 的 `target_rite_id` 必填，范围为完整
`uint32`，**0 合法**；generation 必须保留。可附 `expected_snapshot_revision` 或 `expected_revision`
正整数；同时附两者时必须一致。source 始终来自当前 paused played character，不接受外部 actor 或 raw address。

```json
{"target_rite_id":2197815298,"expected_snapshot_revision":701}
```

完整响应为 `type=command_result`／`protocol_version=1`／原 request ID／`ok=true`，result 包含：

- `accepted=true`、`private_build=true`、`read_only=true`、`advertised=false`。
- `status=observed` 或 `unavailable`，随实际 provider 的 available 判定。
- `domain_key=player_religion_hostility_v1`，`backend_id=ck3-1.20.0.2-native-player-religion-hostility-v1`。
- 实际 `snapshot_revision`、`date_raw`、game version、EXE SHA，以及 `player_religion_hostility` 真实 DTO。

Inner DTO 保留双方 Rite／Faith／Religion／main Rite 完整身份、同 Faith／Religion booleans 和四个
独立方向等级及 stock key。`capture_epoch` 是实际 owner pump epoch，与 published snapshot revision 分开。
native 不可读／无目标／返回 sentinel 时给 typed unavailable；不能把 null 降为 righteous 0。
失败 inner 的 date／played actor 由实际 owner envelope 帧补齐，敌对等级仍为 null。
响应 accepted 只说明查询被处理，不代表任何动作、婚姻合法性或结果成功。

## 实际 owner 路径

```mermaid
flowchart LR
  Q[required full target Rite ID + optional revision] --> P[Parse actual request]
  P --> H[exact adapter / paused published frame]
  H --> S[TrySubmit actual query envelope]
  S --> D[owner pump and drain]
  D --> E[EnterQueryMailbox]
  E --> R[ReadPlayedHostilityTowardsRite12002]
  R --> F[FinishQueryMailbox]
  F --> W[Wait and Reclaim]
  W --> J[actual command_result serializer]
  J -.-> C[central next-increment route / named permit pending]
  C -.-> L[root paused real-game qualification pending]
```

Header／实现／test 为 `religion_doctrine12002_hostility_mailbox.*`；运行入口
`research/religion_doctrine12002_hostility_mailbox_tests.py`。它复用生产 `QueryMailboxEnvelope`、
actual submit/drain/wait/reclaim 和真实 library／serializer，不发现或连接游戏。
中央下一增量登记 flag `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_HOSTILITY_PRIVATE_QUERY_V1`，默认 OFF，
named permit 为 `permitted_executor_religion_hostility12002`，callback 为
`ExecutePlayerReligionHostilityMailbox12002`；本包不改 shared CMake／bridge／mailbox registry。
standalone fixture 使用已有 primary permit，不能把它称为最终 named-slot 组合验收。

## 已通过的范围与剩余

MSVC `/Od`、`/O2`、`/W4 /WX` 各 **50 项检查**通过，各生成 **5 份**实际 command_result：
asymmetric、same-faith、zero-target-id、target-unavailable、native-sentinel。另验证 owner frame
实际变化不给成功包、必填目标／uint32 边界／revision alias，以及 handler 在排队前拒绝缺目标和过期帧。
两构建的五份 JSON bytes 相同；不是 50 场游戏测试，也没有重跑旧 20 项 library 矩阵。

外部 artifact 在
`Z:/ck3_mod_rewrite/artifacts/g2-offline-2026-10-01/religion-doctrines/hostility/mailbox/`；
完整 wire 冻结副本在 `research/religion_doctrine12002_hostility_mailbox_wire_fixtures.json`。
`asymmetric.json` SHA-256 `cd61a8e5bbfd40f2d0617136608c95211d1b68da29c211f55e78f2425a19516a`；
`zero-target-id.json` SHA-256 `29ed0fdadfd442034fe9fabd26f9a188358513d237068657a26a19264317db44`。

底层 native callbacks 使用 fixture-owned 对象；adapter unwrap shim 仅替代 bare adapter identity，
未替换 WorkerAdapter。中央 selector／named permit／默认与选定 build、Python/MCP 正式消费以及 root-only
paused 实机读回仍待后续实际验收；当前首轮运行中的冻结 DLL 不受本后台增量影响。
