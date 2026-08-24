# CK3 1.19.0.6 原生 Merge Armies 契约

## 结论与证据边界

本契约只适用于 CK3 `1.19.0.6`、`ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
本轮只读取了该 exe 与原版 GUI，未连接、注入、启动或操作 CK3。命令 ABI、完整
validator、clone、析构和 executor 均已静态闭合；native fixture 已覆盖构造、数组
深拷贝、validator 拒绝、queue clone、原对象清理和 generation/控制权拒绝。真实存档
执行与后置条件仍标为**未实机**。

对“同省、非战斗的两支玩家军能否安全合并”的精确回答是：命令对象的内存所有权和
提交生命周期已经闭合；若两个 public CUnitID 不同、均由当前玩家控制，并通过原版
完整 validator，且 common submit wrapper 返回 `true`，则可以安全返回 `merge_submitted`。但“同省、非战斗”本身并不充分：
目的军还可能被撤退、移动锁或非法掠夺状态拦截，两军还必须同属陆军或同属海军。
本适配器不猜这些规则，而是把固定的一对 ID 交给原版 validator。

## 稳定公共契约

- capability：`game.command.merge-armies-N-with-N`
- 唯一合法 step：
  `merge-armies-<destination public CUnitID>-with-<source public CUnitID>`
- 两个 ID 必须是完整的正十进制 `int32`，不得带符号、空白、尾缀、第二个分隔符或
  溢出；两者必须不同。
- 两个 ID 都来自 `Snapshot.player_armies[].army_id`，即 generation-bearing public
  `CUnitID`。不得把 `CUnit+0x178` 的内部 `CArmyID` 传入该命令。
- bridge 固定原生 source array 的 `count=1`。原版命令支持批量选择，但公共能力
  刻意只提交一对军队，消除“至少一个 source 可用便整体通过、executor 再跳过无效
  source”的部分成功语义。
- native 同步唯一 typed success 是 `merge_submitted`。它只证明本轮重新读取状态、控制权预检、
  原版完整 validator 和队列提交都成功，不声称 source 已在同一响应中消失；Python driver 可依据下文严格的
  单次 immediate snapshot 后置条件，把上层 `war_action.status` 提升为 `merge_applied`，但不改变 native 回执。
- common submit wrapper 返回 `false` 时明确返回 `submission_failed`，不把被 locked queue 拒绝并清理的 clone
  误报为已提交。

## 原版 GUI 与命令对象

原版 `game/gui/window_army.gui` 使用：

- enabled：`[ArmyWindow.CanMerge]`
- tooltip：`[ArmyWindow.BuildMergeTooltip]`
- onclick：`[ArmyWindow.MergeSelected]`

reflection thunk RVA `0x1241FD0` 进入 player action RVA `0xC71B10`。GUI 从当前目的
`CArmy` 读取 `CArmy+0x124` 的 public `CUnitID`，并从选择列表移除目的 ID，再把其余
public `CUnitID` 组成 source array。它不是两个 `CArmyID` 的命令，也不是只能接受一军
的原生命令；“一对一”是 bridge 的稳定公共收窄。

`CMergeUnitsCommand` 的 exact-build ABI：

| 项目 | 值 |
| --- | --- |
| RTTI TypeDescriptor | `0x54CDE68` |
| primary COL / vtable | `0x496F270` / `0x432D3C8` |
| secondary COL / vtable | `0x496F298` / `0x432D398` |
| 大小 | `0x40` |
| player kind | `+0x20 = 1` |
| destination | `+0x24`，public full-generation `CUnitID` |
| source data | `+0x28`，public `CUnitID*` |
| source capacity / count | `+0x30 / +0x34`，`int32` |
| source allocator | `+0x38`，allocator object pointer |
| serializer | `0x26BA140`；kind/destination/source tags `0x340A/0x6B/0x27F8` |
| type ID | `0x2FA1`，RVA `0x26C2770` |

## 数组所有权与唯一安全生命周期

source array 没有 borrowed、inline-buffer 或 ownership 位。若 `+0x28 != nullptr`，
析构一定经 allocator 的 free vfunc 释放它。因此绝不能把栈上 `source CUnitID` 的地址
直接写进 `+0x28`，也不采用“析构前 detach”这种非原版所有权路径。

bridge 使用原版 canonical 生命周期：

1. 调用零参 factory `0x26C6CE0()`。它以 engine allocator 创建 `0x40` 命令，写入
   正确双 vtable，清空 `+0x28/+0x30/+0x34`，并把 `+0x38` 初始化为
   `base+0x4FEADE0`。
2. 写 `kind=1` 与 destination public `CUnitID`。
3. 对一个局部 `int32 source` 调用
   `0x975ED0(command+0x28, 0, &source, &source+1)`。该 helper 经 allocator 分配
   元素缓冲并同步复制，命令不会借用局部地址。
4. 调用 object validator `0x26BA050(command, nullptr)`。
5. 调用 common submit wrapper `0x973E00(manager, command, 0x0E)`。wrapper 在返回前
   经 primary vtable `+0x40` 调用 deep clone `0x26C26B0`；clone 为自己的 source
   array 再次调用 `0x975ED0`，不与原对象 alias。wrapper 原样返回 locked queue 的 `bool`：
   `true` 才表示接受，`false` 表示 clone 已由队列拒绝并清理。
6. 所有成功和失败出口只调用一次 deleting destructor
   `0x26B5330(command, 1)`。它先经 `0xA7E370` 释放 source buffer，再释放
   factory 创建的 `0x40` 对象。

fixture 用单独 heap buffer 模拟 factory/range-copy，并在 submit 时把 source 内容复制
到独立 queued storage；随后 poison/free 原 buffer，仍能读到 queued source ID。这一
断言防止把普通 `memcpy 0x40` 误当 deep clone，也防止 destructor free 栈指针；另一路 fixture
令 submit wrapper 返回 `false`，证明结果为 `submission_failed` 且原 factory 对象及 source buffer 仍只清理一次。

## 完整 validator 的责任边界

wrapper `0x26BA050(command,error)` 先按完整 generation 解析 destination CUnit，解析
其 owner Character 并执行 player kind gate `0x26B26A0(owner,1)`，再 tail-call
`0x2947D10(destination CUnitID, source array, error)`。

静态确认的完整 gates 包括：

- destination 与 source 均须解析到当前 live component；
- destination 不得在战斗；
- destination 不得撤退，不得处于已承诺的 movement-lock 阶段；
- destination 若为 raid，必须满足原版领土条件；
- source 与 destination 必须是不同 `CArmy`；
- 两军当前 ProvinceID 必须完全相同；
- source 不得在战斗；
- 两军 owner 必须是同一个完整 generation-bearing CharacterID；
- 两军 land/naval mode 必须相同；
- source array 中至少有一项兼容。

原版 validator 没有显式的“必须在战争中”或“不得正在围城” gate。bridge 只提前检查
两个 public ID 都在本轮 `player_armies` 中且 `controllable=true`；同省、战斗、撤退、
移动、掠夺、海陆模式等仍全部交给原版完整 validator。由于公共 count 固定为 1，
“至少一项兼容”在公共语义上正好等价于这一对军队通过，不会出现批量部分成功。

## Executor 与后置条件

secondary executor RVA `0x26B9F60` 进入 bulk core `0x2948680`。它保留
destination `CArmy/CUnit` 身份；对兼容 source 调用转移 core `0x224A460`，把其下属
unit/regiment 关联转入 destination，随后销毁 source `CArmy` 并移除 source `CUnit`。

因此一次 paused-safe merge 的最小成功后置条件是：

1. destination public `CUnitID` 仍存在且仍由玩家控制；
2. source public `CUnitID` 不再存在；
3. 在没有外生同时变化的安全切片内，玩家军 public ID 集合等于提交前集合减去
   source，destination 不应换 ID；
4. destination owner 与 current ProvinceID 保持不变。

若 Merge 用作 `split-army-half` 的恢复配对，规划器应把原本需要保留的军队作为
destination。若该军正在围城，还要额外证明同一个 `active_siege_id` 仍存在、其
`besieging_army_id` 仍指向 destination，并且 siege work/progress 没有异常回退。
这些都是后续 snapshot postcondition，不得由 `merge_submitted` 猜测。本轮未在真实
存档执行 Merge，因此 source 实际消失与围城连续性仍是实机验收项。

## Python/MCP 生命周期

Python 仅接受 hello 中精确的 `game.command.merge-armies-N-with-N`。它为同一 ProvinceID 内 distinct、
`controllable=true` 的 public CUnit 生成两个方向的 ordered pair；已知 `in_combat/combat` 或
`retreating` 状态直接不广告，普通 moving 不被当作 movement-lock，后者仍由上述 native validator 判定。
partial/unknown capability 以及 adapter 自报的 literal 都不会泄漏进 `action_steps`。两个 ID 的 builder/parser
同样要求完整 ASCII 正十进制 int32 且 distinct；合法 literal 被 `is_native_war_step` 固定为 pure-native，MCP
通过通用 `ck3_execute_step` 调用，不另建 Merge RPC。planner 当前刻意不自动选择 Merge。

driver 在 primitive 前保存排序后的可控 ID 集合及 destination/source 状态。primitive 后只读一次 immediate
snapshot，不等待也不推进：destination 必须保留同一 ID、owner 与 ProvinceID，source 必须完全消失，且 after
可控 ID 集合必须精确等于 before 减 source；三项同时成立才返回上层 `merge_applied`，否则一律
`merge_submitted`。目的军移动/换 owner、source 仅失去 controllable、额外新增或移除其他军都不会被误判为完成。
这些 Python/MCP 边界有确定性 unit fixture；仍没有新的 CK3 实机 Merge 声明。

## 版本迁移与解耦

公共 grammar、public CUnitID 语义、typed result 与 snapshot postcondition 属于稳定
层；上述 RVA、vtable、对象大小、allocator、数组布局、validator/clone/dtor/executor
属于 `ck3-1.19.0.6-msvc-x64` 私有层。exe hash 不匹配时适配器不得广告该 capability。

升级 CK3 时必须重新闭合并扫描：GUI reflection、RTTI/双 vtable、`0x40` 布局、
factory 的 allocator 初始化、range-copy 签名与 ownership、object validator 与完整
gates、同步 deep clone、deleting destructor、player flags `0x0E`、executor 的
destination-preserving/source-removal 语义。任何一项未闭合都应只让新版本适配器把
Merge 标为 unsupported；不得复用旧 RVA，也不得退化为栈指针或手写 allocator。

## 离线验收

- anchor scanner：`108` 个唯一签名、`15` 个 vtable 前缀（加入本能力后的冻结计数）；
- native fixture：固定 count 1、public/public payload、factory allocator、canonical
  range copy、完整 validator 调用、flags `0x0E`、deep-clone 后原 buffer 清理；
- negative fixture：相同 ID、过期 generation、destination/source 非玩家控制、native
  validator 拒绝、submit wrapper 返回 `false`；
- 未执行 CK3 live probe，未声称 gameplay postcondition 已实机通过。
