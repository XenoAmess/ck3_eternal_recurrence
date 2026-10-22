# 旅行费最后一层：GUI 接收对象已缩窄，最终计价仍有三条未闭边

`machine_id: 4-8e1c2f1861`；研究观察于 `2026-10-22T04:14:01Z`，源码 `a425c0529b34a2002316b4cd1cbbe6ff8c528e8f`，状态 **SOURCE_ONLY**。实际读取从04:03Z开始；原始观察时间精度、来源SHA和行号保留在[结构化来源](knowledge/pilgrimage-v6-travel-fee-boundaries-12004.json)。入库不追加Native或实机资格。本研究未操作游戏、MCP、Native、屏幕、Git或tracked文件，未新抽取EXE。

目前能补闭的是 **GUI 传给谁、展示哪种费用、现有 Native reader 实际读哪个容器**。主管报价的内部脚本 root/scopes、补给数值 producer、两规划器合计过程仍不能据现有缓存闭合。不能把 F0 的已展开脚本费 176、更不能把一个现场 70 报价，替换成完整计价公式。

## 主管的界面对象与费用名称

旅行窗先取得 `TravelPlanner.GetTravelPlan/GetTravelPlanDraft/GetTravelPlanData`（G01:12–17）。主管栏进一步以 `TravelPlanData.GetTravelLeader` 建立 Character 上下文（G01:720–724），随后才调用 `Character.GetTravelLeaderCost` 和 `GetTravelLeaderCostBreakdown`（G01:748–754）。所以这里的 **GUI 接收对象是当前旅程已选主管**，不能先验替换成出钱的主办者。

任命窗提供独立交叉证据：G02:542–551 先绑定 `AppointCourtPositionView.GetSelectedCharacter`，在旅行相关职位显示同一个 `Character.GetTravelLeaderCostBreakdown`。G02:838–867 的速度、安全称职度是两个独立 getter，文本各自先 `Max(...,0)` 再以 `|0` 格式化。不能拿这两项显示出来的整数，直接冒充内部传入的未格式化 `scope:speed_aptitude/safety_aptitude`。

官方中文将该项写为“旅行开始后的俸禄”，明细标题又称“旅行开始时……的薪水”；英文同样是 wage when the travel starts（G04:6；G05:28–36；G06:30–38）。因此 L 宜称 **每次出发的主管俸禄报价**，与月薪分开，也不要直接称为一次任命费。这些文本只证明界面语义；何时从哪一钱包扣除、归返是否另计，仍需实际计价/扣款调用链，不能由标签推出。

脚本 `travel_leader` 本身早已展开：在其实际 root 的 liege 存在且不是无地冒险者时，金币项为

```text
max(speed_aptitude / 5, 1) + max(safety_aptitude / 5, 1)
```

否则该脚本金项从 0 保持 0，且 `round=no`（G03:662–689）。**本次没有找到 getter 注册/执行体到这个 key 的精确调用**，故 GUI 的 Character 接收者，不等于已经证明脚本 root 就是该 Character；两个 named scopes 的 producer、精度和实际传值也不能追认。脚本分支的 0 不能搬成所有未读出的 GUI 报价为 0。

## 补给是独立资源与独立显示分支

G01:174–183 的补给区只在 `IsLandlessAdventurer(GetPlayer) AND TravelPlanData.IsTravelWithDomicile` 时显示，调用 `TravelPlanner.GetProvisionsCost/GetProvisionsCostBreakdown`。G01:186–189 的普通费用区则在 `NOT TravelWithDomicile` 时显示 `TravelPlanner.AccessCostBreakdown`。

官中明确采用补给图标与补给资源，未写金币兑换（G05:57；英文 G06:62）。本轮因此闭合的是 **显示门和资源语义**，不是 `GetProvisionsCost` 的算法。F0 的有地公爵不满足该补给显示门，也不能由“没显示”宣布后台补给值是 0；更不能将兵士的 provisions_cost 表或一次补充补给事件的数值当成行程补给报价。

## 两个规划器与现有 Native 读口不能混为一层

