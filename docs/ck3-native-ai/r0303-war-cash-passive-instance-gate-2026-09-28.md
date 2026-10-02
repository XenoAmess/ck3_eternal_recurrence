# R0303：战争现金 GUI 被动实例门禁

状态：**精确 EXE 类型指纹已证，当前 Robert/WarID 16777231 的 live 实例与同帧金额未证。**仅静态读取 CK3 1.19.0.6 `ck3.exe`（SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`）。未启动或连接游戏、未占屏、未填现金值。类型校验器 [`verify_war_cash_gui_rtti_candidate.py`](../../ck3_autonomous_player/native_bridge/research/verify_war_cash_gui_rtti_candidate.py)通过普通与 `-O` 精确 EXE 运行，固定输出 `war_cash_formal_eligible=false`。

| GUI 类型 | 精确 RTTI 与虚表 | 被动读数候选和限制 |
| --- | --- | --- |
| `CHudTopBar` | type descriptor RVA `0x51E18F0`；主 COL `0x464A948`、虚表 `0x40E6F68`，次 COL `0x464A970`、虚表 `0x40E7038` 位于对象 `+0x10`。构造函数 `0xD465A0` 于 `0xD46649..0xD4665B` 安装两个虚表，`0xD4661D/24` 将调用者 `RDX/R8` 保存至对象 `+0xC8/+0xD0`；这两个字段只是 owner/context **候选**，调用者来源尚未证实。主虚表首项 `0xD46F60` 的删除析构在 `0xD46F79` 传 `0xFA0` 字节给释放函数。 | #449 的 R0266 顶栏支出研究将费用根、Q100000 raw/scale、back-pointer 与渲染帧标记分别定位到 `+0xAD8`、`+0xB50/+0xB58`、`+0xB68` 和 `+0xF88`。RTTI 双虚表和对象大小可约束**候选对象指纹**，但不是唯一活对象的来源；旧对象、隐藏对象和未刷新缓存都可能通过静态形状检查。 |
| `CMilitaryView` | type descriptor `0x5260210`；主 COL/虚表 `0x46CA510/0x4135EE0`，次 COL/虚表 `0x46CA538/0x4135FB0` 位于 `+0x10`。 | 已有[军费缓存研究](r0266-war-cash-resource-2026-09-28.md)给当前/全军满员预测费率缓存候选。`view+0x248` 仅在 -1 时由玩家 ID 全局槽补写，不能以类型或 GUI 名称认定实例属于 Robert；getter 会刷新 View，桥接不得主动调用。费率不是实际已扣款。 |
| `CFleetEmbarkMapIcon` | type descriptor `0x51FEE88`；主 COL/虚表 `0x4668A58/0x41003F0`。 | [上船报价研究](r0266-embark-quote-abi-static-2026-09-28.md)证明 raw 位于 `*(icon+0x68)+0x78`，wrapper 在图标 `+0x70`；缓存只属于具体预测图标。未证明该图标对应战争规划器选定的军队、路线、上下船事件及暂停帧。 |

## 最小可恢复的纯读门禁

正式生产者必须先从已核的 GUI owner/manager 指针取得**当前唯一对象**；仅在堆中搜出虚表匹配对象不构成 owner 证明。对顶栏需在不调用 getter 的前提下双读：主/次虚表、根行与 back-pointer、全部行数组边界、Q100000 比例、`+0xF88` GUI 渲染帧、原生 played CharacterID、国库、当前 WarID、日期、episode、snapshot/public/native revision 和 paused 状态；两次读取之间不得有修订变化。还需自然 GUI 刷新与原生费用 breakdown 交叉核对，证明缓存属于该暂停帧和该玩家。即使这些条件满足，所得仍是**当前月费率**；`future_war_cost_upper_raw` 另需实际金币入账/扣款节奏、舰队/补员/佣兵及事件费用的有限期上界。

对上船报价，必须额外证明预测图标的 CUnitID 列表、ArmyID、原点、目标和路线与正式选定动作完全一致，且自然更新后行金额与所选动作同 native revision。没有 selected step 或 icon 不存在时，不允许拿旧预测图标报价冒充零费用。

## 精确硬阻断

1. **缺唯一 live owner 边。**本轮 RTTI 和虚表只给对象身份检查；尚无从当前 GUI manager/singleton 到唯一 `CHudTopBar`、`CMilitaryView` 或 `CFleetEmbarkMapIcon` 的已核指针链。不能仅凭内存扫描候选数为一推断生命周期与玩家归属。
2. **缺 native revision 与 GUI 缓存刷新边。**顶栏 `+0xF88` 是渲染帧标记，getter 可能写对象并按帧阈值重算；它不是战争快照 ID，也不能由被动读取证明本次费用已刷新。军队窗口与地图预测图标同样没有已证的原生修订绑定。
3. **缺从费用率到现金扣款的边。**已核 `0x28DC5A0/0x28DC8D0` 的路径计算和展示收支，尚未追到金币余额写入处与扣款账期；完整一月费率预留的一日 horizon 也不能被声称为已证数学上界。
4. **缺所选战争动作绑定。**上船缓存绑定的是可变预测图标，不是 `WarID=16777231` 的正式 action receipt；无同帧 CUnitID/route 比对，不得填即时现金金额。

上述任一缺口未闭合时，静态类型校验器和被动布局解析器只能产生诊断信息，不能批准战争现金字段。下一步需在录制空档作有界 manager 指针/对象构造链静态核查；随后由持有实机独占者用当前配对 DLL/injector 在受管暂停帧完成纯读采样。测试任何 live producer 前，先确定唯一 owner 指针与只读、固定上限的内存访问策略。

## Supplied-byte diagnostic gate (2026-09-28 follow-up)

`war_cash_topbar_passive_layout.py` now requires an explicit, 64 KiB aligned
`image_base` and checks both `CHudTopBar` vtable pointers at object `+0` and
`+0x10` against the verified exact-build RVAs `0x40E6F68` and `0x40E7038`
before it decodes any expense row. A matching fingerprint only narrows an
externally supplied byte candidate. It does not locate the live GUI owner,
prove cache freshness against the native revision, or authenticate a Robert
war cash amount. The diagnostic still emits `formal_cash_eligible=false`.
