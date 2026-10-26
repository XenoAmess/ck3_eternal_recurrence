# 日步 pre 的通用 job dispatcher：clone、handle 与 inline 路径

`machine_id: xenoamess-full-tower-eb9d2c1186`，来源审阅时刻 `2026-10-25T21:51:14Z`。输入是来源机器 `desktop-3fevhd2-1c74096080` 已保存的两片 CK3 1.20.0.4 静态源码，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。跨机器仅复用固定字节，不授本机安装、加载或实机资格。

本次续接[日步 pre callable 容器](campaign-goal-clock-dispatch-12004-20261026.md)，闭合通用 `3F91AD0 → 3F91650` 的对象转发与本地 inline 调用顺序。**原 callable、clone 后的 target、job 和引用 holder 是四个不同对象。** 后续source26已从b64实际取得253 B worker，并将state2绑定到callback正常返回之后；它仍不是游戏日／callback业务成功证明。原历史asm缺失事实保留，未制造同名替代原件。

## 当前可读输入与未读原件

| 输入 | 字节／SHA-256 | 本次实际处理 |
| --- | --- | --- |
| [submit-3f91ad0.bin](evidence/episode04-r08-task-construction-20261021/submit-3f91ad0.bin) | 566 B，`a8ef518f9e1ad2c41579d5489ba6878ba1e690bf4bdbde4abf4ee764754d16ae` | hash匹配；143条指令完整解码，无尾部遗漏 |
| [job-build-3f91650.bin](evidence/episode04-r08-task-construction-20261021/job-build-3f91650.bin) | 414 B，`f6707a9b82263ff34259091e237872405d19075ff35e7932c5f97bb616d22e37` | hash匹配；112条指令完整解码，无尾部遗漏 |
| [原提取metadata](evidence/episode04-r08-task-construction-20261021/SOURCE.actual.json) | 记录来源机器、exact EXE、pdata范围与旧提取边界 | 只复用原固定来源；没有重读EXE |
| [旧 TASK-SELECTION 合同](evidence/episode04-r08-task-dispatch-source-gap-12004/history/TASK-SELECTION.contract.json) | 含3F909F0原253 B body的历史SHA和部分指令 | 其中 `acceptance/2026-10-16-r0174-maintenance-source/upstream-job.complete.asm` 本次实际读取返回 path-not-found；不追认为当前可读完整worker |

完整本次审阅记录为 [HELD-SCHEDULER-DETAIL25B.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/HELD-SCHEDULER-DETAIL25B.json)，SHA `a0a90f4faeacc8c3464e805ef8d4217841e058c4f10b693c0abfd0b7a931d9db`。25B在实际 `2026-10-25T21:54:13Z` 的审阅中纠正25的一处callee转录：实际 `VA14341ED60 - imageBase140000000 = RVA341ED60`，不是 `3F41ED60`；原25保留，request25的worker地址与预算不变。对应[计划](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/research-plan25B.json)和[生成的 Mermaid／边表](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/research-graph25B.md)来自同一数据，check/render实际退出0，仅验证结构与文件完整性；5条static-confirmed、3条unknown、0条live。offline-only／真实运行trigger未指定的提示保留，不是实机准入。

## 本体实际顺序

`3F91AD0` 保存原R9D数量、原RDX wrapper地址与输出handle descriptor。两个内部builder callsite（`3F91BE7`、`3F91C58`）都将这个原wrapper地址作为R8转发给 `3F91650`；不能把相邻manager或数组descriptor当成那个callable。

`3F91650` 的局部循环先以requested signed count做LOCK XADD；count>0才进入构造循环。每次经allocator虚表+8申请0x78 B，初始化 `job+38=null`，若 `originalWrapper+38` target非null，就调用该target虚表+0的clone，将返回target写入 `job+38`。随后复制其他捕获，并设置 `job+60=0,+64=1,+68=0,+70=0`。clone内部行为取决于实际target；本页没有给未核target赋monthly业务名。

接着它另申请0x28 B holder，写 `holder+10=allocator,+18=job,+20=originalManager`，并独立维护 `holder+8` 引用计数。holder不等于job，holder的vptr不等于 `job+38` callable的vptr。

global byte与signed `manager+AC>0` 构成builder的局部predicate。为true时，builder增加 `job+64` 并调用 `3F92670(manager+1C0,job)`。之后正常路径调用 `341ED60`，传入holder与原输出descriptor；其内部效果仍未在这两片body中展开。不能把函数地址或引用计数变化直接命名成已完成任务。

