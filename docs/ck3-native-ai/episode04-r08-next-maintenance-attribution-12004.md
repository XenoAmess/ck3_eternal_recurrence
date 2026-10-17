# 战争四期 R08：已付维护费归因的下一份最小证据（1.20.0.4）

本次只做离线交叉审阅，没有新增游戏、SDK、桌面、构建或 EXE 读取。审阅机器 `machine_id=desktop-3fevhd2-1c74096080`，2026-10-16 09:03–09:07 UTC，仓库基线 `20c7319b6964c80fa419540cf4e30852feff4810`。机器 ID 由当次 `tools/ck3_live_run_id.py machine` 读回；精确输入与审阅时间见[小型来源清单](episode04-r08-next-maintenance-attribution-12004.sources.json)。来源游戏身份仍为既有证据中的 1.20.0.4 / Steam 25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，本次没有重新验收安装或运行环境。

**缺的是军事分量的业务来源及它进入同一次付款的连接；钱包 NET、四 raw 算式、分配函数本身均不能补这条边。** 当前 `maintenance_attribution=unclosed`，已付军事维护费金额保持 `null`。本稿没有增加任何 R08 实机通过数或新百分比。

## 删掉已经完成的重复工作

| 已有证据 | 已闭合的窄事实 | 下一轮不用重复做什么 |
| --- | --- | --- |
| [R0174 真实父链](war-payment-r0174-actual-parent-source-12004.md) | 实际 kind2 ADD 的账户、四 raw、算式及真实 parent；同一 seq12 仅计一次 | 不再重建同一条闭包桥或把 day17/day21 计为两笔付款 |
| [R0178 writer 与695B函数](war-payment-r0178-writer-source-12004.md) | `context+18→2C0`、`+20→2C8` 两个同值物理写；copy 在首次 callee 前发生 | 不再反汇编两个已证 MOV，也不把新 copy trap 当成上游业务值刷新 |
| [435B allocator](war-payment-net-settlement-allocation-12004.md) | 负 NET 分支的整数比例计算；无 CALL、无游戏对象/类别输入 | 不再沿 allocator 找军费 producer，也不把两笔比例 SUB 强制加和成 deficit |
| [现有 getter 清单](acceptance/2026-10-16-r08-cash-getter-inventory/source-index.json) | current 月费率由两个实际 callee 的十资源输出相加；all-raised 是替代情景 | 不重复读取846B current getter，不把两种情景费率相加，也不寻找失效 FAMILYMAP |

这里的 `context=*(Character+1C0)`，a/b/c/d 分别为 `+2C0/+2C8/+28/+30`。R0178 只把 a/b 追到 `+18/+20`；c/d 的 writer、四项的业务名称和刷新/失效合同均未闭合。

## 三个需要分别关闭的缺口

1. **类别来源：** 真正产生 c/d 或其军事子分量的指令与输入来源。必须证明它表示哪种业务、哪个资源槽/账户和何种时间口径；仅见读取、相同数值或“maintenance”函数名不够。
2. **同次应用：** 上述分量怎样进入本次 `N=wrap(a-b-(c+d))`，以及实际 ADD/SUB 参数和 payer wallet store。正 NET 的钱包仍会净入账，军事分量可能已被抵消；金额应分别保存，不能再从净入账额扣一次军费。负 NET 的 F(c)/F(d) 还含分段整数舍入，不等于原 c/d 原样扣款。
3. **刷新与周期：** 该输入何时更新/清零/失效，哪次实际调度消费它。trap 的 QPC、入场 date、两个暂停帧跨日或跨月，以及一次 callback 的日期，均不能单独命名“每日/月结军费”。

一个新的限制推论是：**即使未来把 NET 和四项全部测准，缺口1仍不会自动消失。** 给 c/d 任意交换“军事/非军事”的未证标签，可以得到完全相同的当前 raw、N 和钱包记录；这说明现有观测在业务类别上不能唯一归因。该段是对现有证据可辨识性的推论，不是新的游戏机制事实。

