# 战争四期 R08：2C142B0 已持原件与当前可用边界

**`2C142B0` 的完整函数体已入库，无需重读 EXE。它产生当前军事费用 getter 的第二个十资源向量，尚未连接到已付军事维护费。** `maintenance_attribution=unclosed`，`paid_military_amount_raw=null`；本轮不增加实机通过数。

本次复核机器 `machine_id=desktop-3fevhd2-1c74096080`，观察时间 `2026-10-16T09:59:32.285190+00:00`，仓库基线 `20c7319b6964c80fa419540cf4e30852feff4810`。本次运行 `tools/ck3_live_run_id.py machine` 读回身份，只读既有仓库原件；没有新 EXE 字节、整 EXE hash、SDK、游戏、桌面、构建或注入。来源游戏身份为历史已绑定的 CK3 1.20.0.4 / Steam build 25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，不据此重验本次安装和运行环境。完整 pins 与有限复核结果见[小型来源清单](episode04-maintenance-callee-2c142b0-12004.sources.json)。

## 纠正过时的下一步

[下一份最小维护费证据](episode04-r08-next-maintenance-attribution-12004.md)及其引用的旧 getter inventory 仍称这两个 callee 的 body 未持有。针对本 lane 的 `2C142B0`，这项库存状态已经过时：

| 已有原件 | 当前可直接消费的内容 |
| --- | --- |
| [2C142B0 完整来源合同](acceptance/2026-10-16-current-military-vector2c142b0/SOURCE-CONTRACT.actual.json) | `[2C142B0,2C14D6F)`，2751B、650条指令；原件观察时间 `2026-10-15T23:20:17.216272+00:00`，来源机器与本次复核机器相同。 |
| [原始完整 asm](acceptance/2026-10-16-current-military-vector2c142b0/actual-function.asm)与[原始 bytes](acceptance/2026-10-16-current-military-vector2c142b0/actual-function.bin) | raw SHA `6b3b7a7a3228442366a29e2c15676e55b7364bd29268d3ec721a25a5a5608628`；本次逐行验证650条记录连续且拼接恰好等于完整 raw。 |
| [2C14D70 helper](war-cash-current-military-context-helper-12004.md) | 613B已持完整体，已补齐 `2C14440→2C14D70` 的 local closure / persistent / 双累加器关系。 |
| [262BE10 费用向量](war-cash-persistent-cost-vector-12004.md) | 660B已持完整体，已补齐 raw138 等清零门、实际来源角色、模式分派与后续因子处理的接口。 |

本次还将全部62个 jump 的原 bytes、relative target 和指令边界与既有 branch 原件核对；43个 CALL 记录匹配，直接 CALL 的 encoded target 全部匹配；62个跳转恰好各归入一个既有分支组。此验证只证明保存原件的内部一致性，不自动证明语义或业务验收。原合同中的“helper 未展开”描述其当时的范围；后来的独立来源已经补齐上述两个 helper，后续应沿链接读取，无须重复开源。

## 本体真实提供了哪些数据流

上游实际 `2C14238` 调用 ABI 为 `RCX=out80`、`RDX=Character`、`R8=optional breakdown`；公开 current query 传入 `R8=null`。入口将这三者分别保留为 `R13/R15/R12`。这是输出向量，不是付款事件。

