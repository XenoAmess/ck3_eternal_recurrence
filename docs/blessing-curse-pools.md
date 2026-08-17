# 祝福 / 诅咒奖池（权威表）

**本文件是奖池的唯一权威定义，由 `tools/gen_pools.py` 从 `tools/pools_data.py` 导出，勿手改。**

## 规则框架

- 商店「开始此生」后琉焰卿开启**垂青会**（`xar.0004`）：展示祝福池随机 3 项（无放回）+ 「什么都不要」
- 选中祝福 → 立即发放 → 必须再从诅咒池随机 3 项中选 1（`xar.0005`，无退路）→ 回到祝福事件
- 每场垂青会**上限 3 祝福 + 3 诅咒**；选「不要」或领满即散场，**3 年后**（1095 天）琉焰卿再度现身（`xar.0006` 重置会话）
- 每完成一对祝福/诅咒，**最终结算总分 +1%**（加算，N 对 = +N%），结算明细单列一行
- 角色死亡 → 结算后进入观察者模式，计时自然作废

## 数值与稀有度

- **同类型奖励：祝福量级 = 诅咒量级 × 0.75**（整数类凑整：属性 +3/−4）
- 稀有度：**普通 70 项（权重 10）/ 稀有 25 项（权重 3）/ 传说 5 项（权重 1）**（两池各自）
- 传说诅咒护栏：痛而不毁档——不碰即死/绝育/削头衔
- 金币诅咒只走月收入 drain（1.19 无合规一次性扣金：add_gold 拒负值、remove_gold 已移除）

## 祝福池（100 项）

