# 361 二期：指标、重组与需求交付 CK3 运行时权威规格

状态：**规范冻结；实现 readiness 上限为 `CK3 script static-ready`，不是 live**

覆盖：AA229–241、AG301–311、AJ334–344，共 35 项。优先交付面为 AA 与 AJ；AG 使用同一合同，不得另造一套身份、幂等或资源账。

本文件规定上述 35 项从 Python L0 语义投影到 CK3 scripted effect / character event 的唯一业务合同。它不把 Python 模型测试冒充 CK3 接线，也不把 CK3 静态文件冒充实机证据。

当前 static-ready 投影分为两层，必须分开陈述：

- **35/35 已实现的共同层**：每项都有独立 A/B/C route enum、同一组六字段 receipt、五元 write ticket、显式 provenance、独立 consumer、`visible_value` 和可见 revision；每条路线还落一组确定性的 quality / throughput / management-debt 取舍，因此不是三个同义按钮。
- **已实现的宽领域层**：AA240/241、AG304/306/308/309/310/311、AJ335/336/337/338/340/341/342/343/344 另有样本、份额、矩阵权重、HC、管理容量、历史 owner、紧急槽、签字、WIP、跨期容量和价值 credit 等专门字段与守恒写入。

后文机制表的“consumer 必须发布”列描述该机制最终面向案卷/考核榜/MCP 的丰富查询合同；尚未列入上述两层的细字段不能据此冒充当前已经写入 CK3。当前静态包完成的是可加载目录中的 write→consumer 主链及上述专门字段，查询键、GUI 和 live 证据仍在 readiness 边界之外。

## 权威来源与产物边界

语义参考：

- `tools/zg361_phase3_metrics_reorg_model.py`
- `tools/test_zg361_phase3_metrics_reorg_model.py`
- `docs/361-phase3-metrics-reorg-runtime-spec.md`

共享事务与身份 ABI：

- `docs/361-case-kernel-runtime-spec.md`
- `common/scripted_effects/zg361_case_kernel_effects.txt`
- `common/scripted_triggers/zg361_case_kernel_triggers.txt`

本包应由独立生成器维护，不得手改带 `GENERATED FILE` 标识的结果：

- `tools/gen_361_phase3_metrics_delivery_runtime.py`
- `common/scripted_effects/zg361_phase3_metrics_delivery_runtime_effects.txt`
- `events/zg361_phase3_metrics_delivery_runtime_events.txt`
- `localization/*/zg361_phase3_metrics_delivery_l_*.yml`
- `tools/test_zg361_phase3_metrics_delivery_runtime.py`

本包可调用共享 case-kernel 的公开 effect / trigger，但不得修改共享内核，也不得修改 B1、B2、scoreboard、shared case kernel、中央 on_action 或既有 GUI 文件。

## 角色权限与作用域

运行时只有两类角色：管理者 `owner` 与受评人 `subject`。

- 管理者必须通过 `zg361_case_kernel_can_open_trigger`：天朝制、在任、有地、公爵及以上，并且受评人是其可考核直属封臣。
- 玩家管理者使用 A/B/C 事件链作选择。
- AI 管理者仅适用项目所有者明确授权的“361 第二 AI 例外”：同样必须是天朝制公爵及以上，静默采用确定性的默认 A 路线。该例外只属于本 mod 的 361 管理链，不得外推到其他 mod 或无关 AI 行为。
- 伯爵和男爵可以成为 `subject`、读取并消费绑定给自己的可见结果；他们不能开案、选择路线、推进阶段、分配样本/HC/WIP、替他人考核或调用管理者入口。
- 受评人读取必须通过 `zg361_case_kernel_subject_self_guard_trigger`；该入口只发布自己的结果，不授予任何管理能力。
- 管理事件以管理者为事件 `ROOT`，用已保存的 named scope 指向受评人；所有业务写入发生在受评人 scope，`owner` 永远显式传入，禁止依赖跨事件的隐式 `PREV`。

## 五元冻结身份

