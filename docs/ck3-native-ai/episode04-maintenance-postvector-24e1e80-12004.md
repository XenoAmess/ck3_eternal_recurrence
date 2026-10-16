# 战争四期 R08：24E1E80 的向量修正与已付金额边界

**这条尾部修正已有完整 source，不能继续列为“函数体未持有”。** 本次先查重，复用[既有尾函数专题](war-cash-current-military-vector-tail-12004.md)和可移机 archive，并新鲜执行其 portable verifier，得到 `PORTABLE_SOURCE_AND_ALL_BRANCHES_PASS`。本轮新增 EXE/source bytes 为 **0**，没有重读映像或展开下一层 callee。

本次复核机器 `machine_id=desktop-3fevhd2-1c74096080`，时间和输入 SHA 见[小型来源清单](episode04-maintenance-postvector-24e1e80-12004.sources.json)。原 source 同属该机器，采集时间 `2026-10-15T23:41:35.042039+00:00`；固定 CK3 1.20.0.4 / Steam 25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本次只核仓库持有证据，不重新证明当前安装、Steam 状态、native 调用或现场资格。

## 已持 source 关闭了哪部分

唯一完整区间为 **`[24E1E80,24E215C)`，732 bytes / 211 指令**，SHA `32d27096049217575f2d92104d74cb42198bd53f8cbda90a053703e8810f4a05`，unwind unchained。17 条 jump 的 11 个唯一 target 全在函数内且落在指令边界，portable 校验同时重建了全部 source bytes、分支、四处显式输出 store，以及 caller 的真实 CALL。

已证第一向量来源[28C43A0](episode04-maintenance-callee-28c43a0-12004.md)在 `28C451A` 提交 `(out80,originalCharacter,0)`。尾函数的入口角色为 `RCX=out80`、`RDX=Character`、`R8=optional`。

| 已知路径 | 精确作用 |
| --- | --- |
| `24E1EA5→28C3AC0(Character)` | 取得用于 modifier 查表的返回对象。调用依旧是原函数自己的调用，本次没有再次调用它。 |
| `R8==0` | 第一向量 caller 明确传 0，因此跳过 `24E1ED1→242C370` 的 optional 路径。不能把未知非空 optional 分支强加为本路径的继续条件。 |
| key 查找 | 在返回对象的 `+68` unsigned-WORD key 数组、`+74` signed-DWORD count 中查 **`0xAE`**，命中从 `+D0` 对应 QWORD 数组取 raw；missing 使用 0。 |
| factor | 按原 fixedpoint/低 64-bit 规则处理 modifier，再加 100000，signed 结果为负时设 0。普通值域可理解为 `max(0,100000+modifier)`；大数分解和 wrap 仍须保留原合同，不能用无限精度表达式替换。 |
| 三槽修正 | 将原 `out80` 的槽 **0、6、7** 分别按同一个 factor 做 scale-100000 乘法后写回；显式 store 在 `24E2036`、`24E20B9`、`24E20E7/24E213B`。本体没有向另七槽显式 store。 |

所以，第一向量的最终值是“Army 缓存十槽的累加结果经过三个槽的 factor 修正”，不能再描述为未经处理的缓存之和。调用进入的具体 factor 是当前 modifier context 数据，不是当场已付金额。

## 28C3AC0 对象来源已有共享知识

尾函数旧专题当时没有展开 `28C3AC0`；仓库另一专题已持有它的 exact4 完整 220-byte source，故下一步无需因这个旧 unknown 再读同一 getter。复用[Native71 first-value source](native71-conception-first-value-12004.md)和[默认 context 合同](native71-conception-default-context-12004.md)：

- `Character+1B0→extension+258→Model` 非空且 `Model+8==Character` 时，返回 `C=Model+10`。
- extension/model 缺失或 owner 不符时，原函数进入 default 分支，涉及 guard/TLS 初始化，并选择默认 `C=5D67B90`。只读 observer 不可为了填值调用 initializer；guard completed 也不能单独证明默认容器仍存活。
- 这些是持有 source 的选择语义，不是当前局面的 fresh context observation。同一 Character 的历史 context 或另一次 getter 返回不能自动替代本次返回。

这次只交叉引用既有知识，没有展开 getter body、复跑历史 fixture，或给本机新增 Native71 运行资格。`0xAE` 的具体业务名称、值的 producer/刷新以及本次选择哪份 context 仍需对应来源，不能拿 Native71 使用的另一个 key `0xBF` 给它命名。

## 智能体与视频消费口径

**费率：** 现在可以按精确 image pin 保存“Unit/Army 缓存向量→context key AE→槽0/6/7的同因子修正”这一来源关系。实际模拟数值必须消费 qualified 当前 context 和原算术合同；本文不新增 calculator 或 native getter 调用。

**付款：** `out80+30` 是独立缓冲区的槽6，不能拼成 settlement 的 `*(Character+1C0)+30`。本体没有直读 settlement 四 raw、直写 payer wallet 或调用已知钱包 ADD/SUB；transitive 关系未证，不外推全引擎无关联。`maintenance_attribution=unclosed`，`paid_military_amount_raw=null`。

**周期：** modifier 选择、缓存读和 getter 发生时间没有证明调度或付款周期。仍只沿用既有公开 getter 的费率消费合同。

视频可解释“当前显示费率包含对向量三槽的 modifier 修正”；不能把这段 source 图配成“本月实际已经扣除这笔军费”。已付费用的下一份有效输入仍优先是 source-qualified settlement `context+28/+30` writer，加同次应用和实际 payer store，见[R08 缺口计划](episode04-r08-next-maintenance-attribution-12004.md)。另一向量 `2C142B0` 有独立 source，不由本记录替代。

本次只有小型复核记录；知识可移机使用，原采集机器的环境、容量和实机状态不可跨机外推。没有新增业务通过格或完成百分比，也没有延长旧重型写入例外。
