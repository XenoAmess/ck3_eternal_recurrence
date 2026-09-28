# R0266：常驻顶栏金币支出 breakdown 静态链路

状态：**精确 CK3 1.19.0.6 静态缓存候选，无 Robert 同帧金额。**核对的 `ck3.exe` SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。未连接 CK3、读取进程、调用 getter 或操作桌面。验证器 `ck3_autonomous_player/native_bridge/research/verify_war_cash_topbar_expense_candidate.py` 在普通 Python 和 `-O` 下均通过精确 EXE 与原版 GUI 核对，并固定输出 `formal_cash_eligible=false`。

| 链路 | 精确锚点 | 结论 |
| --- | --- | --- |
| 常驻 UI | `game/gui/hud.gui:6121-6131` 将顶栏金币 tooltip 的 `income`/`expenses` 分别绑定 `InGameTopbar.GetGoldIncomeBreakdown` 和 `GetGoldExpensesBreakdown`；`game/gui/shared/value_breakdown.gui:161-252` 用 `ValueBreakdown.GetSubValues` 显示行。 | 入口属于顶栏玩家金币，而非军队窗口或国库 treasury 的独立入口。GUI 显示值可能舍入，不能直接填原生 Q100000。 |
| 注册和 getter | 费用名 RVA `0x40E5F08`；注册 `0xB0819`，GUI callback `0xD49910` 跳到 getter `0xD47680`。getter `0xD4768D` 指向对象 `+0xB68`。 | 有精确版本的被动缓存地址候选。未找到可直接绑定 Robert 的唯一 live `InGameTopbar` 实例。 |
| 缓存刷新 | getter `0xD4769B..0xD476B8` 读全局渲染帧、与 `this+0xF88` 上次更新帧和阈值比较；过期时先写 `+0xF88` 再调用 `0xD476D0`。`hud.gui:6113-6116` 的鼠标进入处理还调用 `ResetLastUpdateFrame`。 | **getter 不是纯读**，不得由 headless bridge 主动调用。一次被动读取即使结构匹配，也不证明费用缓存属于本次 native revision、日期或当前玩家；需实测刷新与同帧双读。 |
| 玩家绑定 | 刷新函数 `0xD47728` 读取既有 played CharacterID 全局 RVA `0x4FE7EE0`；`0xD4774F` 核解析对象 ID，失败分支 `0xD47754` 取 fallback 指针。 | 刷新链有玩家全局来源，但旧缓存、fallback 或实例复用均可能失配。必须另核 live 玩家 ID、角色对象、WarID 和 paused frame；不能只凭 GUI 名称认定 Robert。 |
| 总额布局 | `0xD47867` 取 ValueBreakdown 对象 `this+0xAD8`；`0xD478BC` 调用费用汇总；`0xD478C8..0xD478CB` 将汇总结果**取负**写入 `this+0xB50`；`0xD47993..0xD4799A` 在 `this+0xB68` 写回指向 `this+0xAD8` 的指针。`+0xB58` 按通用 ValueBreakdown 布局是 scale 候选。 | 被动采样须核 `*(this+0xB68)==this+0xAD8`、scale 精确 `100000`、有符号 raw 与可见总费用相符；取负代表 GUI 支出方向，不能在无行核对时直接把负值绝对化。 |
| 军费子项 | 费用汇总 `0x28DC5A0` 的 `0x28DC635` 调用 RVA `0x290A720`，与 R0266 已验证的 `MilitaryView.GetGoldMilitaryExpenses` 当前军费计算器相同；`0x28DC63A` 取其 raw，`0x28DC78C` 继续加别的支出。 | 顶栏总支出**包含当前军费计算链**，但军费行的独立 live raw、名称/子项、舰队组成和刷新时点均未核。总支出不能直接替代战争军费。 |

## 行结构与实例定位补充

精确 EXE 的 `ValueBreakdown.GetSubValues` 名称 RVA `0x40CC348` 经注册 `0x68649` 到 callback `0xBAFC90`，`0xBAFC9C` 从 GUI wrapper `+8` 返回子行数据模型；`ValueBreakdown.GetName` 经 `0x6811D/0x6819F` 到 `0xBAFAA0`，解引用 wrapper 指向的行对象并取该行 `+0x18` 名称字段。不能把 `GetSubValues` 的 wrapper `+8` 误认作费用根对象的行数组地址。

