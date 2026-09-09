# CK3 1.19.0.6 原版事件知识 Registry

## 当前状态

- [static-ready] 共享 registry 已实现在
  `ck3_autonomous_player/src/xar_autoplayer/vanilla_events/`。它提供合同构建、冲突检测、`$player` 物化和 JSON-safe 查询；全部能力均为离线只读，不依赖已启动的 CK3。
- [static-ready] `ck3_query_vanilla_event_knowledge_v1` 已注册到正式 MCP server。它只按 stable event key 与 CK3 build 查询知识，不选择按钮、不推进时间、不修改存档或 registry。
- [static-ready] 默认扁平 registry 当前为 **159 个 unique vanilla event key**：19 个 vanilla shard、57 个 manager-original、79 个 embedded-original 合并为 155 个 unique key，再加独立的 `tgp_movement_events.0160`、`tgp_dynastic_cycle_events.0001`、`tgp_dynastic_cycle_events.0020` 与 `epidemic_events.1064`。该数量由 registry/migration 测试冻结；以后代码和测试同步调整时，以测试中的当前期望值为准。
- [static-ready analysis / mixed live evidence] 当前同时发布 **159 条 analysis** 与 **7 个 observation keys**。159 条分析中，缺少已冻结 source hash 的旧结论只按既有合同注释、docs/tests 标为 migration-only，不编造 hash；`TGP0160`、`great_holy_war.0011`、`TGP0020`、`TGP0001` 与 `epidemic_events.1064` 已完成 production runner 的真实 drain/advance，`stress_threshold.1721` 与 `epidemic_events.5009` 的第二次合法出现保留为真实 RED observations。
- [static-ready context profiles] prebootstrap 的 `spymaster_task.0381`、`spymaster_task.0399` 两条记录继续作为 seed-capture 上下文 profile 保存，不混入默认扁平 registry。它们与默认 manager 合同使用相同 event key、但冻结不同阶段的精确存档 shape，强行压平会造成有意义的合同冲突。

当前状态表示 registry、默认数据组合和只读查询可以被静态消费者使用，不表示 159 条记录都已有独立 production-live exemplar，也不表示 CK3 自动玩家已经具备完整事件效用判断。production runtime 当前组合 `298` 条事件合同；共享 registry 的 production-live 标签严格只落在上述五条已完成选择与 advance 的切片。TGP0001 与 epidemic1064 均在同一 PID 热恢复后完成 reviewed selection；R372 继续推进并在第二次合法出现的 `epidemic_events.5009` instance `871` park12 动作前 RED 停住。

T0 当前仍为 `50%`、canonical stage `8/11`，source checkpoint `3/4` 且只缺 `capture_cross_cycle_endgame`；T0-P1 未签收，T0-P2 继续 `LOCKED`。`strict 4/361` 与 `definitions 106/626` 只是非阻塞 backlog。

## Exact-build 边界

Registry v1 只支持：

