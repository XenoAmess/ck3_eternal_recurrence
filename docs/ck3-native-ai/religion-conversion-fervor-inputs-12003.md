# 同帧改宗目标 Faith 热忱输入

2026-10-06：A 已整合为可提交源码，**research / INTEGRATED_NOTRUN**。本次独占 worktree 的基线为 `be06a134b9a5472275e08ea452a8e3542b192fb8`，首次候选来源为 `df87fd8562120b901413793ded4680b7b4dabd8e`。游戏冻结身份仍为 CK3 **1.20.0.3 Crozier / Steam 25652598**，复用既有 EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`；本增量没有新 EXE 字节读取、哈希、SDK、游戏或策略操作。

## 原生输入账本先于实现

既有 [普通本人改宗](religion-conversion-native-ai-12003.md)、[Faith 身份](religion-native-ai-faith-identity-12003.md)及[热忱与县改宗](religion-fervor-county-conversion-native-ai-12003.md)保留各自已闭合来源与实机资格。本包先冻结 [NATIVE-TREE.md](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/faith-fervor/NATIVE-TREE.md)及六个 stock 摘录，再获授权实现 A；这些摘录、完整文件哈希及原始行号保存在 [SOURCE-INVENTORY.json](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/faith-fervor/SOURCE-INVENTORY.json)，不冒充新暂停帧。

Stock `common/script_values/02_religion_values.txt:3355–3360,3382–3416` 的本人转换费用使用 actor 与目标 Faith 热忱；`faith_conversion_fervor_mult` 是表达式输入，现成 native paid quote 仍给出完整最终费用。相同文件 `142–218` 的 demand conversion 接受度使用另一组 actor/recipient 接收者，`3248–3352` 的 holy-war defensive join 分数使用潜在参战者的 Faith。它们证明热忱参与各自消费者，但不把本包选中的本人/目标 Rite 对扩成收件人分数或敌方参战预测。

当前 actor fervor、五个 main/current Rite 数值缓存和最终 heresy threshold 已经发布，本包不重复资格。既有 `ck3_12002_religion_conversion_gates.cpp::ReadOnce` 已解析本人及指定完整 target Rite 的实际 Faith；`b.state.context.faith_fervor` 已绑定现 getter `Faith.GetFervor`（RVA `0x243EA90`，signed Q100000）。因此 A 无需新增 RVA、绑定或任意 Faith-ID 查询。

```mermaid
flowchart TD
    F[既有拥有者暂停回调和实际玩家] --> A[当前 actor Rite 到 Faith]
    F --> T[既有指定 full target Rite resolver]
    T --> TF[目标实际 Faith]
    A --> AG[既有 Faith.GetFervor getter]
    TF --> TG[同一 getter]
    AG --> PAIR[新增 conversion_fervor 同 epoch date player target 对]
    TG --> PAIR
    PAIR --> WIRE[既有完整 owner mailbox serializer 和 exact .3 identity renderer]
    WIRE --> P[现 transport 和新增严格 child normalizer]
    P --> MCP[现 registered MCP 直连 NativeDriver]
    MCP -. unknown 首次编译和四场景 compound .-> FIRST[静态资格收据]
    FIRST -. unknown 新鲜 Robert 暂停帧 .-> LIVE[production-live primitive]
    STOCK[stock GetYearlyFervorChange] -. unknown exact .3 数值合同 B NOTRUN .-> Y[独立最终年变化施工]
