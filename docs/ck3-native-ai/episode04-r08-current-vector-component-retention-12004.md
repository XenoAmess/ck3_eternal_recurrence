# E04 R08：现有十槽向量与两个 rate 分量的保留边界（1.20.0.4）

这是供游玩与研究智能体复用的离线知识，未实现新接口，未授予 R08、动态验收或 ABC 分子 credit。研究机器 `machine_id: desktop-3fevhd2-1c74096080`，实际研究时间 `2026-10-20T08:50:06.341494Z`；源码基线 `31ff77a0f07fb21f528c88e56314cbb093972703`。打包时间见[来源索引](evidence/episode04-r08-vector-component-retention-20261020/source-index.json)。游戏来源限定 1.20.0.4 / Steam build25734779 / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；这不是当前安装或运行时资格。

## 游玩智能体现在可以直接使用什么

现有 `ck3_query_war_cash_current_resources_private_v1(expected_revision=F.revision)` 已保留完整的十个 signed64 槽。查询须满足当场公共 host 的 `war_cash_queries=true`、当前 frame/revision 和已有资源准入；本研究没有调用它。只需 slot9 时，不需要新增 getter、SDK 参数或采样 enable。

| 当前 cash DTO 内的字段 | 已证语义 | 使用限制 |
| --- | --- | --- |
| `/military_expenses/current/resource_raw_native` | 当前情景完整十槽向量 | 严格十项 signed64；不可用不能当十个已观测零 |
| 同数组 `[0]` | 与 `gold_raw` 一致 | rate 观测，不是维护实付 |
| 同数组 `[6]` | 与 `treasury_raw` 一致 | rate 观测，不是付款账户或实付 |
| 同数组 `[9]` | 完整传输的第十槽 | 业务资源名仍未知 |

`current` 与 `all_raised` 是替代情景，不能相加。普通查询不自动启用 payment sampling。当前返回的是两次原生 rate 分量合并后的总向量，没有两个独立分量或原生调用内的 invocation token。

实现依据：`.4` 的 [BindWarCashCurrentImage](../../ck3_autonomous_player/native_bridge/src/ck3_12004_war_cash_claim_terms.cpp) 绑定 `0x2C13F60`，复用 [Current / ReadActor](../../ck3_autonomous_player/native_bridge/src/ck3_12003_war_cash_current_reader.cpp) 的十项存储；[serializer](../../ck3_autonomous_player/native_bridge/src/ck3_12003_war_cash_current_serializer.cpp) 输出全部十项，[Python normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_cash_private_transport_v1.py) 检查长度、signed64、actor/war/time basis/month/scale100000 并保留全数组。共享 reader 文件名含 `12003` 不表示采用 `.3` 的旧地址绑定。

不要把另一种 cost ordinal 的 `barter_goods`、HUD currency 名或支付 gateway 的 selector4 名称迁到这里。slot9 与 selector4 的业务枚举名仍各自未知；相邻 token、数值 ordinal 和钱包净差均不补足语义。

## 已有真实小样本排除了一个直接替换

[历史 R213 投影](evidence/episode04-r08-readonly-sufficiency-12004/actual-projection.json)（原 R0208，`machine_id: desktop-3fevhd2-1c74096080`，观测 `2026-10-18T22:42:31.611233Z`，PID27056 / generation1 / actor33388 / date53148408 / native revision136）保留：

```text
current.resource_raw_native = [386622,0,0,0,0,0,0,0,0,0]
c = 310999; d = 0; c+d = 310999
slot9 = 0; c != slot9; c+d != slot9
```

零值来自 available 数组。这只排除该历史包中“c 或 c+d 与 slot9 原样数值相同”的替换。rate 与 raw context 是同包内按顺序读取，未证明原子快照、单位换算、同一次结算或因果。既有 sufficiency helper 原先只比较 gold 槽0。本次重读仓库投影，没有重读原始 5159B cash 文件；其原路径、大小与 SHA 在索引中按历史出处保留。此样本没有付款机会或自然日推进，不能据此报告维护实付、付款者或 cadence，也不能外推为当前场状态。

## 两个分量的精确源码边界

