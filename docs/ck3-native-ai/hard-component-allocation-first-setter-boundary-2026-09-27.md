# 硬伤分摊的首兵团写回与边界：CK3 1.19.0.6 静态勘误

**证据范围。** 只读验证原版 `ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的
`0x239C840..0x239CAD8`。运行
[`verify_hard_component_allocation_boundaries_static.py`](../../ck3_autonomous_player/native_bridge/research/verify_hard_component_allocation_boundaries_static.py)
对 27 条指令、6 条直接调用边和 9 个分支目的地作 hash-bound 检查；它不启动 CK3，也不执行原生函数。
研究问题、调用/消费链及尚待实机闭合的边保存在[同专题研究计划](hard-component-allocation-first-setter-boundary-2026-09-27.plan.json)。
下述机器码顺序为 **static-confirmed**；边界在真实存档中能否出现、特殊 setter 是否触发其他链接对象副作用均为
**live-unverified**。

## 写回入口和选择顺序

`0x239C840(CRegiment*, int64 hard_raw)` 先要求嵌入对象 vcall `+0x08` 为真、
`0x239CEB0(regiment)` 为假、`regiment+0x38 != 0`。通过后读取
`regiment+0x2C` 的 descriptor 数量，按 `regiment+0x20` 存储顺序、每条 `0x10` 字节，
分别在两遍中用 `0x23821B0` 解析 component 指针。第一遍跳过 null component 和
selected count 为零的 component；第二遍只跳过 null，**没有零 selected-count 跳过分支**。
本函数没有按征召兵、职业兵士、骑士、兵种强度或角色名称排序。它决定的是**一个底层 Regiment
内部已存储 component 的写回顺序**；跨 combat entry 的硬伤预算及其先后顺序由上游
`0x23CDF70` 决定，不能从本函数推断“全军先死某兵种”。未绑定 descriptor 与实机兵团名称时，也不能
把第 0 个 descriptor 直接叫成某个玩家可见兵团。

## 数值与检查位置

两遍均把 component 的 `kind(+0x18)==3 && current(+0x04)==0` 编码视为
`selected_count=max(+0x00)`、`setter_base=0`；否则两者都用 `current`。第一遍对 selected-count
非零者执行：

```text
cap_raw       = selected_count * 100000
candidate_raw = signed_fixed_div(low64(selected_count * original_hard_raw), cap_raw)
candidate_raw = min(candidate_raw, cap_raw)
allocated_raw = min(remaining_raw, candidate_raw)
whole         = trunc_toward_zero(allocated_raw / 100000)
0x23D3090(component, int32(setter_base - whole))
remaining_raw = signed64(remaining_raw - allocated_raw)
if remaining_raw <= 0: stop first pass
```

`0x239C9ED..0x239C9FB` 用倒数乘法和符号修正实现向零截整；`0x239C9FE` 是 **32 位**
setter 值相减。第一遍 `0x239CA04` 先调用 setter，`0x239CA09` 扣 remaining，
`0x239CA0C/0F` 才检测并跳出。两遍之间 `0x239CA26/29` 只对**负** remaining 跳过第二遍；
恰好零也会进入。第二遍对每个解析成功者执行：

```text
allocated_raw = min(remaining_raw, selected_count * 100000)
whole         = trunc_toward_zero(allocated_raw / 100000)
0x23D3090(component, int32(setter_base - whole))
remaining_raw = signed64(remaining_raw - allocated_raw)
if remaining_raw <= 0: stop second pass
```

第二遍的 `0x239CAA2 → 0x239CAA7 → 0x239CAAA/AD` 同样是**先写后检查**，所以“零剩余
自动跳过整个第二遍”“负 hard raw 在第一遍之前返回”两句旧说法均不成立。最终
`0x239CACC` 调 `0x239BAD0` 重算聚合。`0x23D3090` 本身可能依条件进一步清零
`max/current`，详见[setter 静态边界](combat-component-writeback-and-terminal-reset-static-2026-09-27.md)；
上面的计算式只描述传给 setter 的值，不承诺所有 guard 下最终 component 恰好等于该值。

正常正数且乘法/中间值不溢出的域内，第一遍 candidate 等于 `min(original_hard_raw, cap_raw)`，
每个 component 的整数减员独立向零截整；不足一人的 raw 尾数不会自动补给最后一个 component。
`low64` 的乘法、fixed-point division 的多路溢出处理和 setter 的条件清零在极值域仍须按原指令
处理，不能把上式简化成无限精度的实数比例。

## 可重算的边界向量和镜像修复

这些是**静态推演向量，并非实机样本**。普通向量：components 的 `(max,current)` 依次是
`(3,3),(5,5)`，hard 为 `456516` raw，第一遍先分给前者 `300000` raw / 3 人，
再分后者 `156516` raw / 1 人；最终 current 为 `(0,4)`，`56516` raw 仅留在 Q100000
账上。此向量在既有单测中已覆盖。

边界向量：第一个 component `(max=2,current=0,kind=3)`，第二个 `(5,5)`，
hard=`150000` raw。第一遍第一个选用容量 `200000`、setter base `0`，分得
`150000` raw / 1 人并写 current=`-1`，remaining=`0`。第二遍依然进入；第一个现在
selected count=`-1`、容量=`-100000`，所以 `min(0,-100000)=-100000` raw，
`whole=-1`，setter 将 current 写回 `0`，remaining=`100000`。然后第二个分得
`100000` raw / 1 人，写 current=`4`。这些 setter 值都小于相应 max，按
`0x23D3090` 的已知 guard 不走额外清零。最终 `(0,4)`，但这组输入是否会由真实战斗生成未知。

智能体的 [`allocate_hard_casualties_to_components()`](../../ck3_autonomous_player/src/xar_autoplayer/simulation/combat_core.py)
此前在**每遍循环顶部**提前检测 `remaining<=0`，与原版顺序相反；现移到每次 setter/remaining
更新之后，并增加负 hard 和零剩余特殊编码回归测试。此 Python 函数的输入是已解析的 component
列表，不包含 vcall、Regiment 聚合以及 setter 的链接对象 guard；它是数值镜像，不应把这两组静态
向量或单测通过写成真实战斗日的原生前后状态校准。

## 仍需实机闭合

要判断边界对整场胜率的真实影响，需在同一 combat tick 的 `0x23CDFD5` 调用及
`0x239C840` 返回两侧采集 full RegimentID、descriptor 次序、`kind/max/current`、hard raw、
setter guard 结果和聚合重算后的值，并与原版 EXE/DLL hash 及 UI 可见兵团对应。
目前没有这样的原版前后值；视频或策略只能把这里标为精确版本的静态规则，不能宣称特殊向量在
玩家正常战斗中发生过，也不能用它给某一兵种贴“优先死亡”的标签。