- CK3 `1.19.0.6`；
- `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；
- canonical `event_definition_key`，例如 `ep3_decisions_event.2001`。

查询其它 build 会返回 `status=unavailable` 与 `unsupported_ck3_build`，不会从相邻版本猜测兼容性。v1 response 同时返回上述 EXE SHA，供消费者绑定 provenance。

当前扁平主键是 exact build 下的 stable event key。v1 尚未接收 playset 或 effective-definition fingerprint；如果其它 mod 覆盖了同名原版 definition，消费者必须将 stock 记录视为不适用，不能因为 key 相同就继续选择。将来若把 effective definition 纳入公共 schema，必须作为显式版本演进，不能改变 v1 的含义。

升级 CK3 后，即使 event key 未变，也要先重新比较定义、相关 ABI 和选项语义。旧 build 的静态记录或 live exemplar 不会自动升级成新 build 证据。

## Canonical ownership 与默认组合

共享 package 是原版事件合同的 canonical owner：

- `records_vanilla_shards.py`：19 条原版专题 shard；
- `records_manager_a.py`、`records_manager_b.py`：57 条 manager-original；
- `records_embedded.py`：79 条原先内嵌于 T0 runner 的 vanilla 合同；
- `records_tgp_movement.py`：当前独立 TGP movement 合同及其分析/观察元数据；
- `records_tgp_dynastic_cycle.py`：独立 TGP dynastic-cycle 合同及其分析/观察元数据；
- `records_analysis_vanilla_shards.py`、`records_analysis_manager_*.py`、`records_analysis_embedded_*.py`：把已有结论迁移为默认 analysis；没有既有 source hash 的条目保持 migration-only；
- `records_prebootstrap.py`：两条不进入默认扁平表的上下文 profile；
- `registry.py`：构建、物化与只读查询实现。

`build_vanilla_event_registry` 对合同、analysis 与 observations 做防御性深拷贝，并拒绝 metadata 引用未注册的 event key。重复 key 的 canonical JSON 完全一致时去重；内容不同时抛出冲突，并保持先前 active registry 不变。查询返回新的 JSON-safe 副本，调用方修改 response 不会污染 canonical record。内部 legacy tuple 到 MCP JSON 边界才投影为 array，metadata 的整数 option key 也只在 JSON transport 中规范化为字符串。

产品不应再复制共享原版事实并长期维护第二份权威定义。迁移期间可以保留 legacy adapter，但必须由定向 parity 测试证明它与 canonical record 一致；产品目录只应新增产品自己的用途约束和后置断言。

## Invariant contract 与 observation exemplar

Registry 将“可复用合同”和“一次实机看到的值”视为两种不同信息。

Invariant contract 用来匹配和处理事件，典型字段包括：

- root、named saved scope 的类型与相等/互异关系；
- source-reviewed 的 scope/option projection variants；
- authored native index、rendered option count 与选择映射；
- 日期/occurrence policy；
- 用于有界 drain 的 `selected_option_number` 与 `selected_native_option_index`。

Observation exemplar 记录一次具体运行的 date、event instance、角色 ID、实际 projection、artifact/checkpoint hash 和是否尝试选择。除非原版定义明确提供 exact anchor，这些值不能因为出现过一次就成为通用日期或人物合同。

v1 的 155 条迁移基线以保持现有 T0 合同逐值 parity 为首要目标，其中仍可能包含原 seed 的日期或人物锚；它们不能自动宣称已经完成全面的 campaign-neutral 归一化。新增或实质修订记录应逐步采用合同/观察分层，不能为了“清理数据”而破坏已经验证的 legacy 行为。

### 当前完整分层样例与首批 live 切片

`records_tgp_movement.py` 对 `tgp_movement_events.0160` 同时维护三块互不混淆的数据：

- `VANILLA_TGP_MOVEMENT_TIMELINE_CONTRACTS`：默认 registry 消费的 campaign-neutral 合同，玩家用 `$player` sentinel 延迟绑定；
- `VANILLA_TGP_MOVEMENT_ANALYSIS`：exact build/EXE、四个原版来源文件 SHA-256、定义行号、yearly caller 与十年 cooldown、三个选项语义、`after_effect=None` 和 safe-option rationale；
- `VANILLA_TGP_MOVEMENT_OBSERVATIONS`：R372 paused-live exemplar，包括 artifact/hash、`date_raw=53436720`、instance `668`、本局人物 ID、scope raw type 和 `selection_attempted=false`。

R372 的日期、instance 和人物 ID 不进入新建或已触达迁移后的通用 timeline contract。当前 MCP v1 在同一个 knowledge envelope 中以彼此独立的 `contract`、`analysis`、`observations` 字段返回这三层；所有 159 条记录已有 analysis，只有七条拥有 observation metadata。元数据可查询，但不会混入选择合同或被物化成当前人物约束。

R372 已在同一 PID/session 上把 `TGP0160`、`great_holy_war.0011`、`tgp_dynastic_cycle_events.0020`、`tgp_dynastic_cycle_events.0001` 与 `epidemic_events.1064` 从共享记录解析到真实 option submission，并验证旧 instance 消失或 advance，因此五条均为 `production-live primitive`。`stress_threshold.1721` observation 保留前一次真实 RED：共享模块 reload 实际已经生效，错误是 submission 阶段再次按 base contract 解析，导致提交了 base route；这不是 reload failure。`.5009` 的第一次交付曾真实 GREEN，当前第二次交付则证明旧 `max_occurrences=1` 错误；park12 仍停在动作前等待通用 repeatable 合同热恢复。五条 GREEN 不能外推为其余 154 条记录已经 live。

批量迁移 analysis 的证据等级低于带 exact source hash 的逐条审阅：它只复用已有合同注释、历史 docs 和 tests。若旧证据没有保存 source hash，metadata 必须明确写 migration-only；不得为了让字段看起来齐全而事后猜测 hash。

Prebootstrap 两条记录采用同一原则，但它们表达的是某个 seed-capture 阶段的精确上下文，不是默认 manager 语义，所以保留为命名 profile，而不是与同 key 的 manager record 竞争 canonical 扁平槽位。

## Safe-choice 语义

当前 v1 沿用经过原版定义审阅的：

```text
selected_option_number       # 1-based consumer 编号
selected_native_option_index # 0-based CK3 authored index
```

这里的 safe choice 只表示对既定用途的最小、有界 drain 路线，例如终止支线、避免新 follow-up 阻塞链、避免资源支付或保持当前任务；它不表示“最佳选项”“绝对无副作用”或完整 campaign utility。TGP0160 就明确记录：native 2 避免十五年 scheme block 和 gold transfer，但仍有少量 intrigue lifestyle XP 与 ambitious stress 影响。

消费者选择前仍须从同一 paused revision 验证 event key/instance、root/scope shape、实际 `shown=true && enabled=true` 以及 native/rendered mapping；选择后须观察 event instance 消失或前进，以及用途需要的状态后置。Command ACK 不是完成证据。

若当前 projection 与合同不符、登记选项不可用或缺少满足当前用途的知识，消费者必须保留 paused RED，并按“查原版定义 → 最小修复 → 定向重跑”补记录。不得降级为 OCR 猜测、盲点第一个按钮，或把 `is_cancel_option` 当作无效果证明。

## Consumer 边界

### CK3 自动玩家

自动玩家和运维 agent 可以通过 MCP 读取当前 stable event key 的 canonical timeline contract，再结合 `current-event-window-context` 和 campaign policy 决定是否采用登记选项。MCP tool 已可调用，但 registry 不直接提交 `select-event-option-N`，也不自动替代现有策略层；选择、instance/revision 绑定和后置验证仍走既有 gameplay command 链。

Registry 是离线静态数据，因此另一台机器只需取得同一仓库/package revision 和依赖，即可通过同一 MCP 查询；不需要复制原机器的 CK3 进程、绝对 artifact 路径或用户存档。

### T0 天朝二期 validator

T0 的 migration parity 测试逐 bucket 对照旧合同，并冻结 `19/57/79` 数量、155 个迁移 unique key，以及两条 prebootstrap 有意 overlap；再加 TGP0160、TGP0001、TGP0020 与 epidemic1064，默认合同与 analysis 均为 159。后续 T0 consumer 应按实际产品路径查询或物化所引用的记录，并继续用产品自己的 window、occurrence、source checkpoint 和业务后置条件验收。

共享 registry GREEN 只说明引用的原版中断知识可解析且与迁移基线一致；它不能提升 T0 stage、四类 source、full-tree 或媒体 readiness。Prebootstrap validator 必须显式选择对应 profile，不能从默认扁平 lookup 取得 seed-capture shape。

### 其它 mod validator

其它 mod 可以复用默认 registry 的相同 event key，并在自己的 validator 中增加窄用途约束和产品后置条件。Validator 只检查该 mod 实际引用的记录；若 mod 覆盖同名原版 event definition，必须建立自己的 effective-definition 合同或返回不适用，不能修改共享 stock record 来迎合单个产品。

## 当前 read-only MCP

正式接口为：

```text
ck3_query_vanilla_event_knowledge_v1(
  event_definition_key,
  ck3_build = "1.19.0.6"
)
```

成功时返回：

```text
schema = xar.ck3.vanilla-event-knowledge
schema_version = 1
status = available
event_definition_key
ck3_build
ck3_exe_sha256
contract
analysis
observations
unavailable_reason = null
```

非法 key、未知 key 或不支持的 build 返回相同 envelope、`status=unavailable`，且 `contract/analysis/observations` 均为 `null`；`unavailable_reason` 分别为 `invalid_event_definition_key`、`event_definition_key_not_registered` 或 `unsupported_ck3_build`。

该 MCP 查询不访问 gameplay driver：离线测试用一个任何 backend 调用都会报错的 driver 验证 tool 仍可 list/call。接口不接受本地路径、人物 ID、按钮选择或写回 payload；返回记录是 detached JSON，不会修改服务端 registry。

## Migration 与兼容

- Schema 当前为 `xar.ck3.vanilla-event-knowledge` v1。消费者必须检查 schema version；未来破坏性字段语义变更应使用新版本，不能静默复用 v1。
- 迁移测试保证 legacy buckets 逐值相等、默认合同与 analysis 均精确覆盖 159 key，并拒绝意外 duplicate/conflict；默认组合故意不加入两条 prebootstrap context profile。
- `$player` materializer 只替换值完全等于 sentinel 的字段，不改写包含该字样的普通字符串，并返回独立副本。
- 查询边界统一将 tuple 投影为 JSON array，从而允许原 Python consumer 保持旧合同类型，同时让 MCP 跨进程、跨机器稳定序列化。
- 新 CK3 build、改变的原版 definition 或 mod override 都需要显式新证据；v1 不提供“相似版本大概兼容”的 fallback。
- Analysis 与 observation metadata 可以增量补充，但不能改变同一 timeline contract 的选择语义而不触发对应定向回归。

## 明确不是 `361/626` exhaustive gate

默认 159 key 是当前按需积累的复用资产，不是覆盖率目标。Registry 不要求在继续 T0、运行其它 mod、CI 或发布前枚举全部 `361` 个场景或 `626` 个 definition。

- `known/total` 只可作为 discovery telemetry，不能换算产品完成百分比；
- 未遇到、未引用的 definition 不进入发布或实机前置门；
- 缺失记录只阻塞真实停在该事件上的下游选择，其他非冲突工作继续；
- 全树扫描可以发现候选和重复项，但不能取代产品验收，也不能自动制造“必须全收录”的任务；
- T0 完成标准仍是主体工程、内容、约定测试矩阵与 hard-gated 最终媒体，不由 registry 数量决定。

Registry 的价值是让已经付出过的原版定义分析可以被下一次事件、下一条 T0 路径和其它 mod 复用，而不是建立一条无限扩张的全树验收线。
