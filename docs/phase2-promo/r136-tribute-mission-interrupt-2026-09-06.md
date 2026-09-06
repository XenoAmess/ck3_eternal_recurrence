# R136 管理周期贡礼事件阻塞取证（2026-09-06）

## 结论

- R136 在 frozen source `acc3aeb7b9b4193f725f64e5d0d8959ede55042e` 与 R130 正式产品投影下成功加载，玩家管理者 `32904` 保持存活、有地且绑定稳定。
- R135 的 `culture_notification.1111` 已按严格契约关闭；B1 随后继续以 5 速从 `date_raw=53147040` 推进到 `53150160`，仍为 active。
- 原版 `tribute_mission.1002` 在该帧暂停流程。它不是产品 RED，也不是角色死亡；它是接受人决定如何处理“人贡”的真实原版玩法事件。
- 该事件不能当作无效果通知。实机为妾室贡礼分支：authored option 3 隐藏，可见 native indices 为 `0/1/3`。option 1/2 会把角色加入玩家宫廷或纳为妾室；选择 native index 3 只在当前事件链记录拒收人贡，并进入后续原版贡礼回报决定，不改天朝二期产品状态。因此 R137 只允许在完整帧严格匹配后选择该拒收分支，后续事件必须另行取证，不能连带盲选。

## 精确实机形状

- root：character `32904`
- 玩家别名：`recipient`、`tribute_mission_target`、`overlord_scope`、`receiving_character`
- 贡使别名：`actor == tributary_scope`，实机 character `34077`
- 人贡别名：`secondary_recipient == concubine_character == human_tribute`，实机 character `54393`
- unavailable character scopes：`secondary_actor`、`intermediary`
- 泛型 scopes：`opinion_of_tributary` value、`tribute_reward_type_treasury` value、`saved_innovation` culture_innovation
- saved scope 总数：14，名称集合必须完全一致
- snapshot option count：4；rendered/native mapping：`0→0, 1→1, 2→3`
- fixed selection：按钮 4 / native index 3

## 来源与证据

- 原版源文件：`game/events/dlc/tgp/tgp_tribute_mission_events.txt`
- CK3 1.19.0.6 原版源文件 SHA-256：`CE127F15422E121D74F0F417BCC5448D31AFD65A7C03DB9FD4BD1E6D35089CBA`
- 实机事件帧：`Z:\p2m136_a\manager-cycle-recovery.json`，SHA-256 `07D975CA1FFDC6392DF1CA5ACB7D678602247D485E048802CAB44363458B0D05`
- runner report：`Z:\p2m136_a\runner-report.json`，SHA-256 `6BA3770E2623125CB15805DE5B6295678AB574DE40010B9AA0A444FF462F518C`
- cleanup：`Z:\p2m136_a\09_phase2_native_session_cleanup.json`，SHA-256 `711FB33B88BD9AD3C6220EC7468B1AA2BC753A3D8E2386F7A13E032294CBABC7`
- R136 不是 manager-owner terminal，不累计用户授权的“三次角色死亡”条件。

## 文件边界

本轮不再扩张既有的大型 checkpoint runner。新增的管理周期随机事件契约测试单独放在 `tools/test_zg361_phase2_manager_recovery_interrupts.py`，并由 seed preflight 以普通和 `-O` 两种模式执行。后续同用途随机事件继续进入该分片；达到 10 个测试场景前评估再分片，原则上不超过 20 个。
