# 圣地等级、效果条件与数量上限（1.20.0.4）

本文区分实际修正生产、界面说明与读取时刻。机器 `4-8e1c2f1861`；研究日期 `2026-10-18`；仓库来源 `d1c2bc7eb568a4eab3f55c065adb645a9dbace6f`；实际 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。复用当日 Root 预检与既有精确映像缓存，没有启动游戏、调用原生函数、编译或修改主工作树。完整来源见[条件合同](evidence/holy-site-grade-effects-limits12004/effect-condition-contract-a03.json)。

## “必须列为主要圣地”只适用于哪些效果

**该 Faith 的全体角色固定、缩放修正，需要该 Faith 将此地列为主要圣地，并且伯爵领持有者的当前 Faith 与它相同。地方修正和特殊参数各有独立条件，不能一并套上主要门槛。** “主要”是每个 Faith 自己的关联等级；同一个地点可对甲是主要、对乙是普通。

| 效果或条件 | 该 Faith 必须列为主要 | 其他已核实际条件 | 原生生产/消费链 |
|---|---|---|---|
| `faith_character_modifier` 固定 | 是 | Site 属于该 Faith；伯爵领持有者当前 Faith 相同；定义块有条目。此生产段不额外检查 Site 缓存 Active | `29CC520 → 24FB270 → Rite+20/+2C`，角色 `291C0B0 → 291F080 → 2438830` |
| `faith_character_modifier_scaled` 缩放 | 是 | 同上；按原版脚本值求倍率。此生产段不额外检查 Active | 同一生产器，类型 `+3D8`，原 HolySite scope 求值 |
| `county_holder_character_modifier` 地方角色固定 | 否 | 缓存 Active；接收角色的 Faith 与地点关联；由两族实际头衔输入限定接收者，不能泛化为所有同 Faith 角色 | `291C0B0 → 291E3A0`，类型 `+218`，实际聚合追加 |
| `county_modifier_scaled` 地方伯爵领修正 | 否 | 缓存 Active；伯爵领持有者 Faith 控制门；类型 `+3F0`；伯爵领模型接收者绑定仍有只读接口缺口 | `2864D93 → 2864E40 → receiver+268 → receiver+8` |
| `has_holy_site_parameter` | 否 | 以 barony 为输入解析 county，遍历该伯爵领地点；缓存 Active；类型参数列表包含指定 token。它没有请求 Faith 参数，也没有伯爵领持有者同 Faith 门 | 注册 `591560`，实际布尔实现 `2B29F00` |
| `controls_holy_site_with_parameter` | 否 | 遍历请求 Faith 的**全部**关联地点；缓存 Active；参数存在；伯爵领持有者当前 Faith 与请求 Faith 相同 | 注册 `591600`，实际布尔实现 `2B2A2F0` |
| `is_holy_site_of`（其他脚本常用） | 否 | 请求 Faith 全部关联地点与该 county 地点列表有交集；该谓词自身不检查 Active 或伯爵领持有者持有者 Faith | 注册 `5914C0`，实际布尔实现 `2B29C70` |

上表 Active 指地点 `+18` 的缓存布尔量。伯爵领持有者控制门 `2441F30` 的实际路径是 **Site 的 barony → county → county holder → holder 当前 Rite → Faith full ID**，不是最高领主、地图颜色或伯爵领民众信仰。固定地方角色路径包含两类头衔来源，不能把其名称直接改写成“所有地方角色”或无条件的“持有该伯爵领者”。

全 Faith 的真实生产器 `24FB270` 遍历 Faith 的全部地点（`+890`），再查该 Faith 的主要名单（`+8A8`）及伯爵领持有者同 Faith 门；固定块取类型 `+58`，缩放块取 `+3D8`。两类之后进入持续 Rite 修正列表，再由接收角色的当前 Rite 加入总聚合。若地点对 Faith 51 是主要、伯爵领持有者却是 Faith 50，Faith 51 在这道实际生产门被排除。单凭“同一地点还关联另一 Faith”或“另一 Faith 认可同一圣物”不能推出另一 Faith 获得全 Faith 修正。

**无 Active 检查不等于一切空圣地随时都已发放数值。** 这是已核生产段的条件；实际 Rite 列表何时重建、角色聚合何时刷新仍须按运行时证据判断。暂停时等级读回已变，不能据此宣称净属性已经变。原 R0009/R0010 的等级、当前重评与聚合观测还显示了缓存差异；不能把当前重评结果套到过去已生产的聚合。

## 缩放倍率、参数和其他效果的反例

