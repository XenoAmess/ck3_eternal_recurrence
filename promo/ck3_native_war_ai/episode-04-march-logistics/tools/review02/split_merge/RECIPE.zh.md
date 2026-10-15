# R0176 的 R09 分阶段 Root relay（准备件，未执行）

本配方只用于 Root 先完成 R13、仍持有同一实际 SDK 会话的 R0176。
来源为 dcda/a06 普通加载；必须提供**新 R0176** 的 actual runtime proof、allocated context、当前 Root request helper 以及各自真实 SHA。
旧 R0175 的 PID/create-time、episode、Army18 及其普通 role-read 成绩不准入。
本 helper 不连接 SDK、不启动 CK3、不推进日期、不操作桌面、不启动或重启 recorder，不写游戏内存。

先检查 `MODULES.pins.json` 与本交付回执的 helper SHA。`--help`、纯 Python tests 可离线执行；以下阶段由 Root 明确逐个调用，不能用循环串起来。
`root_relay.py` 和同目录的 pinned freshsplit consumer 可从外置 overlay 直接运行，不要求把补丁合入当前 dcda。
生产 normalizer、旧 R09 consumer 和源类型说明从 `--repo` 的 dcda 读取并逐文件校验。

每次实际调用使用下列共同参数，替换所有尖括号；不同阶段必须使用不同 `--attempt`，同一组实验保持 `--case-id` 不变：

```text
python -B <root_relay.py> <阶段> --repo D:/workspace/ck3_eternal_recurrence --context <R0176的allocated-context.actual.json> --context-sha256 <当前contextSHA> --runtime-proof <R0176的真实runtimeproof.json> --runtime-proof-sha256 <该proofSHA> --request-helper <当前R0176的Root请求helper.py> --request-helper-sha256 <该helperSHA> --self-sha256 <本root_relay.py交付SHA> --run-id desktop-3fevhd2-1c74096080--vanilla--R0176 --case-id r09-normal-a01 --attempt <本阶段唯一ID> --army-id <Root从当前原生roster选择的source CUnit FullID>
```

准入另外核对 PID 的真实创建 FILETIME、connection generation、episode/actor、精确 1.20.0.4 EXE SHA、ready adapter、暂停且地图 ready、无 modal；context 指向的实际 capacity admission 必须保持原共享 512MiB 和 `2026-10-16T07:45:01.597Z` 截止。Root 仍是共享池总量和录制的唯一负责人。本 helper 每次另核本 run/relay 下一包的有限占用，不能据此声称其他 lane 已自动计量。

| Root 单次阶段 | 真实调用与保存 | 放行给下一阶段的条件 |
| --- | --- | --- |
| `baseline` | `ck3_take_snapshot(include_native_command_history=False)` → `ck3_get_capabilities()` → `ck3_query_army_strengths(army_ids=完整当前player roster, expected_revision=该帧revision, profile="ordinary_core_v1")` → 对全部 Army 独立 `ck3_query_army_commander_candidates_v1(army_id=实际ID, expected_revision=同帧revision)` → 同帧 readback | 全 ArmyID/CArmy 映射、完整 ArRg/DATA/role leaf、真实 commander 可读；写 `baseline.actual.json`。只读。 |
| `split-once` | 新快照必须与 baseline 的 snapshot/revision/nativeRevision/date 一致；重新读 capability；先独占创建 `split.once.claim.json`，再仅一次 `ck3_execute_step(step="split-army-half-N", expected_revision=实际revision)` | 当前 native capability 和具体 action_step 均存在；原生命令自行 Validate，之后才 Queue。ACK 只准进入独立只读后验，不能授 split 生效。 |
| `post-split` | 只读原始 split 请求/响应，再独立采完整 snapshot/strengths/全部 commander | 新 snapshot/revision/nativeRevision、同日期/episode/进程；roster 恰好旧集合＋1，原 source CArmy 世代保留，两个不同 CArmy；以集合差确认新 CUnit FullID，不用 ACK sibling、不猜 ID。调用已封 freshsplit assertions，核物理 DATA、每 ArRg 顺序/反向引用、角色和两军统帅；无关 Army cohort 保持。 |
| `merge-once` | 仅接受已 PASS 的 post-split；destination 固定为原 source，source 为独立确认的 sibling。新同帧快照＋当前 capability 后，先创建 `merge.once.claim.json`，再仅一次 `ck3_execute_step(step="merge-armies-D-with-S", expected_revision=实际revision)` | 同省、两军自有可控、非战斗/非撤退，具体 step 在当前广告内；原生 validator 是最终合法性判断。 |
| `post-merge` | 只读原始 merge 请求/响应，再独立完整 query | roster 恰好移除 sibling、destination CArmy 世代保留；selected 两军→一军 DATA 守恒、允许有 native predicate＋完整 role leaf＋空 DATA 的 1/1 Character 记录变化；独立读新统帅，列出两位旧统帅在 after 中实际解析到的 role rows；无关 Army cohort 不变。 |

baseline 绑定完整 roster（上限 32 个，超过会明确拒收，不静默截断）；所有 Army 的完整 DATA 都在 response-local raw Driver 原件中，derived packet 是明示字段投影并保存原件 SHA。重复物理 DATA 别名按 persistent Regi FullID＋chunk index 去重求总数，同时保留每 ArRg occurrence/顺序/反向引用约束。1/1、统帅、Character role、combat Knights 分开；本接口没有读取 Knights membership，不得称之为骑士数。

新 CUnit 的“类型来源”目前是原生 roster 的 CUnit FullID，加 production `ReadArmyStrengthRow` 对 CUnit 世代及 `CUnit+178` 所链 CArmy 世代的解析；原件源码随 `MODULES.pins.json` 绑定。当前 DTO **不直接发布 CUnit 类型字节或原始 +178**，因此 receipt 明示 `raw_CUnit_type_or_178_published=False`，不能把静态构造链变成现场原始字段观测。split source 的新 CArmy/CUnit 构造和双向链接见已封 `episode04-split-half-source-12004.md`，它仍是源码结论。

发生 false/错误/超时/断开时：保留 claim、原始 request_id 和精确 response path；不删除 claim，不换 case 绕过，不重复提交。`post-split` / `post-merge` 只会读原始响应及新状态，不会补发动作。原响应 pending 就先停；拒收即保留原生原因。当前没有独立公开 split/merge legality preview，所以“capability/step 存在”不能写成 CanExecute 已通过；海上限制以单次原生 Validate 的实际拒收为准，不猜原因、不强制 byte、不换接口绕行。失败时 Root 可以继续原有正片任务，但不能用 ACK 给 R09 成绩。

本微实验应保持暂停、同日期，R13若尚在行军也不自动 Halt/Move。若 Root 要求先驻地，则由现有正常任务自行达到并重新取得本 baseline。整个 relay 没有时间推进阶段。

视频仅能说明独立后验中实际出现的 DATA/角色/统帅变化；静态 source 可解释条件 producer，不能宣称现场观测到了构造指令或每次合军必生 1/1。Root 已开始 recorder 时不得二次 start。动态 split/merge 镜头没有取得时，`dynamic_video_qualification=False` 单列，数据验收与动态镜头资格分别交付。

本交付的离线测试只证明准入、一次性 claim、拒收/超时恢复规则与 consumer 接线。它不是新的运行证明，也不重复已封 source qualification 或 R0175 ordinary role-read 资格。