每个开案、操作、业务写入、消费者和阶段推进必须携带并逐项核对：

1. `owner`：开案时的管理者；换上司不倒改历史 owner。
2. `subject`：被考核者。
3. `cycle_serial`：考核周期号。
4. `case_serial`：该领域案卷号。
5. `expected_state`：操作允许发生的冻结 stage。

五元身份不是“日志备注”，而是写入资格。任何变量读取都必须先置于对应 `has_variable` 存在性门内；字段缺失或任一项不相等均返回 stale no-op，不得落 receipt、业务值、资源变化或 stage 变化。标准入口必须复用 `zg361_case_kernel_full_guard_trigger`，不能用“只比 case_serial”之类的弱化判断。

## Receipt：幂等且 A/B/C 互斥

每个机制 ID 只有一组共享 receipt 身份字段，A、B、C 三条路线不得各自拥有互不相识的 receipt。

执行顺序固定为：

1. 五元 full guard；
2. 对同一 ID 依次检查 choice 1、2、3 是否已有当前 receipt；
3. 任一 choice 已提交，则本次无论重放同路线还是改选另一条路线都为 idempotent no-op；
4. 做全部 typed RED 与资源预检；
5. 调用 `zg361_case_kernel_record_operation_effect` 写唯一 receipt；
6. 仅当内核确认本次 operation applied，才写业务字段、冻结 write ticket、调用 consumer，并在 stage barrier 调用对应 dispatcher。

因此，网络/界面重复提交不会二次扣资源，玩家也不能先选 A 再点 B 把同一事项结算两遍。operation receipt 与 stage transition 仍是两种权限：机制 wrapper 不能自行改共享 state，只能在本规格列出的 barrier 调用 AA/AG/AJ 的公开 `advance` effect。

## Typed RED 与原子预检

`zg361_p3_last_red_code` 是稳定、可查询的数值类型。当前编码为 `ID × 10 + route`，其中 A/B/C 分别为 1/2/3；例如 AA240-B 的原子预检失败写 `2402`。调用方可无歧义地还原失败机制与路线，且不能把 stale、replay 和资源 RED 混为一类：`runtime_status = 3/2/4` 分别表示 stale no-op、idempotent no-op、typed RED。

当前每项都先检查该 domain 的 operation slot；专门资源预检还覆盖 AA240 样本槽、AG309 管理容量、AJ335 紧急槽、AJ337 当期容量/灾害豁免、AJ340 当期容量/WIP、AJ341 当期 reservation/下期容量、AJ344 剩余 value credit。签字、份额与 HC 由生成器写入固定守恒组合，当前不是由外部任意参数输入，所以不会生成不平衡组合；未来若开放 MCP 参数化输入，必须先扩展 typed RED 类别再开放写口。

所有可能失败的检查必须发生在 `record_operation` 之前。尤其禁止“先写 receipt，再发现没容量”；否则重试将永久变成 no-op，并留下未执行却不可再执行的假成功。

## Write → consumer 合同

仅写一个 choice 或 receipt 不算机制完成。每个 ID 必须有独立业务字段与独立 consumer：

- applied 路线写入该 ID 的 semantic value，并同时冻结 `write_owner/write_subject/write_cycle/write_case/write_state`；
- consumer 先 existence-gate，再把 write 五元与当前案卷五元逐项比对；
- consumer 自有 consumed ticket，重复消费不再增加反馈；
- 匹配成功才把 semantic value 投影到受评人的 `visible_<ID>` 结果，并递增可见 revision；
- stale write、别人的 write 或前一周期 write 只能 no-op，绝不能“取最近一条”误投到当前考核；
- 伯爵/男爵的 self-consumer 只读取 `visible_<ID>`，不能反向写 choice、receipt、资源或 stage。

consumer 的下游结果必须是可用于案卷/考核榜/MCP 后续查询的业务事实，例如“样本排队”“WIP 隐瞒债”“旧目标未改写”，而不是仅返回“按钮已点击”。

## 资源账与守恒