另一个时间顺序限制是：已证父函数 `28F7840` 的原始角色scalar／当前十槽向量slot9差额分支位于 settlement 调用之后，因此该次后续调用不能作为同一 invocation 先前 ADD 的直接生产证据。**这也不能反证 getter 的 transitive side effect 或上一轮结果与下一轮输入完全无关**；目前没有足以建立或排除这种跨轮关系的来源。不要把局部先后顺序升级为全引擎无关联。

## 最小下一步：先拿一条能打破类别歧义的边

**有新的 c/d writer 原件时优先处理它。** 输入只需 Root 新场次里一个 source-qualified `+28` 或 `+30` trap：原始 raw 行、完整入场包的精确 pins、source image 身份、线程生命周期/恢复结果、实际寄存器/地址和 post-PC。随后仅按该 post-PC 做唯一包含函数的有限 source 计划；从完整入口解码，证明恰好结束于 post-PC 的写指令和有效写入地址。得到 copy 时继续保持 raw 命名，只把已证直接输入推进一层，不为了找标签展开无关 callee。

没有这份新 trap 时，可以并行准备以下两条窄路线；它们的产物回答不同问题，不能互相冒充完成：

| 路线 | 下一份精确输入/动作 | 成功时新增什么 | 停止位置 |
| --- | --- | --- | --- |
| 费率端 source | 完整来源已由本轮交叉归纳补齐：[28C43A0，402B](episode04-maintenance-callee-28c43a0-12004.md)、[2C142B0，2751B](episode04-maintenance-callee-2c142b0-12004.md)及[后处理24E1E80，732B](episode04-maintenance-postvector-24e1e80-12004.md)。前两者真实 callsite 为 `2C141D7` / `2C14238` | 可复用 Unit/Army full-generation、向量累加和后处理来源；2C142B0及后续 helper 早已在其他专题持有，不能继续按旧库存重读 | 早期 inventory 的 body 缺失描述已过时；费率端闭合不升级为 settlement producer、刷新周期或已付金额。仍优先 c/d 军事类别 writer→同次应用→付款账户 |
| 真实字段 writer | 在另一个获准的新鲜受控暂停窗口重建当前 Character/context 入场；复用已资格的四字段有限 write watch，关注是否出现 c/d 的新 post-PC | 取得新的物理 writer 候选，供下一次有限 source 解码 | 一个预先声明的有限窗口；指针/epoch/window/process改变即退役；超时/零命中只记无保留合格 trap，不延长到“等到有结果” |

这不是新的现场命令或自动执行授权。Root 仍需按当次 source/构建/机器/容量/独占资格安排。原窗口的 PID、地址、日期和资格不复用；2026-10-16 07:45:01.597 UTC 的旧容量例外已到期，本稿不续期、不承诺能继续重型写入。此次只有两份小型知识记录，未复制大原件或生成导出。

### 现有 observer 的具体接口边界

[native observer](../../ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/cold_observer.cpp) 的 `kOffsets`、[cold consumer](../../ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_cold.py) 和 [actual consumer](../../ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_actual.py) 共同冻结 `2C0/2C8/28/30`。既有文档提到将来观察 `+18/+20` 是新合同建议，**不能把它当成当前可用的重定向开关**；不得仅修改 argv/metadata 就声称观察了上游字段。当前 c/d 已在四槽中，追 c/d 不需要为了字段数量新加观察叶。

当前源码还有可选 `known_copy_caller_v1`：只在两个已证 copy post-PC `28A645B/28A6466`，利用已持有 prologue 的 frame 关系 `RSP+178=RBP+78` 读取稳定返回槽。它最多产生该 copy 的 caller 候选；不提供 c/d writer、actual writer date 或业务类别。旧 raw 缺该 leaf 保持缺失，不能补造。源码存在与它在某场 actual 被构建、启用并验收分别是独立事实；本次只读源码，不为该选项新增运行资格。

若上述 source 只给出 setter/copy 的调用者，记录真实 caller edge 后停止并重新列出最小输入；不要自动扩大为任意调度器扫描。若拿到军事类别来源，再决定是否需要[一个 settlement entry/return 叶](war-payment-net-settlement-allocation-12004.md)连接同次 NET/两笔 SUB；现在单独增加该叶只改善交易边界，仍关闭不了类别缺口。

