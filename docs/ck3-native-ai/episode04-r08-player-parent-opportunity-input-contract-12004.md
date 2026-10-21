# exact_one_day 不保证玩家 Character 的维护 parent 机会（1.20.0.4）

本页供文件阅读型 CK3 游玩智能体与后继开发者显式引用。它是来源绑定的知识与输入合同，不是 native 安装、采样启用、调试器、推进或付款授权。研究机器 `machine_id: desktop-3fevhd2-1c74096080`；本轮只读复核自 `2026-10-21T01:35:19Z` 起，文档封存时间见[来源索引](evidence/episode04-r08-player-parent-opportunity-20261021/source-index.json)。本机稳定 ID 于文档准备时再次由 `tools/ck3_live_run_id.py machine` 实际读回。源码限定 CK3 1.20.0.4 / Steam build25734779 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；这些是来源身份，不是另一场或另一机器的安装、运行资格。

**精确推进一个自然日，只证明所用时钟合同的日期变化；它不保证玩家33388在观察窗内经过28F7840或28F785A。** “日期推进”“某批任务包含玩家”“玩家指令执行”“钱包应用”“已付军事维护费”是不同证据边。任一缺失保留 unknown，不填0，也不靠重复同一基线一天补成保证。

**已保存调用链与它的停止位置。** [完整父函数](acceptance/2026-10-16-r0174-maintenance-source/parent.complete.asm)15822B，文件 SHA `36eecdf78b4e958833f90ee903e1cd2cb607e0a1d5e8ea1adb0fc3e1d14f040f`；其1118B原始函数体位于[便携来源JSON](evidence/episode04-r08-parent-order-12004/PARENT-ORDER-SOURCE.actual.json)的 `/body_hex`，SHA `c115401592983d13238154255b9b2583fe85222089d71fde10f0e8aae6c9753c`。[SOURCE-SPANS](acceptance/2026-10-16-r0174-maintenance-source/SOURCE-SPANS.actual.json)保留各实际片段、地址和原字节；不需要重新导出或重哈希完整EXE。

| 已持有来源 | 精确PC或行 | 可以使用的事实 | 不能据此推出 |
| --- | --- | --- | --- |
| [scheduler.complete.asm](acceptance/2026-10-16-r0174-maintenance-source/scheduler.complete.asm) | 行12/14：290DC1F、290DC2B | 读取task+14的signed count、+1C的chunk | 这个task何时创建、为何包含玩家 |
| 同一469B dispatcher | 行17–19：290DC37..3F | task+0是原子cursor；领取start后，start>=count即退出 | task+0是vptr，或全世界角色数 |
| 同一dispatcher | 行34/76/81：290DC80、290DD21、290DD41 | 使用task+68的descriptor、task+70内联上下文，经3978C00执行索引闭包 | 已证明enqueue生产者、calendar或每日调度 |
| SOURCE-SPANS的specific-closure三个片段 | 290FD20..290FD3D | array[index]提供Character RDX，RCX是task+70，R8D是index，尾跳28F7840 | 数组总含当前玩家，或本日一定处理该index |
| parent.complete.asm | 行6–7、53–54 | 保存Character，读取+1C0；正常局部路径汇合到28F7934 CALL28A6D10 | 外层已经选择玩家，或必产生钱包记录 |

scheduler的469B原字节 SHA为 `bca5c9fc39bfdf32c08a634b40b537f895f5e2a39b764a25ec3c2bdc8cf74051`，对应ASM文件 SHA为 `8c8ac4d221abe022eaae29d91d2d6bdbdf1e964e655059773feb29058d61af4f`。count=0或数组不含33388，都是与所持局部源码一致的反模型；这不是声称实际游戏已经生成过这两种task。它们说明“推进一天必有玩家机会”不能从这些来源推导。

