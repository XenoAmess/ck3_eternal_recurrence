# 骑士个人伤死与兵团伤亡写回：1.19.0.6 静态分界

本页限定原版 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。原版 `00_knight_phase_events.txt` SHA-256 `E8F8E4978BB1AF130D74AA6ED72EE41F014B09C9F324608EBFB0E87D56A5EDB1`；`20_health_effects.txt` SHA-256 `6D7DEF1245D899DE4DEBC42136815BC7F4D14F6A467A8320355507AD03528F12`。证据是只读静态反汇编与原版脚本；本次没有启动游戏，也没有新实机伤亡对拍。

## 同一日更中的两条路径

| 路径 | 精确调用/写入 | 已证明的结果 |
| --- | --- | --- |
| 骑士个人事件 | 主 tick `0x2309EF2/0x2309EFA → 0x23CA2F0`（双方），包装器 `0x23CA34E → 0x23C9900`；火点 `0x23C9A6E` 从当前 Regiment 重读 CharacterID，`0x23C9B11 → 0x3380310` 执行编译脚本效果 | `knight_wounded`、`knight_maimed`、`knight_killed` 的脚本效果施加到角色；这条火点函数体没有直接调用兵团伤亡 writer。具体效果下游是间接调用，不能由这条局部无边关系排除其他状态反馈。 |
| 常规兵团伤亡 | 主 tick `0x2309F93/0x2309FAF → 0x23CB1D0` 算双方出伤，随后 `0x2309FE8/0x230A002 → 0x23CE080` 应用伤亡；其 `0x23CDF70` 中 `0x23CDFC3` 加 combat entry soft `+0x20`、`0x23CDFCB` 扣 entry current `+0x18`、`0x23CDFD5 → 0x239C840` 写 backing hard | 这是兵团人数和软、硬伤组件的写回，不是对骑士角色执行 wounded/maimed/death 脚本。该 writer 函数体没有直接调用骑士事件火点或脚本执行器；不能据此宣称角色与兵团在更大调用图上绝对独立。 |

**顺序是事件先于当天出伤和兵团伤亡应用。** 骑士个人受伤、致残、阵亡不能简单用“骑士兵团分到了多少 hard damage”来抽样；常规兵团 soft/hard 也不能把骑士脚本事件当作一个额外 soldier casualty 写回。个人死亡可改变其后可用角色/兵团身份和下一次属性刷新，这一反馈应另行观察和建模。

## 个人事件的数值门槛

原版 `00_knight_phase_events.txt` 的 `knight_wounded`、`knight_maimed`、`knight_killed` 分别以 `100`、`40`、`30` 作为 **base weight**。它们随后经过事件条件、勇武/特质等 modifier、候选资格与抽签；这三个数不是每名骑士每日 100%、40%、30% 的最终概率。`knight_wounded` 命中时调用 `increase_wounds_effect = { REASON = fight }`；`knight_maimed` 经自己的效果分支；`knight_killed` 的死亡效果使用 `death_reason = death_battle`。

原版 `20_health_effects.txt:1204` 的 `increase_wounds_effect` 以现有 wounded trait rank 为显式门槛：`rank < 3` 走增加伤级的效果，`rank = 3` 则执行 `death_reason = death_fight`。不过 `knight_wounded` 自己的 `is_valid` 排除了已到 rank 3 的骑士；这条死亡门槛不能直接解释成该事件会在 rank 3 命中。`maimed_in_battle_effect` 的四个加权分支中有三个可再调用 `increase_wounds_effect`，是另一条应单独核对的入口。增加伤级的具体跨度还受 `increase_wounds_no_death_effect` 内分支影响，不能把“受伤事件”恒等成只加一级或恒等成死亡。这个 rank 门槛仅属于该脚本效果，**不是**常规兵团 hard/soft 转换门槛；后者的 Q100000 分摊和 backing setter 见[逐团伤亡说明](battle-simulation.md#casualty路由与追击)与[组件写回勘误](combat-component-writeback-and-terminal-reset-static-2026-09-27.md)。

## 智能体边界与后续验证

现有 `forecast_fixed_contact` 明确使用关闭 phase events 的 research envelope，将 `commander_or_knight_death_probability` 留为 `None`，并标出 `unmodeled_phase_events`。因此本次没有可由静态边界直接支持的死亡概率修复；把 100/40/30 填成概率或把 hard loss 冒充角色死亡，反会制造确定性错误。可继续使用这套有标记的近似战斗比较，但角色风险仍是独立的未量化域。

下一步需要在同一 CombatID、同一原生日更中成对采集事件的候选、最终权重、抽签及命中角色前后 wounded/maimed/alive 状态，另采常规 writer 前后的完整 RegimentID、combat entry current/soft 和 backing component hard；随后观察角色退出是否改变下一日骑士 entry/有效属性。静态顺序与脚本内容是 **static-confirmed**，事件实际触发频率、完整下游反馈及个人事件与兵团组件的实机对拍是 **live-unverified**。

只读复跑：运行 [`verify_knight_personal_vs_regiment_casualty_static.py`](../../ck3_autonomous_player/native_bridge/research/verify_knight_personal_vs_regiment_casualty_static.py) 的 `--exe <同哈希原版 ck3.exe> --expected <冻结 JSON>`；其 [冻结 JSON](../../ck3_autonomous_player/native_bridge/research/fixtures/knight_personal_vs_regiment_casualty_11906.json) 保留 13 处 RVA 和机器码字节。哈希、锚点、函数体内直接交叉调用或冻结字节不符时会失败；它不验证实时概率或全局无副作用。