### AA：指标与实验

- `zg361_p3_aa_sample_used` 始终满足 `0 <= used <= total`。AA240 A/B 的活跃实验各消费一个槽；C 排队不消费槽。
- 指标分母和时间窗按版本冻结；新版本只能向后生效，旧奖励不得重算。
- AA241 每条路线的建设者、运营者、继任者收益份额合计 10000 bp；延迟成本使用相同三方、相同份额和相同 case provenance，不能只领长尾收益、不背长尾成本。
- 暂记 credit、学习分和虚荣指标追回必须分账；失败实验学习分不得伪装成成功 KPI。

### AG：业务周期与重组

- 双家长的经理权重合计 10000 bp，目标容量份额也独立合计 10000 bp；不得把一份人力给两个老板各算 100%。
- 双帽两组容量权重合计 100，且必须有到期周期和一种补偿支持。
- `manager_hc + expert_hc = total_hc`，调岗只搬移 HC，不凭空新增编制。
- 远程团队可见度行动真实消耗 `management_capacity`，只产生 visibility，不产生伪造的 delivery output。
- 重组前旧目标、旧 cohort、旧绩效档案保持不可变；映射不占用当前 3/6/1 配额槽。

### AJ：需求与交付

- `emergency_slot_used <= emergency_slot_total`；预留槽耗尽后只能显式牺牲旧需求、增加成本或由 sponsor 背责。
- `current_capacity_reserved <= current_capacity_total`，`next_capacity_reserved <= next_capacity_total`。
- 活跃 WIP 不得超过 `wip_limit + signed_or_hidden_exception_count`；隐藏超限必须形成可见绩效债，不能成为免费第四路线。
- 跨周期时先释放当期 reservation，再按未完工量占用下期容量；取消路线精确释放，不得重复退款。
- AJ344 的上线、采用、价值 credit 累计不超过 10000 bp，成熟度只能向前，不能跳过前置阶段或重复领奖。

## Stage 图与 barrier

同一 stage 内可以包含多个机制；这些机制共享当前 `expected_state`。只有该行最后一个 ID 是 barrier，并调用对应 `advance` effect。这样既避免每个按钮越权推进，又保证静默 AI 批处理与玩家事件链得到相同状态轨迹。

| Domain | 当前 state | 本 stage 的 ID | barrier / 下一状态 |
|---|---:|---|---|
| AA | 1 `defined` | 229, 230 | 230 → `zg361_case_aa_advance_01_effect` → 2 `reconciled` |
| AA | 2 `reconciled` | 231, 232, 233 | 233 → `advance_02` → 3 `preregistered` |
| AA | 3 `preregistered` | 234, 235, 236, 237 | 237 → `advance_03` → 4 `running` |
| AA | 4 `running` | 240 | 240 → `advance_04` → 5 `frozen` |
| AA | 5 `frozen` | 238, 239 | 239 → `advance_05` → 6 `interpreted` |
| AA | 6 `interpreted` | 241 | 241 → `advance_06` → 7 `closed` |
| AG | 1 `frozen` | 301, 302 | 302 → `zg361_case_ag_advance_01_effect` → 2 `split` |
| AG | 2 `split` | 303, 304 | 304 → `advance_02` → 3 `quiet_period` |
| AG | 3 `quiet_period` | 305, 306 | 306 → `advance_03` → 4 `mapped` |
| AG | 4 `mapped` | 307, 308, 309, 310 | 310 → `advance_04` → 5 `normalized` |
| AG | 5 `normalized` | 311 | 311 → `advance_05` → 6 `closed` |
| AJ | 1 `entered` | 334, 335 | 335 → `zg361_case_aj_advance_01_effect` → 2 `defined` |
| AJ | 2 `defined` | 336, 338 | 338 → `advance_02` → 3 `estimated` |
| AJ | 3 `estimated` | 339 | 339 → `advance_03` → 4 `in_wip` |
| AJ | 4 `in_wip` | 340, 342 | 342 → `advance_04` → 5 `changed` |
| AJ | 5 `changed` | 337, 341 | 341 → `advance_05` → 6 `delivered` |
| AJ | 6 `delivered` | 343 | 343 → `advance_06` → 7 `adopted` |
| AJ | 7 `adopted` | 344 | 344 → `advance_07` → 8 `valued` 并关闭 |

