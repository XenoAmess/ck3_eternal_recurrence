# CK3 1.20.0.4 MilitaryView 补员按钮：实际分派与下一 callback 入口

本专题把原版 GUI 语义、实际 `.4` 按钮分派器和可读取的 callback 目标分开记录。当前尚未取得 `.4` 的 `MilitaryView.OnMilitaryReinforcementClick` 命名注册记录、实际业务 callback RVA 或该 callback 的开关写回指令。不能以通用 ButtonBase RVA、相似旧版函数或查询 ACK 代替这条链。

本轮机器 `machine_id: desktop-3fevhd2-1c74096080`，实际读取时间 `2026-10-15T18:38Z` 至 `18:40Z`；实际回执内有每次精确 UTC。研究基线 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`，外置根 `C:/ck3-e04-resume-20261015-a01/high-parallel-refill-callback-a08`。这些事实仅适用于该机器、该次观察。没有 SDK、桌面、游戏查询/动作、注入、游戏 attach、新 EXE 构建或执行。

## 来源与有限读取

实际 `.4` 冻结 EXE 为 `C:/ck3-e04-resume-20261015-a01/frozen-game-12004/ck3.exe`，101040248 字节，既有完整 SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。身份回执 `IDENTITY.actual.json` SHA-256 `15ad8093ca23930d7d440752518d3ce89097dec1b00fe234a5115011782b62b9`。本轮复核身份与 stat，没有重读/重 hash 整个 EXE。

已有 `.4` [通用 GUI 迁移](generic-gui-default-path-migration-12004.md)和 `ck3_12004_generic_gui.hpp` 精确给出 ButtonBase 槽13目标 `0x3AA0D20`。经有向 source-plan、check/render 和实际 `.pdata`/unwind 元数据后，读取两个完整函数体：

| 实际范围（结束不含） | 字节 | 原字节 SHA-256 | 入口依据 |
| --- | ---: | --- | --- |
| `3AA0D20..3AA0DC2` | 162 | `92e9d17640095225eba355347cc012e611bfe98a0aaf32a47f7fcf0fe6e3f17d` | 已有 `.4` 槽13绑定 |
| `3A9FA30..3A9FC45` | 533 | `77a7f891988e7619ab99aa536bff6d5f2d9128ff4f31d86a7dfe3275e501b773` | 前函数 `3AA0D9F: E8 8C EC FF FF` 的实际 direct call |

新读取合计函数体 695 字节、元数据 268 字节，限额函数体4096/元数据1024字节。外置保留 `.bin/.asm/.actual.json`、四个计划与 check/render、每次 `READ-*.actual.json` 的实际 argv/读段/SHA；首个计划因缺少 `open_question` 在读取前被 check 拒绝，原 RED 与修正后的 GREEN 均保留。没有扫描字符串/全 `.text`、按旧 RVA 读取或展开无关 callee。

旧 `verify_war_cash_gui_rtti_candidate.py`、`verify_war_cash_military_view_candidate.py` 的 SHA `2D00FF...DB86` 属 **1.19.0.6**，不能称为1.20.0.3，也不能授予本次 `.4` callback 资格。既有小根命名资料中未持有可信 `.4` MilitaryView 注册入口；这个结论限于已经检索的根，并非全机不存在。

## 原版语义与实际通用分派

本机实际 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game/gui/window_military.gui` 为111608字节，SHA-256 `4f5523d249c2e0a4d3c328d789ca375f154c2e102544782480936b4206c57eac`。第6行固定窗口名 `military_view`。第488/898行两个未命名 `button_checkbox_label` 的 onclick 都是 `[MilitaryView.OnMilitaryReinforcementClick]`；第493/903行 checked 都是 `[MilitaryView.IsMilitaryReinforcementsEnabled]`，文本 key 都是 `MONTHLY_REINFORCEMENT_COST_LABEL`。第一个父分支可见性取 `Not(HasRule('conditional_maa_refill'))`；第二个父分支取 `Not(IsType('landless_adventurer_government'))`。仅凭这个文件不能推导编译后 child_path，也不能把第一个可见按钮认作补员按钮。