| id | 稀有度 | 名称 | 效果 |
|---|---|---|---|
| 0 | 普通 | 遗金碎屑 | `add_gold = 50` |
| 1 | 普通 | 余烬遗金 | `add_gold = 100` |
| 2 | 普通 | 沉匣之金 | `add_gold = 200` |
| 3 | 普通 | 焰纹钱囊 | `add_gold = 350` |
| 4 | 普通 | 仲魔的打赏 | `add_gold = 500` |
| 5 | 稀有 | 琉璃金流 | `add_gold = 750` |
| 6 | 稀有 | 咒间金脉 | `add_gold = 1000` |
| 7 | 普通 | 颂歌残章 | `add_prestige = 75` |
| 8 | 普通 | 街角的颂词 | `add_prestige = 150` |
| 9 | 普通 | 众口的颂歌 | `add_prestige = 300` |
| 10 | 普通 | 传唱四方 | `add_prestige = 450` |
| 11 | 普通 | 桂冠的余音 | `add_prestige = 600` |
| 12 | 稀有 | 万邦传唱 | `add_prestige = 900` |
| 13 | 稀有 | 焰名的加冕 | `add_prestige = 1200` |
| 14 | 稀有 | 不朽声名 | `add_prestige = 1800` |
| 15 | 普通 | 烛芯微光 | `add_piety = 75` |
| 16 | 普通 | 静焰的祷声 | `add_piety = 150` |
| 17 | 普通 | 龛前的炽愿 | `add_piety = 300` |
| 18 | 普通 | 圣焰垂听 | `add_piety = 450` |
| 19 | 普通 | 琉璃圣痕 | `add_piety = 600` |
| 20 | 稀有 | 神座侧耳 | `add_piety = 900` |
| 21 | 稀有 | 天国的账页 | `add_piety = 1200` |
| 22 | 稀有 | 圣徒的余烬 | `add_piety = 1800` |
| 23 | 普通 | 蛛丝低语 | `change_influence = 25` |
| 24 | 普通 | 帘后的耳语 | `change_influence = 35` |
| 25 | 普通 | 暗线轻扯 | `change_influence = 50` |
| 26 | 普通 | 耳语之网 | `change_influence = 75` |
| 27 | 普通 | 影子议会 | `change_influence = 100` |
| 28 | 稀有 | 幕后的执笔 | `change_influence = 125` |
| 29 | 稀有 | 垂帘之手 | `change_influence = 150` |
| 30 | 普通 | 巧言 | `add_diplomacy_skill = 1` |
| 31 | 普通 | 蜜语的唇枪 | `add_diplomacy_skill = 2` |
| 32 | 普通 | 琉璃舌 | `add_diplomacy_skill = 3` |
| 33 | 普通 | 戎光 | `add_martial_skill = 1` |
| 34 | 普通 | 战焰的臂膀 | `add_martial_skill = 2` |
| 35 | 普通 | 不坠的战旗 | `add_martial_skill = 3` |
| 36 | 普通 | 权衡 | `add_stewardship_skill = 1` |
| 37 | 普通 | 铁算盘的清响 | `add_stewardship_skill = 2` |
| 38 | 普通 | 金库的守火 | `add_stewardship_skill = 3` |
| 39 | 普通 | 夜眸 | `add_intrigue_skill = 1` |
| 40 | 普通 | 影织的指尖 | `add_intrigue_skill = 2` |
| 41 | 普通 | 无面之契 | `add_intrigue_skill = 3` |
| 42 | 普通 | 烛照 | `add_learning_skill = 1` |
| 43 | 普通 | 烛下千卷 | `add_learning_skill = 2` |
| 44 | 普通 | 智焰长明 | `add_learning_skill = 3` |
| 45 | 普通 | 锋刃 | `add_prowess_skill = 1` |
| 46 | 普通 | 血焰的淬火 | `add_prowess_skill = 2` |
| 47 | 普通 | 琉璃战骨 | `add_prowess_skill = 3` |
| 48 | 普通 | 席间的残局 | `add_diplomacy_lifestyle_xp = 250` |
| 49 | 普通 | 唇舌的年轮 | `add_diplomacy_lifestyle_xp = 500` |
| 50 | 普通 | 万言的余温 | `add_diplomacy_lifestyle_xp = 750` |
| 51 | 普通 | 沙盘的灰烬 | `add_martial_lifestyle_xp = 250` |
| 52 | 普通 | 兵棋的余局 | `add_martial_lifestyle_xp = 500` |
| 53 | 普通 | 烽火的编年 | `add_martial_lifestyle_xp = 750` |
| 54 | 普通 | 账册的灰页 | `add_stewardship_lifestyle_xp = 250` |
| 55 | 普通 | 仓廪的余策 | `add_stewardship_lifestyle_xp = 500` |
| 56 | 普通 | 国帑的长算 | `add_stewardship_lifestyle_xp = 750` |
| 57 | 普通 | 暗巷的足音 | `add_intrigue_lifestyle_xp = 250` |
| 58 | 普通 | 罗网的余丝 | `add_intrigue_lifestyle_xp = 500` |
| 59 | 普通 | 千面的戏文 | `add_intrigue_lifestyle_xp = 750` |
| 60 | 普通 | 书库的残页 | `add_learning_lifestyle_xp = 250` |
| 61 | 普通 | 青灯的余卷 | `add_learning_lifestyle_xp = 500` |
| 62 | 普通 | 智海的拾贝 | `add_learning_lifestyle_xp = 750` |
| 63 | 普通 | 不败之躯 | `add_trait = physique_good_1` |
| 64 | 稀有 | 琉璃体魄 | `add_trait = physique_good_2` |
| 65 | 稀有 | 焰铸圣躯 | `add_trait = physique_good_3` |
| 66 | 普通 | 烛下的容颜 | `add_trait = beauty_good_1` |
| 67 | 稀有 | 琉璃面庞 | `add_trait = beauty_good_2` |
| 68 | 普通 | 灵犀一点 | `add_trait = intellect_good_1` |
| 69 | 稀有 | 慧焰入颅 | `add_trait = intellect_good_2` |
| 70 | 稀有 | 狐焰的狡黠 | `add_trait = shrewd` |
| 71 | 稀有 | 焰筋铁骨 | `add_trait = strong` |
| 72 | 普通 | 壮行的火种 | `add_trait = brave` |
| 73 | 普通 | 不息的炭火 | `add_trait = diligent` |
| 74 | 普通 | 长明的定力 | `add_trait = patient` |
| 75 | 普通 | 余烬钱脉 | `add_character_modifier = { modifier = xar_pb_income_s days = 3650 }` |
| 76 | 稀有 | 琉焰银根 | `add_character_modifier = { modifier = xar_pb_income_m days = 3650 }` |
| 77 | 稀有 | 咒间金泉 | `add_character_modifier = { modifier = xar_pb_income_l days = 3650 }` |
| 78 | 普通 | 温焰护体 | `add_character_modifier = { modifier = xar_pb_health_s days = 3650 }` |
| 79 | 稀有 | 琉璃色的体温 | `add_character_modifier = { modifier = xar_pb_health_m days = 3650 }` |
| 80 | 稀有 | 圣焰织体 | `add_character_modifier = { modifier = xar_pb_health_l days = 3650 }` |
| 81 | 普通 | 薪火相传 | `add_character_modifier = { modifier = xar_pb_fert_s days = 3650 }` |
| 82 | 稀有 | 焰嗣绵延 | `add_character_modifier = { modifier = xar_pb_fert_m days = 3650 }` |
| 83 | 普通 | 俯首的敬意 | `add_character_modifier = { modifier = xar_pb_vassal days = 3650 }` |
| 84 | 普通 | 心静琉璃 | `add_character_modifier = { modifier = xar_pb_stress days = 3650 }` |
| 85 | 普通 | 名望余温 | `add_character_modifier = { modifier = xar_pb_prestige days = 3650 }` |
| 86 | 普通 | 族徽的擦亮 | `dynasty ?= { add_dynasty_prestige = 50 }` |
| 87 | 普通 | 宗门的余晖 | `dynasty ?= { add_dynasty_prestige = 150 }` |
| 88 | 稀有 | 族焰的加冠 | `dynasty ?= { add_dynasty_prestige = 300 }` |
| 89 | 稀有 | 万世谱的烫金 | `dynasty ?= { add_dynasty_prestige = 500 }` |
| 90 | 普通 | 静焰抚平 | `add_stress = -50` |
| 91 | 普通 | 灰烬浴 | `add_stress = -75` |
| 92 | 普通 | 长夜的灰烬浴 | `add_stress = -100` |
| 93 | 稀有 | 忘川的洗礼 | `add_stress = -150` |
| 94 | 稀有 | 不灭的灯芯 | `add_character_modifier = { modifier = xar_pb_life_2 }` |
| 95 | 传说 | 琉焰之拥 | `add_diplomacy_skill = 1 + 	add_martial_skill = 1 + 	add_stewardship_skill = 1 + 	add_intrigue_skill = 1 + 	add_learning_skill = 1 + 	add_prowess_skill = 1` |
| 96 | 传说 | 不灭的灯芯·真 | `add_character_modifier = { modifier = xar_leg_life }` |
| 97 | 传说 | 万邦的账簿 | `add_gold = 1000 + 	add_character_modifier = { modifier = xar_leg_wealth days = 3650 }` |
| 98 | 传说 | 垂青的印记 | `add_prestige = 300 + 	add_piety = 300 + 	change_influence = 100` |
| 99 | 传说 | 预支的来世 | `dynasty ?= { add_dynasty_prestige = 1000 }` |