## 给智能体与视频的直接消费口径

| 输入状态 | 智能体可用结论 | 视频可以说的范围 |
| --- | --- | --- |
| 当前/all-raised 月费率可用 | 保持两个独立情景；gold槽0与treasury槽6分别处理，按既有估计合同使用 | “这是当前/全部集结情景的月费率” |
| 同账户完整 callback + 四 raw 算式匹配 | 该笔钱包净变动与已观测 source 算式一致 | “本次真实净入账已对账” |
| 仅 c/d 新 writer 或 getter 数据流边 | 新增一条 source 关系，业务金额继续 unknown | “已定位某原始字段的写入/计算来源，军费归因待闭环” |
| producer类别 + 同次应用 + payer store闭合，周期尚未证 | 仅声明该次实际应用/付款及对应单位，不推广周期 | 展示这一次明确绑定的金额；不能配“每月固定扣除”的旁白 |
| 无 trap、无 callback、null raw、缓存净差0 | 无可用观测或有限区间未见记录 | 不能说“军费为零/没有收费/没有writer” |

当前 R08 可用的是来源合同、raw/NET 对账和替代费率估计边界；没有新的 qualified paid-maintenance 金额。影片需要“实际已付军费”镜头时，这一格继续未完成。所有小来源清单采用仓库相对路径，供其他机器和智能体阅读；安装、权限、进程与本次容量状态不能随知识文件迁移。

## 2026-10-16 追加：角色scalar／当前向量slot9差额的 raw resource4 应用链

[四包便携整合与精确原件](episode04-r08-rate-resource4-application-12004.md)补齐 `28F7840` 后段→`2BD3320`/current第十槽→`28B9950` selector4 与 `2BAFF30` 的静态分支：物理目标为 `context+4A0`，其中 gate 完整54B、scalar完整938B。原件内含精确hex/原始记录和stdlib离线验证器，跨机器不依赖来源C盘。keyAE只持有consumer合同，正式注册/具名writer/刷新仍未知。

这是本页上文“后续getter不能作为同次先前SETTLEMENT直接producer”的进一步来源，不改变历史实际NET/copy事实，也不证明传递副作用或跨轮刷新不存在。raw4/4A0未获金币或军事账户业务名，c/d军费来源→同次付款→payer/cadence仍未闭合，paid保持null；本次零实机/SDK/EXE读取，不增加R08或动态分子。来源与整合机器 `desktop-3fevhd2-1c74096080`，精确图像和各原始时间见链接；来源机器文件身份不可外推为目标机器运行资格。

2026-10-16来源现状补注：[SubC关联角色的单项贡献链](episode04-r08-contract-contributions-12004.md)已补齐递归scalar、0..100000 bounded raw、fixed-point贡献及两种输出写法；[独立审查](episode04-r08-semantic-attribution-audit-12004.md)区分了registry类型、实际CALL、人工数据流语义与业务推断。未知项继续具体列为业务名/单位、record初值/分配、并行等价及军事c/d→同次付款→payer/周期；不再把已持有body作为待重复读取任务。

## 2026-10-17：补齐 selector4 原 callback 的物理余额观察

[resource4 wallet context](war-payment-resource4-wallet-context-12004.md)将已证缺口落实为可复用代码：旧 gateway 的 `personal_gold_bits` 来自个人 extension+100，不能作为 context+4A0。新增可选 child 仅在既有 kind1/resource4 原回调内读取实际 context 与4A0前后端点；同 record 的 source/caller、sequence、event、session 与 owner 保持原关系。没有主动 getter、新 hook、付款动作或假 settlement token。

完整 producer-shaped wire 的生产 normalizer/consumer 焦点验证覆盖跨 owner、context变化、读取失败，以及个人金币不能替代4A0；源码已可复用，首次 coherent native build／正常冷载／实机仍 pending。物理端点不代表军事分类、正式币名、payer或cadence，paid继续null；下一实际c/d writer与同次付款连接仍按原计划取得，不把本次源码交付计入R08实付闭环。