## AA229–241：数据口径与实验

表内 A/B/C 均是有代价的可执行路线，不是同一结果的三段文案。consumer 列是必须落地的受评人可见业务结果。

| Domain | ID / stage | 业务语义 | A 路线 | B 路线 | C 路线 | consumer 必须发布 |
|---|---|---|---|---|---|---|
| AA | 229 / 1 | 指标字典与唯一口径 owner | 冻结唯一 owner、定义、来源、频率、范围、分母和 provenance；治理最强 | 联合起草但仍指定一名最终 owner；增加协调成本 | 快速临时口径，仍指定唯一 owner；记口径债与较低置信度 | 口径版本、最终 owner、数据来源与口径债，不只显示“已定义” |
| AA | 230 / 1 | 多数据源对账 | 选择权威源；速度快，但权威源 owner 背误差责任 | 多方联合取一致/折中值；更稳健但增加校准成本 | 延迟结算；保留冲突值，不伪造确定结果 | 路线、resolved value 或 pending、责任源和 provenance |
| AA | 231 / 2 | 分母变更与历史版本 | 次周期生效，旧版完全冻结 | 新旧双轨展示一周期；支付迁移/解释成本 | 拒绝临时改分母，保留当前版本并记录需求债 | 旧/新版本号、生效周期、原因、`awards_rewritten = false` |
| AA | 232 / 2 | 缺失数据与人工回填 | 填写人与审批人双签，完整记录方法 | 模型估算并标低置信度，仍需独立复核 | 不回填，调低/冻结目标；受评人不为不可见异常自动背责 | 回填值/缺失状态、方法、两名签字人、偏差归责与 provenance |
| AA | 233 / 2 | 看板访问权不对称 | 向受评人开放完整口径与异常 | 分层访问并保留查询渠道；减少泄露但有沟通税 | 不开放数据；必须同步目标调整并免除未见异常责任 | access level、query channel、目标是否调整、异常是否可归责 |
| AA | 234 / 3 | 领先指标与滞后结果分账 | 领先信号只给 provisional credit，等待结果 | 领先与滞后同时结算；冲突则进入校准 | 只认滞后结果；更慢但不透支 credit | 两类值、recognition 状态、是否因方向冲突需校准 |
| AA | 235 / 3 | 主指标与护栏指标 | 护栏跌破即封顶主指标 credit | 危机特批越过护栏，审批人承接延迟责任 | 优先修复护栏，主动放弃本期部分主指标 | 主指标、护栏、breach、top-credit 资格与 liability owner |
| AA | 236 / 3 | KPI 达标悬崖 | 连续计分，减少 99/100 的断崖 | 混合计分，阈值以上有加速但不归零阈值以下 | 保留 cliff，激励最强但博弈/冲刺风险最高 | 本周期冻结 policy、threshold、`year_end_mutable = false` |
| AA | 237 / 3 | 时间窗挑选审计 | 严格使用预冻结全周期 | 允许披露后的替代窗口，但按全周期归一 | 接受申报窗口送审；若“截最美一段”则加 integrity penalty | 冻结/申报窗口、全期/申报值、cherry-picked 与 settled value |
| AA | 240 / 4 | 实验污染与多团队抢样本 | 预留一个独享样本槽 | 占用一个样本槽并签字切分边界 | 进入队列；不消费槽、不假装实验已运行 | 样本路线、clean claim、queue、槽位余额与 provenance |
| AA | 238 / 5 | 虚荣指标与最终价值 | 已有真实 adoption，保留 provisional credit | 仅有治理/稳定性代理价值，保留部分并标代理 | 只有 PV/点击等虚荣量，追回全部 provisional credit | vanity/adoption/governance 分账、kept credit 与 clawback |
| AA | 239 / 5 | 失败实验的学习收益 | 预注册、证据止损、结论可复用，给封顶学习分 | 部分条件满足，给较低学习分并列缺项 | 无预注册或无可复用结论，不给学习分；也不扣成“成功失败”双罚 | 主目标失败、学习分、成功 KPI 分恒为 0、negative-result quality |
| AA | 241 / 6 | 长尾效果归属期 | 建设者/运营者/继任者 5000/3000/2000 | 三方 3300/3300/3400 近似均分 | 三方 2000/3000/5000，偏向长期继任 | 收益与延迟成本各自合计 10000 bp，三方同份额同 provenance |

