# “自动升级建筑”二期可行性预研与开发清单

状态：**预研完成；开发尚未开始；未执行 CK3 实机验证**

候选版本：`2.0.0`

产品目录：`mod_auto_upgrade_buildings/`

Steam Workshop item：`3800124956`

研究基线：CK3 `1.19.0.6 (Scribe)`、当前维护版 `1.19.0`

## 1. 二期目标与范围

二期必须同时满足两个目标：

1. 玩家直接持有的所有**已有且存在下一等级**的原版省份地产建筑都可以进入自动升级，包括地产主建筑、普通建筑、部落建筑、公国建筑、特殊建筑和曼荼罗神殿城塞建筑。
2. 自动升级必须启动对应的原版施工生命周期：只在开工时扣费一次，建筑不会立即变级，玩家能看到原版施工进度和剩余时间，完成后才替换为下一等级。

“所有建筑”在本文中不包括住所系统、自动填充空建筑槽，也不承诺自动识别任意第三方 Mod 新增建筑。无 `next_building` 的终级建筑不是漏项。第三方建筑兼容要通过显式适配清单或以后单独立项。

## 2. 可行性结论

| 子目标 | 当前结论 | 关键条件 |
| --- | --- | --- |
| 覆盖全部原版省份建筑升级边 | **可行性高** | 用生成器从原版定义建立完整清单，不能继续维护 43 条手写近似链 |
| 普通省份建筑使用原版施工队列 | **有条件可行，Workshop-only 尚未证明** | 需要找到可对真人玩家和指定 province/building 调用的引擎施工命令；公开脚本 effect 中尚未找到该入口 |
| 曼荼罗都城升级 | **可行性中等** | 四级升级走 Great Project 进度，不是地产建筑槽施工；必须单独接入计划、出资和完成生命周期 |
| 两个目标同时以纯数据 Mod 交付 | **尚不能承诺** | P0 原型必须先证明真人玩家的定向省份施工入口；若不存在，只能由外置 native companion 精确完成，或降低目标为非原版的模拟施工 |

总体判断：**省份建筑“全覆盖”本身不是主要难点；真正的技术门槛是从后台为真人玩家启动一个指定建筑的真实原版施工命令。** 只要该入口被证明可调用，省份建筑全覆盖主要是生成、筛选和验收工作；如果该入口只能通过 native bridge 调用，功能仍可在技术上完成，但将不再是仅订阅 Workshop 即可运行的纯数据 Mod，必须在实施前单独确认产品形态。

## 3. 原版建筑清单基线

对本机 CK3 1.19.0.6 的 `game/common/buildings/*.txt` 做嵌套层级解析后得到：

| 省份建筑类别 | 可升级边数 |
| --- | ---: |
| 普通 `regular` | 370 |
| 特殊 `special` | 205 |
| 公国首府 `duchy_capital` | 30 |
| Great Building／Great Project | 4 |
| **合计** | **609** |

其中包括 13 条地产主建筑升级边：城堡、城市、神殿和神殿城塞各 3 条，部落 1 条。神殿城塞另有 `citadel_shrine`、`sacred_pool`、`vihara_halls` 共 21 条独有普通升级边。

费用不能再用“建筑等级 → 固定金币档”近似。609 个目标中：

- 588 个使用 `cost_gold`；
- 5 个同时使用 `cost_gold + cost_prestige`；
- 3 个同时使用 `cost_gold + cost_piety`；
- 9 个使用完整 `scripted cost`；
- 4 个曼荼罗都城目标没有建筑 `cost_*`，因为费用属于 Great Project。

609 个目标中有 605 个声明了至少一项 `can_construct_potential`、`can_construct_showing_failures_only`、`can_construct` 或 `is_enabled` 门槛。逐条手写革新、地产等级和费用只能得到近似行为，无法长期保持原版资格与费用一致。

### 3.1 游牧／牧民地产在二期中的边界

原版 `nomad_holding` 与 `herder_holding` 都带 `no_buildings` 参数；主建筑 `nomadic_camp_01` 和 `herder_camp_01` 也没有下一等级。因此“游牧／牧民地产建筑自动升级”在省份建筑图中实际是 **0 条适用边**。二期应把这两类地产报告为 N/A，不能伪造一个升级结果。