[权威对象修正](evidence/episode04-r08-task-dispatch-source-gap-12004/SOURCE-CORRECTION.final-a03.json)还区分了两种对象：3F90A5E的dispatch对象是 `*(job+38)`，3F90A6C取其vptr，3F90A6F调用slot+10。它与290DC00的index-task不能混作一个对象。实际virtual target、参数调整以及同实例的constructor/enqueue/calendar生产者仍无已闭合输入；旧worker栈返回地址只提供候选，不授权自动追扫。完整边界见[task-dispatch专题](episode04-r08-task-dispatch-source-gap-12004.md)。

**最小机会输入合同：A+B与C+D分别回答什么。**

- A：绑定同一machine、EXE/source、PID/创建代际、connection generation、GameState与玩家FullID的真实task/descriptor实例。当前cash的context或一个相近QPC不能代替这个实例。
- B：保留稳定的task count、chunk、数组、玩家index k及 `array[k]==该Character`，并绑定实际290FD20闭包。A+B至多说明某一批选择包含玩家；没有证明它何时执行。
- C：同实例真实构造/赋值或enqueue的producer PC，以及其实际calendar输入和分支，说明为何这批任务会在指定native date窗口被派发。当前没有可填写的已证producer地址，不能猜“每天”“月初”或next-due字段。
- D：实际READY早于玩家k被claim/执行，线程代际覆盖成立，且观察没有先触及foreign、timeout、cancel或其他清理边界。就算任务已排队，撤销或异常也须保留真实结果；C+D不替代最终实际执行记录。

当前已核公共cash/payment DTO没有task/count/next-due查询合同。只在执行后观察到postload，能补“本窗该点确已发生”，不能倒造事前机会保证。若C仍缺失，后继应先补这一条有限生产者连接，或由Root明确选择一次“机会未知”的有限机制探测；不以“再过一天试试”作为自动重试政策。

**R223与R225的真实计数不能补成调度合同。** R225的 `R08-PARENT-RESULT.json`57653B（索引R225-result）实际为 `actual_days=1 / exact_day_verified=true`，日期只采用53149056→53149080；observer为 `foreign_limit / foreign_count=4096 / target_post_read_retained=false / target_post_read_qualified=false / window_complete=false`。它的 `parent.raw.ndjson`45081B保留首个foreign PC2C06B38及cleanup queued witness PC28C2E2E，都不是目标postPC28F785A。只有首条foreign样本，不能推出4096条的PC分布、频率或不同角色数量。初始arm线程数量也不是Character数量。

上述foreign点不在parent ABI，不能用其RCX-70或R8D反推task与index。未来postload执行模式即使记录foreign，也可能重复观察同一Character的多次invocation，不能把计数当人口或一次批次的count。

R223实际a/b各一条0→0物理copy；其actual consumer两条 `known_copy_caller_v1`与 `actual_writer_game_date`均为null，trigger_phase未知。因此28A645B/28A6466本身没有证明这次玩家parent被调度。R0174的历史seq12曾独立关联actor31254的真实parent栈，但不是当前33388；day17/day21是同一事件副本，不能当两次周期样本。R223的[原始consumer](evidence/episode04-r0223-20261020/observer/ACTUAL-WRITERS.json)已在81ac4459a19451c8435d91f16f9d6ede7038a7ac按原字节归档。R225的[结果](evidence/episode04-r225-live-close-and-source-followup-20261021/raw/r225/R08-PARENT-RESULT.json)与[raw](evidence/episode04-r225-live-close-and-source-followup-20261021/raw/r225/parent.raw.ndjson)按固定110项计划随本次交付入库；须在首批实际commit产生后绑定，当前候选不预填提交，也不声称D冻结树已有这两件。原本地路径作为source_path保留于索引，canonical引用与原bytes/SHA一致。

**null context是合法分支，不等于没有费用。** 在parent中，28F7850保存入口Character到RBP，28F7853加载 `RDX=*(Character+1C0)`；28F785A是下一条指令。实际TEST在28F786F，JE在28F7872，空值分支跳至28F7931并仍到28F7934的settlement call。局部正常控制流“每次parent一次callsite”不等于已经观察到该call执行，更不等于钱包发生付款。详情见[原parent-order结论](episode04-r08-settlement-parent-order-12004.md)。

