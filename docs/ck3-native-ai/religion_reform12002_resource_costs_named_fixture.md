# CK3 1.20.0.2 宗教草案基费专用队列验收

2026-10-01；本包状态为 `static-ready named queue fixture`。
它补齐 [`resource-costs mailbox fixture`](religion_reform12002_resource_costs_mailbox_fixture.md)
未覆盖的专用 callback admission；所有既有 provider、通用队列五源、原生费用矩阵与原生树保持冻结。
本包仅新增 test、runner 和本页三源，没有修改中央接线或访问 CK3。

游戏固定为 **1.20.0.2 Crozier / Steam25588574**，EXE SHA-256
`AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`。
中央已安装的 mailbox 字段为 `permitted_executor_religion_draft_resource_costs12002`，
实际 callback 为 `ExecutePlayerReligionDraftResourceCostsMailbox12002`。

## 实际覆盖

fixture 从默认初始化的真实 `MainThreadQueryMailboxV1` 开始，复用既有 paused owner-pump helper，
清除 helper 原先配置的 `permitted_executor`。其余 permit 保持默认 `nullptr`；
只给上述资源费用专用字段配置精确 callback。
新用例在工作线程调用生产 `RunPlayerReligionDraftResourceCostsMailbox12002`，
由拥有线程 drain，再由实际窗口/费用/base-resource provider 和 serializer 产生完整原生返回包。

```mermaid
flowchart LR
    A[Only resource-cost named permit] --> B[TrySubmit actual named admission]
    B --> C[Owner pump Drain]
    C --> D[Actual visible draft and base-fee quote]
    D --> E[Finish and Wait/Reclaim]
    E --> F[Complete native command_result]
    F --> G[Byte comparison with frozen generic packet]
```

仅 `main_thread_query_mailbox_v1.cpp` 与 `ck3_12002_query_mailbox.cpp` 为消费当前专用字段重新编译。
provider、mailbox adapter 与其他生产依赖直接复用原 GREEN fixture 的已冻结 `/O2` objects。
helper 是 `Z:` artifact 内的一份既有通用 resource testcase 源副本；只改名其外层 main。
嵌套原 12-case main 原本已经改名；两个旧 main 都没有调用，源文件未修改。

本测试直接配置真实 mailbox 字段，因此不声称执行了安装 environment 的传播、worker selector dispatch、
共享 registry/Populate、MCP SDK 或实际游戏回调。中央对这些路径的编译和接线证据单独归中央包。
本结果没有增加 `fixture-live`、`production-live primitive` 或 G2 qualification。

## 首次 GREEN

artifact 根：
`Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\resource-query-named\attempt-001`。

**MSVC `/O2 /W4 /WX`，8 checks / 1 case / 1 完整 command_result，首次 GREEN。**

- `result.json` SHA-256：`7ea5c64a9b3e4865e0f86c40db6a73c0542cc3b429aa82f2496e25c14f9a55b6`。
- `wire/visible-base-fee.json` SHA-256：
  `d954c0c2746f1d9a9d67b1cf3724d2e826fffa76d1db5e0f8827ebfb62b850b6`。
- 与冻结 `resource-query/attempt-001/wire/visible-base-fee.json` **逐字节一致**；
  相同输入、request ID 和 provider，无 serializer 补写或 metadata 拼接。
- 十槽基费向量 `[0,0,9000000,0,0,0,0,0,0,0]`，piety signed missing `-2500000`。
- 主通用 permit 为 `nullptr`；旧宗教/reform/group/Doctrine/Tenet permit 保持 `nullptr`；
  只有当前资源费用的专用 callback 入队并执行。
- 实际拥有线程完成 admission、drain、窗口与基费读取、Finish、wait/reclaim；队列回到 idle。
- 原 12-case、通用 resource 单例、费用 provider 矩阵和 native proof 均未重跑。

查询 scope 仍为 `native_command_draft_base_fee_quote`：只观测草案基费报价。
`actual_debit_observed=false`、`post_action_net_resource_change_observed=false` 原样保留，
没有创建/编辑/选择/提交游戏命令。

可复用命令（已有 GREEN 后不重复运行）：

```text
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe ck3_autonomous_player\native_bridge\research\religion_reform12002_resource_costs_named_tests.py --artifacts Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\resource-query-named\attempt-001 --resource-objects Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\resource-query\attempt-001
```

## 协调者日/周报告字段

- 日期 / ISO 周：`2026-10-01` / `2026-W40`。
- 完成：资源草案基费专用队列的真实 named-only admission 与完整原生返回包。
- 原因：核实中央新槽能够单独执行已冻结的只读费用查询，为中央整 DLL 与实机验收提供输入。
- 测试：一次新 `/O2 /W4 /WX` single case GREEN，8 checks；返回包与冻结通用包逐字节相同。
- 能力/readiness：增加 `static-ready named queue fixture`；没有 live/G2 或实际扣款观测变化。
- RED：本次首次编译与执行无 RED。
- 下一步：中央整 DLL 构建/冻结；根协调者按现有实际草案入口完成 paused visible quote 实机观测。
- Commit / push：由根协调者统一提交推送；本包没有执行 Git。

本包三源路径/哈希、proof、复用 object 和报告字段记录在
`resource-query-named/final-source-package.json`。
