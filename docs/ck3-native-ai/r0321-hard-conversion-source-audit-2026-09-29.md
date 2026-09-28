# R0321 H3911：同帧围城接战输入的硬伤换算诊断

状态：**原生 precontact 数据对拍完成；整场预测与正式行动仍 RED**。本次只读取固定 WAR 文件及其本机逐字节摄入副本，没有启动 CK3、推进日期、提交命令或改变 `COMBAT_ENTRY_EU_ACTIVATION_ENABLED=False`。

## 来源与结果

- 固定 WAR 原始 v3 摘录 `SOURCE-R0321-H3911-V3-RAW-EXCERPT-v1.json`：2,080,166 B，SHA-256 `865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51`。
- 本机已摄入的 H3911 原始 driver：46,002,331 B，SHA-256 `DE09EA8B3648FAE89F90E5459991BC66AE52154971948DB39C353D05EEAAEE33`。诊断工具重新计算两者 SHA，并验证 driver `/command_history/3919` 与摘录 `command_row` 的解析后完整 JSON 值相等。原行 `index=3920`、step `query-combat-simulation-inputs-v3-2629-2630-a-1-83886367-d-2-50331920-83886484`，查询回执 `native:23`、public/native revision `24/23`、sequence 1。
- 再用生产 v3 strict normalizer 验证目标 2629、入口 2630、有序进攻军 `[83886367]`、有序守军 `[50331920,83886484]`、WarID `16777231`、两侧司令与原生 hard modifier 读口身份。独立输出 `D:/ck3-research-artifacts/r0321-h3911-hard-conversion-parent-verified-20260929.json` SHA-256 `5652B8F18B9170E91B39D8CFB9C48F0A7A497CADE120697D3D23C9CF597F35DE`。

| 防守受伤一侧 | 本侧 hard modifier | 对方 enemy hard modifier | 冬季项 | 原版 Q100000 换算候选 |
| --- | ---: | ---: | ---: | ---: |
| 玩家进攻军 83886367 | 20,000 | 0 | 0 | **36,000** |
| 目标省两守军 50331920、83886484 | 25,000 | 25,000 | 0 | **45,000** |

公式为现有原版 `hard_casualty_conversion_raw`：`trunc(30000 × (100000 + 本侧 own + 对方 enemy + winter) / 100000)`。`research_envelope.py` 当前对 `apply_main_phase_casualties` 不传这三项，故两侧研究模型都使用默认 **30,000**。H3911 首帧观察直接证明该默认值与本假设场景的原生 local-shell 读数不同；这会影响研究模型的硬伤尾部，不能把旧研究分布当作已校准风险。

诊断实现见 [`hard_conversion_diagnostic.py`](../../ck3_autonomous_player/src/xar_autoplayer/simulation/hard_conversion_diagnostic.py) 与 [`assess_r0321_h3911_hard_conversion.py`](../../ck3_autonomous_player/tools/assess_r0321_h3911_hard_conversion.py)。后者仅接收精确的 H3911 文件，目标输出必须不存在。普通与 `-O` 模式下 `test_hard_conversion_diagnostic.py` 各 3/3 通过；负例覆盖守军顺序、司令、缺原生读口、冬季 guard 和 bool 冒充整数。

## 仍缺的原版闭环

1. 这四个 hard side raw 来自 v3 **hypothetical precontact local shell**；尚未与同帧真实 `CCombat` 两侧的 `0x18C/0x18D` 及原生主阶段逐团 soft/hard/owner ledger 对拍。H3911 当前未开战，不能为此强行接敌。
2. 即使首帧数值吻合，后续每日司令、加成、战宽、入列、伤病事件和撤退都可能改变转移。现有 managed one-day phase trace 可记录七边界和 outgoing/counter/join 的一部分，`full_mutable_transition_bundle_complete=false`。应从独立原生 battle trace 扩充逐团当前/soft、owner hard、真实效果及同日下一日刷新，逐日比较原版与纯函数的第一个差异。
3. 之后仍需 loaded playset 与 phase effect source/evaluator、不同存档留出校准、人物尾部、attack/avoid/wait 的同帧成本和正式 EU。该诊断的 `actual_combat_parity=false`、`future_daily_refresh_modeled=false`、`planner_usable=false`、`active_attack_allowed=false` 固定；它不产生胜率或允许 R0321 进攻。
