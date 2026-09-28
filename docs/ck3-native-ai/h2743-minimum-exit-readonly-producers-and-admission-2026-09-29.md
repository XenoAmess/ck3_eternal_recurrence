# H2743：最小只读 producer、正式比较字段与下一次无启动准入

本页冻结 #448 截至 2026-09-29 的**静态工程合同**。H2743 attempt-12 已在同一暂停帧证明守方投降当前合法、对方接受，并双读 Title2128 holder 前态、双方资源余额及部分休战输入；其 `read-only-result.json` SHA-256 为 `9414C6D397553F1C00D974DB179EF8C96630C2CAB4C75020E1CDED4FAB37DC9E`。原生选项仍给 `terms_observable=false / cb_specific_terms_not_observable`。本页没有启动 CK3、占用屏幕、调用 effect 或提交动作；后述新读口均未实机验证。

## 现有帧与精确来源

H2743 是 save SHA-256 `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9` 的 WarID `16777231`：`native:3`、public/native revision `4/3`、raw date `53217264`、connection generation `1`、episode `native-29829-2bc2d599f7f9`；主攻 Landolf `30097`、主守 Robert `29829`、CB index `17` `individual_county_de_jure_cb`、目标输入 Title `[2128]`。这组值须整体绑定，不能借用 H2825 或 R0197 的另一帧。

