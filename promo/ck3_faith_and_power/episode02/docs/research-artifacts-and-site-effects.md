# 二期研究：宝物机会成本、殉道／奇迹效果与观测边界

2026-10-20 后续接入：[游玩智能体研究入口](../../../../docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md)汇合本页静态知识、当前接口和后续实机边界。本文原始“当前／尚未实现”以各段记载时刻为准；新增接口与场次不追认早期资格，普通 auto 尚未自动消费本研究。

本页提炼 R2/R3 离线研究、独立 source 审计与 B1 预览证据，供讲稿、原生接口续建和后续拍摄复用。结论分为原版定义、实际 consumer 条件、当前公开能力和现场预览；这些层之间不能互相替代。

机器与时间：`machine_id: 4-8e1c2f1861`，本次 `tools/ck3_live_run_id.py machine` 独立返回同值；本次来源重核为 `2026-10-19T19:53:26.224451+00:00` 前后（北京时间 2026-10-20）。仓库上下文为 `17f7fb69cdae7fd67afdd385f5b1e922d17e2a0c`。实际原版资源对应 CK3 `1.20.0.4/build25734779`；既有 EXE 绑定为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本次重核 19 项原版／源码文件 SHA，未重新 hash EXE，未启动、连接或操作 CK3，未编译或应用任何原生补丁。安装资源字节与既有 runtime 回执分别列证。

本机外置资料根记为 `B1 = C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b1-a01`。本页的 `B1/...` 定位仅属于上述机器，不是其他机器的路径、部署或资格证明。全文知识已在此归纳；外置原件到期或回收后，应保留“原件是否仍可读取”的真实状态，不建立同名替代证据。

## 1. 当前可用结论

个人装备、宫廷展示、圣地供奉属于三个槽域。现有圣地查询可以独立读某件物品的玩家／圣地归属和是否属于玩家装备槽，却没有个人装备收益正文、耐久或个人 equip/unequip 公开动作。因此“放弃个人使用、改供奉”的具体机会成本仍须补物品原页与装备状态观察，不能拿既有供奉回调代替装备回调。

殉道和奇迹可以直接比较原版四层定义，但实际收益必须逐 consumer 验证。全 Faith 两层与地方两层的主要关系、Active 和收件人门不同。当前 aggregate 读口只覆盖部分人物 fixed key 总量，不覆盖兵士维护、最大战斗骰或县域 scaled 项，也不提供单站归因。

B1 已取得原版创建页的类型预览、稀有度 4 与 8 的选择读回，以及三种类型的可读画面。全部保持 `create_invoked=false`。它们足以作为“看类型和预览”的材料，不证明创建、付款、个人装备动作或角色／县／战斗的实际净收益。

## 2. R2：个人装备与供奉

### 已有公共能力

当前 [`mcp_server.py`](../../../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py) 在 2083–2147 行注册以下圣地域入口：

- `ck3_query_player_holy_site_relic_action_context_v1`、`...permissions_v1`、`...context_v1`。
- `ck3_select_holy_site_relic_artifact_v1`、`ck3_set_holy_site_relic_slot_selection_v1`、`ck3_enshrine_holy_site_relic_v1`、`ck3_remove_holy_site_relic_v1`。

创建页另有类型、地点和材料选择。上述都不等于个人装备。对本次列明的 MCP/Service 与 native `src/include` 做有界检索，未找到公开个人 equip/unequip、inventory window kind 或 court-artifact 呈现／状态工具。`court_artifacts`、`royal_court` feature flag 只能证明功能开关；`ck3_inspect_save_artifacts_v1` 是保存文件检查，不是玩家宝物库存。该缺口结论只覆盖本次实际源码，不外推未来分支或其他外置工程。

现有 [`holy_site_relic_action_context`](../../../../ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_relic_action_context.cpp) 的 `OwnershipRead`（113–135 行）可复用：