| 路段 | 已证指令关系 | 对智能体的意义 |
| --- | --- | --- |
| 初始开关和 factor | `2C142E3` 解引用 `Character+1C0`，缺失则开关0，否则读 `+4A9`。`28C3AC0` 的返回表按 raw key `AE` 查值，缺失取0；加100000，再以 CMOVS 将负结果设0。 | 原始 key/返回对象的正式业务名称仍未知；不得改叫结算 c/d 或已付军费。 |
| 第一 cohort | 解引用 context 的 `+108` descriptor，逐个解析完整 generation 的 persistent FullID；`2C14440` 调已持 `2C14D70`。closure 的 `+10/+18` 是本次调用两个栈上十槽向量的地址。 | 累加器 A/B 有明确对象来源，不能与 context c/d 混名。 |
| 条件附加 cohort | `28C2DF0` 返回对象 raw byte `4D6==5` 时才展开 context `+1E0`，再遍历所解析对象 `+2D8/count+2E4` 的 persistent FullID。 | 这里只记录真实门槛和容器，raw byte 不能自行命名政府或兵种。 |
| persistent 候选费用 | `2C145BE` 的 `CanReplenish` 只参与某条 slot0 modifier 路径；`2C145D8/2C14685` 调 `262BE10(...,R8B=0,R9B=1)`，另一分支 `2C14708` 调 `(...,1,0)`。 | false 路径仍调用费用 getter；它既不证明零费，也不证明一定有正费用。 |
| 共同变换 | `2C1485F` 调 `30C1510(out64,original Character,0)`；`2C148A6/2C148DA` 用同一返回 raw factor 调 `18B5590`，分别处理 A/B 的拷贝。 | 本 scope 不展开这两个因子 callee，不能声称其完整公式已闭合。 |
| 返回 | null breakdown 在 `2C148E2` 直接跳到 `2C14CD2`；先复制变换后的 A，再逐槽 ADD 变换后的 B，`2C14D58` 返回原 out 指针。 | 可抽象记为 `out[i]=T(A,F)[i]+T(B,F)[i]`；T 保持原生未知变换标签，ADD 遵循原始64位机器运算。 |

这里的 `out+28/out+30`、stack vector `+28/+30` 与 `Regi+28` 是不同 receiver，均不能替代 `*(Character+1C0)+28/+30`。完整本体没有对后者或 `context+2C0/+2C8` 的直接 load/store；这一窄事实不排除未知 callee、其他调用者或跨轮刷新关系。

## 后续来源已经改变的解释

旧 `2C142B0` 与 `2C14D70` 合同将 `262BE10` 两个末参数写成 bool 形状。后来的完整 `262BE10` 来源证明 **R8B 是至少含0/1/2的 raw mode**：0按原生条件递归选择1或2，1选择 `30BD510`，其他非零（包括真实递归的2）选择 `30BD3C0`。正式枚举名仍未知；R9B 仍只按实际零/非零路径描述。

`262BE10` 最早的 raw138非零清零门发生在后续定义、来源角色与模式分派之前，因此该门成立时，该次该 getter 的十槽贡献为0。这个结果不能扩展为所有事件军、全部费用渠道、raw138终生不变或实际支付为0。R8B=0 的自动选择依据该 Regi 实际来源 Character 的开关，不能替换成 played Character 的开关；直接mode1/2还会绕过这段开关判断。

这些是既有后续来源的复用结论，本轮没有重新采集，也没有把额外源码覆盖率计成新动态验收。

## 当前剩余最小缺口

研究“已付军费”时，继续优先取得 **结算 c/d 的实际 writer 及业务输入**，随后连接同次应用与 payer wallet store，再核刷新/失效和真实调度周期。单独补 rate 的 callee 不会消除类别歧义；钱包 NET 也不能直接命名军事分量。

如果研究目标转为完整解释这个 rate 分量，现有来源下一层具名叶包括 `30BD510/30BD3C0` 的定义费率组合，以及外层共同 `30C1510/18B5590` 变换。它们分别回答费率组成和因子计算，不自动回答 c/d writer、付款或周期。本 lane 没有扩读它们，也不把这里的候选列表当成现场执行计划。

智能体可沿已持接口使用 current rate 情景、保留资源槽0/6及其来源分解；实际 paid 字段保持 null。视频可解释“当前费用向量的原生组成和补员条件”，不能配成“已证明本月实际扣除这些军费”的旁白。知识原件使用仓库相对链接供其他机器读取，机器安装、权限、容量和实机事实仍需目标机器重新验收。

本次仅新增两份小型 record，不复制大原件，不续期旧容量例外；按通用存储策略在 `2027-04-14` 复核整合价值。重型写入和旧外置原件的保留资格均不由本稿授予。