若新来源合格的postload执行记录得到RDX=0，只报告该次load的结果；不要拒掉合法null，也不要报无维护费。若RDX非零，只取得实际context/caller候选。保留loaded值、独立post-read样本与admission指针是否相同的真实差异，不能用旧context重新绑定下一窗。该点的参数由保留寄存器重建，`entryExact=false`，RFLAGS已被SUB改变；四参数不是a/b/c/d四项维护raw。未命中只报告有限窗未取到目标。旧入口17Q、data-watch21Q不自动授予postload执行模式，其构建、cold、公共接线与现场许可分别核验。

**付款与预算的保守消费规则。** [下一份归因证据](episode04-r08-next-maintenance-attribution-12004.md)把缺口分成类别来源、同次应用、刷新/周期。parent命中不提供C/D writer，也没有同次NET token、实际payer或cadence。后续若取得真正C/D post-PC，才按那一个PC做有限source定位；copy继续只标copy。付款必须另外核同账户、同session的实际wallet记录与原始端点，不能用日期接近拼接。

游玩不必因R08未闭而停下合法战争处理。文件阅读型agent可采用以下规则：

1. 当前/最大维护rate可作来源明确的预算情景，不是历史已付金额；current与all-raised是替代情景，不相加。钱包NET或同值copy不能改名军费，不从已记录NET再武断减一份rate。
2. 战时先核同帧现金、已承诺支出、未决采购与可用雇佣应急报价，并保留原资金用途，避免重复计算reserve。未知付款结果不重投；尚未到账的退款、贷款、未来收入不算可用现金。
3. 只有军事现金确实充裕才允许可选新建、升级或新地产。现金、承诺或紧急雇佣输入缺失时，延后可选建设，继续既有合法应战；不能仅凭军队正在推进便认为可建设。
4. 若现金不足或败战风险重大，评估合法取消项目、借款或雇佣，但须实际资格、报价/条款和独立到账/效果后验。兵数改善不是胜率，ACK不是已付款、到场或胜利。不能直接写金币或绕过原生可负担检查。

**现有消费者与本文的接线边界。** [current raw context](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_cash_current_raw_context_v1.py)验证的是暂停态当前输入；[payment normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_payment_observations_v1.py)消费已发生callback及session/source关系，均不产生scheduler机会。[战时建设现金gate](../../ck3_autonomous_player/src/xar_autoplayer/wartime_construction_cash_v1.py)要求同帧维护rate、现金、既有reserved和合法雇佣报价，缺输入返回defer；其中数值是可审政策，不是引擎或用户固定门槛。[现金floor候选](../../ck3_autonomous_player/src/xar_autoplayer/war_cash_floor_policy_provenance_v1.py)要求独立审核pin的JSON政策及不重叠用途，不接受把本文Markdown当作自动授权，且候选验证不等于正式现金回执。

本交付只有Markdown与来源索引，没有修改普通planner的loader、registry、typed producer或调用点。文件阅读型agent可显式引用；不能因为文件入库就报告普通planner已自动采用，也不能仅因helper存在就宣称本场执行过。若需程序自动消费，后继须另做明确、来源绑定的typed接线与相应验证；这不是本页已实现的能力。本文不改变R08实付、业务、动态主题或ABC验收计数。



2026-10-21 归档补注：上文候选时的待提交状态保留为历史。R225 两份原件已在 `992ca426939c19dcb62375344fc4a230e86a38f1` 实际发布；逐项绑定见 [Root 实际采用与发布绑定](evidence/episode04-r08-player-parent-opportunity-20261021/ROOT-RESEARCH-DOCUMENT-ADOPTION.actual-a01.json)。普通规划器仍不自动读取本文。
