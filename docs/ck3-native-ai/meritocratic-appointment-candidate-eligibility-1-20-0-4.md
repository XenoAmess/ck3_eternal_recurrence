# R58 贤能任命：一次有限静态资格定位

**贤能池不是行政的 holder_close_family 池。** 本机 CK3 1.20.0.4 原版 `common/succession_appointment/meritocratic_governor.txt:1–5,64–68`：文官和武官均使用 `level=merit`、`allowed_candidate_tier=lower_or_equal`、`cooldown=yes`。官方 `_succession_appointment.info:19–25` 明确 level 模式的默认候选为达到相应等级的合资格人物，并忽略 `default_candidates`。不应把 R57 family 来源解释套给 R58。

| 现成官方源 | 实际规则及导航含义 |
| --- | --- |
| `common/defines/00_defines.txt:1860` | `APPOINTMENT_MERIT_TIER={0 1 1 3 5 7 9}`；注释明确按目标头衔tier规定候选所需货币等级。较低tier对应较低门槛，可优先实际确认的较低tier自然title。 |
| 同文件`:249` | `MAX_APPOINTMENT_BY_LEVEL=5`，注释为期望继承人数，超过时丢弃较低等级人物。不是“所有人无条件最多5名”，也不能由当前pool4反推本场具体缺人原因。 |
| 同文件`:1866` | `RECENT_APPOINTMENT_COOLDOWN=1825`；原版类型启用cooldown。当前31883是否处于该状态没有实际数据。 |
| `_succession_appointment.info:32–41` | 有地人物获任较低有地头衔须是该头衔的de-jure liege；lower_or_equal也允许同tier。独立皇帝身份本身不证明所选实际title满足该关系。 |
| `common/laws/00_succession_laws.txt:1711–1756,1792–1837` | civic/military法分别接meritocratic_civic_governor / meritocratic_military_governor；现持法者的军事契约flag决定两类law适用。这里can_keep/potential中的`is_independent_ruler=no`针对持法者，不能直接当“独立候选一律非法”的证明。 |

文武资格源码边界：`common/scripted_triggers/10_tgp_triggers.txt:312–334` 定义 civilian/military trigger，分别检查 appointment_trait_override 对应教育trait，或 civilian_province / military_province trait flag。但这次有限源码不能证明该trigger就是当前native merit池的硬剔除调用，不能据此认定31883具体失败。`common/script_values/07_appointment_values.txt:968,1153,1253` 是军务、文官、非军务分数；分数/教育加成不能自动改称入池资格。

既有fixture `tools/ck3_mod_acceptance_cases/xqol_followup_cases/meritocratic_appointments/fixture/events/zqagov_events.txt:9–16,27–41` 只确认1066.9.15的自然e_goryeo持有者切为独立贤能人类，及有地臣属存在两类任命法；没有保证该人类对具体title的merit等级、冷却、de-jure关系或完整池成员资格。因此当前只能证明fixture前提不足以保证人类入池；不能证明原规则与独立人类要求绝对冲突，也不能替R58指定唯一底层原因。

Operator可用的唯一规则导航建议：沿本场已有合法GUI/typed入口，优先玩家**实际de-jure范围内、较低tier、仍有原目标civic/military有效law**的自然臣属title。先省略breakdown_character_id读当前真实完整池；实际含本场独立人类与AI后，再请求真人类breakdown并原off/on/off百万差分、switch恢复、AI真实任命/继任全验。只降低目标原生等级门槛的导航选择，不保证存在合格title，不改人物merit/trait/冷却，不猜title或fullID，不用静态源替代31883实际资格。

原R57未知及R58已观察到的人类缺席保持；没有新增实机采样、active大报告读取、ABI研究、构建、prepare、测试、fixture/helper/MAIN/Git改动或新门禁。现场预算、截止和停止条件完全沿原case；本卡不延长原deadline、不授PASS。