AA 的 stage 顺序特意把 240 放在 238/239 之前：先冻结实际运行的样本与污染，再解释价值或学习收益，禁止用事后结论倒推“当时实验一定干净”。

## AG301–311：业务周期与重组折算

| Domain | ID / stage | 业务语义 | A 路线 | B 路线 | C 路线 | consumer 必须发布 |
|---|---|---|---|---|---|---|
| AG | 301 / 1 | 核心业务光环折算 | 强证据下按顺风、资源和规模难度校正，调整有上限 | 保留更多 raw outcome，同时列明资源优势债 | 弱证据采用保守小上限，避免“核心业务天然满绩效” | raw outcome、personal increment、adjustment 与 cap |
| AG | 302 / 1 | 衰退业务的逆风责任 | 公开基线，按少跌多少奖励高质量防守 | 批准转守/止损计划，成果与 sponsor 责任分账 | 隐瞒逆风或只报绝对下跌，追加 integrity penalty | expected/actual decline、avoided decline、防守质量与披露状态 |
| AG | 303 / 2 | 孵化团队限期分布保护 | 最多两周期保护，出口为 graduate | 最多两周期保护，出口为 pivot | 最多两周期保护，出口为 close | 起止周期、milestone evidence、出口；`permanent_c_immunity = false` |
| AG | 304 / 2 | 项目归属/职能归属双家长 | 60/40，项目 owner 最终拍板 | 50/50，指定唯一 final owner 破平局 | 40/60，职能 owner 最终拍板 | 两名 manager 权重=100、goal shares=100、唯一 final owner |
| AG | 305 / 3 | 校准前重组静默期 | 遵守静默期，延后移动 | 危机特批：理由+上级签字，移动但冻结旧 cohort | 取消本轮重组，在下周期重开 | 是否 quiet period、危机理由/签字、moved subjects、old cohort frozen |
| AG | 306 / 3 | 双帽临时负责人容量拆分 | 管理/专业 30/70 | 两边 50/50 | 管理/专业 70/30 | 两组权重合计 100；`two_full_targets = false` |
| AG | 307 / 4 | 利润中心/成本中心记分卡 | 利润中心：收入+质量，不能只认收入 | 成本中心：节省+稳定性+内部价值 | 双视图对照，不强迫两类团队用一把尺 | center type、metric keys 与 `forced_common_metric = false` |
| AG | 308 / 4 | 管理岗与专业岗比例 | 管理偏重，缩小 span 但提高 reporting tax | 平衡配置 | 专业岗偏重，提高 span、降低汇报税 | manager/expert HC、总 HC 守恒、reporting tax、management span |
| AG | 309 / 4 | 边远团队可见度折损 | 实地走访，消耗 10 管理容量并增加 visibility | 远程证据会，同样消耗 10 管理容量 | 不占管理容量，但 visibility 为零并形成可见度债 | 消耗的 management hours、visibility gain；不凭空生成 delivery output |
| AG | 310 / 4 | 并入团队的旧档映射 | equivalence：建立可比映射 | context-only：旧档只作背景 | common-baseline：只映射到共同基线 | old ratings、mapping route、historical-only、current quota slots=0 |
| AG | 311 / 5 | 战略转向不得倒改旧目标 | 冻结旧目标完成度，新目标按生效日启用 | 一段可见 overlap 后切换，旧账仍冻结 | 关闭旧目标再立新目标，承认中断成本 | old/new goal、effective day、old completed 与 `old_goal_rewritten = false` |

