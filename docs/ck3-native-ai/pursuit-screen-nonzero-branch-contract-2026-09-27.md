# 追击期非零掩护：静态分支向量与下一次原版对拍合同

状态：**原版 1.19.0.6 的既有静态调用链 + 离线回归；非新增实机确认**。本轮没有启动 CK3。原版 EXE SHA-256 的既有研究身份为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；本轮环境未取得 EXE bytes，因此没有重新验证该哈希。精确函数、字段和算序见 [战斗模拟专题的 pursuit / screen 节](battle-simulation.md#pursuit--screen)。

## 现有实证覆盖到哪里

[attempt-004 的三日追击](battle-simulation-episode01-live-case.md#2026-09-26-追击三日同一独立回放的逐团与账本对拍)在同一第 28 日原版输入上独立连算，第 29–31 日败方软伤 `72/72`、可读逐团硬伤 `69/69` 零差，总硬伤 `6,294,269` Q100000。其追击出伤每天 `75,203,000`，**败方掩护聚合每天为 0**。首日输入的退却损失修正是 `-25,000`，故这不是“所有修正都为 0”的样本。胜方条目即使有非零 `screen_raw`，也不能替代败方 `screen_raw × soft_raw` 的验收。现有报告只证明该样本的方向和整数链；不能把它扩写为非零败方掩护也已 live-confirmed。

`combat_core.apply_pursuit_day` 当前按既有静态链在每个 entry 乘法后截断，相加得到 `toughness_soft_raw`、`pursuit_damage_raw`、`screen_raw`；再以 `extra=max(0,pursuit-screen)`、`floor=max(base if extra>0 else base-screen+pursuit, minimum)` 各算两域的每日预算，最后按存储顺序处理第一遍比例和第二遍余数。审阅该路径没有发现与现有静态公式冲突的代码分支。`research_envelope` 传入冻结的初始 entry，并显式假定 `omit_unobserved_pursuit_modifiers=True`；它也固定完整三日追击，不获取真实逐日有效属性或修改后的 `0x105/0x18B`。所以研究 envelope 的胜负分布不能借用上述追击零差作为整场原版校准。

## 非零掩护压过追击的静态向量

这是按上述 **静态公式手工推导**、由 [`PursuitGoldenTests.test_screen_dominates_pursuit_static_boundary`](../../ck3_autonomous_player/tests/unit/test_combat_simulation_core.py) 锁定的反例分支；不是原版实机回执。单位均为 Q100000 raw。败方按原生顺序有 levy 1、levy 2、MAA 3：

| entry | soft | toughness | screen |
| --- | ---: | ---: | ---: |
| levy 1 | 7,000,003 | 1,000,000 | 2,000,000 |
| levy 2 | 5,000,007 | 1,200,000 | 500,000 |
| MAA 3 | 3,000,011 | 2,000,000 | 1,000,000 |

胜方一个 MAA 的 `current=9,000,013`、`pursuit=600,000`；追击效率修正 `0`，败方损失修正 `+25,000`，合并倍率 `125,000`。每个乘除之后立即向零截断：

| 检查点 | raw | 推导 |
| --- | ---: | --- |
| toughness-soft | 190,000,334 | `70,000,030 + 60,000,084 + 60,000,220` |
| pursuit damage | 27,000,039 | `mul(mul(600,000, 9,000,013), 50,000)` |
| screen | 195,000,205 | `140,000,060 + 25,000,035 + 30,000,110` |
| base / minimum | 9,500,016 / 1,900,003 | toughness-soft 各乘 `5,000 / 1,000` |
| extra / floor | 0 / 1,900,003 | 掩护压过追击，`proposed=-158,500,150`，由 minimum 托底 |
| floor/toughness ratio | 999 | `div(1,900,003, 190,000,334)`；不能当作理想的 `1,000` |
| levy daily A/B | 0 / 49,950 | 冻结初始 soft `12,000,010`，逐步乘 ratio、`125,000`、再除 `3` |
| MAA daily A/B | 0 / 12,487 | 冻结初始 soft `3,000,011`，同样的截断顺序 |
| levy 1/2、MAA 3 hard | 29,138 / 20,812 / 12,487 | levy 第一遍为 `29,137/20,812`，剩余 `1` 给存储顺序首项；MAA 单项余数 `1` |
| 当日总 hard | 62,437 | 两域预算之和 |

这个向量同时检验 `screen>pursuit` 时 `extra=0`、minimum 托底、`999` 的整数比率以及最早 entry 承接余数。它不能替代逐团原版输出校验。

## 下一次受管实机的最小采集与验收

1. 从独立、可恢复的原版战例自然取得至少一个**败方 `soft_raw>0` 且有效 `screen_raw>0`** 的 pursuit day。冻结 EXE/DLL/save/checkpoint 哈希、CombatID、日期 raw、phase/day、winner side、双侧指针/entry census 和原生存储顺序；首日 `CCombat+0x6E8/+0x6F0` 的 levy/MAA 初始 soft pool 必须同一边界可读。不得拿胜方 screen 或 earlier paused control 的有效属性代替败方当天值。
2. 在 `0x23CD2E0` 输入边界被动观察每个 entry 的 kind、regiment ID、`+0x18 current`、`+0x20 soft`、`+0x48 toughness`、`+0x50 pursuit`、`+0x58 screen`，以及胜方/败方 `0x105/0x18B` **side-effective** 修正；同时记录 skip-pursuit byte、recipient thread、date/revision。旁路只读，不调用 tick 或刷新 helper。若来源跨线程、同帧身份不一致或任一字段缺失，整次不计作 live parity。
3. 被动保存 `0x23CD660` 两域 A/B 入参、cap 前后预算和逐 entry soft/hard 写回；另从下一 paused 原版帧读回 soft、可读的逐团 hard 与参战者 hard 总账。逐个核对 `toughness×soft`、`pursuit×current`、`screen×soft` 的截断、`extra/floor` 分支、每日预算、两遍余数和 backing component 整数写回。null 硬伤字段保持 null，不当作 0。
4. 至少一个 `screen>pursuit` 样本验证 `extra=0` / minimum 分支；另一个 `0<screen<pursuit` 样本验证双 component 同时存在。若还要推广至整场时长，独立记录 phase day `1/2/3` 和 day `4` 的 terminal 转换、跳过追击与提前穷尽情形，并验证模型无需用次日原版状态重新喂入就能连算。每个自然条件是单独覆盖项，不能因本静态向量通过而标为实机完成。

原版截图新鲜度与 Steam 离线 UI 仍是启动门；参见[受管桌面截图合同](steam-offline-frame-freshness.md)。当前门未恢复时，不启动新 CK3 run，保持现有 attempt 的 RED/部分证据原样。
