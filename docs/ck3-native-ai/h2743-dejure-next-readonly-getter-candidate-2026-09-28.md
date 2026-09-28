# H2743 de-jure 退出：下一只读 getter 候选与硬阻断

本页基于 [attempt-11 同帧只读结果](h2743-defender-dejure-readonly-attempt-11-2026-09-28.md)、CK3 `1.19.0.6-steam23530548` EXE 与原版脚本，仅做磁盘静态研究。没有启动 CK3、占用屏幕、调用 setup/resolve/effect/preview 或提交终战。[可重跑校验器](../../ck3_autonomous_player/native_bridge/research/verify_h2743_dejure_readonly_getter_candidates.py)检查完整 EXE/脚本 SHA 和六处有界磁盘 RVA 字节；外置回执 `D:/ck3-research-artifacts/war31-h2743-20260928/attempt-11-dejure-baseline-no-launch/h2743-getter-candidates-static-01.json` SHA-256 `B83133F4E631AF9C75B7816CB56B47C97BD7AD67C82FBFDE82DF7102C7DEB006`。它不是原生 live getter 回执。

## 可实现的最窄候选：休战公式的两个输入

`00_dejure_war.txt` SHA `D8737A22…B6EE` 在胜利支路调用 `add_truce_attacker_victory_effect`；`00_war_values.txt` SHA `ED1CDB6E…FDF3B` 中的 `standard_truce_duration_days` 独立使用五个条件。已有[精确静态公式](h2743-exit-resource-truce-static-envelope-2026-09-28.md)是先按 FLEX、SHORT、LONG、NOMAD_BOTH 修正 1825 天并取 730 下限，最后按 BORDER_RAID_PAIR 乘二。以下两项有现成的原生**只读取数路径候选**，但 H2743 尚无 live 值：

| 条件 | 脚本证据与精确 ABI | 安全读取的边界 |
| --- | --- | --- |
| `FLEX`：攻方 Landolf `30097` 有 `flexible_truces_perk` | 原版 `has_perk = flexible_truces_perk`。EXE SHA `2D00FF31…3DB86` 的 `GetOwnedPerks` RVA `0x2669170` 从 `Character+0x1A8` 取非空对象，直接返回其 `+0x220` span；磁盘 RVA `0x2669174/17B/1A8` 的指令已冻结。`HasPerk` RVA `0x2668EA0` 首先调用该 getter。已有 [LIFE2 ABI](../../ck3_autonomous_player/native_bridge/research/player_lifestyle_snapshot_v1_abi.json) 和 [native span reader](../../ck3_autonomous_player/native_bridge/src/player_lifestyle_snapshot_v1.cpp)将该 span 解释为 `data+0`、`count+0xC`、8 字节 Perk* 行、每个 `Perk+0x18` stable key，最多 512 行。 | 下次版本只在 `Character+0x1A8` 非空且完整 ID/generation 双采样稳定时**复制**该 span；空对象、无效行、重复/不可解 stable key 均 typed unavailable，不能冒作 `false`。原 LIFE2 读口面向当前玩家，Landolf 外部角色复用还需同帧 live 核验；仅列表 key 命中不能在未核 stock predicate 语义前宣称已证明原版 `has_perk` 结果。 |
| `NOMAD_BOTH`：攻守双方均有 `government_is_nomadic` | 原版两方 `government_has_flag = government_is_nomadic`。现有 [combat_v3 原生读口](../../ck3_autonomous_player/native_bridge/src/combat_v3.cpp)以 lookup-only `0x3B588E0` 查 ID、`0x3B58970` 回读精确 key，再用 `CharacterGovernment` RVA `0x26165B0` 与 `Government+0x48` 的有序 int32 span 判断；`+0x48` span 是 `data+0/count+0xC`。其 alive-landed 返回分支在磁盘 `0x26165E0` 读取 `Character+0x1B8`，`0x2616671` 取 landed 对象 `+0x3F0`。既有[原版 evaluator 审计](combat-phase-events.md)把这条路径标为 canonical read-only。 | 复用原生 resolver 和 flag-span 校验，同时绑定两名角色的完整 generation、当前 paused WarID、native revision，并双采样。若任一角色不是已证明的 alive-landed 路径，或 canonical 政府/flag span 不可证，返回 typed unavailable；不得把读失败当 `false`。只发布两个角色原始 observed 布尔与其 conjunction，不发布休战天数。 |