## AJ334–344：需求入口与交付价值

| Domain | ID / stage | 业务语义 | A 路线 | B 路线 | C 路线 | consumer 必须发布 |
|---|---|---|---|---|---|---|
| AJ | 334 / 1 | 统一需求入口与来源标签 | 上司/战略需求，冻结 sponsor | 属地/用户需求，冻结受益方 | 故障/跨部门需求，冻结提出者与紧急来源 | demand ID、source、source owner、proposer、queue sequence、provenance |
| AJ | 335 / 1 | 紧急插单预算 | 使用预留 emergency slot；有槽才可选 | 等量换出旧范围，不消耗 emergency slot | 拒绝紧急标签，保留普通队列顺序并记 queue debt | 是否耗槽、scope trade、queue debt 与槽位余额 |
| AJ | 336 / 2 | 需求准入与完成定义 | 信息不足退回，不承诺容量 | 小额探索，受严格容量上限约束 | 明确 benefit/acceptance/boundary 后承诺；若强压则冻结 forcing owner | 准入路线、DoD 三字段、依赖、估算、admitted 与 forced liability |
| AJ | 338 / 2 | 范围—期限—质量三角签字 | 缩范围并签字 | 延期限并签字 | 追加 HC 并由 owner 签预算 | tradeoff enum、签字 receipt 与 signer；不能同时宣称三项全保 |
| AJ | 339 / 3 | 估算校准而非只奖准时 | 复杂度误判：记录可学习 estimate error | 外部阻塞：从 normalized actual 中扣除 | 明显 padding：按证据记缓冲，不把“提前”直接当高绩效 | estimated/actual/normalized、error 与 reason |
| AJ | 340 / 4 | 在制品上限（WIP） | 正常 WIP 槽；同时预留全量当期 capacity | 具名 owner 签署 WIP 例外；仍需足额 capacity | 隐藏超限；仍占容量并产生可见 hidden-WIP penalty | active、WIP used/limit、reserved capacity、exception owner 或隐藏债 |
| AJ | 342 / 4 | 阻塞时间归因 | 已及时升级：阻塞 owner 承担协作责任 | 未升级：执行者与阻塞者共享责任 | 外部不可控阻塞：保留证据，免低产出罚但不免协作复盘 | blocker owner、起始/升级日、executor penalty、shared responsibility |
| AJ | 337 / 5 | 需求变更税 | 延期并支付额外 capacity tax | 增配/等量删减，仍把变更税显式入账 | 一次 disaster waiver，不扣容量但生成 policy debt；不可复用 | change route、tax、approver、capacity 余额、waiver-used 与政策债 |
| AJ | 341 / 5 | 跨周期未完工债 | 释放当期 10 并向下期结转 10 | 释放当期 10、验收 5、向下期结转 5 | 取消并释放当期 10，不占下期容量 | transfer/accepted hours、当期释放、下期占用、WIP 关闭与取消状态 |
| AJ | 343 / 6 | 提出/执行/验收三方签收 | 三角色 receipt 后 accepted | 三角色 receipt 后 conditional | 三角色 receipt 后 rejected | proposer/executor/acceptor 三个角色签收位与 outcome；真实人物互异性留给后续输入接口验证 |
| AJ | 344 / 7 | 上线/采用/价值三阶段结算 | 上线/采用/价值 6000/2500/1500 | 三阶段 3000/3000/4000 | 三阶段 1000/2000/7000 | 三段 share 合计 10000，remaining 归零；不重复领奖 |

## 事件链接口

每个 domain 至少公开一个“在受评人 scope 执行、管理者为 `ROOT`”的 launch effect：

- AA launch 调用 `zg361_case_aa_open_effect`；
- AG launch 调用 `zg361_case_ag_open_effect`；
- AJ launch 调用 `zg361_case_aj_open_effect`。

