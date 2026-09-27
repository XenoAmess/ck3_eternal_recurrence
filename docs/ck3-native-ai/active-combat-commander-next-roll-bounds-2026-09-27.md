# 现役战斗下一次将领掷骰上下限（CK3 1.19.0.6）

范围：现役 `CombatID` 的主阶段继续演算输入。静态证据绑定 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。086 同暂停帧已经证明 battle-control 与 v3 都能查询、选中将领的 ID 可配对；它没有证明 v3 的假想接战上下限就是现役值，详见 [现役输入缺口](active-combat-forecast-input-gap-2026-09-27.md)。后续 087 已对新读口做独立实机只读回读。

## 原版直达调用链

对该 exact EXE 的静态反汇编：`main_tick 0x2309E80` 在 `CCombat+0x6E4 == 0` 时，于 `0x2309F09..0x2309F1E` 沿 `Combat+0x6B8 -> Province+0x20 -> terrain+0xB8` 取**本场战斗**的地形。`0x2309F21` 把 `Combat+0x20` 攻方 side 与此地形传入 `0x23CBFA0`，返回值写 `Combat+0x6D0`；`0x2309F32` 对 `Combat+0x368` 守方 side 做同一调用，写 `Combat+0x6D4`。因此当前 roll 字段是上一次抽签结果，不是下一次可抽范围；轮次条件还受 `+0x6E4` 控制。

`0x23CBFA0` 从传入 side 的 `+0x74` 读**该场选中将领**的 full-generation CharacterID；它不是任一 `CArmy+0x120` 的 raised-army commander。该函数经 `0x26172C0` 取得角色 modifier aggregator、`0x20AB950` 读取四个 signed Q100000 modifier，按各项分别向零截断：

```text
min = int32[base+0x570ED7C]
    + trunc(modifier[0x108]/100000)
    + trunc(modifier[uint16(terrain+0x76E)]/100000)
max = int32[base+0x570ED80]
    + trunc(modifier[0x109]/100000)
    + trunc(modifier[uint16(terrain+0x770)]/100000)
```

stock base 为 `0/10`。无有效选中将领时，原版 null-object 分支是 `0/0`。函数在算完端点后于 `0x23CC150` 调 `0x356A0A0` 消费全局 RNG；暂停查询只能镜像端点，绝不能直接调用 `0x23CBFA0`。这与 [战前输入](combat-simulation-inputs.md) 的 `ReadCommanderRollContext` 使用同一四项算式和同一角色 modifier 读法，区别是**输入身份**：v3 使用假想接战目标地形与逐军候选将领，现役必须用 `Combat+0x6B8` 的地形与 side `+0x74` 的选中将领。

## 本轮 typed 投影与边界

`ReadBattleControlSnapshotSample` 在已有暂停、真实 CombatID、full-generation ID、daily-dispatch gate、两次 sample 和前后 world snapshot 约束内，向两侧 `ReadBattleControlSide` 传入同一实际 terrain 指针。只读复用 `ReadCommanderRollContext` 算端点，随后复核 side 将领 ID、Combat Province 与 terrain 指针。`active_combat_resume_inputs_v1.observed.side_0/1_selected_commander_next_roll_bounds` 分别发布 `status=available`、signed int32 端点和空 reason，或 `status=unavailable`、null 端点及机器可读 reason。只在**两侧均 available** 时移除 `missing_required_domains` 中的 `selected_commander_next_roll_bounds`；整个 resume 输入仍是 `unavailable`，其余缺域不能由本次推断补齐。

非主阶段或已 finalized 时，当前帧没有可承诺的下一次主阶段掷骰，逐侧保持 `unavailable/next_main_roll_not_applicable_in_phase`。无地形、modifier binding、角色 generation、aggregator、modifier 读取、int32 算术或双采样稳定性时不得用 `0..10` 或 v3 值填空。主阶段将领缺席是明确的 `0/0 available`，与身份/读取失败不同。086 已证两查询同帧可达；新增端点由下述 087 独立 attempt 回读。此静态结果不能被标为现役整场胜率 ready。

## 087 原版冻结存档只读回读

[live-observed] 新独立 attempt `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-roll-bounds-attempt-087` 使用相同第 11 日冻结存档 SHA `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`、exact EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，以及这次新编译 DLL SHA `EC0B57EC5036A10A87FDCBB8CC2E9DAB12EE2629CD442DBB9AC76BF0BAE63B92`。启动前另取随 Steam HWND 移动变化的新截图并直接审阅“离线模式”；ToDesk 未重启，CK3 未联网。两次外层暂停快照同为 `native:3`、public/native revision `4/3`、raw date `53146488`。其间 battle-control 查询 `CALL_COMPLETED`，真实 `CombatID=16777218`、ProvinceID `2633`、subject ArmyID `18` 在守方 side 1、主阶段第 7 日、roll cadence `1`。双方当前 roll 点数为 `7/8`，实际选中将领 CharacterID 为 `34320/29829`；新 typed **下一掷骰**上下限分别为 `[0,10]/[0,10]`，两侧 `status=available`。当前 roll 点数和下一次可抽范围是两个不同量。

原始前帧、战斗查询、后帧的 SHA-256 分别是 `59BBCA62C10D4E900C77C16F697EF090092A7F777824914C4AED4CC8194A7E9C`、`3D8ECE6EE38809E370891668022445C94A9BC57DD6F97898607C93F5F78D753C`、`39C137C40788171FA429D56C8A37994D9D27E3BD26F6038B3763BF20C6968F46`；清场回执 SHA `DE39DF25956F79FDD132D402931F83184C6257BE48D986FFEA38A7F005ADBE36` 记录 capture 返回 0、进程树消失、最终 CK3 活进程 0。可重放的[精确投影器](../../ck3_autonomous_player/tools/project_active_roll_bounds_087.py)和[机器向量](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_active_roll_bounds_087.json)冻结源哈希、同帧身份、数值与清场。`selected_commander_next_roll_bounds` 已从本次回执的缺域列表移除，但整体仍为 `unavailable/same_frame_resume_operands_incomplete`，余四项未补。

本次没有推进一天或拦截真正 RNG 结果，因此验证的是**现役同帧原生输入回读**和静态直达读法对应，尚不是下一 tick 掷骰落点或整场结局的对拍。上述 `0..10` 与旧 v3 候选巧合一致，不能推出其他地形、将领更替或 modifier 状态也一致。