建议下一只读 wire 命名 `xar.ck3.defender-de-jure-truce-inputs.v1`，仅加 `attacker_flexible_truces_perk`、`attacker_government_is_nomadic`、`defender_government_is_nomadic` 的逐域 `observed/unavailable_reason`、原始 source/frame/WarID/双方/CB 身份和双采样证据。它可与现有 V1 baseline 同一 paused transaction 读取，但须新 DLL、独立精确 pin、新 attempt 和 live 校验。即便三项均读到，`SHORT`、`LONG`、`BORDER_RAID_PAIR` 仍为 `null`，`evaluated_days=null`、`persisted_expiry_date_raw=null`、`material_complete=false`。不应把这个部分 wire 接成正式退出动作或费用结论。

## 不能从当前状态安全求值的域

| 域 | 具体阻断 / 最小新来源 |
| --- | --- |
| 运行时 `scope:target`、逐项 Title/封臣变化 | 脚本在 `target_titles` 循环外才调用一次 `setup_de_jure_cb(title=scope:target)`；当前 `[2128]` 是战争目标输入。`0x336AB40` 的虚分派目标/传递写集合、`setup` change 数组列语义、`resolve_title_and_vassal_change` 的最终操作仍未闭合。需已物化且可双读的 effect/WarID 目标槽，或完整静态语义+纯投影。不能调用 setup/resolve 来制造值；见 [V2 作用域门](h2743-dejure-exit-v2-fail-closed-plan-2026-09-28.md)。 |
| `cb_prestige_factor` | `setup` 内 `0x2E9FF30` 的动态处理计数乘 100000 后经 `0x2E9F2C0→0x33590D0` **写** identifier 82 的上下文 row；不是纯读 getter。需证明计数业务含义与最终 factor 槽，或读已经存在且与本 war/effect/revision 绑定的 factor。当前 F 及总威望/名望差额保持 null。 |
| `SHORT`、`LONG` | 原版 `any_character_struggle` 对另一方的 shorter/longer 参数分别判定；当前 bridge 没有绑定相同 struggle/effect scope 的原生只读结果。需枚举 Landolf 的完整 struggle 集、对 Robert 的条件和各自参数，并与 stock evaluator 语义交叉核对；两布尔独立，不能默认互斥。 |
| `BORDER_RAID_PAIR` | 原版检查攻方任意在役战争中另有同 primary attacker/defender 对且 CB `fp2_border_raid`。attempt-11 `active_wars` 仅是**玩家** Robert 视角名册，不证明 Landolf 的完整其他战争集。需全量、同帧、generation-validated 的攻方战争枚举与逐战争 CB/双方绑定，缺枚举完整性就不能填 `false`。 |
| 有向休战的**实际**天数/到期日 | 五个条件全可读时，[现有纯函数](../../ck3_autonomous_player/native_bridge/research/project_h2743_exit_static_envelope.py)只给脚本候选天数；当前有向槽、覆盖/合并规则及未来结算后持久化仍未证。旧 G2 的直接 `0x3373000` evaluator 私有调用曾在首调用退出进程；被动 native callsite observer 只有真实效果路径发生时才有返回，不能为 H2743 反事实投降主动触发。故不可复用它绕过禁用的 effect preview。 |
| 条件资源与总后果 | 两方 14 行余额只是前态。Mandala realm-law flags、合法性资格/title tier、佣兵合同/欠款、hook、vassal opinion、House feud、战俘及共享 war-end 分支尚无完整同帧条件与有符号 delta。需逐分支原生读数、作用对象和可审计纯投影；无直接赔款指令不等于金币 0。见 [attempt-11 效果缺口](h2743-attempt11-surrender-effect-gap-2026-09-28.md)。 |

因此下一安全工程包是 **部分 truce 输入读口**，不是完整条款预览。若无法在候选 DLL 中同时证明非玩家攻方的 perk span 与双方 government flag 的双读身份，连这两个布尔也继续 typed unavailable。正式比较器仍须拒绝 H2743，终战 `selected_step` 守卫保持生效。
