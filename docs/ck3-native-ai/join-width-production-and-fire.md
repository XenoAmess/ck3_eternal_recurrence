# CK3 1.19.0.6：增援加入后的战宽缓存与主阶段出伤读取

本页绑定原版 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。以下调用、字段与先后次序为 **exact-build 静态确认**；078 已在实机取得 join 前后两点战宽，首次 phase-fire 第三点仍未取得，不能把完整传递链写成已实测。

| 生产或消费点 | 原生行为 | 被动读取的字段 |
| --- | --- | --- |
| `0x23040A0` join wrapper | 插入增援侧成员后，`0x2304255/0x2304261` 依次调 `0x23CB840` 刷新两侧缓存 | `CCombatSide+0x98` 两组 entry 的 current-soldier Q100000 总和，`+0xA0` 第一组 subtotal；side 位于 `CCombat+0x20/+0x368`，故双方总和也可读作 `CCombat+0xB8/+0x400` |
| `0x2304266..0x2304272` | 检查加入前已有的 `CCombat+0x6C0 > 0`；成立才调 `0x2305580`。`0x23041B5` 已将比较寄存器 `r12d` 置零 | 旧 base width `CCombat+0x6C0` 与更新门是否真正经过 |
| `0x2305580` | 用刷新后的 `+0xB8/+0x400` 计算候选；base width 先至少为 1，再与旧 base 取较大值，写回 `+0x6C0`；经 `CCombat+0x6B8` 的 Province → terrain `+0x58` 乘数计算并最低宽度钳制，写 `+0x6C4` | `+0x6C0` int32 base width、`+0x6C4` int32 final width、Province ID 与 terrain 乘数 |
| `0x2309E80` 下一次 main tick | `0x2309E92/0x2309EA1` 再刷新 side totals；这个函数体在出伤前**没有直接调用** `0x2305580` | 此时 side current totals 可能又变，不能仅用此刻人数反算有历史最大值的 base width |
| `0x2309F7F/0x2309F98` phase-fire | 两次从**存储的** `CCombat+0x6C4` 读取 int32 final width，分别作为 `R8D` 传给 side0/side1 `0x23CB1D0`；callee 于 `0x23CB1D0` 保存参数，`0x23CB445` 取回，并与本侧 `+0x98` fighting total 进入后续比率及伤害计算 | 两次实际传入出伤器的宽度，以及两侧同一阶段的 `+0x98` |