| 字段或原生来源 | 能证明 | 不能据此推出 |
|---|---|---|
| 完整 `artifact_id`、`character_owner_id`、`holy_site_owner_id`、rarity；artifact `+78/+7C/+B0` | 当前物品身份、两类 owner 与稀有度；各有 availability/reason | 个人属性、耐久或最终收益 |
| 玩家 Inventory `+58` 完整 ID 序列 | `player_owned_reference_member` | 可见候选完整性、可装备或具体装备槽 |
| 原 `22E4420(Inventory*,Artifact*)`；Inventory `+40/+4C`、24 B 槽行 | `player_equipped_slot_member`、`site_equipped_slot_member` | 实际槽 key、个人 CanEquip 或 modifier 到账 |
| `destination.effective_slot_index/replacing_artifact_id` | 圣地供奉有效目的槽与替换物 | 个人装备槽或个人替换规则 |

`2531200(artifact,site,null)` 属于原供奉候选，不能当作个人 CanEquip。owner 与 owned reference 需分别核；装备通常保留玩家 owner，供奉归属须以实际后验为准。

### 最短合法原版路径与尚缺定位

| 阶段 | 已 pin 的原版入口 | 最小续建范围 |
|---|---|---|
| 打开个人库存 | `gui/shared/buttons_icons.gui:749–754`，`ToggleGameViewData('inventory',Character.GetID)`，保留 local-player/物品/claim 的原门 | 定位当前玩家 inventory typed 开窗链、实际注册对象和独立 window 读回；当前接口不接受任意字符串猜开窗 |
| 当前个人候选 | `window_inventory.gui:455–469,725–768`；`GetSortedArtifacts`、`IsInventoryArtifact`、实际 selected slot 的 `CanHoldArtifact` | 定位真实候选 producer、排序／筛选与失效；不能用所有 owned refs 冒充当前可见列表 |
| 装备点击 | `window_inventory.gui:766–768`，`InventoryView.OnClickArtifact(Artifact.Self)` | 定位精确 callback、最终 command guard、有效目的槽与替换规则；不能照圣地 ABI 猜个人 ABI |
| 卸装 | `window_inventory.gui:842–864`，`InventoryView.Unequip(InventorySlot.GetArtifact)` | 绑定实际已装备槽、完整物品 ID 和原 command；不用未知 toggle 重试 |
| 宫廷展示 | inventory `:658–671` 的 IsCourtArtifact 行处于另一分支；`window_royal_court.gui:1680–1692` 是另一个 OnClickArtifact，含 `Inventory.CanEquipReplace` | R2 优先选个人 inventory 物品；若实物只可宫廷展示，另建 court owner/candidate/slot 合同 |
| 效果正文／耐久 | `window_artifact_details.gui:336` 的 `Artifact.GetModifierEffects`；inventory `:914,1002,1016,1026` 的 DurabilityTooltip/GetDurability | 定位 getter、可用条件和字符串生命周期；正文与装备后角色聚合分别观察 |

`common/artifacts/slots/00_default.txt` 将个人和 court 槽分开；court 有 `has_royal_court` 可用性。`_slots.info:27–37` 说明 available 在装备与月度重验。`01_holy_site.txt:1–20` 的三个圣地槽另设 `holy_site=yes`、`allow_any_type_or_category=yes`；通配不取消原生许可。

脚本里存在 `equip_artifact_to_owner=yes`：日本继承逻辑先检查 `artifact_owner.can_equip_artifact=prev`（`10_dlc_tgp_japan_scripted_effects.txt:3972–3975`）；初始圣物播种明确说明设置 owner 再 equipping 跳过正常供奉规则（`02_starting_holy_site_relics_effects.txt:1592–1598`）。这些是定位 effect/trigger 的线索，不能用 fixture 直接 equip 冒充正常 GUI 装备验收。

### 最小施工与拍摄顺序

1. 先增加玩家限定的只读 `artifact_equipment_context` 域（**提案名，未注册**）：inventory owner、ordered owned refs、真实 slot key/index/category/occupied ID、指定物品 type/category/owner/rarity/equipped slot、原 CanEquip/Unequip/Replace 与拒绝文本、有效槽／替换物、原效果正文和 durability。逐字段 availability；身份漂移整域拒绝，不把未知库存当空集。候选初版上限可暂设 64 refs/64 slots、指定物品 1、替换物 1；经实际模型验证后确定，溢出拒绝而非截断冒充完整。
2. 增加有限 typed inventory／物品详情呈现和独立读口，复用既有 Driver/Service/mailbox。作者可先用同一实物正文、供奉预览和实际费用解释机会成本，无须等装备动作完成。
3. 确需两种实际状态时，再增加独立默认 OFF 的 equip/unequip 动作：desired equipped bool、完整 artifact ID、冻结的有效个人 slot／替换 ID、当前 preview identity 与 expected public revision。派发前 native 重取 owner、原 Can 与当前按钮；已满足 desired 状态只读报告，不再 toggle。
4. 最窄对照为同一已披露母档的 A 装备臂／B 供奉臂，或“已装备 → 合法卸装 → 独立后读 → 供奉 → 独立后读”。卸装和供奉各自是世界动作与代价，不是免费 undo。能否直接供奉已装备物，以真实候选、Can 与后态为准。