dispatcher另行读取同形predicate。如果它自己的局部predicate为false，builder返回后遍历原输出descriptor中的每个holder，取 `holder+18` job，以 `RCX=job,RDX=manager+1C0` 调用 `3F909F0`（真实literal site `3F91CDA`），再进入正常RET。这个局部分支证明存在inline执行路线。dispatcher与builder分别读predicate，静态形状不能证明并发期间global值稳定，也不能证明当前游戏走过哪一支。

Campaign已从独立held来源确认 `29897F0` 的非null handle wait和normal-return后原callable容器cleanup；其wait接受state2或3，没有赋两者成功／失败语义。本页不以generic dispatcher返回替代那一层wait，也不把两层合成“所有monthly callback成功”。

## 下一有限读取与边界

唯一新增源码请求为 [NATIVE-SOURCE-REQUEST25.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/NATIVE-SOURCE-REQUEST25.json)：恢复 `RVA3F909F0` 的253 B body（历史end `3F90AED`），由Root指定的唯一b64静态producer执行。下节记录实际到件；本岗没有执行EXE读取，没有扫描.text或启动Game。body返回仍不能制造实际callable业务成功。

## Source26：实际worker原子claim、invoke与state2

`2026-10-25T22:12:03Z` 已审阅b64 batch02实际window35。原件为 `D:/ck3-state/ck3-java-g2-native-static-resume61/batch02/capture01/window-035.raw`，253 B，SHA `426e7b7c3e47980c4975bff0745518c9539d7bd06ae6f7f44d973789a7f3c11e`；原producer结果索引 `BATCH02-RESULT01.json` 为37364 B、SHA `4f117d56895dd986010e34f3691601bc882e218c34acbf4811513bf174ebf3bb`，保存请求、准入、输入／身份与终态边界。没有把工具调用ACK当成body到件。

完整68条指令覆盖全部253 B、decode gap0。实际来源审阅与精确ref为 [ACTUAL-GENERIC-WORKER-SOURCE26.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/ACTUAL-GENERIC-WORKER-SOURCE26.json)，SHA `5be615505c1e946b1f74bb13e6e6273e4a078c0f4a472bef1f8b7f7002ee4490`。新[计划26](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/research-plan26.json)与[生成图26](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/combat_phase/research-graph26.md)实际check/render退出0，4来源、7条static／2条unknown；仍仅结构／文件完整性。

| 实际路径 | 已证边界 |
| --- | --- |
| `3F90A07` LOCK CMPXCHG `job+60`：expected0→1；失败到`3F90ADA` | 失败分支直接ALfalse／RET，没有invoke或state2；只证明这段local atomic claim。 |
| 成功后`3F90A51`写`job+70`，`3F90A5A` LOCK XADD原RDX所指counter,-1 | counter先于callback减少，不能称作已完成callback／日期计数。 |
| `3F90A5E..3F90A6F`读取nonnull `job+38`，call `[target.vptr+10]` | 单一local callsite无本地循环可重复到达；当前target来自实际clone，generic body不赋monthly业务名。 |
| callback正常返回后`3F90A72..3F90A77`写EAX2并XCHG `job+60` | state2可绑定到该call正常返回；callback返回寄存器被覆盖，没有把其业务返回值判定为成功。 |
| state2之后再计算并写`job+68` timing、ALtrue／RET | waiter看见2时，不能因此断言尾部timing或整个worker RET已经完成。 |
| null `job+38` 转`3F90AE7` CALL42207F8／INT3 | 本地没有正常RET或state2发布；外部helper异常行为未展开。 |

该完整body没有state3 writer或reset0。Campaign独立wait接受2／3，现在只给2添加上述正常return来源；3仍为unknown。没有因此赋予完整callback成功、每游戏日一次、async线程身份、战果、付款、月度发布或SAVE信用。

async `3F92670` 的真实dequeue、执行线程、pre／post之间的运行时对象关系、callback reentry与once-per-day cadence均未由本页闭合。monthly `1A34A30`／`476CA28` 的实际consumer仍归Campaign来源链。没有因研究缺口改变普通auto战争意愿或增加首场启动前置。

25／25B仅复用held来源，新增EXE读取0；source26的唯一b64 producer实际新增253 B／1个body读取，本岗只消费其原件。native build、JVM、Game／pipe动作与新增游戏日仍为0。derived解码和小型来源记录按统一存储策略在 `2026-10-27T18:00:00Z` 复核；原raw仍服从其来源记录，不通过复用刷新原期限。