`3AA0D20` 的标准点击分支检查 input `+10 == 0x1D` 且 widget `+D0` 的 bit1未置位；写入栈上零 DWORD。随后传 `RCX=widget`、`RDX=widget+3F8`、`R8=widget+338`、`R9=&zeroDWORD` 到 `3A9FA30`。其后的 widget `vtable+50` 调用不提供 MilitaryView 语义证明；其他输入支路、声音和 tail jump 没有在本轮展开。

`3A9FA30` 的 primary 有四个 `0x20` 大小描述符，data在 `+0`、count DWORD在 `+C`，运行游标/结束位置在 `+18/+1C`；各描述符分别适用 mode0、bit0、bit1、bit2。标准零 mode 只选择 primary第0组；其 count为零才选 fallback第0组。row stride `0x48`，callback对象在 row`+40`，对象虚表在 `+0`，调用槽在虚表`+10`。调用 ABI 是 **`RCX=callback_object`、`RDX=&widget_pointer`**，后者是指向 widget 指针的地址，不能传成裸 widget。实际 callsite 为 `3A9FA94/3A9FAF5/3A9FB55/3A9FBB1/3A9FC00`。这些函数没有提供 `OnMilitaryReinforcementClick` 的名字注册或业务写回。

## 可施工候选：复用现有固定窗口 census

外置相对 patch 为现有 `inspect-gui-window-tree-v1` 增加固定 `window_kind="military"`、固定根 `military_view`。它复用既有 owning-thread mailbox、命名窗口解析及2048行/64MiB上限。新 scope 仅接受 exact `.4` GUI ABI、实际 EXE SHA；不接受 caller指针、RVA、child_path、任意窗口名或 fixture函数替换。没有新增顶层 query、没有新动作。

查询 DTO/serializer/严格消费者已接通。每行先检查实际 widget虚表槽13是否精确等于 `.4 3AA0D20`；匹配才只读标准点击所选 primary/fallback第0组。每组最多256个 callback，输出每项连续 index、`callback_vtable_rva` 和 `callback_slot2_rva`。非 ButtonBase行明确为 `not_button_base`。callback对象和 row的 heap地址均不对外输出；虚表/目标必须在实际 image范围内。读取失败、越界、负count或过大count拒绝整次观察，不能伪造空列表。

JSON 的 `callback_binding_source_12004` 固定 EXE SHA、ButtonBase/组分派器 RVA及 input_modifier=0；每行 `standard_click_binding_12004` 保存 group和callback列表。严格消费者保留实际 child_path、顺序与新叶，拒绝旧版身份、修改mode、截断树、缺叶、非整数/越界RVA、跳号、假非按钮callback及新增method_name字段。结果显式 `callback_method_name_available=false`、`click_action_available=false`。消费者 SHA大小写与原生 serializer所用常量做交叉核对。

三个修改原生 TU `/Zs` 实际退出0；8个新增 strict-consumer测试通过，包含有效primary/fallback及上述反例；相对 dcda `git apply --check` 退出0。这些验证没有执行原生候选，资格是 **SOURCE_ONLY**，不代表 MilitaryView语义、开关动作、实机query或业务后验已验收。

## 下一精确入口与动作后验

下一次获准现场先打开原版军务窗口，经上述只读 scope取得实际树和callback槽目标。保留实际 player/full ID、日期、query revision、模块身份、可见/可用行及原版source profile。未命名控件的 child_path需经原版profile或命名注册结果确认；不能从可见性或位置猜其语义。

对已确认补员 source控件，其实际 `callback_slot2_rva` 就是下一条精确元数据入口：仅查该 RVA所属 `.pdata`/unwind，再按实际完整body界限制定有限 plan读取wrapper；沿wrapper的实际 direct call/具名表达式记录定位 MilitaryView业务 callback，直到实际开关writer。不重复读取邻域或扫描全EXE。若该槽是多个表达式共用wrapper，只能授予wrapper身份，必须继续记录其具体receiver/表达式绑定，不能直接宣布它就是补员callback。

现成 `DispatchFixedGuiWidgetNativeV1` 可以在 source控件身份闭合后复用。它已有 exact `.4` shortcut manager路径、actualvtable/槽13、GUI context、可见可用、callback组、modal admission和 `3ABC4B0` 语义输入构造；下一动作应固定补员profile并在同owner线程重新解析/校验，而不开放任意child_path动作。调用 ACK保持 verification_pending。