| 精确输入 | SHA-256 | 用途 |
| --- | --- | --- |
| source save | `A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9` | 唯一 H2743 checkpoint；不得覆盖。 |
| source driver | `F31460BAA126BAED289CBA20A6FEFF59AAF6EF87BA3B29943C892236B6D15069` | 原始会话状态。 |
| family sidecar | `12D7B2B006E409DB69F7F442107B01B5D38D8C589A7F494B24519094024B5724` | 精确家族状态。 |
| source DLL | `8C3A9523D14DEDB6C44AC04F748BFC9D086E983B2A973A956CBADD21F07A8A5C` | 接收来源资产，不充当新读口。 |
| v4 candidate DLL | `1361FC0991D1FA09CB7272112D73F7F50736B7BBAD6A3656C33F9FB200CA1BAA` | attempt-12 的已验只读实现；任何新增 native 字段须重新构建、重新 pin。 |
| injector | `C89F1A919514A7E664AEE8FAF165B78C693ABA4EA2105289BDA2DB4BAC6A84FF` | 受管原生会话组件。 |
| CK3 EXE | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` | 仅适用 `1.19.0.6-steam23530548`。 |

源资产位于 `D:/ck3-research-artifacts/war31-h2743-20260928/source-verified-01/`；v4 DLL 在同根 `build-truce-inputs-002/xar_ck3_bridge.dll`。旧 attempt-11/12、固定 WAR 请求与回执保持原样。当前 [v4 实机报告](h2743-defender-dejure-partial-truce-attempt-12-2026-09-29.md)的 FLEX 是攻方 owned-perk span **key 命中** `false`，不是已认证的完整 stock `has_perk` 语义；双方游牧标志和合取同帧为 `false`。SHORT、LONG、BORDER_RAID_PAIR 各为 typed unavailable，休战实际天数和持久化到期日为 `null`。

## 最小新增只读输入：完整战争槽扫描

原版 `00_war_values.txt:54–65` 的 BORDER_RAID_PAIR 是攻方 `any_character_war` 中存在另一项 `primary_attacker=scope:attacker`、`primary_defender=scope:defender` 且 `using_cb=fp2_border_raid`。当前 V1 `active_wars` 是**玩家 Robert 视角**，不能证明 Landolf 没有另一场符合条件的战争。下一个安全候选仅补这个布尔输入，不改 `query-defender-de-jure-exit-terms-v1-16777231` 的只读命令含义：

1. 复用 `ck3_11906.cpp:7430–7469` 已有的 `game_data + war_manager_offset`、war storage `+0x20`、`slots +0x20`、capacity `+0x2C` 与 0x10 步幅全槽遍历；capacity 必须在 `(0, 1,000,000]`，扫描到每一个槽。空槽及已结束槽可跳过，任何非空且未结束槽的完整 WarID/generation、slot index、War 对象往返回查必须有效，不能对未知槽静默 `continue` 后发布 `false`。
2. 对每个在役 War 只读主攻／守方完整 CharacterID、active CB 指针、database index/key；对候选同双方战争还须证明 Landolf 在进攻方参与者集合中。目标 WarID 自身必须恰有一行，指针、双方、index/key 与现有 V1 当前帧一致。`fp2_border_raid` 命中才可给 `true`；只有**全槽完整、所有潜在同双方战争的 CB 都可解、没有匹配**才可给 `false`。
3. 在同一暂停 native revision 内取两次完整槽结果；比较 capacity、每个在役 War 的完整 ID/对象、双方与 CB 身份、目标 War 指针，且前后 `ReadSnapshot`、source save、连接代次均不变。溢界、槽/指针漂移、未知 CB、重复 WarID、缺目标 War 或任何读取失败只给 `unavailable` 和具体原因。只读扫描不得调用 CB evaluator、effect、preview 或修改 WarManager。

新增的[纯函数全槽准入投影](../../ck3_autonomous_player/src/xar_autoplayer/bridge/h2743_border_raid_pair_scan_v1.py)只检查候选原始槽列表是否覆盖 capacity、目标 War 完整 generation 与双方/CB 是否匹配、两份列表是否相同；缺槽、错代次、同帧漂移会拒绝 `false`。它不读取 CK3 内存、不认证 native producer 的真实性，即使输入结构齐全也只返回 `structural_candidate_only`、`native_condition_observed=false` 和 null 动作。合成负例不是 H2743 当前 live 值。

这是 **producer 实施与验收要求**，不是已经取得的 H2743 `BORDER_RAID_PAIR` 值。`any_character_war` 与全局战争槽的实际等价性仍须用精确 ABI 和原版脚本验证；等价性未闭合时即使扫得匹配布尔，也只保留候选证据并使正式 `truce_inputs_v1.border_raid_pair` typed unavailable。V1 `evaluated_days`、`persisted_expiry_date_raw`、`directed_truce` 和 `material_complete` 继续为 `null/null/null/false`。

## 完整退出比较还缺什么

[纯函数合同](h2743-formal-exit-comparison-contract-2026-09-28.md)必须在相同 checkpoint SHA、snapshot、public/native revision、raw date、episode、connection generation、WarID、双方、CB index/key 和目标列表下收齐四份数据：

| 输入 | 现状与最小 producer 门 |
| --- | --- |
| native surrender option | attempt-12 同帧合法且会接受；新 checkpoint 要重新查询 exact request/envelope/payload，不能用历史选项。 |
| actual surrender terms | 缺运行时 `scope:target`、完整 title/封臣 old→new、`cb_prestige_factor` Q100000、双方七类资源的 14 行**有符号总差额**、攻击方→防守方实际休战天数及 expiry、带 source node 覆盖的条件 effect 树。当前 V1 只给前态和部分公式输入。`setup_de_jure_cb` 的因子路径写 context row，不能作为纯 getter；广义 loaded-effect preview 曾 live crash 且已停用。[clone observer 静态候选](h2743-clone-passive-observer-seams-2026-09-29.md)也尚未证明 context 实例、detour 安全或整棵效果树。 |
| finite-horizon continuation risk | 缺同帧、有界正时域下的双方 14 行资源 lower/upper、可能 title/封臣操作、战分界与完整接触参战集合及证据 SHA。H2743→H2825 历史续战仅作观测，不是未来损失上界。 |
| policy and one-shot authority | 即使上述输入全齐，比较器只给分量关系，不推导偏好。仍需有来源的策略阈值、绑定此 comparison SHA 与 checkpoint 的未消费授权，提交前原生按钮再验证和终战后置读回。R0197 授权不可复用。 |

SHORT/LONG 需要攻方完整 struggle 集及对守方 shorter/longer 的 stock 谓词同帧读口；两个条件独立，不能假定互斥。五个条件即使全读到，[静态休战纯函数](h2743-exit-resource-truce-static-envelope-2026-09-28.md)也只产脚本**候选**天数，不能代替结算后持久化的有向休战。余额前态、Title2128 当前 holder、静态威望公式、历史 −30 或无显式赔款指令均不能补全实际差额。

## 下次无启动／只读准入次序

当前屏幕由更高优先级现金任务使用，本页只给计划，不领取 `ck3-screen` 或启动 CK3。若新增 WarManager producer，先在独立 build 目录编译并记录新 DLL bytes/SHA、源码 commit、EXE/原版脚本 SHA、完整命令及负例；旧 v4 `1361…` DLL 和 attempt-12 不能改写。下次独立 attempt 的次序为：

1. 静态 `--check-static` 校验四件来源、injector、EXE、**新**候选 DLL 与 CLI；以 candidate 版本明确选择新读口。当前 `run_h2743_dejure_readonly_v3.py --candidate partial-truce-inputs-v4 --check-static` 只能校验旧 v4，不能充作新 DLL 的准入。
2. 在屏幕真正释放后，先确认 CK3/录制进程空和任务总线独占；取得当次可见窗口位移的新鲜 Steam **离线模式**原图，再执行新 attempt 的 prepare/rebind/native preflight。no-launch 必须回执 `ck3_launch_attempted=false`，所有 source/placed hash 与预定 candidate 相同；任何环境门失败保留 RED，不复用旧 GREEN。
3. 只有 no-launch GREEN 才可启动受管只读会话。按现有冷启动实证设 readiness 至少 1800 秒、会话总时限至少 3000 秒，并在等待期每 60 秒续租。只允许同一暂停会话的 V1 baseline 双读、`query-war-termination-options-16777231`、前后快照；若加全槽扫描，也必须在这组身份/日期不变门内双读。零提交、零日期推进、零 `setup/resolve`、零 broad preview。
4. 先受管 stop、supervisor=0、stdout reader 停、CK3 PID 空、loaded path＋当前磁盘 SHA、四件源资产及 placed save/sidecar 再验、任务总线 RELEASE，然后才生成成功结果。loaded path＋磁盘 SHA **不是**内存映像哈希。任何字段未证都返回 typed unavailable，正式比较与 terminal selected-step 守卫继续关闭。

本轮仅对**旧 v4** 执行无启动静态校验：首次 CLI `--help` 探测超过原有 30 秒而停为环境 RED，外置 `D:/ck3-research-artifacts/war31-h2743-20260928/minimum-producer-static-001/static-help-red.json` 保留该次失败；未准备 profile 或启动游戏。将同一探测的单命令上限有界调整为 90 秒后，重新执行 `--check-static` 得 `static_bytes_verified_no_launch`，外置回执 `v4-check-static-retry.json` SHA-256 `0411102C139A0F5774C5A2EE5744E7B9252517102F4FBF997E75DB306222BCB6`。它验证的是旧 v4 精确资产和 CLI，不是未来新增 WarManager DLL 的准入，也不替代屏幕释放后的新鲜 Steam 离线画面。

当前可复用退出决策的状态仍为 `comparison=unavailable`、`recommended_outcome=null`、`action_literal=null`；本页和未来部分输入不授权 H2743 投降或白和平。
