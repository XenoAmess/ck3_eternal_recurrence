# 现役战斗：同帧反制条件出伤用于观察节奏（2026-09-27）

## 改动与边界

生产 `strategy.py` 在现役主战阶段原先只计算 **neutral advantage、no counter** 的条件出伤。它已用 `battle_control_snapshot_v1` 的实际 `final_combat_width`，所以战宽本身没有漏接；首次接战 `forecast_fixed_contact` 也已用 v2/v3 的 `target_province.precontact_width.final`。两种战宽分别属于真实 CombatID 与假设接战，绝不能互换。[战前/战中入口审计](active-combat-strategy-forecast-ingress-audit-2026-09-27.md)的已有 ongoing CombatID 拒绝门保持原样。

现在只在暂停同帧的 battle-control 经生产 normalizer 认可、阶段为 main、尚无 winner/finalizer、双侧 `full_side` 名册及兵量缓存一致、`final_combat_width>0`、`active_counter_inputs_v1.status=available` 且双侧 class/stack/target/context census 完整时，计算一组 **same-frame counter-conditioned、neutral-advantage** 出伤。反制核按当前逐团 Q100000 `current_chunk_raw` 重新累计本类 chunk 和对方按目标类施压，逐类算 retention，再对对应职业兵士的有效伤害逐项相乘；征召兵保持原值。最后两侧仍调用现有 `outgoing_damage_raw`，共用本帧实际战宽和当前人数。它与老的 neutral/no-counter 基准并列回报；只用更具体的当前帧反制基准判定是否出现严重条件劣势，且该判定**仅缩短可恢复的下一次观察步长**，不能提交开战、撤退或宣称整场胜率。

[098 双侧原生日界输出](active-counter-output-trace-attempt-098-2026-09-27.md)和[100 相邻日回放](active-counter-output-cross-check-100-2026-09-27.md)在 CK3 1.19.0.6、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 下取得两侧 13/13 类条件公式零差；100 的侧 0 class 8、侧 1 class 0/1 各达 `10000` retention，其他类 `100000`。这些原生向量各自来自**其实际日界**，不是可以灌进更早暂停帧的未来数据。本次生产接线只消费当前 battle-control 自己的同帧 census，并在回执中固定标 `next_tick_retention_validated=false`。下一日可能有增援、属性/反制上下文刷新、优势与掷骰变化；现役 `active_combat_resume_inputs_v1` 仍是 `unavailable`，`whole_battle_win_probability` 继续为 `null`。105 正在进行的同源增援日采样可用作后验检查，不能预先充当本帧输入。

## 可复算受控向量

单测从已有 battle-control 合法结构构造一组**合成**双方职业兵士与定向反制（不冒充实机新战例）。同帧 neutral/no-counter 的己/敌出伤基准为 `313200000000 / 347760000000` Q100000；本帧类 retention 为 side0 `[10000,100000]`、side1 `[100000,100000]` 后，己/敌条件出伤为 `156600000000 / 347760000000` Q100000。合成己方存量与留存率没有触发旧的数量劣势门；无反制切片时也没有触发 neutral 出伤劣势，策略选既有 `battle-decision-epoch` 等待；同帧完整反制切片触发条件出伤劣势，改选 `life-advance` 下一日观察。两路都不产生整场概率或进攻/撤退授权。缺反制切片保留 neutral/no-counter 路径；读口身份、名册或日期不一致由原有 battle-control normalizer 拒绝。

聚焦验证覆盖真实核函数的出伤调用、同帧合成数值、行动步长差异和缺反制回退；此次未启动 CK3。后续须把 105 的 next-day 原始反制输出与暂停帧输入分别标时再比较，才能判断条件模型在增援日的时序偏差。
