# E2-04 d06 当前骑士窄读口：静态移植回执

2026-09-29。状态：**代码候选；完整 DLL/injector link 与离线夹具通过，未作实机查询，d06 数值仍 UNKNOWN**。此移植在隔离分支从 #451 `70b450d34e32fa19b4fd07184826f470c610cab0` 开始。未启动 CK3、未读取原片、未把旧 t010 或历史战斗条目当作新帧。

## 精确来源与版本

- 目标二次冷载 d06 存档 SHA-256 `F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A`；原生保存 sidecar SHA-256 `85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B`。旧会话源码 `e4957f17eb2c36aaf8e9e4c4afeaaf16d100b44a`；这些原件身份来自 [封口回执](e2-04-a08-d06-coldload-media-boundary-20260929.md)。新读口须在**新独立 run** 复载同一不可变存档后重新记录其自己的 DLL/injector、EXE、save、sidecar SHA。
- 旧 a08 `a08-d06-observation.json` SHA-256 `8E36F3FE8F2B51D69340940D5444A579F8453AEEFCE7107439DA1ED0E139A56D`；`a08-d06-cold-control.json` 66,331 B、SHA-256 `5469D9F7F066B805581038E8D9735CF51C3616823E5CAAFEF390059E73983C19`。旧 wrapper/native revision `4/3`、snapshot ID `native:3`、date `53146368`、played Character `29829`、War `4`、public CUnit/native CArmy `18`、Combat `16777218`、Province `2633`。这些值只用于静态示例；新 run 重新取其当帧 revision。
- 精确游戏版本 CK3 `1.19.0.6`、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。读口复用当前 `ck3_11906.cpp` 的 `ReadEncounterEffectiveStats`（原生省份评估 RVA `0x239CAE0`）、`ReadCombatKnights` 的 Character `+0xE8` 当前有效勇武与原生效能（RVA `0x28FD990`）交叉校验，仍由 exact-build binding gate 限制。

## 新私有查询合同

`ck3_query_current_battle_knight_v1` 显式接收 subject CUnit、CharacterID、RegimentID，以及 played Character、War、native CArmy、Combat、Province、date、wrapper revision、native revision、snapshot ID。Python native driver 将前三个 ID 编为 `query-current-battle-knight-v1-18-34333-61`，其余作为 request fields；hybrid 只把 wrapper revision 交给外层审查，把 native revision 交给 DLL。命令只在现有 battle-control application-main mailbox 的一次执行中运行：先完整双采样 battle-control，再验证目标团唯一地在该 CUnit 当前 battle roster 中，然后对 generation-valid 团/人物的双向链接、当前 `character+0xE8`、Combat/Army/Province/date 和当前省份原生评估做两次目标采样。world snapshot 在目标读取前后必须相等，桥工作线程完成前还要核原始预期帧。

成功结果的 `current_effective_prowess`、`province_evaluated_damage_raw`、`province_evaluated_toughness_raw` 是新帧当前值；`stored_combat_entry_damage_raw`、`stored_combat_entry_toughness_raw` 是旧战斗 entry 投影的**存储值**，仅作对照。倍率为 `100000`。省份 helper、效能读口、溢出、骑士公式、ID 代际、重复团、日期或采样漂移任一失败均返回 typed unavailable；不回退到历史 `150/30`、UI 姓名或 V3 route/scenario。无自动重发已执行查询。

旧 a08 控制原件尚无 `knight_character_id_raw` 与 `34333` 的当前有效勇武，故本页没有证明 Geoffroy 名单第 5 行 7 勇武属于 CharacterID `34333`，也没有证明 `612.5/122.5` 是本帧团 61 的攻防。新 DLL 候选不可与 E2-05 selector 候选混称同一二进制；各自需独立 SHA 和实机回执。

## 离线验证与待验门

- `xar_ck3_battle_control_snapshot_v1_mailbox_test.exe` 通过：精确 step/帧参数、重复团、错误 Character/Province、fresh/stored 分离、helper typed unavailable、公式不合/溢出、双采样漂移。目标测试使用任意合成 `11/110/22` 数值，只验证代码合同，绝不作为 a08 实机事实。
- MSVC `19.51.36256.0` 对 `battle_control_snapshot_v1_mailbox.cpp`、`bridge.cpp`、`ck3_11906.cpp`、`ck3_11906_adapter.cpp` 对象编译通过，完整 `xar_ck3_bridge.dll` 与 `xar_ck3_bridge_injector.exe` 链接成功；CTest `xar_ck3_native_bridge_battle_control_snapshot_v1_mailbox` 1/1 通过。Python 显式驱动测试 4 项与既有 battle-control 85 项通过，`native_driver.py`、`service.py`、`mcp_server.py` 可编译。
- 仍需独立静态审阅与 exact-build 产物身份冻结，再由新的 managed 冷载 run 只读查询。实机查询要保留原始 request/response、DLL/injector/EXE/save/sidecar 精确 bytes/SHA、session/run ID；任何 unavailable 保持 UNKNOWN。此文档不授权在 E2-05 捕获窗口启动游戏或占屏。
