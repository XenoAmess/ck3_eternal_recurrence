# R228：正现金净结算已计入非零军费缓存

此条目供文件读取型 CK3 游玩智能体与后继开发者显式引用；它是知识候选，不是运行时策略或新 registry。普通 planner 不会自动加载本 Markdown。现有玩法入口的追加条目见同包的 `gameplay-v1.entry.patch`；采用者需把本专题与[精确来源索引](evidence/episode04-r228-net-settlement-20261021/source-index.json)一并交给代理。索引列出原始保留路径、字节数、SHA-256 与建议仓库映射；未发布的证据不能仅凭建议路径宣称可读。

机器：`desktop-3fevhd2-1c74096080`。实际窗口为 R0228；小投影观察时间 `2026-10-21T11:34:11.791692+00:00`，Root 限定采用时间 `2026-10-21T11:54:32Z`。原生来源为保留的 1.20.0.4 / build25734779 代码，EXE 来源 SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本条目没有重新检查安装或运行游戏。

## 这次实际证明了什么

R228 的一个已完成个人钱包 ADD 把非零军费缓存项计入了净额。该结论依赖钱包回调自身的原调用、前后余额、上下文字段和 unwind；不依赖把独立 postload 采样器强行拼成同一次调用。[实际结果](evidence/episode04-r228-net-settlement-20261021/observations/R08-POSTLOAD-RESULT.json)、[限定采用原件](evidence/episode04-r228-net-settlement-20261021/ROOT-R228-LIMITED-NET-SETTLEMENT-ADOPTION.actual-a01.json)的完整 pins 在来源索引。

| 同一钱包回调的实际输入 | raw 值 |
| --- | ---: |
| 个人余额 before → after | 25455910 → 25567301 |
| 实际 ADD amount / 余额差 | 111391 |
| a = X+2C0；b = X+2C8 | 384653；0 |
| c = X+28；d = X+30 | 273262；0 |
| N = a−b−c−d | 111391 |

上述四项在该钱包回调的 before/after 读回中均稳定，X 为 `"2856717694048"`。这里只报告 raw 单位，不补猜显示单位。原件 JSON 指针为 `/payment_before_disable/records/0`；其中 `original_called`、`original_returned` 为 true，角色 FullID=31254，原钱包 wrapper 与角色扩展的 +F8 相符，余额与 wrapper 余额一致。

钱包自身调用栈保留 `28A6D7C → 28F7939 → 3978BF8`：原生 parent 在 28F7934 调用结算，返回 28F7939；结算体入口 28A6D10 调用个人 ADD 285EE40，返回 28A6D7C。因此此条实际 ADD 是已包含 c 的净结算；无需再找到一条独立扣 273262 的 gross 军费 SUB，才能承认这条净额已计入军费缓存。此处不是“实际独立支付军费 273262”的结论。

## 原版来源如何限定字段含义

[正常生产者 a05](evidence/episode04-r08-task-construction-20261021/normal-producer-a05/FINDINGS.md)与[精确选段](evidence/episode04-r08-task-construction-20261021/normal-producer-a05/SELECTED.asm)表明：

- 28F6187 调用 28C43A0，28F619A 调用 2C142B0；两个向量的首个 QWORD 相加，在 **28F61A5 写 X+28**。现有 current-military 2C13F60 的 null-breakdown 路径用相同两个 getter、实参及 slot0。故 c 有正常军费向量 gold slot0 的来源关联，是缓存分量；这次没有直接观察 c 的写入时刻，也没有证明此 writer 独占。
- **28F6300 写 X+30** 的正常来源包括宫廷职位工资、宫廷开支与传奇开支。不能把 d 简写为借贷还款；a/b 也仍保留 raw 项身份，不改名为完整税收或完整总支出。
- [保留的完整结算体](acceptance/2026-10-15-maintenance-cache-source/inputs/saved-settlement-asm.asm)按 `N=wrap64(a-b-(c+d))` 分支。N>0 走个人 ADD；非正净额分支按 c、d 权重分摊净缺口，再走相应 SUB。该 SUB 不是 gross c，定点舍入与溢出也不能由无条件浮点比例公式替代。本次数值没有跨 signed64 溢出边界，表中整数等式可直接核对。

正常源链支持“c 是军费缓存分量”。它不保证未来任意时刻读取的 current-military 数值都等于这次缓存，也不补足实时刷新 epoch。来源 a05 的原始 3717 字节 producer spans 与完整函数 pins 均由 source-index 回链，不需要重新扫描整个 EXE。

