# H2743 de-jure 退出：只读预测与隔离副本的准入边界

本页只审计 CK3 `1.19.0.6-steam23530548` 的原版磁盘文件和仓库内既有原生读口。EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，`00_dejure_war.txt` 为 `D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE`，`00_war_values.txt` 为 `ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B`。本轮没有启动 CK3、占用屏幕、读取进程、调用 effect/preview、执行投降或复制存档。`verify_h2743_dejure_readonly_getter_candidates.py` 的完整 EXE/脚本 SHA 与有界 RVA 校验通过；它只证明静态候选，不是 H2743 live 结果。

## 当前没有可安全主动调用的完整条款 producer

`individual_county_de_jure_cb` 的胜利分支在 `00_dejure_war.txt:455–472` 先创建 conquest change，在 `target_titles` 循环内保存临时 `scope:target`，**循环外**将此 scope 传给一次 `setup_de_jure_cb`，接着 `resolve_title_and_vassal_change`。因此当前战争输入 `targeted_title_ids=[2128]` 与 Title2128 的行动前 holder `33435`/personal liege `29829` 均不能直接当作执行时目标 scope 或最终 old→new 结果。

已入库的[窄原生审计](h2743-dejure-narrow-native-producer-boundary-2026-09-28.md)将 `setup` 的目标求值追到动态虚分派，将 `cb_prestige_factor` 追到动态容器计数和 identifier row **写入**。`resolve` 的 preview `0x7E9220` 只返回 true；执行 `0x2EC43F0` 经 `0x27CD510/0x27CD6A0` 进入全局 change 队列。[预入队回执](../../ck3_autonomous_player/native_bridge/research/dejure_resolve_prequeue_gate_1_19_0_6.json)中 `0x24CC9A0` 在空容器路径写 `change+0x260`，非空路径调用 `0x24BC660`。本轮有界磁盘反汇编还确认 `0x24BC660` 读取 `change+0x58/+0x70/+0x88` 并建本地处理容器，`0x24CBD80` 遍历 12 字节 change 记录、查询全局 component 表并可调用 `0x260AA00`；后者可继续到全局管理器调用 `0x2644FA0`。这些事实尚不足以判定每条记录的业务含义，但足以拒绝“浅拷贝 change 后调用原生 resolve 就是只读预测”的假设。它的指针、上下文、全局表和后续写集合没有隔离证明。

要把原生路径变成纯投影，必须先闭合四项：

1. 运行时目标 scope 的实际节点类型、完整求值上下文、返回 TitleID 与身份稳定性。
2. `setup` 写入的五组 change 记录列语义、所有条件分支与 `cb_prestige_factor` Q100000 数值；不能用目标列表长度代计数。
3. `0x24CC9A0` 的全传递调用和写集合、全局 component 查询以及 `0x27CD6A0` 后的实际消费/持久化规则；读写都必须在纯数据模型中重建，不能在权威进程上执行原生 effect。
4. CB 之外的 war-end effect、条件资源变化和有向休战覆盖/合并规则。原版脚本直接分量不能冒充完整 14 行有符号资源 delta。

当前没有满足这四项的可调用只读 producer，也没有已物化、可按 WarID/effect/revision/generation 双读的完整终战结果槽。正式出口的 `title_vassal_delta`、`signed_resource_delta`、`directed_truce`、`recommended_outcome`、`action_literal` 继续为 `null`；不可从历史 R0197 投降后存档外推 H2743。

## 可补的单项只读输入：另一场边境突袭

`00_war_values.txt:54–65` 的 `BORDER_RAID_PAIR` 要求攻方 Landolf 的 **任意战争**同时满足主攻 `30097`、主守 `29829`、CB `fp2_border_raid`。现有 `ReadWarsAndArmies` 在 `ck3_11906.cpp:7430–7469` 已只读逐槽遍历 war-manager，但随后按当前玩家 Robert 是否参战过滤，因此 Robert 的 `active_wars` 并未证明 Landolf 的枚举完整，也不能据此填 `false`。

下一版只读读口可复用这个全槽扫描，逐槽校验未结束状态、完整 WarID/generation、主攻 `war+0x288`、主守 `war+0x28C`，并由 `war+0x100` 的 CB pointer 回读数据库 index 和 stable key。只有扫描前后 war-manager 容量、全部候选槽身份及 H2743 的 WarID/双方/CB/native revision 均一致，且任何候选 CB 都可解析时，才发布 `observed true/false`；其余为逐域 typed unavailable。此读口不求值 script，也不调用提交器。它补一个休战条件，不产出实际天数或持久化到期日，且需新的 DLL、pin、独立 live attempt 与负例验收；当前 v4 partial-truce 候选静态准入不应因本页被写成已具备此值。

## 可验证隔离副本的最低合同

若纯投影短期无法闭合，可单独设计 **反事实实验**：从 SHA 固定的 H2743 精确存档创建一次性、独立 `-userdir` 和新 attempt，核对 CK3 EXE、DLC/mod、driver/sidecar、初始暂停帧及 WarID/主攻守/CB/Title2128 前态完全相同；仅在该副本执行一次合法守方投降，保留执行前后完整原生快照、原始存档、日志和全部命令回执。至少两份互不复用输出目录的副本应独立重放，并逐域比较 TitleID/holder/liege/直接封臣、双方资源、相关第三方资源、全部有向 truce slots 及其他 war-end effects。任何随机或非确定性差异、缺失域、对象身份漂移、实际游戏版本差异或不完整持久化都必须给出 typed unavailable，不能取某次样本当作正式预测。

这个实验**会在副本中执行游戏动作**，因此不是只读 native query，也不是本页已实施的方案；它不能修改或覆盖权威 H2743 存档。即使两个副本后态相同，仍需证明当下待决策帧与副本前态按所有 effect 相关输入等价，以及比较器所需的继续作战损失上界，才能给正式退出建议。未满足时保持原有 `selected_step` 拒绝和 `material_complete=false`。