游牧毡帐等可升级内容属于独立的 `Domicile` 住所系统。按用户明确范围，**二期不包含任何住所建筑**；不得用住所覆盖替代省份地产覆盖，也不得为此扩展二期实现和验收。

### 3.2 曼荼罗都城不是普通施工条

`mandala_capital_01 → 05` 的四条边由 `great_project_type` 连接。原版 schema 明确说明：升级期间建筑槽本身没有施工进度，进度显示在 Great Project 上。二期应自动规划并推进原版 Great Project，而不是对建筑槽调用 `add_building` 或伪造普通施工条。

## 4. 当前实现为何不能满足目标 2

当前生成器为 43 条链生成 301 条分支，每条成功路径直接执行：

```text
add_building = <next tier>
aub_pay_building_cost_effect = { ... }
```

`add_building` 会立即改变建筑等级，没有 ongoing construction 对象。它不会给 `GUITrackItem.GetConstructionProgress` 和 `GetConstructTimeLeft` 提供一个可读的正常施工状态；手工扣款也不会自动继承原版的费用计算、施工速度、取消退款和完整开工／完工生命周期。因此二期不能只给现有 effect 加一个延迟事件，也不能把自制倒计时称为“原版一样”。

原版地产界面的升级按钮调用 `GUITrackItem.OnClick`，可用性由 `GUITrackItem.CanConstructNextBuilding` 判断，进度由同一 `GUITrackItem` 读取。当前已找到的脚本 effect `ai_attempt_to_build_building_effect` 确实能让引擎选择建筑并开始施工，但二进制诊断明确拒绝非 AI 角色，而且它不能指定目标建筑，不能作为玩家自动升级入口。

## 5. 推荐技术路线与决策门

按以下优先级推进，不先把 609 条边全部生成后再验证底层入口：

1. **首选：纯数据 Mod 的真实施工命令。** 逆向 GUI command/datacontext 是否存在可从 scripted GUI 或 effect 对真人玩家、指定省份、指定下一等级调用的稳定入口。
2. **次选：窄 native bridge。** 复用项目既有逐版本 native adapter，只暴露“查询指定升级资格／价格”和“提交一次原版施工命令”两个能力；命令仍由 CK3 引擎结算费用、施工和 on_action。
3. **不作为目标达成：脚本模拟队列。** 自制变量、延迟事件和进度 GUI 最多是兼容降级方案；它不能被标记为目标 2 GREEN，也不能在 Workshop 文案中声称使用原版施工队列。

P0 完成后必须作一次产品决策：

- 找到稳定的数据层入口：继续 Workshop-only 实现；
- 只有 native 入口：先明确是否接受外置 companion、版本绑定和安装步骤，再开发；
- 两者都不能稳定调用：停止“原版施工”发布，不以即时升级或模拟进度冒充完成。

## 6. 二期开发工作包清单

### P0：最小可行性原型（阻断门）

- [ ] 从 exact CK3 1.19.0.6 冻结 `ck3.exe`、`_buildings.info`、holding GUI 和相关 on_action 的哈希与证据位置。
- [ ] 建立一个只含 `outposts_01 → outposts_02` 的普通地产原型；对真人玩家定向提交施工，不允许使用 `add_building`。
- [ ] 证明开工后建筑仍为 `outposts_01`、`has_ongoing_construction = yes`、费用只扣一次、界面显示进度，完工后才变为 `outposts_02`。
- [ ] 证明施工速度修正、开工／取消／完工 on_action、取消退款与手动点击同一升级的结果一致。
- [ ] 证明 `CanConstructNextBuilding` 对革新、地形、文化、地产等级和互斥建筑的拒绝能够被自动路径复用，而不是复制一个不完整的近似条件。
- [ ] 对 `mandala_capital` 做最小 Great Project 原型，确认自动路径能否合法 plan/start/fund，而不直接替换建筑。
- [ ] 输出 P0 结论：`data-only`、`native-companion-required` 或 `blocked`；未通过本节不得进入全量 dispatcher 开发。

### P1：原版图谱生成器与冻结合同