开关读回复用 [episode04 refill应用](episode04-refill-application-12004.md) 的军队/Regi实际来源解析和 a07 `refill_permission_switch_v1`（a07候选需先合入）；它从真实 source Character `+1C0` 的 military组件读 `+4A9`，重核完整代际ID/Char magic/组件，非零为enabled。特殊definition分支需独立解析 `R+130/title` 与 `R+12C Character`，不能套玩家switch。未来普通点击后必须用更新query独立读回同实际来源owner的raw byte变化，才能证明开关已切换。当前尚无callback→writer源链，不能把reader、ACK或七槽net增长升级为 actual_ADD；actual物理 ADD `2A98B88` 仍是独立资格。

## 存储与交付边界

a08所有新文件限1MiB，计入Root active32MiB池及既有metadata17MiB子额，原截止 `2026-10-16T07:45:01.597Z` 不延长。闭场实际占用、容量、机器与patch/source SHA见 `DELIVERY.actual.json`；本轮仅外置写入。资料在截止前作为下一callback研究关键输入保护，届时由统一 [存储策略](../storage-retention-policy.md)复核继续用途，不能无限续存或把其他机器状态外推到本机。


## 2026-10-16 R0177：实际共用slot2的下一真实跳转

machine_id: `desktop-3fevhd2-1c74096080`。Root现场响应 `R0177/responses/013-a07-military-tree-before-open.json` 实际时间 `2026-10-15T20:04:08.912599Z`，832958B，SHA-256 `fe643e91cd66cf723ffad34dca66812231ff2b34bc08d9ea8fc31b042a6cac23`。完整树506行、military root存在且hidden；两原版source祖先下的外层group实际路径 `0/0/0/2/3/0/0/0`、`0/0/0/3/5/0/0/0`，都具有fallback callback slot2 `3AA30E0`。这是共用wrapper，不能命名为MilitaryView业务callback。内层checkbox的另一个slot2不作为业务callback入口。

原版 `gui/shared/buttons.gui` SHA-256 `88403785a1acdacc628730aaa101a04b2ae6293e74aa706a93e0e1695f3b1a0c` 第1313行证明 `button_checkbox_label` 是button_group，内含flowcontainer、button_checkbox和text_single。onclick在外层group，checked在内层checkbutton。常规group来源为 `tab_your_armies/footer`，另一个在provincial armies的footer；此来源匹配不替代具体表达式/receiver证明。

外置研究根 `C:/ck3-e04-resume-20261015-a01/refill-toggle-actual-next-a09`。actual3AA30E0元数据查询用108B发现不被pdata覆盖，RED回执保留。随后新的有限prefix计划通过check/render，从该actual入口逐字节解码，首unconditional jmp立即止；实际只读18B，不猜fullbody/邻域，不重读3AA0D20或3A9FA30。原字节为 `488BC1488D5110488B89F000000048FF6008`，SHA-256 `7a37683abfa5cb9317164e719bc14ba7cc067f79fee8e086267a11d8b18f3563`：

```asm
3AA30E0 mov rax, rcx
3AA30E3 lea rdx, [rcx+10]
3AA30E7 mov rcx, [rcx+F0]
3AA30EE jmp qword ptr [rax+8]
```

因此下一实际控制流目标在callback_object `+8`；callee的RCX来自对象`+F0`，RDX为对象`+10`参数块地址。receiver类型和参数块内部语义仍未知。不能继续猜callee RVA，也不能把此18B source prefix冒称有pdata/fullbody完整资格。

最小只读生产候选继续使用同一个military census。实际遍历前核对loaded18B source pin；仅当callback_slot2等于3AA30E0时读取对象`+8/+F0`，重读对象/vtable/entry/receiver保持一致。输出 `indirect_target_3aa30e0.native_target_8_rva` 与 `receiver_f0_present`，不输出heap指针、不读取未知参数块。DTO/serializer/strictconsumer已接通；source metadata另含固定thunk RVA及18B SHA。旧a07 source profile仍可读，但不能声称有新字段；新profile要求该thunk的每个row带完整新叶，其他handler禁止借其布局。loaded pin、读取/范围/稳定性失败拒绝观察。