旅行确认区使用 `TravelPlanner.AccessCostBreakdown`（G01:188）；活动最终确认区使用 **另一个对象上下文** `ActivityPlanner.AccessCostBreakdown`（G07:1801–1803、2182–2184），其按钮另行读取 `CanProgressPlanningStage`（G07:1819–1824、2191–2195）。共享组件 `cost_breakdown_vbox` 又按各资源名调用 `GetCost`、`AccessBreakdownTooltip`，并单独调用 `CanAffordCosts(GetPlayer)`（G08:883–1035）。GUI 这些入口并未展示两对象如何在内部累加，也没有给出主管费是否已经包含的答案。

当前源码已有普通 pious 朝圣的有限 typed FullCost reader，不能继续把早期“只有 Feast 分支”的研究状态当成当前全部事实。但这个 reader 的能力是读取当前规划器配置报价，不是复原所有 producer：

1. 限制 stage 5、实际 actor/owner/planner/type、当前选择与正常 refresh；缺样本是 `no_normal_refresh`，不写成免费（N01:126–145、185–243）。
2. **当前 .4 布局为 `CActivityPlanner + 0x1B10`**，不是旧 1.19 的 `+0x1AD8`（N03:41–61）。reader 实际取该容器的十个 indexed totals（N01:245–257）。
3. 已绑定的 named getter 经当前迁移映射到 `0x310ADF0`，用同一容器做 named/indexed 一致性核对；本合同仅明确命名 `gold/treasury/piety/barter_goods` 四项，不能把未命名项或补给默填成 0（N01:50–91、264–286；N02:159–181；N04:81–84）。
4. 返回前重核选择、owner、配置指纹、refresh sequence 和 totals；另读 final CanStart。它不会因为读到了数值就替代实际支付后态（N01:288–341）。

这里引用的是现有生产来源；本线程没有重新读 EXE 代码体、调用这个 reader 或增加任何 Native 资格。已声明的 `.4` refresh 映射 `0x11BA6B0` 与 slot12 return `0x11B5B3F`（N04:35–40、62–63）只定位现有刷新链；它们不自动证明刷新函数内部如何组合 travel/活动/主管费用。

## 精确停止点

| 未闭边 | 已有端点 | 缺失的最小证据 |
| --- | --- | --- |
| 主管 L | GUI 当前主管/已选候选人 → `Character.GetTravelLeaderCost[Breakdown]`；另有已知 `travel_leader` script cost | exact .4 注册回调/执行体 → named-cost key → 实际脚本 root 与两个 aptitude scopes 的构造、单位及求值路径 |
| 补给 | landless + domicile 显示门 → `TravelPlanner.GetProvisionsCost[Breakdown]` | exact .4 getter/producer → 路线、人员、兵士或时间输入的实际读取，以及最终资源数值；不能凭相关常量拟合 |
| 最终合计 | `TravelPlanner.AccessCostBreakdown` 与 `ActivityPlanner.AccessCostBreakdown` 两个 GUI 调用者；当前 ActivityPlanner 的有界同配置报价 reader | 两对象各自刷新/聚合 producer、相互包含关系、L/选项是否已包含、负选项的钳制顺序、人数去重与最终扣款命令消费 |

两名既有研究作者分别确认没有上述三个 exact .4 getter/producer 的已封函数体缓存；XP 的 a01/a02 缓存也不属于旅行费用。旧 1.19 的函数图不能外推作 .4 新证据。本轮到这些缺边停止，不新开大范围反汇编。

可直接用于作者注的结论：**176 是 F0 已展开的脚本费用模型；主管另有出发俸禄报价，补给有独立资源和显示条件，最终规划报价由当前规划器读取。未闭合前不把这些分项、某一个现场报价或它们的随意相加说成完整实付。**

原知识索引的 `travel_leader_binding` 与 `provisions_and_aggregate_quote` 仍保留 unknown；本补记只把其中的 GUI 接收对象、显示门和现有读取容器缩窄，不回写旧包，也不新增 ordinary-auto 资格。

## 作者后记：稍后实机观察与本研究分开

稍后R32界面报价70只属于该次具体配置，不能拟合成通用公式；0.10／月薪不是独立的出发俸禄报价L。后续事实见[本地审片记录](production-v6-local-review-2026-10-22.md)。这些后续观察不并入04:14:01Z的SOURCE_ONLY数据，也不改变本文保留的未知。