- [ ] 新增建筑 schema 解析器，读取全部原版省份 building 定义，正确处理嵌套 block、分支升级与 scripted cost。
- [ ] 生成省份建筑清单：981 个定义、609 条升级边、目标存在、无环、类别和费用形状与冻结基线一致。
- [ ] 将主建筑、普通、部落、神殿城塞、公国、特殊和 Great Project 分为显式 adapter 类别；未知类型静态失败，不静默漏过。
- [ ] 保存 CK3 版本和输入文件哈希；游戏升级后只有审阅过 inventory diff 才能刷新冻结合同。
- [ ] 为 DLC 不可用、定义存在但内容未启用的情况保留原版 gate，不自行绕过 DLC／文化／信仰要求。
- [ ] 把现有 43 链／301 边生成器标为一期兼容实现；二期切换完成前保留旧存档的启用 flag 和事件 ID。

### P2：省份地产真实施工 adapter

- [ ] 只遍历启用玩家直接持有、未出租的 province；每个地产已有施工时零副作用。
- [ ] 使用 P0 证明的引擎命令查询并启动指定 `next_building`，由引擎计算真实费用和施工时长。
- [ ] 覆盖城堡、城市、神殿、部落、神殿城塞五种有升级边的 primary building。
- [ ] 覆盖 370 条 regular 边，包括部落普通建筑和神殿城塞 21 条独有边。
- [ ] 覆盖 30 条 duchy-capital 边，并保持公国首府和角色资格门槛。
- [ ] 覆盖 205 条普通 special 边，并保持地点、宗教、文化、决议和互斥条件。
- [ ] 同一地产一次最多启动一个项目；一次轮询不得在同一建筑链连续开工多级。
- [ ] 冻结确定性的候选顺序和资金保留策略；玩家能预知哪个建筑会先被选择。
- [ ] 开工失败时资金、建筑和循环状态全部不变；不得先扣钱再尝试启动。

### P3：曼荼罗 Great Project adapter

- [ ] 将 `mandala_capital_01 → 05` 四条升级边从普通建筑 dispatcher 中排除。
- [ ] 使用原版 `can_plan_great_project` 和对应 command/effect 判断是否可以规划下一等级。
- [ ] 自动创建或启动正确的 Great Project，并通过原版出资机制推进；不直接调用 `add_building`。
- [ ] 项目进行中不重复创建、不为同一等级重复出资；与角色已有其他 Great Project 的并发规则一致。
- [ ] 进度、阶段、费用、取消和完工建筑等级均由 Great Project UI 与状态证明。

### P4：调度、设置与迁移

- [ ] 保留 `enable_auto_build`、`auto_build.0003/.0004` 等一期公开存档入口，增加一次性二期迁移标记。
- [ ] 维持唯一全局循环；扫描间隔默认仍为 15 日，实际施工中不得重复扣费或续开同一地产。
- [ ] 提供类别开关：主建筑、普通、部落、公国、特殊、Great Project；默认全部启用。
- [ ] 提供最低资金保留值，且由引擎返回的最终价格参与判断；默认值和一期兼容行为在实现前冻结。
- [ ] 提供最近一次自动开工／拒绝原因的轻量反馈，不能暴露验收专用术语。
- [ ] 多人环境按玩家分别保存设置；AI 无启用决议，也不被后台玩家循环代管。

### P5：静态与生成测试

- [ ] 测试所有生成文件可重复、输入哈希绑定、定义计数、边计数、类别计数、无缺失目标和无环。
- [ ] 对四种费用形状和 Great Project 无建筑费用的例外建立表驱动测试。
- [ ] 静态拒绝二期生产路径中的 `add_building`、`replace_building_effect` 和对真人玩家调用 `ai_attempt_to_build_building_effect`。
- [ ] 静态检查每种 adapter 都有正例、资格拒绝、资金不足、正在施工和终级建筑用例。
- [ ] 扩展 release allowlist、manifest 和 deterministic ZIP 测试；验收夹具与 native companion 不得误入 Workshop staging。
- [ ] 日常只改简中和英文；正式发布前按仓库流程完成其余七语审计。

### P6：实机验收矩阵