```

## 实际生产接线和 DTO

原 query 仍为 `ck3_query_player_religion_conversion_inputs_v1(expected_revision,target_rite_id)`，沿用原 `allow_private_player_religion_conversion_inputs_query` 和 `XAR_CK3_ENABLE_G2_RELIGION_CONVERSION_PRIVATE_QUERY_V1`。MCP 的现注册函数直调 `NativeHeadlessGameplayDriver.query_player_religion_conversion_inputs_private_v1`，然后进入 transport/normalizer；这里没有 conversion-input Service 方法，本次不新增 forwarder 或改变路由。

新 leaf `ck3_12003_conversion_fervor_inputs.hpp/.cpp` 仅解析暂停帧实际 alive played actor、其 current Rite→Faith 与 getter 一致性，以及现 full-generation target resolver 的真实目标 Faith。`ResolveConversionTargetRite12002` 只是既有私有 `ResolveRite` 的薄导出。两个真实接收者调用原 getter 后，标准 owning callback 二次读比较身份、日期与数值。没有 AI/任意 actor 覆盖入口。

现 owning mailbox 只在真实 reviewed `.3` descriptor 时读取并发布可选 `conversion_fervor`；新 DTO 的身份与 frame join 到已有 actor/date/epoch/target 和可用 gate Faith IDs。原 `g.available && p.available` 与 envelope status 语义保持；新字段不成为 final paid admission。

| 字段 | 真实合同 |
|---|---|
| `schema/read_only` | `ck3_12003_conversion_fervor_inputs_v1 / true`，可选 `.3` child |
| `available/unavailable_reason` | 独立采样结果；失败具体 reader reason，不能把 null 当已完成观测 |
| `capture_epoch/date_raw/played_character_id/requested_target_rite_id` | 既有 owner callback 的实际 epoch、日期、玩家和本次指定 full Rite |
| `actor_faith_id/target_faith_id` | 实际完整 Faith IDs；合法 ID 0 和 same Faith 均可用 |
| `actor_fervor_raw/target_fervor_raw` | getter 的 signed int64 对；合法零值保留；失败同时清空两项并保留已采身份/frame |
| `raw_scale/unit` | `100000 / fervor_points` |
| `is_final_conversion_cost/is_final_conversion_desire` | 均为 false |

Python 新严格 leaf 校验 exact `.3` build、16 个 keys、类型/units、实际完整 ID 和 owner frame/target join。既有 transport 只接受原 top keys 或原集合加此一可选 child；旧 gates、prediction、top status 不被新 normalizer 改写。

## Root 首次联合资格入口

源码已采用；**本工作包没有执行任何 project imports、测试、构建或实机**。Root 的下一 64-jobs joint batch 是首轮资格，不能提前写 static-ready 或 live。

Native 生产目标仍为 `xar_ck3_bridge`。新增目标/CTest 名为 `xar_conversion_fervor_inputs_first_test`，CMake 使用本增量自有 `conversion-fervor-inputs.cmake`；实际 compiled reader→owner mailbox submit/drain/wait/reclaim→完整 serializer→生产 `RenderCrozierBuildIdentity` 产出 `<build>/conversion-fervor-first-wire/`。旧 named fixture 仅增加新 leaf 的必要 link dependency，不要求重新执行旧 suite。

四个 FIRST 场景是 `distinct_faith_positive_values`（7,500,000 / 6,000,000）、`legal_zero`（0 / 0）、`same_faith`（5,500,000 / 5,500,000）及 `getter_failure_independent_of_old_gate`（child target getter unavailable / 两 raw null / old top 仍 observed）。所有身份与数值是 controlled synthetic material，不是 Robert live 数据。

唯一消费者为 `ck3_autonomous_player/tools/conversion_fervor_registered_mcp_compound.py`。Root 用下列 argv 消费实际完整 compiled packet，通过 `create_server(driver).call_tool` 注册链进入真正 driver/transport/normalizers；它保留编译原始 bytes、source request ID 与 native result/body，仅依现 offline PacketDriver 模式关联外层 request nonce。Receipt 明示这项适配、synthetic snapshot metadata 和 `live=false`，不伪造 native domain。

```text
py -B -X utf8 ck3_autonomous_player/tools/conversion_fervor_registered_mcp_compound.py --source-root <integrated-root> --native-fixtures-dir <build>/conversion-fervor-first-wire --output-dir <fresh-attempt-directory>
```

Compound 收据为新 attempt 的 `RESULT.json` 和 `observed.json`。通过后才允许提高相应静态资格；之后由 Root 在唯一 Robert 29829 普通战役取得 fresh choices 的有效 full target Rite，并用原 query 保存实际暂停结果，要求两个真实 non-null raw 与 actor/target Faith/frame。same Faith 结果只证明该分支，不虚构异 Faith live 覆盖。无需转换动作或推进日期。本包不授予 OODA、paid conversion、recipient acceptance、holy-war join 或新游戏日信用。

## 2026-10-06 22:38：首次实际 fixture 链接 RED 与源码修复

Root 在 joint source `71b729f0cc4894331f1dadb89155920fccd42a00` 的原 strict cache 执行 completion01；[实际 completion receipt](Z:/ck3_mod_rewrite_process_assets/g2-background-round33-20261006/joint-source-cap64-root/remaining-original-targets-completion01/ROOT-ACTUAL-COMPLETION-RESULT.json) 为 RED/exit1。原 [CP936 stdout](Z:/ck3_mod_rewrite_process_assets/g2-background-round33-20261006/joint-source-cap64-root/remaining-original-targets-completion01/COMPLETION-STDOUT.log) 显示 fervor target 的 `ck3_12003_adapter.cpp.obj` 有 **17 个 LNK2019 / LNK1120=17**，涉及实际 Maa、battle、supply、combat、route、refill、war-cash 和 `.2` adapter/factory 依赖；新 EXE 不存在，CTest 与 wire consumer 都没有运行。失败保留，不能把它称为 component 观测或 qualification GREEN。

修复只在新 fixture 的自有 CMake 链接中增加现有 `xar_ck3_12002_runtime`，保留当前 reader/owner/serializer/真实 `.3` renderer 源、fixture adapter macro、`/W4 /WX` 和其余 compile/link options。这 17 个实际定义已由现 runtime 的源码及 scoped/ordered-refill CMake 加入；不新增 binder stub，不修改 runtime、生产 reader、DTO、serializer 或 MCP 路由。该 target 通过真实库继承全部 PUBLIC feature/layout definitions；Root 外置投影若导入原 runtime archive，必须同时保留原 `INTERFACE_COMPILE_DEFINITIONS`、include directories 和 link dependencies。普通 archive extraction，无 `/WHOLEARCHIVE`；现 fixture 的 `NativeAdapter12002` 只保留既有 offline harness seam，未新增假的真实 helper。

这是 **harness link RED 的 source-only 修复**，实际 relink/native FIRST/registered-MCP compound 继续 NOTRUN，readiness 仍 research。Root 在下个外置 projection 首次编译修复后目标；四场景和 fresh Robert live 仍待真实结果，B 保持独立不阻挡 A。

## 2026-10-06：实际四目标复链 RED 与最小 helper 修复

Root 的 [four-link repair 实际 receipt](C:/codex-ck3-background/joint-source-cap64-batch/repair-four02/FOUR-LINK-REPAIR-BUILD-RESULT.json) 使用 fixture source `2738568d62a6ded29ac3b66fc564185e6b19ba16` 和原 `71b729f0cc4894331f1dadb89155920fccd42a00` runtime/protocol archive，保留实际全部 **68 项 PUBLIC compile definitions**、include 及 `bcrypt` link usage；两 archive 没有重编。该四目标批次仅本 Fervor target 链接 RED，原 [GBK stdout](C:/codex-ck3-background/joint-source-cap64-batch/repair-four02/FOUR-LINK-REPAIR-BUILD-STDOUT.log) 第 94–100 行显示 `ck3_12002_family.cpp.obj` 引出的两个真实未定义符号：`ValidateCurrentFirstHeirBilateralRelationshipV1` 和 `PrepareCurrentFirstHeirBetrothalFulfillmentSubmissionV1`。这次实际失败和前次 17-symbol RED 都保留，不覆盖原 attempt。

独立 base2738 修复只在新 fixture 自有 `add_executable` 中补现有 `current_first_heir_relationship_v1.cpp`、`observed_heir_marriage_private_v1.cpp`。两定义各位于第 28、66 行，受已继承的 `XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1` 宏控制；已复用 Creation fixture 的同一两-helper closure。runtime archive、PUBLIC 定义、现 stub seam、生产 reader/MCP 和 `/W4 /WX` 等选项均未修改。外置单目标 [projection recipe](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/faith-fervor/link-repair02/single-target-projection/RECIPE.json) 从冻结 metadata 整体导入 PUBLIC usage，并只编译当前 fixture 源和这两个真实 helper；它没有创建新的 runtime。

这是 **source-only harness link 修复**：本工作包没有构建、CTest、project import、wire consumer、游戏或新 EXE/hash 操作。Root 的下一次真实 relink 才能判断修复结果；本 A 仍 research，native FIRST / sole registered-MCP compound / fresh Robert paused read 全部待执行，B 继续不阻挡 A。Oct6/W41 增量字段见 [repair02 REPORT-FIELDS.json](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/faith-fervor/g104-compound/link-repair02/REPORT-FIELDS.json)。

## B 和其他未完成项

B 年变化继续 **NOTRUN，不阻挡 A**。stock `window_faith.gui` 使用 `Faith.GetYearlyFervorChange`；旧 `.2` 候选 body `0x243EC60..0x244088D` 及已有 special cache 不等于 exact `.3` callable contract 或最终当前年变化。本包保留独立 [12-byte-only metadata request](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/faith-fervor/EXACT-METADATA-REQUEST.json)，没有新 EXE 采集。实际年净变化、signed contributions、未来累计结果仍各自未发布；不能以长期 null 或参数 +0.5 代替它们。

Oct6/W41 可核验工作字段在外置 [REPORT-FIELDS.json](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261006/faith-fervor/implementation-A/REPORT-FIELDS.json) 和 Root 接收的 integration receipt，统一日报/周报与 push 由 Root 合并。原 current/五 cache/threshold 的资格不变；本新增 component 仍 research，等待一次首次 compound 和新鲜暂停帧。