费用根对象从顶栏 `+0xAD8` 开始：数组指针在 `+0xAD8`，容量 DWORD 在 `+0xAE0`，数量 DWORD 在 `+0xAE4`。精确 `0x98BE50` 的清理循环每次走 `0x90` 字节，`0x21C7660` 的追加逻辑也按 `9×16=0x90` 步进并更新数量。每个行对象的 `+0x18` 是名称字符串，`+0x28/+0x30` 是长度/容量，`+0x78/+0x80` 是有符号 raw / Q100000 scale；通用构造函数 `0xBC3D70` 初始化这些字段。这是**离线解码布局**，不是 live 行值。

`0x290A720` 的原生军费链静态引用六个标签键：`BREAKDOWN_ARMY_MAINTENANCE`、`BREAKDOWN_ARMY_MAINTENANCE_EMBARKED`、`BD_UNRAISED_MAA_MAINTENANCE`、`BD_UNRAISED_MAA_MAINTENANCE_BASE`、`BD_UNCONTROLLED_MAA_MAINTENANCE`、`BD_UNCONTROLLED_MAA_MAINTENANCE_BASE`，其中多个分支直接调用 `0x21C7660` 追加 breakdown 行。原版英文分别称已征召军队、上船军队、未征召兵团及转隶兵团。**同名/嵌套行可能不是互斥费用桶**；不能盲加所有六行，也不能以缺一行推断其费用为零。需要实际行树、当前 army/舰队状态与 `0x290A720` 独立总额交叉核对。

`InGameTopbar` 类型名 RVA `0x40E5FF8` 的已核引用在注册 RVA `0xD4B330`，这里只说明 GUI 类型注册，**没有定位唯一 live 对象指针**。因此本轮没有能在 H3568 直接使用的无扫描实例 locator。新增纯离线工具 `war_cash_topbar_passive_layout.py` 只接受外部已取的精确顶栏字节、行数组字节及名称字节，核 back-pointer、Q100000 scale、数组边界、步长和标签；它不连接 CK3、不读取任何进程，并固定 `unique_live_topbar_instance_proven=false`、`same_frame_cache_freshness_proven=false`、`formal_cash_eligible=false`。其诊断不能进入 R0266 正式现金收据。

原版军队窗口称其费用为月度维护，顶栏金币余额也呈现收支速率；这不证明金币实际扣款日、次序或每次扣款上界。舰队还可使实际军费高于全军征召满员预测值，见 [月费节奏审计](r0266-war-cash-cadence-static-audit-2026-09-28.md)。因此本候选即使取得总月费，也**不能**填 `future_war_cost_upper_raw`、最低保留、待办现金或动作即时费用。

## 最新来源帧可验证路径与当前门禁

来源已把 H3568 升级为 R0298 正式 H3603/raw53219352，随后 R0299 于约 09:40Z 继续推进，因此 H3603 已是历史帧。接收端对 H3603 七件完成 7/7 精确传输哈希验收，未完成本机配对。在当时**最新**帧自身官方 save/driver/sidecar/DLL/injector family pair、接收端无启动配对及受管暂停帧证明齐备后，才可尝试**被动**读回：先确认唯一顶栏实例及其 vtable/生命周期来源（目前缺），再在 GUI 正常刷新后取得 `+0xB68` 指回、`+0xB50/+0xB58` raw/scale、`+0xF88` 渲染帧标记、玩家全局 ID 和原生玩家角色 ID。刷新前后要由正式桥接双读同一 episode、snapshot/public/native revision、date、WarID、gold 与暂停状态，并核可见 tooltip 费用。任何一处失配或未定位唯一对象，即标为诊断 RED。若需鼠标触发 tooltip，应由拥有 `ck3-screen` 的执行者按桌面坐标合同操作；本静态研究不做该步。

取得总额候选后，还需以同一帧的 `ValueBreakdown.GetSubValues` 或原生独立军费 readout 精确识别军费行，并与 `MilitaryView` 当前值交叉核对；光有总额不足。未来成本上界仍需实际付款节奏、舰队和补员等完整风险合同。历史 H3603 即使被动读到总额也无法证明现行 R0299 条件，当前战争现金各输入继续为 `null`。