## 给代理的 if / then 输入与动作规则

| 若当前证据是 | 可采用的结论与下一动作 |
| --- | --- |
| 只有钱包上涨，缺上下文与来源绑定 | 支出分解未知；**不能记军费为 0**。继续合法战争与事件处理，另取当前已支持的原生资金输入。 |
| 完成的同钱包回调有稳定四项、公式等于实际余额差，并有本条限定的 source/caller/unwind | 可记“这一条净结算已计入非零 c”；保存 raw 值、角色/进程代际、来源和时间。不要把 c 再当作本条已结算现金之外的一笔实际扣款。 |
| 只有 current military rate、军队预算或旧缓存 | 作为来源注明的预算输入；不是已付款、下次到期日或扣款周期。预测未来负担须另给时域、刷新时间与承诺来源。 |
| 军费刷新时间、承诺或应急雇佣资金不足以确认 | **只延后可选建设**，不停止合法战争处理。结合当前战况、失地风险、可及时到场的有效兵力和合法雇佣报价保留资金；不把缺字段/null 代填 0。 |
| 正在战争且评估新建、升级或地产 | 使用当前实际余额，另保留尚未结算的已知承诺、未来军费与可用雇佣应急资金；仅资金非常充裕时考虑可选建设。此规则不是数值阈值公式，不凭本条历史余额承诺当前可负担。 |
| 需通过取消建设或借款筹钱 | 只走现有合法原生资格、报价与动作；退款/到账后独立读钱包和项目/借款状态，不预支未知款项，不绕过原生可负担检查，未知提交结果不重放。 |
| postload 无命中、loaded context 为 null、journal 空、或一次 exact day 没有目标记录 | 均不证明军费为 0，也不保证下一天会调度玩家 parent。保留机会缺口，转到已有[调度输入合同](episode04-r08-player-parent-opportunity-input-contract-12004.md)，不盲目循环到命中。 |

“不要重复扣算本条净额中的 c”不等于从未来战争预算删掉军费。实际余额、已知未付承诺、未来预算与应急 reserve 应按各自时间和证据区分；未知 freshness 不能让战争停机，也不能变成无条件建设窗口。此候选只提供可引用守卫，没有声称运行 planner 已执行这些判断。

## 保留的未知与原始异常

1. 原 typed 结果仍为 `natural_parent_matches=false`、`qualified_records=0`；`paid_maintenance_raw`、`payer`、`cadence` 保持显式 null。观察到某角色个人钱包变化，不等于通用军费 payer 角色与 cadence 已闭合。
2. postload 原件只捕获加载后的 context/寄存器，**没有在那个时刻读取四个 slots**。四项来自钱包采样器；两者没有 shared invocation ID。相同线程/context 与来源兼容性不能冒充唯一跨采样器 join。有限净额结论使用的是钱包采样器自身 unwind。
3. legacy journal 原日期为十进制字符串 `"300064548703630608"`，是把 32 位日期读成 64 位造成的高位污染。low32=53146896 只作诊断，不能改写原件或倒授旧 typed 资格。实际窗口日期单独采用原生 before/after 的 **53146872→53146896**，不经该宽日期推导。
4. 实际 c 刷新 epoch、排他 writer、完整扣款归属/周期仍未知。不要把 source 支持的正常 writer 当作本场 writer 命中；不要把净额支出分摊当 gross 军费付款。
5. Root 此次仅限定采用净结算证据；**fullR08=false，正式主题 8/11，B=0/2，ABC=0/3**。本条不新增影片/人工镜头验收或普通 one-life 资格。小投影当时 Game 仍被 owner 持有，不能据投影宣称整场已关闭；闭场由 owner 独立回执说明。

## 阅读与复核顺序

文件型代理先读本条的 if/then，再核 source-index 的精确 pins、Root 限定采用及实际钱包记录；需要追溯字段时读 a05 与已保留完整结算体。原件含 legacy 大整数，直接读取时须用精确整数解析；本候选索引中的 FILETIME、指针与异常宽日期均用规范十进制字符串。缺失与显式 null 不能合并。

新机器可复用机制知识和代码；上述安装、实机、进程与采样事实仅属于记录中的机器/时点，不能外推本机通过。建议于 2026-10-28 复核这些来源是否仍供当前任务使用；本候选不复制 Save、完整 wire 或 EXE，不因引用而永久保护所有历史大件。

状态：source-only candidate；planner_autoload=false；plan/replay not applicable。当前文档没有新增原生请求或动作。