工作量参考：只读 context＋有限原页呈现约 4–8 代理小时；独立装备／卸装动作再约 4–8 小时，未知 ABI 故障另估。每段只跑相关 focused fixture、真实 SDK 消费和最小实机，不全仓回归。当前类型预览制作可与此研究并行。

### 单次动作与 unknown

动作前冻结 machine/EXE/PID/connection-generation/episode、actor/rite/Faith、日期与 public/native revision、完整物品／槽／替换物／报价、实际 Can 和 preview identity；原 intent 先排他落盘，然后仅调用一次正常原按钮。

超时、ACK 丢失、回调异常、窗口重置、`verification_pending` 或 `dispatch_result_unknown` 均不重复提交。下一次独立 owner callback 读原物 owner、owned refs、相关装备槽、替换物 owner/slot、实际钱包／奉献、site slot/Active/cachedR/currentR；关闭窗口后仍读对象归属。已满足则报告后验；不变但命令可能排队则保持 unknown；只有明确派发前拒绝，才在修正前置并重新规划后提出新请求。不能通过重命名 request、删除 intent 或回载拼接绕过未知结果。

## 3. R3：殉道与奇迹的四层定义

来源为实际 `01_dynamic_holy_site_types.txt:24–96`。令 `R` 为该 consumer 实际读取的缓存有效圣物稀有度和，`L` 为每个接收角色自己的奉献等级。下表是原始定义贡献，尚不是现场净增。

| 效果层 | 殉道之地 `site_of_martyrs` | 奇迹之地 `site_of_miracles` |
|---|---|---|
| 地方角色 fixed | `county_opinion_add=5` | 月虔诚倍率 `+5%` |
| 地方县 scaled | 发展增长倍率 `+1%×R`；建造时间项 `−1%×R` | 县税倍率 `+1%×R`；抗疫力 `+2×R` |
| 全 Faith 角色 fixed | 每级奉献勇武 `+1`；其他 Faith 角色对其好感 `−5` | 月虔诚倍率 `+5%` |
| 全 Faith 角色 scaled | 兵士维护费 `−1%×R` | 最大战斗骰 `+0.5×R` |

三个口播边界已有原版文本依据：

- `different_faith_opinion` 官方简中 `modifiers_l_simp_chinese.yml:980` 明确为“不同[faith|E]角色对其的好感度”，方向是其他 Faith 人物看待受益者。尚未闭合双角色 opinion consumer 实测，不能宣称具体两人关系净差。
- `build_speed` 格式在 `00_definitions.txt:2389–2394` 使用 `MOD_TIME_PREFIX`、percent 与 bad 颜色，应说“建造时间项减少”。具体工程天数仍读实际报价，不需要为影片等待自然竣工。
- `max_combat_roll` 是最大战斗骰；不是最小值，不是每次掷骰固定加值，更不是胜率。实际战斗 consumer 应绑定真实指挥官；君主有修正不证明未由其指挥的军队受益。

### 实际 consumer 门与缓存

详见仓库已归纳的[圣地等级、效果条件与数量上限](../../../../docs/ck3-native-ai/holy-site-grade-effects-and-limits-12004.md)第 7–42 行，不能因二期换 type 就省掉既有门：