具体算术与 Q100000 截断次序见[战斗模拟文档的战宽公式](battle-simulation.md#参战者与战宽)；本页补的是**增援 join → 缓存写入 → phase-fire 读出**这条时序。`0x23CB840` 与 `0x2305580` 都是变更游戏状态的函数，暂停查询只能读取字段，不能为取样而主动调用。尤其 `+0x6C0` 是不下降的历史 base；在 main tick 刷新 `+0x98` 后，它不必等于用当前两侧人数重新算的候选。

建议的原生被动探针在同一 CombatID 和原生日期上记录三处边界：join wrapper 进入前；两条分支汇合的 `0x2304277`（同时记录是否经过 `0x2304272`）；首次 `0x2309F7F` phase-fire 宽度读取前。join 入口/返回必须彼此同线程；077、078 证明不能把任一实际战斗线程预设成 private begin 的 mailbox 线程。每处记录 phase/day、两侧 entry current-soldier 汇总与存储的 `+0x98/+0xA0`、`+0x6C0/+0x6C4`、Province/terrain 身份，以及 incoming ArmyID。它能区分“增援确实改变战宽”“已有历史宽度压住新候选”“宽度更新门未经过”和“主阶段只是复用缓存”。任何一个场景都要以实际记录为准；078 已取得入口/返回宽度，但未取得首次 phase-fire 的实际传参，完整传递归因仍待复测。

### 有界私有观测器（逐门实机验证）

当前实现选择更安全的三点：`0x23040A0` join wrapper **入口**、同一 wrapper **正常返回后**、首次 side0 `0x23CB1D0` 入参 `R8D`。返回点已经越过 `0x2304277` 汇合，但不是汇合指令本身；因此仅凭这三点不能直接证明是否经过 `0x2304272`，需要用前后宽度和后续证据判断。wrapper 的 RCX 为 `CCombat*`、RDX 为 incoming `CArmy*`；前置计划冻结候选 ArmyID 及完整代际对象指针。钩子只对这一个 CombatID/候选指针采集，返回后在有界原生 side army ID 向量中确认落入 side 0/1。三条记录分别含实际线程 ID、原生日戳、phase day、两侧 `+0x98` Q100000 总量、`+0x6C0/+0x6C4` int32 战宽，以及 side0 出伤调用实际传入的宽度；其中 join 两条线程 ID 相同，phase-fire 线程 ID 可不同。首个边界的 side 尚未加入，记为 `-1`；返回后才填实际 side。尚未采集 Province/terrain 及 `+0xA0`，不能以当前字段独立重算地形修正。

私有 begin 必须同时给 `candidate_joining_army_id` 正整数和严格布尔 `capture_runtime_join_width:true`；默认不安装 join 补丁，也不改变七边界 wire。成功的可选 `trace.runtime_join_width` 是 3 条 `boundary=0/1/2`，分别代表入口、正常返回、首次 side0 出伤前；无目标增援是 `no_join_observed`，部分记录/宽度不一致是 `failed`，原始 failure flag 保留。边界 2 的 `outgoing_width_argument` 必须等于当时 `+0x6C4`。075 的真实增援观测为探针 RED，不能把离线夹具数字当作 CK3 战况。

安全门：EXE SHA-256 为页首 exact build；入口 `0x23040A0` 的 16 字节 `48895C24104889742418555741544156` 是完整无相对地址的指令，下一条 `0x23040B0` 才开始 `4157`。专用 16+14 字节 trampoline 避免通用 15 字节补丁截断指令；离线可执行夹具核对原返回值、钩住后的返回值和卸载原字节一致。补丁安装/卸载仅在已验证暂停静止的 main-thread mailbox 执行，失败保留 trampoline 与停止门，钩内不分配也不调用 CK3 helper。实机前还需记录独立 DLL SHA、源存档/配对回执 SHA、新鲜 Steam 离线帧和任务总线独占；一天回放后必须冻结原始 finish bytes/SHA 以及 clean-exit 回执。两份自然增援案例应分别使用新 attempt，不得改写历史素材。

### 075 自然增援实机 RED 与下一道诊断门

独立外置 attempt `D:\workspace\ck3_native_war_ai_promo_work\episode01-join-width-live-attempt-075` 使用第 11 日冻结存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`、配对保存回执 SHA-256 `DD986180C7E9C4B42D43FC634884F5294387D18CF8F798012FAD621B37E9E4A5` 和私有 DLL SHA-256 `E48EB9A6745F5544F2F45B98AE11498C67230CE905350CB6229BA9F2A2F86A0C`。private begin 接受了 `candidate_joining_army_id=22`、`capture_runtime_join_width=true`；原生日期 `53146488→53146512` 恰为一天。七边界记录显示 CombatID `16777218` 的 side 0 军队 ID 从 `[16777221,16777231,27]` 变为 `[16777221,16777231,27,22]`，故目标自然增援确实发生。

然而原始 `jwidth075-finish.json` SHA-256 `71699B47C3091D44E990BEB17E3477ADE3C97769528347B985AA1DFCB3E006C6` 报 `trace.failure_flags=262144`（`1<<18` join-width），`runtime_join_width.status=failed,count=0,boundaries=[]`。不能从它得出宽度是否更新。源码中空记录本身不置该位：`CompleteAndDrainCombatPhaseEventTraceRingV1` 只对 **非零但不足三条** 置位，因此在 075 的已冻结二进制里，有候选指针匹配后第一条拒绝；可疑谓词仍包括 ArmyID、日期对象、CombatID、线程和 side backpointer，原始 wire 无法区分。受管清场回执 `session-result.json` SHA-256 `8B116F9C52F2FE99C2CBB4720471C98119A8E5B1CDA4017DF70EFE2376A5B2B1` 证明 CK3 进程全灭、job active 为 0，任务总线 `ck3-join-width-attempt-075-20260927` 已释放 CK3。外置 `start.py` 把非空的 final-inventory **容器**误判成仍有进程，使自己的 `cleanup-check.json` 假阴性；原始文件保留，另附 `cleanup-recheck-note.md`。

后续默认关闭诊断版在可选 `runtime_join_width.first_failure_code` 记录首次拒绝谓词，不改默认 wire：`1` 顺序、`2` ArmyID、`3` 日期对象、`4` CombatID、`5` owner 线程、`6` side 回指、`7` side roster、`8` side 身份、`9` 传入宽度、`10` 内存故障，`0` 无失败。该值只是**观测器校验失败原因**，不是 CK3 战宽公式。离线 DLL SHA-256 `7203C732512536794C2DD4B90894CF459B504E872D617F194565A716C31ACD64`、聚焦 CTest 5/5。ABI 再核：原版 `0x23040C1` 将 RDX 保存到 RSI，`0x23040FC` 读其 `+0x124`，`0x230422D` 写其 `+0x128` CombatID；后者也正是已解析 `CArmy` 的 combat ID 字段。因此本钩子的 RDX 为 `CArmy*`，先前把它写成 CUnit 的文字不能作为本入口的证据。下次采样必须新 attempt、原始 bytes/SHA 和 clean exit，不能重写 075。

### 077 线程门实机勘误

独立 attempt `D:\workspace\ck3_native_war_ai_promo_work\episode01-join-width-live-attempt-077` 使用同一冻结源档/配对回执，但私有诊断 DLL SHA-256 为 `7203C732512536794C2DD4B90894CF459B504E872D617F194565A716C31ACD64`，只推进同一 CombatID 的一天。原始 `jwidth077-finish.json` SHA-256 `25F11353ED45992B7971581440D58A055274A271BE734968CA593B3B64CFF96D` 返回 `runtime_join_width.status=failed,count=0,first_failure_code=5`、`failure_flags=262144`。该诊断码是在候选 ArmyID/完整对象指针命中后检查线程时产生，故 **join wrapper 的执行线程不同于 private begin 的 main-thread mailbox**；不能继续要求 join 与 phase-fire 都使用 begin 线程。它尚未提供 join 线程的实际 ID，也未提供任何宽度值，不能把旧的全线程一致性假设当作原版规则。受管清场 `session-result.json` SHA-256 `C16B93E1CC80B1E26A3CB6EA7A0A59048D75FBA8BE9A3F7E0F7346D43974044D`：cleanup proven，job active 为 0，最终 CK3 inventory 空；任务总线 `ck3-join-width-attempt-077-20260927` 已释放 CK3。

077 后的首轮修正让同一个 join wrapper **入口与正常返回在同一实际 join 线程**采样，却仍错误地要求首次 side0 phase-fire 处于 mailbox/main-tick 线程。三点都必须绑定同一 CombatID 和原生日期，且 side0 R8D 必须等于当时 `+0x6C4`；前后宽度相等也仍是合法采集结果。`first_failure_code=11` 专用于跨边界日期不符。不同线程共享的数据以原子 `join_width_count` 的 release/acquire 提交与读取，不在钩子里分配或主动调用原版 helper。该首轮修正 DLL SHA-256 `8EEFBE8854BFC28FA9CD61F1677B7AB66C642C6F005EBB9661775E2FFE7FE0A0`，聚焦 CTest 5/5（含跨线程夹具）；078 随后证明其中 phase-fire 的线程假设仍错。

### 078 两点战宽实采与第三点线程门

独立 attempt `D:\workspace\ck3_native_war_ai_promo_work\episode01-join-width-live-attempt-078` 使用同一第 11 日冻结源档与配对回执，并使用上段的首轮修正 DLL。原始 `jwidth078-finish.json` SHA-256 `9BFCEFF0BD1454F47B2371683B342E4FB8EC634CE4AF1397937375873FD51FF8`：`runtime_join_width.status=failed,count=2,first_failure_code=5`，`failure_flags=262144`。这份 collector **整体仍是 RED**，但两条原始边界记录直接证明目标 `CombatID=16777218`、增援 `ArmyID=22`、原生日期 `53146512` 的 join 前后缓存发生变化；不能把缺失的第三点补成已观察。

| 边界 | 实际线程 ID | side | phase day | `+0x6C0` base | `+0x6C4` final | 两侧 fighting totals（Q100000） |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| join 入口 `0` | 3816 | -1 | 7 | 1645 | 1480 | 160317482 / 89325449 |
| join 返回 `1` | 3816 | 0 | 7 | 2467 | 2220 | 410690163 / 82785368 |

返回时两侧总量合计 `493475531`，按 Q100000 去缩放并除以 2 得 `2467.377655`，截断为 `2467`，与实采 base 宽度一致。入口时同法得到 `1248.214655`，小于缓存的 `1645`，符合历史 base 可保留较大值；两次比较只是算术对拍，不能据此单独证明实际经过 `0x2304272`，也不能在未采 terrain 时声称 final 的确切乘数来源。第三点因观测器预设的 mailbox 线程不符而拒绝，故尚无原生出伤调用传入 `2220` 的动态证据。受管清场 `session-result.json` SHA-256 `68FE6AEE11DEA5F3D5B50FD6124A250334C39B85BB2F453F68CCDB78E59F565A`，capture 返回 0、最终 CK3 inventory 空，任务总线 `ck3-join-width-attempt-078-20260927` 已释放资源。

智能体可复用的[078 机器可读局部向量](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_join_width_partial_078.json)将源 finish SHA、CombatID/日期/ArmyID、mailbox 与 join 线程、两点战宽及差额固定下来，显式写 `three_boundary_complete=false`、`fire_width=null`。只读投影器 `ck3_autonomous_player/tools/project_join_width_partial_078.py` 对本机冻结的原始 `jwidth078-finish.json` 校验精确 SHA 和 RED 合同，再与仓库向量逐字段对拍；它不会读取或写入游戏，也不把失败的完整 collector 升格为 GREEN。

下一版仅取消第三点的 **mailbox 线程等式**，在精确 side0 返回地址钩子中记录实际线程 ID；候选对象、CombatID、原生日期、side 身份与 `R8D == +0x6C4` 校验均保留。join 入口/返回仍须同实际 join 线程。独立私有 DLL SHA-256 `8DC462F92BA1FBF7066FC9C87601651DAB34626FDF5D9289A5839CB7ED821109`，聚焦 CTest 5/5（含第三点由另一个非 mailbox 线程采集的夹具）；离线通过不等于实机验证。使用全新 attempt 重放一天，要求三点完整、原始 bytes/SHA、失败码和 clean exit 后才给整条链 GREEN；历史 078 回执不得改写。

### 079 实机前环境 RED

独立目录 `D:\workspace\ck3_native_war_ai_promo_work\episode01-join-width-live-attempt-079` 的 DLL 私有 ON 静态自检通过，但 Steam 当前离线状态无法取得**实时可读**的 UI 证明：旧桌面帧的系统时钟停在 `04:06`，与观测时本机时间不符；079 的 GDI 与 Windows.Graphics.Capture 窗口帧内部均为黑色，其中可运行的 WGC 原始 PNG SHA-256 `9A30B47D0E7715F3E6F6B68E55FADCDFD456615A72D2B7B2431DA9B3D9A38CA7`。当前 `steam.exe` 同次进程的 `Start offline - 1` 日志、后续没有 logged online marker、`WantsOfflineMode=1` 只是启动和持久偏好的旁证，不能冒充当前 UI。预检回执 `prelaunch-red.json` SHA-256 `212F4ABDD74CD61AB2BDA03DC7178C24CBA476FF5F6269309F35529372FE8469` 精确绑定原始诊断。079 没有启动 CK3、没有发 private begin、没有生成 `ck3-output`；任务总线 `ck3-join-width-attempt-079-20260927` sequence `1361` 为 `done/resources=[]`，系统进程清单无 `ck3.exe`。第三点仍未实采，下一次需要新的独立 attempt 和可读的当前离线 UI 门，不能改写 079 RED。

有界复核（只读 EXE，不运行 CK3）：

```text
<python-with-pefile> ck3_autonomous_player/tools/project_native_join_width_spine.py --exe <exact-1.19.0.6-ck3.exe>
```

校验脚本只验证指定的相对 call 目标和 11 个字段操作指令，不做全 EXE 反汇编；输出中的 `live_case_width_values_sampled=false` 是证据边界，不是宽度为零。
