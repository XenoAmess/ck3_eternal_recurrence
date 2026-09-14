# CK3 1.19.0.6 Steward「发展伯爵领」原生 AI 决策树

## 状态与范围

- **[static-confirmed]** 本专题冻结 `task_develop_county` 与默认
  `task_collect_taxes` 的 authored task 权重、发展目标候选过滤、任务完成后的冷却，以及发展进度的原版数据来源。
- **[unknown]** 引擎何时重新评估 `ai_will_do`、何时在多个正权重任务间抽样、无
  `ai_target_score` 时的精确随机分布和任务切换 command ABI 尚未闭合。图中均以虚线表示。
- **[static-ready; exact enumerator observer ready; live reader pending]** `query-steward-develop-county-candidates-v1` 的严格 v1 合同、native mailbox/serializer、离线 source fixture、Python service 与 MCP 查询面已经实现。DEV2 已把候选枚举收窄到 exact `CCouncilWindow` 调用点和一个默认关闭的只读 observer；生产 reader 仍因 paused-live 行 identity、最终 legality 与发展输入 ABI 未闭合而返回 `reader_not_implemented`。该返回现在是有明确 capture 入口的临时状态，不是终态。本包没有启动 CK3，也没有新增动作。
- 施工范围只覆盖和平治理中最高价值的 steward 发展分支。`task_promote_culture`、
  `task_accept_culture`、`task_convince_dejure` 仍参与完整 steward 任务池，但不在本包内假装已完成比较。
  宫廷司祭及通用 faith/doctrine 系统继续遵守 owner-deferred 边界。

## Exact-build 冻结

| 资产 | 精确值 |
|---|---|
| CK3 build | `1.19.0.6` |
| `binaries/ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| `game/common/council_tasks/00_steward_tasks.txt` SHA-256 | `B3087378E04D0CDF7B1C1BEBF97FD17E36D8684DDD157D4FB0647B1D5681FC4B` |
| `game/common/council_tasks/_council_tasks.info` SHA-256 | `CA9BC5D06ADC414ED8A28B47E4D3BDACDBB30093E94FBD33FE1A80FE518B8A2A` |
| `game/common/script_values/01_dynamic_values.txt` SHA-256 | `049303EFF8ABFDFCADCC31D27E2633A26A2E877E4E2980D4A42C53D6B76D7064` |
| `game/common/script_values/99_steward_values.txt` SHA-256 | `6A4AC7C1E575E54FBA4A3BE06F58146F753629622491FDDAE25D09C439699C3B` |

以下行号均指这组文件的 1.19.0.6 原始字节。任一文件或 EXE 变化后，结论先降回未验证，重新计算 hash 并复核定义后才能继续消费。

## 任务权重：发展与默认收税

### 默认任务 `task_collect_taxes`

`00_steward_tasks.txt:1-130` 将收税定义为 `default_task=yes`、
`general/infinite`。其 `ai_will_do` 从 `1` 开始，按 authored 顺序增加：

1. liege 的正 `ai_greed / 5`；
2. `stewardship_wealth_focus` 加 `15`；
3. `tax_man_perk` 加 `15`；
4. 公爵及以上且 gold `<100` 时加 `500`；否则，较低级别且 gold `<10` 时加 `500`；
5. `conqueror` 变量存在时再加 `500`。

因此收税始终提供正权重 fallback，而且低储备统治者会显著偏向它。这个权重是 CK3 AI 的 authored preference，不是玩家效用或财政最优证明。

### `task_develop_county`

`00_steward_tasks.txt:626-666` 的 authored 权重按顺序执行：

1. 初值 `0`；
2. steward 已在执行该任务时加 `10000`；
3. liege 有 `no_ai_increase_development` 时乘 `0`；否则，gold 达到
   `steward_increase_development_value` 时加 `300`；
4. gold `<10` 时再次乘 `0`；
5. 有效的 `vassal_directive_improve_development` 最后加 `50000`。

`01_dynamic_values.txt:2062-2066` 把发展储备阈值定义为：

```text
steward_increase_development_value = max(2 * yearly_character_income, 50)
```

顺序有实际含义：注释中的“已选就一直做”仍会被后面的冷却或破产门乘为零；有效直属封臣指令在两个乘零门之后加权，因而可以重新产生正权重。没有指令、当前也未在发展时，只有 gold 达到上述阈值才得到 `300`。

这仍不是完整 task-choice 概率。其它 steward 任务也有自己的 `ai_will_do`，而调度器的候选构造、重评 cadence 与最终抽样调用链尚未闭合。

```mermaid
flowchart TD
    S["[static] steward task pool"] --> C["[static] Collect Taxes<br/>weight starts at 1"]
    S --> D0["[static] Develop County<br/>weight starts at 0"]
    D0 --> A{"[static] already active?"}
    A -->|yes| A1["+10000"]
    A -->|no| A2["+0"]
    A1 --> CD{"[static] no_ai_increase_development?"}
    A2 --> CD
    CD -->|yes| Z1["multiply 0"]
    CD -->|no| G{"[static] gold >= max(2 x yearly income, 50)?"}
    G -->|yes| W["+300"]
    G -->|no| W0["+0"]
    Z1 --> B{"[static] gold < 10?"}
    W --> B
    W0 --> B
    B -->|yes| Z2["multiply 0"]
    B -->|no| V{"[static] valid improve-development directive?"}
    Z2 --> V
    V -->|yes| P["+50000"]
    V -->|no| F["final authored weight"]
    P --> F
    C -. "[unknown] complete task pool and scheduler cadence" .-> R["engine task selection"]
    F -. "[unknown] complete task pool and scheduler cadence" .-> R