| 层或值 | 实际链与输入 | 继续保留的边界 |
|---|---|---|
| 全 Faith fixed/scaled | `29CC520 → 24FB270`，Faith 全站点 `+890` 与主要数组 `+8A8`；`2441F30` 从 site barony→county→holder 当前 Rite/Faith；写 Rite `+20/+2C`，角色 `291C0B0→291F080→2438830` 消费 | 需要该 Faith 主要关系与县主同 Faith；该 producer 没有同一个 Active 门。Rite 列表重建／聚合刷新时点仍须实测，空站或新等级不能直接宣布到账 |
| 地方角色 fixed | `291E3A0`，type `+218`，缓存 Active、角色 Faith 关联、两族实际 Title 输入 | 不能说所有同教角色；也不能无条件把任意 county holder 当真实收件者 |
| 地方县 scaled | `2864D93→2864E40`，type `+3F0`，缓存 Active 与县主 Faith 控制门 | 生产只读口尚缺 receiver `+298` owner、owner `+18` TitleID 的绑定；人物总聚合不能当县税／发展／抗疫／建造项 |
| `holy_site_total_artifact_rarity` | evaluator `2B0C740` 读取 site `+1C` 缓存，不调用当前重评 `265A3F0` | 同存 cachedR/currentR 与不一致；query capture epoch 不是缓存生成时间 |

当前 [`holy_site_modifier_aggregate.cpp`](../../../../ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate.cpp) 第 86–140 行只复制 type `+58/+218` 两个 fixed PC 的 u16 keys，读取玩家与派生县主的人物总聚合。其 [serializer](../../../../ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_modifier_aggregate_json.cpp) 第 19–25 行明确 `names_bound=false`、`site_attribution_observed=false`、`scaled_effects_observed=false`。所以兵士维护、最大战斗骰及所有县 scaled 均不在该实际值接口内；fixed 总量也不是该站净值。

### 一县实际归因的最小观测

每次前后态保存 machine/EXE/PID/connection-generation/episode、暂停日/public/native revision/capture epoch、site 完整 ID/type、barony/county 完整 ID、所有关联 Faith 及请求 Faith 的主要关系；县主与玩家的完整 ID/current Rite/current Faith；每个物品槽完整 ID/rarity/认可矩阵；cachedActive/cachedR/currentActive/currentR；实际冷却／报价／钱包。不要调用 producer 人为刷新后再称自然到账。

人物层还要真实收件者 ID、自己的 `L`、实际 Title 输入、aggregate owner/backlink、loaded modifier u16 key 与来源绑定名称、definition/scaled coefficient 和实际聚合数值。无来源列表时保留 `site_attribution_observed=false`。异教好感另需有向双方 ID/Faith、两方向原 opinion 来源；官方标签仅解释方向。

县层还要 receiver/owner Title 绑定、县 aggregate 中来源明确的税／发展／抗疫／建造项，以及当时实际建筑报价的完整费用与天数、其他影响源。最小续建先闭 loaded key 的 source-bound 名称，再选一项 fixed 人物项；县 receiver/scaled 另包。

最小有意义对照选一种 fixed 人物项：普通空站 → 主要空站 → 合法供奉后分别独立采集，保持 type、holder、日期和其他输入一致。玩家与县主若相同，不能假装有两个独立收件者。收费导致的 `L` 变化须单列。奇迹在玩家同时满足地方与全 Faith 门时可能分别存在两个 `+5%` 块；按来源分层，不重复计账。

## 4. B1 已有预览与证据限制

以下均为 `machine_id: 4-8e1c2f1861`、C2 actor `15893`、Faith `50`、暂停 `date_raw=51394920` 的既有现场回执，本次只读归纳。

| 预览与原件定位（相对 B1） | 实际观察 UTC | 选择与原生读回 |
|---|---|---|
| `capture-plans/martyrs-take01-observation.actual.json` | `2026-10-19T19:23:15.579542+00:00`（内含 source step 完成时间 `19:21:05.244348`，不将汇总时间冒充派发时间） | 殉道、barony `6622`、artifact `[237]`、预览稀有度 `4`、epoch `20168` |
| `live/4-8e1c2f1861--faith-engine--R0001/capture-observations/miracles-take01.actual.json` | `2026-10-19T19:23:40.342689+00:00`；内含 step `19:23:21.587226–19:23:21.763131` | 奇迹、同地点／artifact、稀有度 `4`、epoch `35084` |
| 同目录 `wisdom-take01.actual.json` | `2026-10-19T19:24:03.975295+00:00` | 智慧、同地点／artifact、稀有度 `4` |
| 同目录 `wisdom-rarity8.actual.json` | `2026-10-19T19:26:28.578472+00:00` | 智慧、artifact `[237,267]`、稀有度 `8`、epoch `49592`；这是拍完后的截图／读回，不追认为 raw take 内已有该状态 |