open 成功后：

- 玩家管理者保存该 domain 的 subject named scope，并进入按表中 ID 顺序排列的 character event 链；每个事件恰有 A/B/C 三个业务选项。
- 每个选项只调用对应 ID 的 route wrapper。wrapper 若 `applied = 1` 才继续下一个事件；typed RED、stale 或 receipt no-op 均安全终止当前链，不伪造后续成功。
- 获授权 AI 管理者不弹窗，使用完全相同的 wrapper、五元 guard、consumer 和 stage barrier，确定性执行默认 A 路线；不能另写一条跳过权限/资源账的 AI 捷径。
- 受评人的 self-read effect 只执行 consumer/read projection；它不能打开或推进案卷。

本包不新增顶层 GUI 按钮，也不直接接考核榜。未来 GUI 或 MCP 只能调用上述公开入口/读取可见字段，不能复制一套业务逻辑。

## 本地化合同

所有事件 title、desc 与 A/B/C option 均必须有静态 key。typed RED 和 consumer 当前是变量查询合同，尚无玩家可见的错误/摘要文本；接 GUI 或 MCP 时必须另补对应 key，不能假称已经本地化。

- `simp_chinese`：原创简体中文。
- `english`：原创英文，不是机器逐字占位。
- `french`、`german`、`japanese`、`korean`、`polish`、`russian`、`spanish`：本开发阶段逐 key 使用英文结构占位，以保证九语加载结构完整。
- 九种语言 key 集合必须完全相等；YML 有正确语言 header 与 UTF-8 BOM。
- 七语英文占位不得称作“已翻译”或“已完成发布国际化”。只有用户明确进入发布流程后，才按发布本地化规范补译与审阅。

## 静态验收合同

独立测试至少证明：

1. 生成器 `--check` 可复现且全部产物 UTF-8 BOM；
2. ID 集合严格等于 229–241、301–311、334–344，无漏号、多号或空壳 wrapper；
3. 每 ID 有 A/B/C 三路线、共享 receipt、full guard、独立 semantic write 和独立 consumer；
4. 任一路线 receipt 存在时，另外两路线同样 no-op；
5. 所有资源预检文本位于 `record_operation` 之前，RED 后无 receipt/业务/资源副作用；
6. 三个 stage 图、barrier 与共享内核公开 `advance` effect 一致；
7. AA240、AA241、AG304、AG306、AG308、AG309、AJ335、AJ337、AJ340、AJ341、AJ344 的守恒断言存在；
8. 玩家 A/B/C 事件链和授权 AI 默认 A 路线复用同一 wrapper；
9. 管理入口要求天朝制公爵及以上，伯爵/男爵只有 subject self-consumer；
10. 九语 key parity、中文/英文原创集合、七语英文结构占位和 BOM 均通过。

这些测试只证明生成结构与静态合同，不证明 CK3 实际解析、事件作用域、存读档或 UI 呈现。

## 诚实 readiness 边界

当生成器与上述独立 L0 测试全部通过时，本包最多标记为 **`CK3 script static-ready`**。以下项目均明确未由本规格或静态测试完成：

- 没有中央 `on_action` 周期调度；AI 静默入口存在也不会因此自动定期触发；
- 没有新增 GUI，也没有考核榜接线或按钮阻塞审计；
- 没有 MCP named action/query、paused snapshot 或 fixture 对接；
- 没有 CK3 parser/error.log 加载证据；
- 没有真实角色/头衔作用域、玩家事件链、授权 AI 批处理、伯爵/男爵只读边界的实机证据；
- 没有跨存读档、跨周期、批量整局或发布 staging 证据；
- 九语中只有简体中文和英文是原创文案，其余七语仍是英文结构占位。

所以不得写 `fixture-live`、`production-live primitive`、`production-live loop` 或 `complete`。下一阶段必须经 MCP 优先的 paused 实机批量验收，保存日志、snapshot 与可复现 artifact 后，才能按证据逐级提升 readiness。