已保留的 getter `[0x2C13F60,0x2C142AE)` 共846B，原始字节 SHA-256 `20f7733ca5f0c06b12c85d7844fb2225cd95aeb9bc700b0b3d329bcd82ab555d`。来源索引内嵌完整字节、211个指令边界及关键指令核对，不依赖旧 C 盘路径才能复核。本次没有读取或重 hash EXE。

下面仅适用于原始 `breakdown=null` 路由。RBX 是原输出80B，R14 是原 Character，RDI 是原 breakdown。

| 原生步骤 | 关键位置 | 能保留的事实 |
| --- | --- | --- |
| 首次调用 `0x28C43A0` | CALL `0x2C141D7`；`0x2C141DC` 将返回 RAX 存入 RDX | 第一分量的实际返回向量指针 |
| 第一轮十槽相加完成 | **执行 `0x2C1422D` 之前** | RDX 指向第一分量，RBX 包含第一累计向量；第二次调用尚未开始 |
| 第二次调用 `0x2C142B0` | CALL `0x2C14238`；`0x2C1423D` 将返回 RAX 存入 RDX | 第二分量的实际返回向量指针 |
| 第二轮十槽相加完成 | **执行 `0x2C1428E` 之前** | RDX 指向第二分量，RBX 包含总向量；尚未恢复栈帧 |

两个调用复用 `RSP+0x70` 的同一80B临时区。只在末尾读取它，只保留了第二分量；用总向量减它得到的第一分量是推算，不能称为独立实际观测。两次 merge 区内没有 CALL。分量机制的既有范围分别见 [28C43A0](episode04-maintenance-callee-28c43a0-12004.md) 与 [2C142B0](episode04-maintenance-callee-2c142b0-12004.md)，不能由 rate 组成直接命名军事实付类别。

## 下一合法观测与施工入口

业务优先仍是[当前 c/d writer 入口](episode04-r08-b-next-20261020.md)：按当场准入保留实际命中后的 PC、c/d 原始生产者、同钱包应用与账户/日历来源。现有 fixed-four-field writer observer 不支持上述两个执行 PC，不能更换 argv 冒充已有能力。rate 分量拆分不能替代 c/d writer，也不增加 R06/R04 前置条件。

若独立研究确实需要拆分 rate，可从 `ck3_12003_war_cash_current_reader.cpp::Current` 与精确 `.4` binder 施工，保留**它既有那一次原生调用**的两个固定边界；不要额外调用 getter。建议的可选子对象名 `current_components_raw_v1` 仅是施工名，现有 SDK 没有 component-mode 参数，尚未实现、构建或执行，也没有当前 A40/A41 资格。

最小合同为：

1. 由 `Current` wrapper 为原调用持有有作用域的 invocation token；同一 token、thread、frame、actor、out80 与固定 PC 顺序都要匹配。日期、线程或复用栈地址相同不能代替 token。
2. 在第一个固定点读实际 A80 与第一累计80，在第二点读实际 B80 与总量80。每份80B在固定点双读且完全相同；最多640B、每次 query 保留一条记录。检查原返回指针、输出与临时区不重叠、RDI为0及完整来源字节范围。
3. 保留全部 signed64（包括0和负数），逐槽要求 `A == 第一累计` 与 `总量[i] == wrap_i64(A[i]+B[i])`。缺点、读不稳定、身份或调用变化、组合不合等均保留 unavailable，不补推算分量。
4. 完成新的 native source/binding、cold/runtime 资格后才可部署。输出名只用 `source_callee_28C43A0_raw` 与 `source_callee_2C142B0_raw`，不预授付款语义。

## 仍然未知与停止重复的边界

维护军事分量的实付数额、payer、cadence、c/d producer store、slot9 资源名及 selector4 资源名均未闭。不得把钱包净差、同值 copy、rate 相加或 getter ACK 写成维护实付。[parent order](episode04-r08-settlement-parent-order-12004.md) 已证同次 parent 内结算在后续 getter 之前；不能用晚 getter 正向生成早结算输入，也不能推成全局无关联。现有研究已足以复用十槽读取和两个 callee 边界，下一步不需要重复大扫 EXE、零候选 xref 扫描或重新导出已保留 callee。