新候选不增加工具、顶层query或action。两修改原生TU `/Zs` 实际退出0，10项新增严格消费者测试通过，并交叉核对actual18B等于native pin和消费者SHA；相对patch `git apply --check` 通过。这是SOURCE_ONLY，不代表新叶已在游戏运行。下一Root获准构建/现场读回 `native_target_8_rva` 后才对那个实际目标继续有限pdata/body研究；隐藏tree无需先打开窗口即可提供该source入口。Root016 Knights打开尝试因当前`.4` UI只支持army query/select而失败，不允许重放或放宽旧版RVA gate。

独立开关后验继续使用实际available Regi来源叶的完整身份。a09另有纯 `military_refill_switch_transition_12004.py` 候选和8个新测试，核same full persistent/sourceCharacter、来源引用/分支不变、after desired；模块不授dispatch、callback语义、动作或actualADD资格。当前游戏没有执行任何补员toggle。a09所有新输出限2MiB、计active32MiB池，原截止 `2026-10-16T07:45:01.597Z` 不延长。


## R0178 actual +8 后的表达式调用边（2026-10-16）

机器 `desktop-3fevhd2-1c74096080`；Root 的 R0178/a08 实际只读时间
`2026-10-15T21:40:02.225461Z`，native/runtime source 均为
`b42afbbd85df3802b1fa6222f7aac403c2adf735`。原军务 opener 已由 Root 独立
after-read 证实 `military_view` effective_visible；本研究未提交点击。

两处来源结构对应的补员外层 group 实际 `+8` 都为 **`3A9F960`**，
并非业务 setter。有限计划先 check/render，再查实际 pdata 并取得完整
`3A9F960`194B → `3AC38C0`927B → `3E4C090`406B。
加上此前18B入口，a09累计函数1545B、metadata492B，未扫描字符串/邻域，
没有展开类型、容器或分配 helper。字节、SHA、实际 extent、Root原件 pin 见
[精确来源记录](evidence/military-refill-expression-call-chain-12004.json)。

`3AA30E0` 先把 callback+10 传作参数块。`3A9F960` 包装 callback+F0 的 typed
上下文后，真实调用 `3AC38C0`；后者从该参数块准备变量/参数再调用 `3E4C090`。
因此字段偏移以 **block=callback+10** 计：

| 该次 evaluator 实际读取 | 来源语义 |
|---|---|
| block+18 / signed count+24 | 24B receiver-chain；每项 typeID+0、kind+4、函数+8、userdata+10 |
| block+30 / +34 / +38 / +40 | 最终 typeID、kind、函数、userdata；只在 kind3或4 时调用最终函数 |
| block+48 / +4C | 期待 receiver typeID 和 raw flag；flag参与最终 null receiver 分支 |

所以 **实际下一业务函数指针位于 callback+48（block+38）**；receiver-chain
函数也必须保持逐项顺序，不能跳过链而假定 callback+F0 就是 Character。
这些函数尚未由当前 a08 publisher 发布，不能从 generic +8 命名
`MilitaryView.OnMilitaryReinforcementClick`，也未证明哪一 store 写4A9。

后续候选复用同一个 `inspect-gui-window-tree-v1(window_kind="military")`：
仅在 slot2=3AA30E0 且 +8=3A9F960、三段实际代码字节 pin 均通过时，增加
`indirect_target_3aa30e0.expression_3a9f960` 只读 scalar 子叶。
最多16条 receiver-chain，函数只输出模块RVA，userdata只输出present；全字段和
chain pointer重复读回、再复核 callback对象/vtable/+8/+F0稳定性。旧 V1/V2
source profile可继续消费，新 profile要求准确子叶，缺失/越界保留 unavailable。
这不是任意指针读取或执行入口；method/action available仍false。

下一步必须由新匹配 native+Python 查询取得这些实际 chain/final RVA，再沿该
真实来源边作有限源码验证。开关动作仍需 source-qualified固定控件、owner-thread
单次派发和来源 Character+4A9 的独立新查询；不直接改字节，不影响R07两臂原开关。

此后续 source-only 候选的8项新增严格消费检查、两个修改TU的 `/Zs` 均通过；
没有重跑旧测试，没有新EXE或实机动作，尚需未来成对native/Python build后的实际只读回执。


R0180 的实际补员 final target 与完整 28B 包装函数已补入 [1303D40 专题](military-refill-finaltarget-1303d40-12004.md)；唯一下一源码入口为实际 call `12FF8D0`，未执行开关。
