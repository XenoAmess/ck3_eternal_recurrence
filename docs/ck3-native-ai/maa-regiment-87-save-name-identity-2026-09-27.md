# CK3 1.19.0.6：兵团 87 的存档类型与玩家可见名称

第 11／21 日冻结的原生 v3 `base_inputs` 把 `RegimentID 87` 列为职业兵士，但 `maa_type.key=null`。[先前门禁](maa-regiment-87-human-identity-gate-2026-09-27.md)对**那两份 v3 回执**仍成立。本页另用与两次实机查询配对的不可变原生存档建立**存档身份链**，不回填旧回执，也不把存档类型证据称作同帧 modifier 读数。全部新增来源、Rakaly 解码文本、原版定义和本地化的路径及 SHA-256 冻结在[独立 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_maa87_save_identity_v1.json)；[只读投影工具](../../ck3_autonomous_player/tools/project_native_maa87_save_name_identity.py)核对精确 EXE、Rakaly 0.8.19、存档及每个映射文件。

| 配对来源 | 兵团存档记录 | 与冻结 v3 的连接 |
| --- | --- | --- |
| 第 11 日 `trace-d11-immutable.ck3`，SHA `3F4B2FDA...2BB6953`；Rakaly 解码 SHA `A82FDD3A...79A01C6` | 解码行 `3908059–3908076`：`87={ type="mubarizun" ... army=16777221 }` | 同一 source save SHA 由暂停帧逐团报告保存；v3 中 RegimentID 87 位于 ArmyID `16777221`，目标 ProvinceID `2633`。 |
| 第 21 日 `trace-d21-immutable.ck3`，SHA `E16B8EDE...F7630A`；Rakaly 解码 SHA `48F2EA80...503089B61` | 解码行 `3926034–3926051`：同一 `87 → mubarizun → 16777221` | 同一 source save SHA 与 RegimentID／ArmyID 再次绑定，v3 目标仍为 `2633`。 |

原版 `common/men_at_arms_types/00_cultural_maa_types.txt:578–584` 将 `mubarizun` 定义为 `heavy_infantry`，基础伤害 `45`、基础坚韧 `25`、追击 `0`、掩护 `0`；简中 `regiment_l_simp_chinese.yml:143` 显示 **穆巴里尊**，英文 `regiment_l_english.yml:154` 为 **Mubarizun**。`ProvinceID 2633` 在 `map_data/definition.csv:2634` 是 `MESSINA`，在 `00_landed_titles.txt:14181–14182` 对应 `b_messina`，简中 `titles_l_simp_chinese.yml:6579` 为 **墨西拿**，英文为 Messina。冻结 v3 还记载其目标地形 key 为 `forest`，所属军队是进攻侧 `active_war_enemy`，owner CharacterID `31549`；本页未把该 CharacterID 翻译为人物姓名。

用于下一期视频数字板或智能体日志时，可以写作“**进攻侧穆巴里尊（RegimentID 87，ArmyID 16777221），目标墨西拿（ProvinceID 2633，森林）**”。这行名称的证据级别是“配对存档类型 + 原版定义／本地化”，不是原生 v3 当前帧直接给出的 type key。旧缓存坚韧 `25.00`、暂停帧原生重算和随后 schedule 坚韧 `26.25`（均由 Q100000 原始整数换算）恰好满足 `25×1.05=26.25`，但这只是数值等式；[属性源审计](maa-regiment-87-refresh-source-boundary-2026-09-27.md)列出的 type、class、兵团上下文与目标输入均可能参与，尚无同帧 enum／中间向量读数，不能称某个 `+5%` modifier 为原因。

复核命令使用同一工具的 `--check-sidecar` 模式，向其传入 sidecar 所列 day11/day21 原存档与解码文本、Rakaly exe、原版 game 根目录及精确 `ck3.exe`；该模式只读比较重建对象，不修改任何旧证据。首次生成 sidecar 的 `--output` 模式使用独占创建，拒绝覆盖。