原生回执包含 `create_invoked=false`、`read_only=true`、`action_ready=false`；cached resource vector 的虔诚分量为 `200000000/100000=2000`，但 `cached_quote_freshness_observed=false`、`native_affordability_observed=false`，所以只能说当时缓存预览显示 2000，不能说最新可负担报价或已付款。

`authoring/continuous-v0/b1-type-preview-visual-candidates.v0.json` 绑定了三张原始 2560×1440 PNG 与原生 context SHA。图片供创建预览讲解，须保留“创建圣地／萨迈拉／总宝物稀有度／未生效／仅主要”语境。完整画面右下有无关物品 tooltip；不是整幅干净画面，也未批准任意裁切组合。

`footage-review-a01/REVIEW.actual.json` 的来源直接看图记录为 `2026-10-19T19:29:05.047360+00:00`：已严格全解码一次，raw 时长 `104.866 s`、2560×1440、2716 帧；只直接审阅 source PTS `20/40/60/90 s` 四帧。20 为殉道、40 为奇迹、60 与 90 为智慧；mark 或文件名不能代替真实画面。实际 PTS 间距有偏离，不能用 `frame_index/30` 对时，也不宣称 CFR 或连续 clean span。旧蓝窗“未见”只覆盖这四帧，未作全片目视认证。

关键媒体 pin：raw `captures/e02-b1-types01/raw-gameplay.mkv` 为 78,922,317 B，producer SHA `25f8daad1db44f374c83a5762269fb24219ca0a9820edb6349a6e5adb0247d18`；本次未重 hash raw。三张截图 SHA：殉道 `c7bd70d5c66cc08538888d9fa91f3a347750068c9ea6491b14b31516eafa9da3`；奇迹 `d70750d018b7ad8ede5cc4da76a7576ffe076d4c6c919903fee35eccb90cf41c`；智慧 `880a2f51db1ae00bfe14c1ab06906f18d745333efb89674de16da74c53642438`，均继承上述 visual manifest，未声称本次重新看图。

`EXECUTION-CLOSURE.actual.json` 记录 `2026-10-19T19:51:20.723101+00:00`：raw 在 keeper 故障前完成；原 public run exit 2，错误为 `Original screen keeper no longer owns this held scene`；随后原 host 实际退出、CK3 PID 列表为空并释放 screen。闭场不授 ordinary case/GUI 资格；原生只读预览、媒体可读帧与场次执行错误各自保留。

## 5. 独立 source 审计可复用的跨章节约束

外置 `research/independent-audit-a01.md/json` 在 `2026-10-19T19:20:03.779266+00:00` 对十项高影响说法取得 `PASS_SOURCE_BOUND`，没有 live 资格。与本页相连的关键区别如下；精确来源行号在该 JSON，后续应并入对应建制／朝圣专题而非强行扩充本页装备范围。

- 创建精神领袖的一处站点条件允许普通圣地，但还需原 control／县主同 Faith；主流／非主流礼仪奉献门分别为 2／3。虔诚费用与金币／国库费用不是同一乘数：虔诚的非主流 ×2 不自动乘到金币；缺合资格 eminent site 的 ×1.5 也保留自己的关联与控制条件。不是所有创立者都成为精神领袖，非主流礼仪创建后主流礼仪变更要读实际后验。
- 大圣战“解锁宗教状态”“Faith 发起资格”“筹备对象”“实际宣战”是不同结果。120 天不是所有明确目标路线共同的硬等待，合法 explicit kingdom target 另有路径；后续筹备仍可能为 365–545 天。
- 当前 rite 有 `mandatory_hajj` 且无 `hajjaj` 时，普通 pious/worldly 均不可用。普通朝圣三个月指到达后的目的地停留，不是整趟旅行。目的地激活、结束奖励与返程分开观察；7000 的 tooltip 展示不是重复发奖，9001 不是第二份完成虔诚。
- 普通圣地 ×0.5 位于 `give_piety_reward_effect` 的特定计算内，检查目的地县中本 Faith 的普通站点；同县多个站点必须考虑。它不统一减半 fulfillment、legitimacy 或其他独立奖励；当前 rite 的 mandatory-pilgrimage/Hajj fulfillment 定义为 +10，否则 +5，实际上限和到账另读。