原版 `holy_site_total_artifact_rarity` 不是每次都现场重算圣物价值。它引用 `root.total_active_artifact_rarity_sum`；实际 evaluator `2B0C740` 验证 Site scope/full ID 后直接读 Site `+1C` 的缓存整数。它不调用当前重评器 `265A3F0`。因此必须分别保存缓存 Active/rarity、当前重评以及实际聚合，不能用某个 `current_evaluation=0` 推翻另一个缓存值，也不能把 `capture_epoch` 当缓存生成时间。

当前安装的 336 个 HolySiteType 定义只使用上表四种 modifier 块；没有据旧知识发明额外的固定县块或地方角色缩放块。其中六个定义有参数，参数是裸 token 列表，判断**存在与否**，不是 `yes/no` 数值：

| 地点 | 参数 |
|---|---|
| Jerusalem | `jerusalem_conversion_bonus` |
| Kerala | `kerala_conversion_bonus` |
| Iona | `iona_conversion_bonus` |
| Visoki | `visoki_conversion_resistance_bonus` |
| Cordoba | `cordoba_conversion_bonus` |
| Wadi el-Milk | `wadi_el_milk_conversion_resistance_bonus` |

已完整枚举安装目录的相关脚本文本。实际业务使用位于宫廷司祭传教数值：`00_court_chaplain_tasks.txt:453 → court_chaplain_conversion_contextual_bonuses`，后者的参数分支再调用具体参数数值 helper。例如 Jerusalem/Kerala/Cordoba 的传教分支使用 `controls_holy_site_with_parameter` 与固定 barony 的 `is_holy_site_of`，均未要求主要；因此“普通圣地不能提供任何特殊效果”是错误的。完整脚本仍要求自己的地理、关联及任务 scope 条件；Iona 另有地理条件，两个 resistance 分支的外层伯爵领民众 Faith 与内层司祭 Faith 条件不同，不能抽去这些条件直接承诺抗性已经生效。

其他原版效果也需逐消费者判断。例如 `00_special_buildings.txt:52–73` 的大教堂建造/启用条件使用 `barony.is_holy_site_of = scope:holder.faith`，还保留部落/革新等自己的建造条件。这个地点关联谓词没有主要或 Active 门槛；建筑修正属于建筑系统，不能算成 HolySiteType 四块之一。这里只证明该脚本门的范围，没有新建造或启用实机验收。

反过来，**四类修正之外也存在明确区分普通/主要的脚本，不能说“主要只影响全 Faith 修正”。** 对完整原版 `common/events/history` 文本中的 eminent 迭代器、谓词及 `is_eminent` 的命中逐类核对后，需额外区分：

| 其他消费者 | 实际等级条件与范围 |
|---|---|
| 朝圣虔诚结算 `give_piety_reward_effect` | `00_pilgrimage_effects.txt:609–620` 对当前 Faith 在活动目的县的普通地点乘 `0.5`；没有把这一段改写成 HolySiteType modifier，也不把活动、意图等其他倍率省掉 |
| 旅行兴趣点到访 | `travel_point_of_interest_types.txt:465–519` 普通与主要分支分别使用 minor/普通 piety 值；特定 Christian Church phase 参数还分开给学识/学者经验。该分支自身未加缓存 Active 或伯爵领持有者同 Faith 门 |
| 建立属灵教宗费用 | `02_religion_values.txt:4139–4152,4170–4183` 若没有本人控制、伯爵领持有者 Faith 相同的该 Faith 主要地点，相关 piety/gold 费用乘 `create_hof_no_eminent_holy_site_cost_mult=1.5`。只针对该属灵分支；不能泛化给世俗教宗或所有建立条件 |
| 初始圣物播种事件 | `historical_artifacts.0050` 对主要/普通地点分派不同创建 helper，并检查伯爵领持有者 Faith；第二轮 tolerated 主要地点又有自己的关注人数、空库存和敌对度条件。这是初始化事件，晋升不表示重跑该播种或立刻赠送圣物 |
| 朝圣目的地说明 | `pilgrimage.txt:424–433` 因主要关系添加描述；此处本身不是修正发放或奖励代码 |

这些是所枚举脚本中的明确等级分支，另有圣地管理决议的资格、AI 候选和选择逻辑。脚本条件名不应倒推所有编译原生路径；本轮没有声称穷尽引擎中一切用途。规划器应按实际活动或决议消费者读取，不能只保留一个通用“圣地有效”布尔量。

界面效果描述 `2659880` 则是另一条链：缓存 Active 为 false 时整个说明为空；为 true 时显示地方效果，再按请求 Faith 是否主要追加主要说明。它不等同于上表实际伯爵领持有者控制门，所以描述中的列项不是该 Faith 已经到账的证明。

## 当前原版与 DLC 的 9/3 到底是什么