## 诅咒池（100 项）

| id | 稀有度 | 名称 | 效果 |
|---|---|---|---|
| 0 | 普通 | 钱袋的细沙 | `add_character_modifier = { modifier = xar_pc_drain_a days = 3650 }` |
| 1 | 普通 | 渗漏的钱袋 | `add_character_modifier = { modifier = xar_pc_drain_b days = 3650 }` |
| 2 | 普通 | 漏底的荷包 | `add_character_modifier = { modifier = xar_pc_drain_c days = 3650 }` |
| 3 | 普通 | 暗账的虫蛀 | `add_character_modifier = { modifier = xar_pc_drain_d days = 3650 }` |
| 4 | 普通 | 无声的分流 | `add_character_modifier = { modifier = xar_pc_drain_e days = 3650 }` |
| 5 | 稀有 | 咒痕的利息 | `add_character_modifier = { modifier = xar_pc_drain_f days = 3650 }` |
| 6 | 稀有 | 琉焰的月贡 | `add_character_modifier = { modifier = xar_pc_drain_g days = 3650 }` |
| 7 | 普通 | 背后的低笑 | `add_prestige = -100` |
| 8 | 普通 | 暗处的嗤笑 | `add_prestige = -200` |
| 9 | 普通 | 宴会的冷场 | `add_prestige = -400` |
| 10 | 普通 | 名望的剥落 | `add_prestige = -600` |
| 11 | 普通 | 众口的毒刺 | `add_prestige = -800` |
| 12 | 稀有 | 桂冠的蒙尘 | `add_prestige = -1200` |
| 13 | 稀有 | 耻辱的烙印 | `add_prestige = -1600` |
| 14 | 稀有 | 遗臭的批注 | `add_prestige = -2400` |
| 15 | 普通 | 龛火的摇曳 | `add_piety = -100` |
| 16 | 普通 | 圣像的沉默 | `add_piety = -200` |
| 17 | 普通 | 祷词的哽塞 | `add_piety = -400` |
| 18 | 普通 | 香灰的迷眼 | `add_piety = -600` |
| 19 | 普通 | 神坛的冷寂 | `add_piety = -800` |
| 20 | 稀有 | 圣痕的逆灼 | `add_piety = -1200` |
| 21 | 稀有 | 天听的掩耳 | `add_piety = -1600` |
| 22 | 稀有 | 神眷的断约 | `add_piety = -2400` |
| 23 | 普通 | 线的松脱 | `change_influence = -35` |
| 24 | 普通 | 暗桩的倒戈 | `change_influence = -50` |
| 25 | 普通 | 耳语的退潮 | `change_influence = -65` |
| 26 | 普通 | 断线的傀儡 | `change_influence = -100` |
| 27 | 普通 | 罗网的破眼 | `change_influence = -135` |
| 28 | 稀有 | 帷幕的坠落 | `change_influence = -165` |
| 29 | 稀有 | 垂帘的断手 | `change_influence = -200` |
| 30 | 普通 | 锈死的门环 | `add_diplomacy_skill = -1` |
| 31 | 普通 | 结舌的毒涎 | `add_diplomacy_skill = -3` |
| 32 | 普通 | 失声的琉璃 | `add_diplomacy_skill = -4` |
| 33 | 普通 | 钝刃的锈斑 | `add_martial_skill = -1` |
| 34 | 普通 | 战阵的迷途 | `add_martial_skill = -3` |
| 35 | 普通 | 折戟的残旗 | `add_martial_skill = -4` |
| 36 | 普通 | 蒙尘的算珠 | `add_stewardship_skill = -1` |
| 37 | 普通 | 烂账的霉斑 | `add_stewardship_skill = -3` |
| 38 | 普通 | 金库的漏底 | `add_stewardship_skill = -4` |
| 39 | 普通 | 褪色的心眼 | `add_intrigue_skill = -1` |
| 40 | 普通 | 影子的叛逃 | `add_intrigue_skill = -3` |
| 41 | 普通 | 无面的弃契 | `add_intrigue_skill = -4` |
| 42 | 普通 | 蒙尘的经卷 | `add_learning_skill = -1` |
| 43 | 普通 | 青灯的油耗 | `add_learning_skill = -3` |
| 44 | 普通 | 智海的沉船 | `add_learning_skill = -4` |
| 45 | 普通 | 锈甲的呻吟 | `add_prowess_skill = -1` |
| 46 | 普通 | 战骨的酥蚀 | `add_prowess_skill = -3` |
| 47 | 普通 | 断刃的迟暮 | `add_prowess_skill = -4` |
| 48 | 普通 | 席间的冷羹 | `add_diplomacy_lifestyle_xp = -350` |
| 49 | 普通 | 唇舌的石蜡 | `add_diplomacy_lifestyle_xp = -650` |
| 50 | 普通 | 万言的失声 | `add_diplomacy_lifestyle_xp = -1000` |
| 51 | 普通 | 沙盘的塌角 | `add_martial_lifestyle_xp = -350` |
| 52 | 普通 | 兵棋的乱局 | `add_martial_lifestyle_xp = -650` |
| 53 | 普通 | 烽火的湿薪 | `add_martial_lifestyle_xp = -1000` |
| 54 | 普通 | 账册的墨渍 | `add_stewardship_lifestyle_xp = -350` |
| 55 | 普通 | 仓廪的鼠患 | `add_stewardship_lifestyle_xp = -650` |
| 56 | 普通 | 国帑的空算 | `add_stewardship_lifestyle_xp = -1000` |
| 57 | 普通 | 暗巷的迷灯 | `add_intrigue_lifestyle_xp = -350` |
| 58 | 普通 | 罗网的断丝 | `add_intrigue_lifestyle_xp = -650` |
| 59 | 普通 | 千面的哑剧 | `add_intrigue_lifestyle_xp = -1000` |
| 60 | 普通 | 书库的蠹痕 | `add_learning_lifestyle_xp = -350` |
| 61 | 普通 | 青灯的泪尽 | `add_learning_lifestyle_xp = -650` |
| 62 | 普通 | 智海的搁滩 | `add_learning_lifestyle_xp = -1000` |
| 63 | 普通 | 抽骨的酸软 | `add_trait = weak` |
| 64 | 普通 | 盘根的绊足 | `add_trait = clubfooted` |
| 65 | 普通 | 琉璃的脆纹 | `add_trait = physique_bad_1` |
| 66 | 普通 | 蒙灰的铜镜 | `add_trait = beauty_bad_1` |
| 67 | 普通 | 膝软的阴影 | `add_trait = craven` |
| 68 | 普通 | 席地的沉疴 | `add_trait = lazy` |
| 69 | 稀有 | 缠身的病影 | `add_trait = sickly` |
| 70 | 稀有 | 负山的佝偻 | `add_trait = hunchbacked` |
| 71 | 稀有 | 雾锁的灵台 | `add_trait = intellect_bad_1` |
| 72 | 稀有 | 熄焰的空颅 | `add_trait = intellect_bad_2` |
| 73 | 稀有 | 碎面的铜镜 | `add_trait = beauty_bad_2` |
| 74 | 稀有 | 窥隙的疑目 | `add_trait = paranoid` |
| 75 | 普通 | 蚀骨的寒痕 | `add_character_modifier = { modifier = xar_pc_health_s days = 3650 }` |
| 76 | 稀有 | 寒焰的蚀体 | `add_character_modifier = { modifier = xar_pc_health_m days = 3650 }` |
| 77 | 稀有 | 余命的漏刻 | `add_character_modifier = { modifier = xar_pc_health_l days = 3650 }` |
| 78 | 普通 | 薪火的湿薪 | `add_character_modifier = { modifier = xar_pc_fert_s days = 3650 }` |
| 79 | 稀有 | 嗣线的霜结 | `add_character_modifier = { modifier = xar_pc_fert_m days = 3650 }` |
| 80 | 普通 | 阶下的窃议 | `add_character_modifier = { modifier = xar_pc_vassal_s days = 3650 }` |
| 81 | 稀有 | 俯首的假面 | `add_character_modifier = { modifier = xar_pc_vassal_m days = 3650 }` |
| 82 | 普通 | 心弦的绷响 | `add_character_modifier = { modifier = xar_pc_stress_s days = 3650 }` |
| 83 | 稀有 | 梦魇的常客 | `add_character_modifier = { modifier = xar_pc_stress_m days = 3650 }` |
| 84 | 普通 | 名望的漏勺 | `add_character_modifier = { modifier = xar_pc_mprestige days = 3650 }` |
| 85 | 普通 | 龛火的断供 | `add_character_modifier = { modifier = xar_pc_mpiety days = 3650 }` |
| 86 | 普通 | 族徽的蒙尘 | `dynasty ?= { add_dynasty_prestige = -65 }` |
| 87 | 普通 | 黯淡的族徽 | `dynasty ?= { add_dynasty_prestige = -200 }` |
| 88 | 稀有 | 族焰的萎灭 | `dynasty ?= { add_dynasty_prestige = -400 }` |
| 89 | 稀有 | 谱系的断页 | `dynasty ?= { add_dynasty_prestige = -650 }` |
| 90 | 普通 | 压舱的石契 | `add_stress = 65` |
| 91 | 普通 | 账契的枷锁 | `add_stress = 100` |
| 92 | 普通 | 梦魇的加演 | `add_stress = 135` |
| 93 | 稀有 | 心渊的坠石 | `add_stress = 200` |
| 94 | 稀有 | 灯芯的焦痕 | `add_character_modifier = { modifier = xar_pc_life }` |
| 95 | 传说 | 蚀魂的寒斑 | `add_character_modifier = { modifier = xar_leg_cold days = 3650 }` |
| 96 | 传说 | 琉焰的抽成 | `add_character_modifier = { modifier = xar_leg_tax days = 3650 }` |
| 97 | 传说 | 众叛的耳语 | `add_character_modifier = { modifier = xar_leg_vassal days = 3650 }` |
| 98 | 传说 | 褪色的馈赠 | `add_diplomacy_skill = -1 + 	add_martial_skill = -1 + 	add_stewardship_skill = -1 + 	add_intrigue_skill = -1 + 	add_learning_skill = -1 + 	add_prowess_skill = -1` |
| 99 | 传说 | 重压的账契 | `add_stress = 150 + 	add_character_modifier = { modifier = xar_leg_stress days = 3650 }` |

## 实现位置

- 数据表：`tools/pools_data.py`（改条目改这里，再跑 `py tools/gen_pools.py`）
- 抽取/发放：`common/scripted_effects/xar_generated_pools_effects.txt`（GENERATED）
- 选项槽文本：`common/customizable_localization/xar_generated_pool_loc.txt`（GENERATED）
- 修正：`common/modifiers/xar_generated_pool_modifiers.txt`（GENERATED）
- loc：`localization/<lang>/xar_generated_pools_l_<lang>.yml`（GENERATED，9 语言）
- 事件：`events/xar_events.txt`（xar.0004 / xar.0005 / xar.0006，手写不变）
- 结算加算：`xar_compute_score_effect` 末尾 ×(1 + 0.01 × xa_bless_count)