独立 patch 审计也保留源码与生产资格差别：`research/pilgrimage/patch-candidate-a01` 的新当前玩家 pilgrimage identity 查询复用 owner-thread 通用 hosted reader；筛选精确类型、保留完整 ID、unknown 为 null、observed zero 为 0，空集明确 `absence_is_completion=false`。它绕开 Feast 的 Capture/Cost/Start 业务条件，但仍处于既有 Feast Start 编译 gate。a01 唯一 router spy 缺新 serializer 的 R1，在 `patch-candidate-a02` 的 test `449–456` 已源码关闭；本次复核 3 source pins、候选 SHA 和 9 hunks，通过决定为 **a01＋a02 可进入冷构建资格**，不是已应用或编译通过。现有 synthetic `.2` mailbox＋`.4` descriptor 只测分发；真实 reader→serializer→Python→注册 MCP 与新 binary／暂停现场仍待验证。

## 6. 精确来源索引与失效条件

19 项来源在 `B1/research/economy/source-pins-a01.json` 初次记录于 `2026-10-19T19:21:01.438177+00:00`，本次实际文件 SHA／大小重核全部一致。原版相对路径均位于该机器实际 CK3 `game/`；仓库路径位于上列冻结上下文。

| 来源及本页相关行 | SHA-256 |
|---|---|
| `gui/shared/buttons_icons.gui:749–754` | `f5d8e398a396b75f588a3abd9cb07b51639d7201c71fe7a68ec869b40ce215e6` |
| `gui/window_inventory.gui:455–469,654–671,725–768,814–887,998–1028` | `475e3a692e4594e170c42d661247db29b1d4adbf62dedf9a3fc8f3463573cc6a` |
| `gui/window_royal_court.gui:1678–1693` | `425cbfa044e12800a0202f37292ec26efd1ec944ba9f86e1afd1530d33d94bad` |
| `gui/window_artifact_details.gui:330–350` | `718c86ae7abc6b884a52ffb8807e94638e5e03ec8042ca5f2b55bc8e89e4699e` |
| `common/artifacts/slots/00_default.txt:1–78` | `dc2a21281fd9275ef9de2d271ff835b181e46d1dac6f6d953e092cfc13914a69` |
| `common/artifacts/slots/01_holy_site.txt:1–20` | `748a4c2f87bfea5959843c88456f38851eb968e507ef376bff0a725a6ac425df` |
| `common/artifacts/slots/_slots.info:1–47` | `c27465fe6938235786b578d58b47fdb673845787e1e4d775be4fb782f669ca62` |
| `common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt:3972–3975` | `cf6fa3ec4e072dc3ec0bb79985443860f868536e120d1b88d9ca64eb4850022f` |
| `common/scripted_effects/02_starting_holy_site_relics_effects.txt:1592–1598` | `1a4012823cfc44808ca113b786713ca387230a397ba54bab4245627618e9092a` |
| `common/religion/holy_site_types/01_dynamic_holy_site_types.txt:24–96` | `30cac0199fb08edccfb6b4e96f505efa20ba0adb897846f121db80e51511e6bc` |
| `common/modifier_definition_formats/00_definitions.txt:1158–1172,2389–2394,2710–2712` | `a1db27f5dc5ae1c1e89764ccb265d4167ba8be5be40b88602b0d90b471287cc4` |
| `localization/simp_chinese/modifiers/modifiers_l_simp_chinese.yml:980,1113–1114,1134–1135,1150–1151` | `c4b669dff52effa52412c52746845d4879f012e22b122e81e10ab19833650ada` |
| `ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py`（本次注册行 2083–2147） | `c34e7d5454d0a877c83fd4969c734437208bc756fc5d2d3fdcbfae5e50462722` |
| `native_bridge/include/xar_bridge/ck3_12004_holy_site_relic_action_context.hpp:21–54`（前缀 `ck3_autonomous_player/`） | `46fb983154c2fe9ec267f1018fefa63e45a6003760d700d7b1a619311deb9e28` |
| 同 `native_bridge/src/ck3_12004_holy_site_relic_action_context.cpp:113–135` | `dc92910eff4655918c345c216f71e52f01eae803e391abccb3afb22dbee08894` |
| 同 `native_bridge/src/ck3_12004_holy_site_modifier_aggregate.cpp:86–140` | `2a023fd29490bd6a895d54ac76a6f81ad11b0ada67c5f8ad5a47fe3054ec8c4b` |
| 同 `native_bridge/src/ck3_12004_holy_site_modifier_aggregate_json.cpp:19–25` | `170f96ca47b9e9cd78aa40a4d4f2daf81dea1d447a6a4aa33d622cdaf619b14e` |
| `docs/ck3-native-ai/holy-site-grade-effects-and-limits-12004.md:7–42` | `fcc49801f96cd21feb1caefc358d7a848b1ce3fd3ace5e8310d9543b0534f9c0` |
| `docs/ck3-native-ai/holy-site-major-grade-value12004.md:93–114` | `4623caf9380de03f1dac2d63cc4dde36683a1e2a8a18594a597cfe2d44f3b592` |