**本次实际安装的全部原版与已安装 DLC 定义，均使用总数最多 9、主要最多 3；9 已包含最多 3 个主要，不是 9+3。** 这是 Religion 定义的规则上限，不是 Faith 的任意修正属性，也不是所有模型集合永远不能越过的硬不变量。

原版 `00_defines.txt:920–926` 给出默认总数/主要上限 9/3、两种下限均为 1；Religion 格式允许四项分别覆盖。已穷尽全部 49 个实际顶层 Religion 定义，四项覆盖全部缺省。其实际装载器也已闭合：`32838C0` constructor 把四个 int32 初始化为 `-1`；由 vbtable/adjustor 绑定的 `3283FD0..3284156` finalizer **只在字段仍为 -1 时** 填入 NReligion 默认值，显式覆盖会保留。

当前 Faith `+8C` 存 Religion full ID；解析 Religion 后，其 `+20` 指向定义。四项位于定义 `+9E8/+9EC/+9F0/+9F4`，依次是总数下限/上限、主要下限/上限。实际 script value evaluator `2B2B540..2B2B6FA` 仅读这些字段，没有 doctrine、tradition、government、modifier 或 DLC 动态增容回调。全安装脚本文本也没有额外容量覆盖。政体/教义仍可改变管理资格、对象、费用或距离等条件；例如神权管理回退不是增加上限。

| 当前数量/规则 | 本版已核情况 |
|---|---|
| authored 初始名单 | 共 103 个实际顶层 Faith 定义（不是文件数、匹配数或当前存档 Faith 数），全部在 `00_faith_types.txt`，先收集全部定义再核名单；无字段遗漏或重复定义 |
| 初始总数/主要数量分布 | 4/2×1、4/3×1、5/2×72、5/3×21、7/3×5、8/3×3；总数为普通与主要两名单之和，本语料无交叠或重复；没有 authored 初始超 9/3 |
| Adopt | 决议 `50_holy_site_decisions.txt:499` 要当前总数 `< Religion.holy_sites_max`；`allow_adopt_any_holy_site` 只放宽对象，不绕容量；AI 另外为玩家保留一格不是把上限改为 8 |
| Create | 实际 `CanCreate 29A5AD0..29A646B` 的 `29A5C61` 直接比较当前总数与定义上限，满额不能通过普通容量分支；其他材料/权限/冷却条件仍需独立满足 |
| Promote / Demote / Abandon | 晋升要主要数 `< 主要上限`；降级要主要数 `> 主要下限`；退出要总数 `> 总数下限`；还要满足本站等级、控制、管理和其他原版条件 |
| 强制/脚本/外部存档 | 底层 eminent setter `2441990` 在原会员存在且未列为主要时追加主要数组，不先比较 Religion 上限。故 3 不是该 setter 的硬不变量；本轮没有穷尽所有低层 add/dynamic Faith 路径，也没有证明任意强制脚本都能越限 |

资源范围为此机安装的 game：51,498 个文件的元数据；全部 txt/gui/info/asset/dlc 共 7,536 文件、222,428,209B 的源清点，含所有已安装 DLC 的共用 `common/events/history` 脚本。DLC 子目录 235 个文件、30 个描述；没有未展开 zip/pak/pck/bundle/archive/7z/rar 包。没有观察购买资格或当前存档启用哪些 DLC。完整定义、所有命中与文件 SHA 可重放，不只搜索 `dlc` 子目录。Doctrine 实际目录为 `doctrine_types/category_types/group_types`，tenet 为 `tenet_types`，均在完整清单；旧类别摘要使用过时目录前缀得到 0，已单独勘误，不能当作没有教义或漏扫的证明。

因此可以对本版本玩家说“原版通常按总额 9、其中主要最多 3 操作”，同时保留具体 Religion 可配置、初始名单数量不同、动态/改造 Faith 和存档实读不同的边界。新模组或另一版本不能沿用此穷尽结论。完整上限合同见 [limits-source-contract.json](evidence/holy-site-grade-effects-limits12004/limits-source-contract.json)。

## 智能体读取和决策合同

现有 `ck3_query_player_holy_site_v1(expected_revision, holy_site_id=None)` 可读当前 Faith 的地点名单、关联 Faith 与每 Faith 的主要关系。`ck3_query_player_holy_site_relic_context_v1(expected_revision, holy_site_id)` 还读共同库存、全 Faith 认可矩阵、缓存 Active/rarity、当前重评、派生伯爵领持有者以及固定 PC 的角色总聚合；`ck3_query_player_holy_site_relic_action_context_v1(expected_revision, holy_site_id, artifact_id)` 读当前原版候选、实际两物主人与认可矩阵。这两个 context 在现源码中由实际 owner 附带观察域，不存在可猜用的额外可选观察参数。

