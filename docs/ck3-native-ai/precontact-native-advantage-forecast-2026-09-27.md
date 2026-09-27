# 战前有界预测使用同帧原生优势值（2026-09-27）

## 接线结果与证据边界

[static/source-confirmed, no new live run] CK3 **1.19.0.6**、原版 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的 [v3 原生优势读口](combat-simulation-inputs.md) 已经输出 native `0x23C8A60` 选中的 battle commander，以及 `0x2308D50/0x2307CB0` 原始 helper 对拍通过的零掷骰优势。此前策略层虽查询 v3，却在 `forecast_fixed_contact` 里按最大兵数选 army，并用 generic commander 与静态地形近似重算优势；二者可能与该帧原版不同。

本次只在**同一次 v3 查询**的 `phase_event_inputs.advantage_model.resolved_dynamic` 为 available、`helper_status=original_helpers_matched`、`original_total_helper_match=true`、零 roll 策略和 scenario/army/commander 身份均匹配时，将 selected commander 与 `resolved_advantage_at_zero_roll_raw` 输入研究核。`advantage_model` 是 `phase_event_inputs` 的**直接子项**，不在 `raw` 内。两侧 side total、base 加减与 original helper 再作本地算术核对；输出另给整个 model 的 canonical JSON SHA-256。已入库的原生 v3 production wire fixture SHA-256 为 `ABB94ABB054B03BFBAE3BD53736F33BC3F5332E3CDACC9ADD36267232AD267E7`；其 selector 为 attacker CharacterID `16777218`、defender 无将领，零掷骰优势 `-600000`，即 **-6 点**。该 fixture 本身还包含 ongoing CombatID，所以只能验证 DTO 提取，不能借它声称前接战 trial 实机对拍。

研究核每个 trial 日取 `A_raw = zero_roll_raw + (attacker_roll - defender_roll) × 100000`，优势方出伤倍率取 `100000 + floor(|A_raw| × 5000 / 100000)`；例如原生零值 `-600000` 且当日掷骰分别为 `7/0`，则 `A_raw=100000`，进攻方倍率 `105000`（1.05）。roll 调度仍按被原生选中的将领的同帧有效上下界；若原生明确无将领，则该侧不抽将领 roll。旧的 integer-point 路径保留给没有可信 native advantage 的条件输入。

## 回退与未来日限制

- v3 phase 原子 `unavailable` 且同一 payload 的 v2 base 仍 `input_observation_ready=true` 时，明确回退到既有 generic/terrain 近似，并在 `advantage_input.fallback_reason=phase_event_inputs_unavailable` 标记。旧 v2/base-only 夹具则标 `native_phase_not_in_payload`。生产围城解围策略也准许这类完整 base 的有界试算，不因 phase 原子不可用而丢掉现有计算。
- v3 phase 宣称 available 但 schema、原生来源、辅助计算、选中将领、军队顺序或倍率不一致时，返回 `model_unavailable`，不悄悄套用近似值。已在战中的所选军队继续拒绝战前预测，必须使用现役续算入口。
- `advantage_input.source=same_frame_v3_native_zero_roll_frozen_future` **只表示初始同帧的原生非 roll 优势条件**。trial 将该值和所选将领冻结到未来每一天；未来天气、补给、债务、地点、将领变更与其他非 roll 来源没有逐日重新读取。`future_daily_refresh_modeled=false`、`same_frame_native_advantage_frozen_for_future_days`、`future_daily_non_roll_advantage_refresh_unmodeled` 与准入回执的 `future_daily_non_roll_advantage_refresh` 风险字段共同公开此限制。它不是未来逐日原版对拍，也不使预测成为校准的原版整场胜率。

## 具体回归向量

聚焦单测把已有 paused-live v2 接战输入作为**冻结 base**，再合成一个形状与正式 v3 相同的优势切片；这是单元测试的受控输入，**不是该战局的真实 v3 查询**。固定 16 trial、4 日，其他输入和随机种子相同：旧 generic/terrain 路径的玩家 p90 硬伤亡为 `1,450,921` Q100000（约 `14.50921` 人）；合成 `zero_roll_raw=-600000`（-6 点）后为 `2,321,550` Q100000（约 `23.2155` 人）。两者均 `0` 胜、`0` 负、`16` 未决；这证明原生优势值进入真实伤亡演算，不提供真实胜率校准。把 helper 改动 1 个 raw 单位或选中将领改成不存在的 ID，模型都返回 `CombatInputError`。独立的原生 v3 fixture 测试验证上述真实 wire 的 `-600000` 与选中身份。

验证：`test_general_battle_forecast.py`、`test_combat_provisional_defense_canary.py`、`test_active_combat_resume_kernel.py` 聚焦运行通过。此次没有启动 CK3；后续应以实际**前接战** v3 同帧回执比较预测输入、日内优势 helper 与最终战果，尤其按天检查非 roll 优势刷新。