原始正／零命中范围另见 `B1/research/economy/source-searches-a01.json`；本页不把零命中当作全世界不存在。版本、GUI、原脚本、loaded source 或 SDK 发生变化即重核相关 pin、consumer 与注册能力，不沿用旧实例的 revision、指针或输入资格。

第 5 节跨章节约束的精确 pin 以下继承独立 source 审计原件；这些不是本次 19 项重核的一部分，原观察时间为 `2026-10-19T19:20:03.779266+00:00`，来源机器同上。行号保留实际条件／effect 调用，不把旧注释当运行时 caller。

| 原版来源与独立审计相关行 | SHA-256 |
|---|---|
| `common/activities/activity_types/pilgrimage.txt:1392–1456,2380–2410,2459–2489,2574–2579` | `24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f` |
| `common/decisions/10_religious_decisions.txt:3076–3158` | `6ef6123e5f0ae31789f8f854043ba4d11278af0470871ba77d3df0cffc2da30c` |
| `common/decisions/dlc_decisions/pam/pam_decisions.txt:1177–1180` | `fe113568051ccf2243f08543a522bc5afeb3e25e6fb97e5440d2fae7a4cb7a64` |
| `common/on_action/travel_on_actions.txt:1466–1475` | `cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70` |
| `common/script_values/00_basic_values.txt:83–114,665–670` | `c379cc0c58ed1574033f0e07a58697dfc6f8475c26aa4b117f2332008d4a27ef` |
| `common/script_values/02_religion_values.txt:4094–4189` | `9e55618b00b463589af310bd17511b4f260fea4d3acb43e512e209cfc1517ded` |
| `common/script_values/pam_values.txt:2175–2179` | `458d1bd882e8854005e3158339fca343177cff13eac7f83cb5877a8a37171965` |
| `common/scripted_effects/00_pilgrimage_effects.txt:54–91,516–629,1136–1206` | `4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80` |
| `common/scripted_effects/00_religion_effects.txt:383–455,479–505` | `5bf6b0df3316f72f711507c310a349d508a3b83aef99373ea6440de20e4e4931` |
| `common/scripted_triggers/00_great_holy_war_triggers.txt:38–52,69–87` | `7e449bcfa18bc02cf97cffff950d7b6f2d97aab7e0e93110db6c39d5e26505ba` |
| `common/scripted_triggers/00_religious_triggers.txt:1404–1449,1488–1528` | `e9d0b56130464eabdcd670fa6cf814534d11c99da1e8b3fc1e69e9c3e36d2bb2` |
| `events/activities/pilgrimage_activity/pilgrimage_events.txt:9059–9104,15089–15094,15187–15279` | `900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06` |
| `events/religion_events/faith_creation_events.txt:156–258` | `419c04b9ca889e96e572b894ec346ae6119af2fd6eb9be4833d6659edfba923e` |
| `events/religion_events/great_holy_war_events.txt:45–73,121–126,1047–1124,1146–1192` | `dfac5841107682613a78ec817d48c10b6ffb7ad411d9043901079de0a27897c0` |

本次只新增这份小型仓库知识文档和外置 a02 审查记录，不复制 EXE/DLL、完整资源、存档、原片或全量导出。外置活跃候选及必要证据按[通用存储策略](../../../../docs/storage-retention-policy.md)和版本化参数，于 `2026-10-26T19:02:10.097469+00:00` 前复核；本页与精简审计属 record，按政策复核归纳，不自动延长大原件保护。