```

## 发展目标候选树

`task_develop_county` 是 `county/value` task；玩家可见范围是 `realm`，而 AI 专用枚举范围明确收窄为 `ai_county_target=domain`（`00_steward_tasks.txt:133-142`）。

`potential_county` 位于 `00_steward_tasks.txt:406-451`。所有候选必须：

- 不是 landless-type title；
- `development_level < max_development_level`；
- 对有首都的 AI liege，同时满足下列两组条件：
  - 是 liege 的首都伯爵领，或由 liege 亲自持有且 capital province terrain 为
    `oasis`、`farmlands`、`floodplains` 之一；
    - 有效的 improve-development 指令、县与 liege 同文化、两文化接受度至少 `50`、liege 低于公爵级，或 liege 带 de-escalation agenda 且县为异文化，五者至少满足一项。

AI liege 没有首都时，`trigger_if` 不进入这两组附加限制；这不代表一定有可选目标，前面的 domain 枚举、非 landless 和发展上限条件仍然生效。

该 task block **没有** `ai_target_score`。`_council_tasks.info:5-7` 明确：未提供该字段时目标选择完全随机；提供时才对正分目标做 weighted random。因此 exact source 只能证明引擎从合法 domain 候选中随机选择，不能宣称偏爱最低发展、首都、最高回报或某种稳定顺序，也不能从一次 active target 反推排序。

```mermaid
flowchart TD
    T["[static] AI domain counties"] --> L{"[static] non-landless title?"}
    L -->|no| X["reject"]
    L -->|yes| M{"[static] development < max?"}
    M -->|no| X
    M -->|yes| H{"[static] capital county<br/>or personally held preferred terrain?"}
    H -->|no| X
    H -->|yes| U{"[static] directive / same culture / acceptance >= 50<br/>or rank below duchy / de-escalation exception?"}
    U -->|no| X
    U -->|yes| K["valid candidate"]
    K -. "[unknown] no ai_target_score:<br/>exact random distribution not documented" .-> Q["selected county"]
    Q --> AC["ActiveCouncilTask target ProvinceID"]
