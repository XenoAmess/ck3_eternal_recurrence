# CK3 1.19.0.6：穆巴里尊 87 号兵团的类型、修正与 `25 → 26.25` 边界

本页继续[兵团 87 来源审计](maa-regiment-87-refresh-source-boundary-2026-09-27.md)和[配对存档名称链](maa-regiment-87-save-name-identity-2026-09-27.md)，不改写两份原始回执，也不声称已查明 `+5%` 的具体来源。结论是：**原生求值的固定坚韧 enum、class 行入口、定点应用顺序与兵团到军队的来源路径可以静态核对；有效属性 type 与 v3 counter type 来自兵团两个不同偏移，是否同指针仍未观测。** 因此现有 class index `0` 不能直接拿来读有效属性 class 行，更不能仅用 `25×1.05=26.25` 给修正归因。

本次只读校验绑定 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、当前 bridge 源码、[两份冻结 v3 原始回执](maa-regiment-87-human-identity-gate-2026-09-27.md)及[配对存档身份 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_save_identity_v1.json)。[新只读投影](../../ck3_autonomous_player/tools/project_native_maa87_dual_type_source_boundary.py)产出[机器边界](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_dual_type_source_boundary_v1.json)，其 SHA-256 为 `D1818747CEC9E3335C8368BE6BB3B7A55F3DA2F0776F6E6A22FF55C79A462660`。未启动 CK3，未产生新的原生运行时读数。

| 问题 | 精确来源 | 可以确认什么 |
| --- | --- | --- |
| 87 的原版兵种 | 第 11／21 日配对存档 `87={type="mubarizun", army=16777221}`；原版定义 `heavy_infantry`、基础坚韧 `25` | 玩家可见名称为“穆巴里尊”；这仍是**存档身份**，不是 v3 求值时的类型指针回读。 |
| v3 counter class `0` | bridge `ReadCombatCounter` 从 `CRegiment+0x18` 取 `inner_type`，再取 `inner_type+0x270`；第 11／21 日 v3 的 87 均为 `counter.class_index=0` | 这是 counter 所用的 class。v3 的 `maa_type.key=null` 同时保留，不能据此断言有效属性 type 为 null。 |
| 有效属性 class | exact EXE `0x2C8F1D6` 从 **`CRegiment+0x118`** 取 type，`0x2C8D6B7` 读这个 type `+0x270`，通过全局 class count 选择步长 `0x58` 的行 | 两个 type 的**指针相等性未采**。即使两个 `+0x270` 最终都为 `0`，也须同帧读取后才能把 class 行绑定为本团实际行。 |
| 固定坚韧修正 | `0x2C8D8E0/0x2C8D902/0x2C8D92B` 对应 enum `0x1AC/0x1AD/0x1A7`：`MOD_MAA_TOUGHNESS_ADD`、`MOD_MAA_TOUGHNESS_MULT`、`MOD_ARMY_TOUGHNESS_MULT` | 均经 `0x2940E80` 读实际值；原始 v3 **没有**返回这些分量。 |
| class 动态坚韧修正 | `0x2C8D94D` 读选中 class 行 `+0x2E` 的 add enum，`0x2C8D97E` 读 `+0x3A` 的 multiplier enum；`0xFFFF` 则跳过 | 还缺实际行内容、enum 名称与实际返回值，不能把它们默认作零。 |
| 军队来源路径 | `0x2C8F374 → 0x2396490`；后者从 `CRegiment+0x28` 取另一个完整兵团 ID，经已知 `CRegiment` storage 解析并读 `+0x140` ArmyID；返回对象的 `+0x38/+0x44` 被 `0x2C8F3DB` 遍历 | 路径可静态追踪；尚未回读 87 的 `+0x28` 和实际返回 ArmyID，不能把本次修正简单贴给 owner CharacterID `31549` 或某一骑士。 |
| 定点应用与目标上下文 | `0x2C8F7B9 → 0x23C2DF0`；其中 `0x23C2EE9` 选 `Stats38+0x20` 坚韧槽，`0x23C2F39/+0x3D` 加对应向量分量，`0x23C2F55/+0x6C` 取 multiplier 并乘；随后 `0x2C8F8E2..0x2C8F928` 从目标 Province 上下文取六维向量，把其 `+0x20` 再加到坚韧 | 应用阶段的 Q100000 形式是 `trunc((此前坚韧原始整数 + 累积 add) × 累积 multiplier ÷ 100000)`；这**不是**最终完整公式，后续目标上下文也能改值。 |

第 11／21 日均见旧控制缓存 `2,500,000`、暂停直接求值和下次 schedule `2,625,000`。仅凭两个终值，既不知道旧缓存形成时是哪组修正，也不知道新求值中基础、固定 enum、动态 class enum、目标向量各贡献多少。先前列出的原版脚本 `army_toughness_mult=0.05` 和 `heavy_infantry_toughness_mult=0.05` 仍只是**候选示例**；本次没有将其中任何一项提升为生效事实。

下一次最小被动同帧采集先以 `CombatID 16777218`、RegimentID `87` 的全 generation、ArmyID `16777221`、目标 ProvinceID `2633`、source date 与线程绑定 `0x239CAE0` 外层调用。每次有效求值必须同时只读记录：`CRegiment+0x18/+0x118` 的指针与 `+0x270` class 值、`CRegiment+0x28` 及 `0x2396490` 返回 ArmyID、有效属性 class 行 `+0x2E/+0x3A` enum、三个固定坚韧 enum 与两个动态 enum 的 `0x2940E80` 原始返回、基础坚韧、`0x2C8F7B1` 应用前 add/mult 向量、`0x23C2DF0` 后坚韧、目标六维向量及最终 `Stats38+0x20`。记录每个指针的可解析 generation 身份，并在 hook 内限制为本团、固定容量、默认关闭；不得从探针主动调用原生求值器或状态 mutator。

要解释 **`25 → 26.25` 的变化原因**，还必须在旧 entry 缓存形成边界、暂停直接求值和下次 schedule 入口分别采同类值。若只有后两者，只能解释当前 `26.25` 的组成，不能说明旧 `25` 为何不同。任一时点的 type 指针、目标、实际 class 行、来源军队、线程或完整兵团 ID 未绑定，整次归因拒绝；不得用数值吻合补洞。目前 Steam 离线画面新鲜度门未恢复，故仅留此采集合同，不启动新实机 attempt。

复核时先验证本 worktree 使用的 Python 环境有 `pefile`；本次因独立 worktree 没有相对 `.venv`，显式使用主 worktree 的 `tools/.venv/Scripts/python.exe`（`pefile 2024.8.26`）并确认精确 EXE、两个 v3 回执、sidecar 和 bridge 源码存在。运行 `project_native_maa87_dual_type_source_boundary.py --help` 查看五个必选来源参数，再以 `--check-sidecar` 指向上述机器边界文件；校验只读，不连接 CK3。
