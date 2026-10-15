# CK3 1.20.0.4：首个维护费向量的尾部因子处理24E1E80

已完整取得 `24E1E80..24E215C`，732B/211条指令，17个jump对应11个唯一target，全部位于本extent且落在完整指令边界；220Bmetadata/20reads，unchained。该函数直接按查表因子缩放独立80B输出缓冲区的槽0/6/7（offset0/30/38），没有直接把金额写进结算raw四字段或wallet。军事已付分量仍unknown，`maintenance_attribution=unclosed`。

精确游戏1.20.0.4 / Steam25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，机器desktop-3fevhd2-1c74096080。先有[首向量402B source](war-cash-current-military-first-vector-12004.md)的真实directcall `28C451A→24E1E80(out80B,originalCharacter,0)`，再新建有限plan读取唯一callee；没有整EXE哈希、xref、邻域或下游callee读取、SDK、桌面、注入、构建或native EXE执行。完整plan/actual原件及本篇全部source决策见[归档索引](acceptance/2026-10-16-current-military-tail24e1e80/ARCHIVE-INDEX.json)与[source合同](acceptance/2026-10-16-current-military-tail24e1e80/SOURCE-CONTRACT.actual.json)。

## 入参与两处call

entry RCX为out80B，保存到RBX；entry RDX是Character；entry R8是opaque可选第三参数，保存到RBP。`24E1EA5`以RCX=Character调用 `28C3AC0`，其返回对象保存为RDI。该对象类别没有展开，本轮只按本函数实际读取的key/count/value表描述它。

第三参数非空时，`24E1ED1`还会调用 `242C370`：RCX=第三参数、RDX=刚返回的对象、R8d=0xAE、R9d=100000，第五参数0。已证首向量caller传入第三参数0，这个call在该已知路径跳过。两处callee均未继续读取，不能从函数名字、ID常数或这一可选call猜测游戏对象类别。

## 查表与输出修改

函数从RDI+68取u16 key表、RDI+74取signed32 count，按源码的二分循环定位key0xAE。选定位置越界、key检查不通过或负index时走missing支，modifier取0；有效index从 `*(RDI+D0)[index]` 取signed64原值。key0xAE的脚本/业务名称不在本轮source内，继续unknown。

modifier经过源码fixedpoint乘法处理后加100000；加法后的signed结果为负时CMOVS将其设0。正常值域可写 `factor=max(0,100000+modifier_raw)`；精确机器规则包含64位wrap和大数分解，保留在source合同，不能宣称有额外上界或饱和。

| 原buffer槽 | 源中的显式store | 直接效果 |
| --- | --- | --- |
| 0 / offset0 |24E2036|旧值与factor作scale100000的signed fixedpoint乘法后写回|
| 6 / offset30 |24E20B9|同一factor处理该槽|
| 7 / offset38 |24E20E7或24E213B|正常/大数分支处理后写回|

另7槽在本体没有显式out store。大数路径采用max/min与商余拆分，不能把所有输入简写成无限精度 `old*factor/100000` 后宣称与机器完全相同。所有source路径、CMOV决策和17个jump的覆盖一一记录，未跳过反方向或missing case。

## 完整分支分组

- 可选第三参数：24E1EBE；count/二分循环：24E1EE8、24E1F0C。
- missing key/index：24E1F2B、24E1F31、24E1F3C；modifier正常/大数join：24E1F53、24E1FA3。
- 槽0正常/大数：24E1FC1、24E1FC6、24E1FE3；槽6：24E2044、24E2049、24E2066；槽7：24E20C8、24E20CD、24E20EB。

这些17个source跳转恰好覆盖原反汇编的所有jump指令。查表CMOVB、各fixedpoint分解CMOVL/G、factor下界CMOVS是额外的branchless条件选择，合同分别保留。source合同和原receipt同时保存每个jump的原bytes、target、fallthrough与指令边界，不把语义分组当作缺失branch的替代。

## 与结算、付款和Agent决策的关系

这里的out由已证caller提供局部80B向量；offset30是向量槽6，**不是** `*(Character+1C0)+30` 的结算term d。原函数没有直接dereference Character+1C0或调用已知wallet ADD/SUB，也没有直接读取/写入结算四raw字段。未展开的 `28C3AC0`及其他调用者关系保持未知，不能把“本体没有”扩大为全引擎没有任何关联。

这补齐了[首向量专题](war-cash-current-military-first-vector-12004.md)当时未读的尾函数本体，仍未取得它的factor业务名称，更没有得到该query rate如何写入settlement c/d的边。另一向量2C142B0由独立owner研究，本轮未读；不要把其局部累加器同名offset拼接到secondary context。

Agent可以按既有公开getter合同保留当前rate向量及其source分解；若另有估计策略必须保留估计标签。它不能将本次因子缩放、raw字段相等、无trap或[实际经济NET](war-payment-net-settlement-allocation-12004.md)改写成已付军费。`actual_military_applied_component`仍null，禁止与实际NET钱包变化重复扣账。

下一具名source候选只有 `28C3AC0(Character)` 的返回对象来源，以及在其他非空第三参数路径中的 `242C370`。本已知query路径优先前者；任何新读取仍需Root另授有限scope，本轮不自动扩展。

## 可移机原件

[小archive](acceptance/2026-10-16-current-military-tail24e1e80/originals.zip)保留完整732B/asm、所有branch、plan/check/read/执行回执、已持402B caller和静态身份/layout。历史绝对路径与executor只供阅读，不授新host执行或游戏入场资格；无EXE/DLL/媒体。

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-current-military-tail24e1e80/verify_repository.py
```

该stdlib入口只复核包/全部archive成员、连续source字节与17branch目标、caller directcall及三个out store原bytes，不执行游戏、历史executor或factor计算，也不闭合新的付款含义。