- [ ] 启动前从分配器取得当前机器／当前 mod 的下一个实机编号；不预写或复用某个历史 R 号。
- [ ] 普通封建地产：普通建筑开工、进度、完工、一次扣费。
- [ ] 地产主建筑：castle/city/temple 的合法升级和等级门槛拒绝。
- [ ] 部落：`gold + prestige` 费用、部落主建筑和普通部落建筑。
- [ ] 神殿城塞：primary building 与三类独有建筑各一条代表边。
- [ ] 公国建筑：正确首府成功，错误首府拒绝。
- [ ] 特殊建筑：普通特殊升级成功；地点／信仰／文化门槛拒绝。
- [ ] 游牧／牧民：province 端报告 N/A，且自动循环不扣费、不造出不存在的建筑；住所系统不进入本矩阵。
- [ ] 曼荼罗都城：Great Project 被规划、出资、显示进度并最终升级。
- [ ] 比较自动路径与同一日期、同一角色、同一建筑的手动按钮路径：价格、资源种类、时长、on_action 和最终建筑完全一致。
- [ ] 验证施工速度／费用修正、取消退款、资金不足、重复轮询、保存重载、新征服直辖地、禁用和重新启用。
- [ ] 验证 fresh-cache 正式 staging，不以 source tree 或验收夹具替代发布候选。

### P7：发布收口

- [ ] 更新 README、Workshop BBCode 和玩家可见兼容说明，诚实声明是否需要 native companion。
- [ ] 构建正式 staging、manifest 和 ZIP；确认 canonical `descriptor.mod` 不含 `remote_file_id`。
- [ ] 更新同一 Workshop item `3800124956`，下载订阅缓存并逐字节复核。
- [ ] 上传成功后编写 `docs/release-changelogs/auto-upgrade-buildings/<version>.md`，记录上一公开版本、commit/tag、迁移、限制和实机证据。
- [ ] 提交并推送 exact release commit/tag/changelog；恢复 Steam 离线模式。

## 7. 玩家可证伪验收合同

二期只有同时满足以下条件才能标记完成：

1. 对清单中每个适用类别至少有一条真实成功样本，并由完整生成清单证明没有静态漏边。
2. 自动开工的瞬间只发生一次正确扣费，建筑等级不变并出现原版 ongoing construction；完成日期到达后才升级。
3. 自动路径与手动路径对价格、资源、时长、资格、取消、on_action 和最终状态一致。
4. nomad/herder province 的无建筑状态被诚实报告为 N/A，住所系统不计入二期完成度。
5. 曼荼罗都城显示 Great Project 进度，而不是伪造地产建筑槽进度。
6. 不满足原版门槛、资金不足、已有施工、已到终级或 DLC 不可用时均零副作用。
7. 保存／重载、禁用／启用和 15 日重复轮询不产生双扣款、重复项目或瞬间跨级。
8. 如果最终方案依赖外置 native companion，则 Workshop-only 安装不得被描述为功能完整；companion 的 CK3 版本绑定和失效提示必须通过验收。

## 8. 明确禁止的捷径

- 不用延迟事件包裹 `add_building` 后把自制等待称为原版施工。
- 不通过短暂切换玩家为 AI 来调用 AI 建筑逻辑。
- 不复制 605 组复杂 gate 后宣称与引擎 `CanConstructNextBuilding` 永久等价，除非有生成合同和逐版本差异门禁。
- 不把普通特殊建筑、Great Building 和 Great Project 当成同一种施工通道。
- 不把“游牧省份没有可升级建筑”误写成成功升级；正确结果是无适用对象且零副作用。
- 不把住所系统加入二期目标、实现、测试或发布声明。
- 不在 P0 底层入口未证明前实施全量生成器和 609 条 dispatcher。

## 9. 证据来源与边界

本次预研只使用本地静态证据，没有启动 CK3，也没有改变 Steam 离线状态：

- 当前 Mod：`tools/auto_upgrade_buildings_data.py`、`tools/gen_auto_upgrade_buildings.py`、`mod_auto_upgrade_buildings/events/auto_build.txt`。
- 原版 schema：`game/common/buildings/_buildings.info`、`game/common/holdings/_holdings.info`。
- 原版数据：`game/common/buildings/*.txt`、`game/common/holdings/00_holdings.txt`。
- 原版 UI：`game/gui/window_county_view.gui` 中 `GUITrackItem.OnClick`、`CanConstructNextBuilding`、施工进度和 Great Project 分流。
- 原版生命周期：`game/common/on_action/province_on_actions.txt` 的 `on_building_started` 与 `on_building_completed`。
- exact-build 二进制注册说明：`ai_attempt_to_build_building_effect`、`rebuild_great_building` 和 `replace_building_effect`。

清单计数是 CK3 1.19.0.6 的静态冻结基线，不代表二期已经实现，也不代表任何 P0 原型或实机矩阵已经 GREEN。