固定 PC 观察以真实类型 `+58`/`+218` 内的 u16 key 为来源，仅读当前玩家与派生伯爵领持有者，`property_name=null`；`definition_raw_q64` 是定义值，`aggregate_raw_q64` 是该角色所有来源的总聚合，不是此地点贡献。无可用 owner/模型时保持 unavailable/null。缩放 PC 的实际单独贡献、完整伯爵领模型修正、六种参数的实时存在/控制布尔量、缓存生成时间仍未由这些口给出。静态脚本算式可以给预期，不能替代这些实际字段。

最小后续能力是给现有 HolySite snapshot **增添只读 `limits_current`**，无需开放任意 Faith/角色入口或新增动作：

1. 沿已绑定当前玩家 Faith，读其 Religion full ID；解析 Religion storage 时核完整 generation ID，取 Religion `+20` 的定义。
2. 复制四个 int32：`holy_sites_min/max` 与 `eminent_holy_sites_min/max`，同时读当前全部/主要名单及数量；同 owner/frame 前后重读身份、数组与定义值。允许报告真实超限状态，不能因已超限就删除它或伪成正常数。
3. 返回 Religion/当前 Faith ID、四限值、当前两数量、来源与 unavailable 原因；不走引擎默认对象，不把缺字段替换成 9/3。计数小于上限只是必要条件，原版决议的全部条件和最终 `CanConfirm` 仍是动作资格。
4. 局部实施点为 `ck3_12004_holy_site_snapshot.hpp/.cpp`、`_json.cpp` 与现 Python transport/normalizer；继续既有 religion owner 只读 mailbox/旗标，新增少量精确 fixture 验当前 Religion、定义、超限、身份漂移及缺失值，不重跑旧完整矩阵。此处是施工方案，本次没有实现、编译或实机通过。

规划时分别保存 `associated`、`eminent`、伯爵领持有者当前 Faith、缓存状态、当前重评、原版条件与实际聚合；每一项都带自己的 available/reason。对用户说“这里提供了某效果”前，还要区分定义、满足生产条件、缓存已刷新以及独立实测变化四层。ACK 只表示提交，既不是等级变化，也不是修正到账。

## 证据范围

本次是精确构建的静态 producer/caller/consumer 研究与穷尽定义清点。研究计划检查只核结构、文件与 SHA，不自动证明语义，也不授游戏运行；offline-only 没有 live window，`--for-observation` 的拒绝保留为边界。`open_kaishek` 的脚本 parser/有限运行模型不覆盖本次原生内存布局和实际聚合路径，因此没有用旧脚本样本制造通过。

初次参数 census 错把裸 token 列表当键值对，曾报告 0；原记录保留，已由 `parameter-consumer-census-a02.json` 的 6 个列表逐块源行替代。零文本命中只排除所枚举安装语料中的字面量，不排除原生实现、Workshop 模组或未安装版本。机器、版本和安装资源范围变化时必须重核；保存中的动态 Faith、历史事件结果与强制脚本修改不能由 authored 定义数外推。

## 决议、事件或效果能否把最大值提高

已进一步检查完整原版脚本、原生登记标识、实际 getter 与已绑定写入链：**没有找到原版可用的决议、事件或 effect 提高圣地总数/主要最大值。** Doctrine、Faith/Rite 参数、flag、modifier、政体和 HolySiteType 本身也没有进入这四个上限 getter 的动态求值。此结论不是把字面零命中说成引擎内存永不可改；更改 Religion 定义的模组或定义重载属于另一层。

加名单与加容量分别核实：原版 `add_holy_site` 唯一业务调用是 Adopt（决议 L557），其外层 L495–500 仍要总数小于上限；`make_holy_site_eminent` 唯一业务调用是 Promote（L79），外层 L32–39 仍要主要数小于上限。AI 没有放宽这些满额守卫；`add_eminent_holy_site` 没有 authored 调用。`set_holy_site_owner` 是圣物转入库存，`scripted_costs.create_holy_site` 是费用块，均不是增加 Faith 名单或容量。普通 Create 的实际 validator 也检查总数上限。

因此本轮**没有可证明的原版自然第 10 个/第 4 个例子**。裸模型 setter 可直接追加、外部存档或强制路径的可能越限，不等于原版事件在满额时可达，也不会使 getter 报告的最大值变大。有限位移扫描保留未绑定的 owner/别名/泛拷贝边界，不能据此宣称穷尽所有 native 写内存方式。详细动态范围、原件行号与写候选见[动态上限研究](evidence/holy-site-grade-effects-limits12004/dynamic-limits/DYNAMIC-LIMITS-RESEARCH.md)及其来源合同。
