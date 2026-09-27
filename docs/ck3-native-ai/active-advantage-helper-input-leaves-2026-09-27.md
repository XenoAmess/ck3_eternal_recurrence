# 原版现役优势两个输入叶子：角色整数与战斗标志（2026-09-27）

本页只审 CK3 `1.19.0.6` 的 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。它接续[原调用分项观测器](active-combat-original-advantage-observer-2026-09-27.md)，从将领和 side 聚合 helper **各固定一条输入读取链**，并不以已观察的 helper 返回值构造未来日优势。此次未启动 CK3，未改 103 使用的 DLL。

只读 [`verify_active_advantage_leaf_inputs.py`](../../ck3_autonomous_player/native_bridge/research/verify_active_advantage_leaf_inputs.py) 的 `--exe <ck3.exe> --expected ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_leaf_inputs_11906.json` 同时核对 EXE 哈希、已有缓存链及 `.pdata` 来源、13 处精确指令字节、调用顺序与条件分支目标。冻结[叶子夹具](../../ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_leaf_inputs_11906.json) SHA-256 为 `DFA0247F843D0C91EFB6CBE2CC6C6B7C4E05CD8701A0BE85EE39F6EE3EEC610B`。对应 verifier 聚焦测试会拒绝角色读取字节或分支目标的篡改。

| 链 | 已证明的原版机器事实 | 对续算输入的意义 |
| --- | --- | --- |
| 将领 helper 的角色整数 | side total 在 `0x2307E7A` 将已解析角色指针放入 `R8`，`0x2307E88` 调 `0x2307680`；helper 的 `0x23076B8` 读取 `int32 [R8+0xD8]`，`0x23076BF` 乘 `100000`，`0x23076C6` 写入初始输出 qword；其后仍有 helper/modifier 累加，最终返回值在 `0x2307E90` 加入 side total。 | `selected_commander_character_id` 只标识角色，不能代替当次角色对象 `+0xD8` 的有符号值或完整 helper 返回。[后续时序核查](active-advantage-paused-input-timing-2026-09-27.md)结合已有技能 ABI，已把 `+0xD8` 闭合为统率 martial 整数点；此行保留原研究当时的证据边界。 |
| side 聚合 helper 的战斗标志 | side total 在 `0x2307EB5` 调 `0x2307230`；该 helper 的 `0x230725D` 保留传入的 Combat 指针，`0x23074C9` 比较 `byte [Combat+0x6FD]` 与零；`0x23074D1` 零值跳至 `0x23075E9`，绕过 `0x23075E6` 的条件项加法，再继续后续计算。非零只允许进入该块，不保证最终聚合贡献必定非零。 | 该字节是当前调用的一个分支输入，不是可从当前 roll、人数或 helper 总返回残差反推的常数。[后续时序核查](active-advantage-paused-input-timing-2026-09-27.md)已定位构造时从目标 Province 谓词写入；中途间接写入与跨日变化仍未闭合。 |

现有 [`active_combat_resume_inputs_v1`](../../ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py) 的 `observed` 明确包含同帧 roll、选中将领 ID、下次 roll bounds 和兵团/军队数；它既无角色对象 `+0xD8` 的同次读取，也无 Combat `+0x6FD` 的同次读取或两者下一日转移。native 生产者继续列出 `next_day_non_roll_advantage_sources` 缺域，`status=unavailable`、`input_observation_ready=false` 必须保持。即使 103 的原调用 observer 对拍出 `commander_raw` 与 `aggregator_raw`，那也是**发生后的输出**，不能据此把未来日叶子输入标成 available。

若要把这些叶子用于整场续算，后续核查已确认 `+0xD8` 为统率、`+0x6FD` 的构造写入时点；仍需闭合无将领时的 fallback 对象数值、统率的后续写入、modifier 来源与下一次刷新结果。随后按同 CombatID、side、角色 generation、日期，在游戏原调用前读取叶子并与原调用分项及下一日缓存消费对拍；动态将领替换、事件、增援、撤退各需覆盖。没有这一套时序证据，不得把 `commander_raw`、`aggregator_raw` 作为先验输入，也不得移除续算缺域。