```

## 进度、完成与冷却

原版把展示进度与实际县发展过程连接起来，而不是单独积累一份 council 计时器：

- `task_current_value` 读取目标县 `development_towards_level_increase`，最大值是 `100`；
- `full_progress` 读取目标县完整 `development_rate`；
- `99_steward_values.txt:164-171` 的基础贡献是
  `0.1 + 0.175 * councillor.stewardship`，随后再叠加关系、perk、dynasty/house、tribal、当前发展惩罚与县发展倍率；
- `00_steward_tasks.txt:453-483` 通过县 modifier 把相应贡献施加到真实
  `development_growth`，所以只读 current/max 不能替代完整 rate；
- AI 每次完成该 county task 都在 `on_finish_task_county` 进入默认任务；
- 月度检测到发展等级实际上升后，通常设置 `no_ai_increase_development` 五年。如果 liege 为国王及以上、realm 内存在与其文化接受度 `<52` 的县，并且未选 `stewardship_domain_focus`，冷却延长为十五年（`00_steward_tasks.txt:520-563`）。

完成回默认、月度 flag 写入和下一次调度器重评的精确先后调用链仍是 **[unknown]**。本文只记录各 authored effect，不把其文本顺序冒充运行时 cadence。

## 当前 observation 能回答什么

现有 [内阁观测专题](council-and-development.md) 已能在支持的标准 landed、非 nomadic 范围同帧回答：

- `councillor_steward` 是否 occupied；
- 当前 stable task key 是否为 `task_develop_county`；
- 当前 target ProvinceID、current/max raw progress 与 frozen；
- 玩家当前 gold、月收入、主头衔 tier 和 capital ProvinceID（来自 campaign-root 其它字段）。

它还不能回答“现在能否合法开始发展”“有哪些合法县”“每县完整发展速度/ETA”“选择后会否改善玩家亲自持有的经济中心”。尤其不能用当前 `player_monthly_gold_income * 12` 代替原版 `yearly_character_income` evaluator，也不能用当前 active target 冒充完整候选集合。

## 下一条最小只读 bridge：优先级

### P0：`query-steward-develop-county-candidates-v1`

先做一个独立、有界、只读 query；不要把全 realm 县明细塞回每回合必读的 campaign-root。最小字段为：

| 字段 | 必要性 |
|---|---|
| player/date/snapshot/native revision 与 steward full CharacterID | 绑定同一 paused frame，复用现有 council owner/incumbent 校验 |
| `task_key=task_develop_county`、`shown`、`valid`、typed failure reason | 消费原生最终 task legality，避免 Python 重写 natural-disaster/ministry 等触发器 |
| 原版最终 `steward_increase_development_value` raw 与当前 gold raw | 精确回答储备门；不得由月收入近似重建 |
| 当前 `no_ai_increase_development`、有效 improve-development directive 的最终布尔结果 | 解释 stock AI authored weight；不暴露任意变量读取 |
| 每个候选的 full county-title ID、capital ProvinceID、holder CharacterID、`is_player_capital`、`directly_held_by_player` | 形成可执行目标 identity，并区分自有长期收益 |
| 每个候选的 final native legality、development level、towards-next-level、完整 monthly rate、max level | 形成最低发展 ROI/ETA 输入；非法行只保留 typed reason，不发布伪值 |
| terrain stable key、`same_culture_as_player`、final cultural-acceptance-threshold result | 解释 exact potential filter；文化只保留稳定 identity/最终阈值结果 |
| `target_selection_mode="engine_random_unscored"` | 明示 stock task 没有 `ai_target_score`，防止下游虚构原版排序 |

查询只枚举当前 task 的 native legal domain candidates，并用 full-generation title/province/character identity round-trip 与双采样拒绝漂移。`faith`、doctrine、tenet 和通用 culture tree 不进入 schema；这里只读取 source 已证明直接参与该 task 过滤的文化相等/接受度最终结果。

#### P0 合同实现边界（G2-M4-DEV1）

公共 capability 为 `game.command.query-steward-develop-county-candidates-v1`，固定 step 为
`query-steward-develop-county-candidates-v1`；MCP 工具
`ck3_query_steward_develop_county_candidates_v1(expected_revision)` 只在 paused snapshot 上执行，并把 public/native revision、日期与 snapshot identity 绑定到同一查询。

v1 payload 固定 `contract_stage=exact_build_enumerator_observer_pending_live_layout_closure`。离线 fixture 可以验证完整 available 形状、full-generation identity 往返、重复 ID 拒绝、native-legal-only 候选、双采样与前后 frame 稳定性；这一 fixture 不进入生产模块读取。生产 exact-build 路径在 paused-live 行 identity 尚未闭合时返回 `status=unavailable`、`unavailable_reason=reader_not_implemented`、`readiness=false`、空候选和空观测值，不能把现有 active task、observer 原始指针或 Python 重写的 trigger 当成候选结果。

候选顺序原样保留 native 枚举顺序，但 v1 不把顺序解释为分数或偏好；`target_selection_mode=engine_random_unscored` 继续是唯一允许的原版目标选择语义。当前唯一后续逆向入口记录为
`paused_live_develop_county_enumerator_capture_then_row_identity_and_final_legality`。只有原始枚举行的 county identity、最终 task/county legality、rate evaluator 和 identity round-trip 在真实 paused frame 共同闭合后，才可把 `reader_mode` 从 `native_enumerator_observer_pending_live_reader` 提升并开展有界 live 验收。

#### Exact 枚举器与唯一 capture seam（G2-M4-DEV2）

对 SHA 已冻结的 `ck3.exe` 做有界反汇编与直接调用交叉引用后，`RVA 0x105B6A0` 只有两个 direct-call xref：

- `0x10545EA` 是只需要“是否至少有一个位置”的 validity probe，调用前把栈上 bool 设为 `true`，返回后只检查输出 count 是否非零；
- `0x105629C` 是 `CCouncilWindow` 的 county/value task refresh 路径，调用前把 bool 设为 `false`，把输出绑定到 `RDI+0x100`，因而保留完整枚举行。这个调用点是下一轮 live capture 的唯一入口。

`0x105B6A0` 的静态数据流证明输出 vector 为 `data qword / capacity int32 / count int32`，每行宽 `0x18`，三项 qword 依次为 raw candidate pointer、传入 task-type pointer、query-owner pointer。它还证明 task type 从 `R8` 传入、scope 从 `R9` 传入。静态证据尚不能把第一项 raw pointer 命名成 county title、province 或 GUI wrapper，也不能把“出现在 vector 中”直接升级成公共 `native_legal=true`；这些语义必须由一次 paused exact-build capture 配合 full-generation round-trip 闭合。

DEV2 新增 `steward_develop_county_enumerator_observer_v1`：

- 只在 private build 的 `XAR_CK3_ENABLE_STEWARD_DEVELOP_COUNTY_ENUMERATOR_OBSERVER_V1` 显式开启，默认关闭且不广告公共 capability；
- 只在 primary thread 尚未恢复时安装，逐字节核验 `0x1056289..0x10562A0` 的 24-byte exact anchor；
- trampoline 原样执行被覆盖的 scope/vector 写入和唯一 native call，调用后只复制 raw vector 元数据及最多 32 个 `0x18` 行，不主动调用枚举器、不提交命令、不改游戏状态；
- 用已复用的 `CCouncilTaskType+0x18` key 布局只保留 `task_develop_county`，并分别计数 key 读取失败、vector 读取失败和显式截断；
- 安装/卸载具备 exact identity 和原字节回滚，private heartbeat 暴露 raw capture，公共 steward v1 字段集合与 readiness 均未改变。

ABI 与证据边界见 `native_bridge/research/steward_develop_county_enumerator_observer_v1_abi.json`。本轮没有运行 CK3，因此 observer 的 `static-ready` 只说明 anchor、trampoline、过滤、行复制和回滚经过离线验证；它不是 live row，也不允许把公共 P0 标为 production-live。

### P1：只读 task-pool comparison

在 P0 使“发展哪里”可决策后，再发布同一 steward 的完整 shown/valid task rows 与 final native
`ai_will_do` raw。它用于解释原版行为和离线校准，不应直接当玩家 utility。只有收税与发展两行时不得标记完整，因为 promote/accept/de-jure 任务仍可能参与候选池。

### P2：动作与后置状态

动作包必须复用 P0 返回的同帧 candidate identity，native 端重新执行 task/county legality，再提交一次
`task_develop_county` 切换。ACK 只表示提交；后置查询至少要看到同一 steward 的 active task key、目标 ProvinceID 和新 progress binding，才算 applied。任务切换 command ABI 和冷却/取消成本在这一步施工前继续保持 unknown。

## 对 G2-M4 counter-policy 的直接结论

1. 原版 AI 只在至少 `max(2 * yearly income, 50)` 的储备门后常规启动发展，而低储备时默认收税权重急升；G2 的第一版玩家策略应保留独立应急储备门。
2. 原版目标在 filtered domain 内没有 ROI score。玩家策略没有理由复制随机选择；P0 到位后可先用确定性规则比较“玩家亲持、首都优先、达到下一级所需月数”，并把未纳入的建筑槽、control、税收和风险记为质量差距。
3. 已在发展时的 `+10000` 与完成后的五/十五年冷却说明原版倾向连续完成一次增量、随后轮换；在缺少完整 rate 与任务后置前，planner 不应频繁重派 steward。
4. 当前 bridge 只证明正在发生的任务，不能支撑新动作。M4 的下一施工入口是 P0 候选查询，不是继续用 `life-advance` 等待随机命中，也不是先写猜测性的选县策略。

## 证据边界

- **[static-confirmed]** task 定义、script value、候选过滤、authored weight 与 authored cooldown 来自上表 exact-build 文件。
- **[inference]** “发展一次后轮换”是 completed-task fallback、cooldown 与权重组合的策略解释；scheduler cadence 未闭合，因此不能当 exact 运行时保证。
- **[unknown]** 完整 task pool 最终抽样、无 target score 的具体 RNG 分布、任务切换 command、取消/重派成本与同帧后置 ABI。
- **[live pending]** G2-M4-DEV1 没有 paused snapshot；available 只由隔离 source fixture 证明，生产 reader 明确 typed-unavailable，因此不改变 `council-and-development.md` 已有 production-live 状态，也不把 P0 或 M4 标为 complete。

#### DEV3 / 旧轮次 R682：live harness RED，未进入 observer ABI 验收

DEV3 先证明旧轮次 R681 的 campaign-root checkpoint 不在标准 landed council 范围内，无法在“只加载、零 UI”边界触发 `CCouncilWindow` 的 county/value refresh，因此以 no-launch RED 收口。随后 DEV3B 改用已冻结的 R639 标准统治者存档：角色 `29829`，源存档 SHA-256 为 `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63`。

旧轮次 R682 在 fixed commit `7429d84a33359eabde8cbd69bbcc474782c1b507` 上直接以 `-loadsave=dev3b_r639` 启动，CK3 PID 为 `163928`，creation time 为 `20260914160709.405754+480`。日志在 `16:10:33` 进入 `Load Save` idler，并在 `16:10:37` 进入 game-state setup。live harness 随后看到首个 `map_ready=true`、`paused=true` 的语义帧，但该帧的 `played_character.character_id` 尚未发布；`NativeHeadlessGameplayDriver` 因而也尚未绑定 `episode_character_id`。旧 harness 仅凭 map-ready 与 paused 就放行到身份断言，得到 `episode_character_id=null` 并触发 RED。

该 RED 的边界如下：

- 它是 **harness readiness RED**，不是 CK3 启动崩溃。停止前受管 Job 仍有一个活动 CK3 进程，`stop_tracked(require_running=True)` 无合同错误；exit code `1` 来自随后受管终止。
- 没有发出任何 UI 输入，没有推进日期，没有选择或提交 council task；源存档与一次性副本的哈希在停止后均未改变。
- harness 尚未读取并验证 private observer heartbeat，也没有触发 `0x105629C`；因此 observer 安装状态、row ABI、候选 identity 和 native legality 均不能从本轮判为成功或失败，继续保持 `unknown`。
- 清理通过：CK3 Job 归零、watchdog absent、控制文件清除，CK3 / injector / watchdog 三路均无残留。

冻结 artifact 位于 `Z:\ck3_mod_rewrite_process_assets\g2-m4-r682-devcounty-observer-r639-7429d84`；artifact manifest SHA-256 为 `9FB6C13F6352BEC9A568D4DFBF60508DFCA727DAD0FFD9D66308AE8A41FC3470`。该目录中的 `red-analysis.json`、`round-metadata.json` 和 `postflight-three-route-zero.json` 分别保存分类、轮次身份与清理证明。不得把本轮 RED 写成 observer ABI RED，也不得据此生成 raw row 映射。

#### DEV4：期望角色绑定成为可复用 live readiness gate

`native_auto_run._wait_for_readiness(...)` 现在接受可选的 `expected_character_id`。已知存档身份且随后会发出 UI 或 gameplay 输入的 live runner 必须传入该值。放行条件同时包括：

1. 原有 native transport、exact-build、mailbox、`map_ready`、`paused` 与 active episode 条件全部满足；
2. `played_character.character_id` 是有效整数且存活；
3. projected `episode_character_id` 与 played character 相等；
4. 两个 ID 都等于调用者冻结的期望角色；
5. bridge/session/date/run binding 以及 played/episode 两个 ID 在指定 `stable_seconds` 内不变。

已存在的双角色 campaign-root live runner 会把 `first_character_id` 传给该 gate，因此在第一幕查询或角色切换前不会再接受“地图已就绪、角色尚未发布”的过早帧。聚焦回归同时覆盖：旧轮次 R682 的空身份帧会继续等待、错误但稳定的其他角色会超时 RED、非法期望 ID 会在启动动作前拒绝；normal 与 `python -O` 模式均通过。

这次修复只改变 live harness 的放行条件，没有修改 native observer、public steward v1、MCP schema 或 action。下一次另行授权的 live 轮次仍应使用同一冻结 R639 存档；只有在角色 `29829` 的 played/episode 双绑定稳定后，才允许执行一次 Council → steward → `task_develop_county` 目标刷新。

#### DEV6 / 旧轮次 R683：expected-character readiness live GREEN

旧轮次 R683 对 DEV4 的期望角色稳定门禁给出了实机证明：放行帧处于 `paused=true`，`played_character.character_id=29829` 且 projected `episode_character_id=29829`，两个身份在稳定窗内共同绑定后 harness 才进入后续观测。旧轮次 R682 仅因 `map_ready` 与 paused 便过早放行、随后看到空 `episode_character_id` 的故障未再复现；因此 DEV4 readiness gate 由聚焦回归提升为 **production-live GREEN**。

本轮的下一个结果要与 readiness 分开解释：当次启用的是 `g2_domain_construction_candidate_observer_v1`，不是 steward develop-county observer。它在有界的 60 秒 paused 观测窗内保持 installed，failure flags、read failures 和 accepted captures 均为零，但 producer call count 也为零，最终状态为 `no_producer_return_observed`。这是该 construction producer 调用点没有在当前输入边界内命中的独立 **NO-GO**，不是 readiness RED，也不是 observer RED；它没有提供 steward 候选行、row ABI 或 native legality 映射证据，因此不改变本专题 P0 reader 的尚未闭合边界。

冻结证据位于 `Z:\ck3_mod_rewrite_process_assets\g2-m4-r683-construction-observer-live-50b69df`，最终自包含的 `artifact-manifest.json` SHA-256 为 `C3D2301E647BBDEF1A7CFB33CF2795EA9905BFBC98671371DD2C5D66055DFABC`。旧值 `177F4F3EAB41570F005132E294ADEEBBEEA6DD7E1BF704CF004DB0F00F846DF4` 是复制四个 exact candidate binaries 之前的历史 seal，已由最终 manifest 的 `previous_manifest_sha256` 保留。本轮 UI 输入为零、游戏日期未推进、源存档未改变，结束后清理证明通过。
