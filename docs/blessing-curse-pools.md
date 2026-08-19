# 祝福 / 诅咒奖池（权威表）

**本文件是奖池的唯一权威定义，由 `tools/gen_pools.py` 从 `tools/pools_data.py` 导出，勿手改。**

## 规则框架

- 商店「开始此生」后琉焰卿开启**垂青会**（`xar.0004`）：展示祝福池随机 3 项（无放回）+ 「什么都不要」
- 选中祝福 → 立即发放 → 必须再从诅咒池随机 2 项中选 1（`xar.0005`）；拥有封印时可消耗封印免除本次咒痕
- 两项诅咒的稀有度均不得低于所选祝福稀有度减 1：传说祝福只会抽到稀有/传说诅咒；普通/稀有祝福允许全池
- 每场垂青会恰好**一对祝福/诅咒**；成交或拒绝后散场，**3 年后**（1095 天）琉焰卿再度现身（`xar.0006` 重置会话）
- 每完成一对祝福/诅咒，琉焰之视获得 **1 经验**；每拒绝一次祝福会，**最终结算总分 -1%**（加算，最低为 0）
- 角色死亡 → 有继承人时结算后进入观察者模式；无可玩继承人时由原生继承窗结算并退出主菜单；计时自然作废

## 数值与稀有度

- **同类型奖励：祝福量级 = 诅咒量级 × 0.75**（整数类凑整：属性 +3/−4）
- 稀有度：**普通 70 项（权重 10）/ 稀有 25 项（权重 3）/ 传说 5 项（权重 1）**（两池各自）
- 传说诅咒护栏：痛而不毁档——不碰即死/绝育/削头衔
- 金币诅咒只走月收入 drain（1.19 无合规一次性扣金：add_gold 拒负值、remove_gold 已移除）

## 祝福池（100 项）

| 稳定 ID | wire id | 稀有度 | 标签 | 名称 | 效果 |
|---|---:|---|---|---|---|
| `bless.000` | 0 | 普通 | 财富 | 遗金碎屑 | `add_gold = 50` |
| `bless.001` | 1 | 普通 | 财富 | 余烬遗金 | `add_gold = 100` |
| `bless.002` | 2 | 普通 | 财富 | 沉匣之金 | `add_gold = 200` |
| `bless.003` | 3 | 普通 | 财富 | 焰纹钱囊 | `add_gold = 350` |
| `bless.004` | 4 | 普通 | 财富 | 仲魔的打赏 | `add_gold = 500` |
| `bless.005` | 5 | 稀有 | 财富 | 琉璃金流 | `add_gold = 750` |
| `bless.006` | 6 | 稀有 | 财富 | 咒间金脉 | `add_gold = 1000` |
| `bless.007` | 7 | 普通 | 威望 | 颂歌残章 | `add_prestige = 75` |
| `bless.008` | 8 | 普通 | 威望 | 街角的颂词 | `add_prestige = 150` |
| `bless.009` | 9 | 普通 | 威望 | 众口的颂歌 | `add_prestige = 300` |
| `bless.010` | 10 | 普通 | 威望 | 传唱四方 | `add_prestige = 450` |
| `bless.011` | 11 | 普通 | 威望 | 桂冠的余音 | `add_prestige = 600` |
| `bless.012` | 12 | 稀有 | 威望 | 万邦传唱 | `add_prestige = 900` |
| `bless.013` | 13 | 稀有 | 威望 | 焰名的加冕 | `add_prestige = 1200` |
| `bless.014` | 14 | 稀有 | 威望 | 不朽声名 | `add_prestige = 1800` |
| `bless.015` | 15 | 普通 | 信仰 | 烛芯微光 | `add_piety = 75` |
| `bless.016` | 16 | 普通 | 信仰 | 静焰的祷声 | `add_piety = 150` |
| `bless.017` | 17 | 普通 | 信仰 | 龛前的炽愿 | `add_piety = 300` |
| `bless.018` | 18 | 普通 | 信仰 | 圣焰垂听 | `add_piety = 450` |
| `bless.019` | 19 | 普通 | 信仰 | 琉璃圣痕 | `add_piety = 600` |
| `bless.020` | 20 | 稀有 | 信仰 | 神座侧耳 | `add_piety = 900` |
| `bless.021` | 21 | 稀有 | 信仰 | 天国的账页 | `add_piety = 1200` |
| `bless.022` | 22 | 稀有 | 信仰 | 圣徒的余烬 | `add_piety = 1800` |
| `bless.023` | 23 | 普通 | 权谋 | 蛛丝低语 | `change_influence = 25` |
| `bless.024` | 24 | 普通 | 权谋 | 帘后的耳语 | `change_influence = 35` |
| `bless.025` | 25 | 普通 | 权谋 | 暗线轻扯 | `change_influence = 50` |
| `bless.026` | 26 | 普通 | 权谋 | 耳语之网 | `change_influence = 75` |
| `bless.027` | 27 | 普通 | 权谋 | 影子议会 | `change_influence = 100` |
| `bless.028` | 28 | 稀有 | 权谋 | 幕后的执笔 | `change_influence = 125` |
| `bless.029` | 29 | 稀有 | 权谋 | 垂帘之手 | `change_influence = 150` |
| `bless.030` | 30 | 普通 | 属性 | 巧言 | `add_diplomacy_skill = 1` |
| `bless.031` | 31 | 普通 | 属性 | 蜜语的唇枪 | `add_diplomacy_skill = 2` |
| `bless.032` | 32 | 普通 | 属性 | 琉璃舌 | `add_diplomacy_skill = 3` |
| `bless.033` | 33 | 普通 | 属性 | 戎光 | `add_martial_skill = 1` |
| `bless.034` | 34 | 普通 | 属性 | 战焰的臂膀 | `add_martial_skill = 2` |
| `bless.035` | 35 | 普通 | 属性 | 不坠的战旗 | `add_martial_skill = 3` |
| `bless.036` | 36 | 普通 | 属性 | 权衡 | `add_stewardship_skill = 1` |
| `bless.037` | 37 | 普通 | 属性 | 铁算盘的清响 | `add_stewardship_skill = 2` |
| `bless.038` | 38 | 普通 | 属性 | 金库的守火 | `add_stewardship_skill = 3` |
| `bless.039` | 39 | 普通 | 属性 | 夜眸 | `add_intrigue_skill = 1` |
| `bless.040` | 40 | 普通 | 属性 | 影织的指尖 | `add_intrigue_skill = 2` |
| `bless.041` | 41 | 普通 | 属性 | 无面之契 | `add_intrigue_skill = 3` |
| `bless.042` | 42 | 普通 | 属性 | 烛照 | `add_learning_skill = 1` |
| `bless.043` | 43 | 普通 | 属性 | 烛下千卷 | `add_learning_skill = 2` |
| `bless.044` | 44 | 普通 | 属性 | 智焰长明 | `add_learning_skill = 3` |
| `bless.045` | 45 | 普通 | 属性 | 锋刃 | `add_prowess_skill = 1` |
| `bless.046` | 46 | 普通 | 属性 | 血焰的淬火 | `add_prowess_skill = 2` |
| `bless.047` | 47 | 普通 | 属性 | 琉璃战骨 | `add_prowess_skill = 3` |
| `bless.048` | 48 | 普通 | 生活方式 | 席间的残局 | `add_diplomacy_lifestyle_xp = 250` |
| `bless.049` | 49 | 普通 | 生活方式 | 唇舌的年轮 | `add_diplomacy_lifestyle_xp = 500` |
| `bless.050` | 50 | 普通 | 生活方式 | 万言的余温 | `add_diplomacy_lifestyle_xp = 750` |
| `bless.051` | 51 | 普通 | 生活方式 | 沙盘的灰烬 | `add_martial_lifestyle_xp = 250` |
| `bless.052` | 52 | 普通 | 生活方式 | 兵棋的余局 | `add_martial_lifestyle_xp = 500` |
| `bless.053` | 53 | 普通 | 生活方式 | 烽火的编年 | `add_martial_lifestyle_xp = 750` |
| `bless.054` | 54 | 普通 | 生活方式 | 账册的灰页 | `add_stewardship_lifestyle_xp = 250` |
| `bless.055` | 55 | 普通 | 生活方式 | 仓廪的余策 | `add_stewardship_lifestyle_xp = 500` |
| `bless.056` | 56 | 普通 | 生活方式 | 国帑的长算 | `add_stewardship_lifestyle_xp = 750` |
| `bless.057` | 57 | 普通 | 生活方式 | 暗巷的足音 | `add_intrigue_lifestyle_xp = 250` |
| `bless.058` | 58 | 普通 | 生活方式 | 罗网的余丝 | `add_intrigue_lifestyle_xp = 500` |
| `bless.059` | 59 | 普通 | 生活方式 | 千面的戏文 | `add_intrigue_lifestyle_xp = 750` |
| `bless.060` | 60 | 普通 | 生活方式 | 书库的残页 | `add_learning_lifestyle_xp = 250` |
| `bless.061` | 61 | 普通 | 生活方式 | 青灯的余卷 | `add_learning_lifestyle_xp = 500` |
| `bless.062` | 62 | 普通 | 生活方式 | 智海的拾贝 | `add_learning_lifestyle_xp = 750` |
| `bless.063` | 63 | 普通 | 特质 | 不败之躯 | `add_trait = physique_good_1` |
| `bless.064` | 64 | 稀有 | 特质 | 琉璃体魄 | `add_trait = physique_good_2` |
| `bless.065` | 65 | 稀有 | 特质 | 焰铸圣躯 | `add_trait = physique_good_3` |
| `bless.066` | 66 | 普通 | 特质 | 烛下的容颜 | `add_trait = beauty_good_1` |
| `bless.067` | 67 | 稀有 | 特质 | 琉璃面庞 | `add_trait = beauty_good_2` |
| `bless.068` | 68 | 普通 | 特质 | 灵犀一点 | `add_trait = intellect_good_1` |
| `bless.069` | 69 | 稀有 | 特质 | 慧焰入颅 | `add_trait = intellect_good_2` |
| `bless.070` | 70 | 稀有 | 特质 | 狐焰的狡黠 | `add_trait = shrewd` |
| `bless.071` | 71 | 稀有 | 特质 | 焰筋铁骨 | `add_trait = strong` |
| `bless.072` | 72 | 普通 | 特质 | 壮行的火种 | `add_trait = brave` |
| `bless.073` | 73 | 普通 | 特质 | 不息的炭火 | `add_trait = diligent` |
| `bless.074` | 74 | 普通 | 特质 | 长明的定力 | `add_trait = patient` |
| `bless.075` | 75 | 普通 | 修正 | 余烬钱脉 | `add_character_modifier = { modifier = xar_pb_income_s days = 3650 }` |
| `bless.076` | 76 | 稀有 | 修正 | 琉焰银根 | `add_character_modifier = { modifier = xar_pb_income_m days = 3650 }` |
| `bless.077` | 77 | 稀有 | 修正 | 咒间金泉 | `add_character_modifier = { modifier = xar_pb_income_l days = 3650 }` |
| `bless.078` | 78 | 普通 | 修正 | 温焰护体 | `add_character_modifier = { modifier = xar_pb_health_s days = 3650 }` |
| `bless.079` | 79 | 稀有 | 修正 | 琉璃色的体温 | `add_character_modifier = { modifier = xar_pb_health_m days = 3650 }` |
| `bless.080` | 80 | 稀有 | 修正 | 圣焰织体 | `add_character_modifier = { modifier = xar_pb_health_l days = 3650 }` |
| `bless.081` | 81 | 普通 | 修正 | 薪火相传 | `add_character_modifier = { modifier = xar_pb_fert_s days = 3650 }` |
| `bless.082` | 82 | 稀有 | 修正 | 焰嗣绵延 | `add_character_modifier = { modifier = xar_pb_fert_m days = 3650 }` |
| `bless.083` | 83 | 普通 | 修正 | 俯首的敬意 | `add_character_modifier = { modifier = xar_pb_vassal days = 3650 }` |
| `bless.084` | 84 | 普通 | 修正 | 心静琉璃 | `add_character_modifier = { modifier = xar_pb_stress days = 3650 }` |
| `bless.085` | 85 | 普通 | 修正 | 名望余温 | `add_character_modifier = { modifier = xar_pb_prestige days = 3650 }` |
| `bless.086` | 86 | 普通 | 宗族 | 族徽的擦亮 | `dynasty ?= { add_dynasty_prestige = 50 }` |
| `bless.087` | 87 | 普通 | 宗族 | 宗门的余晖 | `dynasty ?= { add_dynasty_prestige = 150 }` |
| `bless.088` | 88 | 稀有 | 宗族 | 族焰的加冠 | `dynasty ?= { add_dynasty_prestige = 300 }` |
| `bless.089` | 89 | 稀有 | 宗族 | 万世谱的烫金 | `dynasty ?= { add_dynasty_prestige = 500 }` |
| `bless.090` | 90 | 普通 | 压力 | 静焰抚平 | `add_stress = -50` |
| `bless.091` | 91 | 普通 | 压力 | 灰烬浴 | `add_stress = -75` |
| `bless.092` | 92 | 普通 | 压力 | 长夜的灰烬浴 | `add_stress = -100` |
| `bless.093` | 93 | 稀有 | 压力 | 忘川的洗礼 | `add_stress = -150` |
| `bless.094` | 94 | 稀有 | 秘契 | 不灭的灯芯 | `add_character_modifier = { modifier = xar_pb_life_2 }` |
| `bless.095` | 95 | 传说 | 秘契 | 琉焰之拥 | `add_diplomacy_skill = 1 + 	add_martial_skill = 1 + 	add_stewardship_skill = 1 + 	add_intrigue_skill = 1 + 	add_learning_skill = 1 + 	add_prowess_skill = 1` |
| `bless.096` | 96 | 传说 | 秘契 | 不灭的灯芯·真 | `add_character_modifier = { modifier = xar_leg_life }` |
| `bless.097` | 97 | 传说 | 秘契 | 万邦的账簿 | `add_gold = 1000 + 	add_character_modifier = { modifier = xar_leg_wealth days = 3650 }` |
| `bless.098` | 98 | 传说 | 秘契 | 垂青的印记 | `add_prestige = 300 + 	add_piety = 300 + 	change_influence = 100` |
| `bless.099` | 99 | 传说 | 秘契 | 预支的来世 | `dynasty ?= { add_dynasty_prestige = 1000 }` |

## 诅咒池（100 项）

| 稳定 ID | wire id | 稀有度 | 标签 | 名称 | 效果 |
|---|---:|---|---|---|---|
| `curse.000` | 0 | 普通 | 财富 | 钱袋的细沙 | `add_character_modifier = { modifier = xar_pc_drain_a days = 3650 }` |
| `curse.001` | 1 | 普通 | 财富 | 渗漏的钱袋 | `add_character_modifier = { modifier = xar_pc_drain_b days = 3650 }` |
| `curse.002` | 2 | 普通 | 财富 | 漏底的荷包 | `add_character_modifier = { modifier = xar_pc_drain_c days = 3650 }` |
| `curse.003` | 3 | 普通 | 财富 | 暗账的虫蛀 | `add_character_modifier = { modifier = xar_pc_drain_d days = 3650 }` |
| `curse.004` | 4 | 普通 | 财富 | 无声的分流 | `add_character_modifier = { modifier = xar_pc_drain_e days = 3650 }` |
| `curse.005` | 5 | 稀有 | 财富 | 咒痕的利息 | `add_character_modifier = { modifier = xar_pc_drain_f days = 3650 }` |
| `curse.006` | 6 | 稀有 | 财富 | 琉焰的月贡 | `add_character_modifier = { modifier = xar_pc_drain_g days = 3650 }` |
| `curse.007` | 7 | 普通 | 威望 | 背后的低笑 | `add_prestige = -100` |
| `curse.008` | 8 | 普通 | 威望 | 暗处的嗤笑 | `add_prestige = -200` |
| `curse.009` | 9 | 普通 | 威望 | 宴会的冷场 | `add_prestige = -400` |
| `curse.010` | 10 | 普通 | 威望 | 名望的剥落 | `add_prestige = -600` |
| `curse.011` | 11 | 普通 | 威望 | 众口的毒刺 | `add_prestige = -800` |
| `curse.012` | 12 | 稀有 | 威望 | 桂冠的蒙尘 | `add_prestige = -1200` |
| `curse.013` | 13 | 稀有 | 威望 | 耻辱的烙印 | `add_prestige = -1600` |
| `curse.014` | 14 | 稀有 | 威望 | 遗臭的批注 | `add_prestige = -2400` |
| `curse.015` | 15 | 普通 | 信仰 | 龛火的摇曳 | `add_piety = -100` |
| `curse.016` | 16 | 普通 | 信仰 | 圣像的沉默 | `add_piety = -200` |
| `curse.017` | 17 | 普通 | 信仰 | 祷词的哽塞 | `add_piety = -400` |
| `curse.018` | 18 | 普通 | 信仰 | 香灰的迷眼 | `add_piety = -600` |
| `curse.019` | 19 | 普通 | 信仰 | 神坛的冷寂 | `add_piety = -800` |
| `curse.020` | 20 | 稀有 | 信仰 | 圣痕的逆灼 | `add_piety = -1200` |
| `curse.021` | 21 | 稀有 | 信仰 | 天听的掩耳 | `add_piety = -1600` |
| `curse.022` | 22 | 稀有 | 信仰 | 神眷的断约 | `add_piety = -2400` |
| `curse.023` | 23 | 普通 | 权谋 | 线的松脱 | `change_influence = -35` |
| `curse.024` | 24 | 普通 | 权谋 | 暗桩的倒戈 | `change_influence = -50` |
| `curse.025` | 25 | 普通 | 权谋 | 耳语的退潮 | `change_influence = -65` |
| `curse.026` | 26 | 普通 | 权谋 | 断线的傀儡 | `change_influence = -100` |
| `curse.027` | 27 | 普通 | 权谋 | 罗网的破眼 | `change_influence = -135` |
| `curse.028` | 28 | 稀有 | 权谋 | 帷幕的坠落 | `change_influence = -165` |
| `curse.029` | 29 | 稀有 | 权谋 | 垂帘的断手 | `change_influence = -200` |
| `curse.030` | 30 | 普通 | 属性 | 锈死的门环 | `add_diplomacy_skill = -1` |
| `curse.031` | 31 | 普通 | 属性 | 结舌的毒涎 | `add_diplomacy_skill = -3` |
| `curse.032` | 32 | 普通 | 属性 | 失声的琉璃 | `add_diplomacy_skill = -4` |
| `curse.033` | 33 | 普通 | 属性 | 钝刃的锈斑 | `add_martial_skill = -1` |
| `curse.034` | 34 | 普通 | 属性 | 战阵的迷途 | `add_martial_skill = -3` |
| `curse.035` | 35 | 普通 | 属性 | 折戟的残旗 | `add_martial_skill = -4` |
| `curse.036` | 36 | 普通 | 属性 | 蒙尘的算珠 | `add_stewardship_skill = -1` |
| `curse.037` | 37 | 普通 | 属性 | 烂账的霉斑 | `add_stewardship_skill = -3` |
| `curse.038` | 38 | 普通 | 属性 | 金库的漏底 | `add_stewardship_skill = -4` |
| `curse.039` | 39 | 普通 | 属性 | 褪色的心眼 | `add_intrigue_skill = -1` |
| `curse.040` | 40 | 普通 | 属性 | 影子的叛逃 | `add_intrigue_skill = -3` |
| `curse.041` | 41 | 普通 | 属性 | 无面的弃契 | `add_intrigue_skill = -4` |
| `curse.042` | 42 | 普通 | 属性 | 蒙尘的经卷 | `add_learning_skill = -1` |
| `curse.043` | 43 | 普通 | 属性 | 青灯的油耗 | `add_learning_skill = -3` |
| `curse.044` | 44 | 普通 | 属性 | 智海的沉船 | `add_learning_skill = -4` |
| `curse.045` | 45 | 普通 | 属性 | 锈甲的呻吟 | `add_prowess_skill = -1` |
| `curse.046` | 46 | 普通 | 属性 | 战骨的酥蚀 | `add_prowess_skill = -3` |
| `curse.047` | 47 | 普通 | 属性 | 断刃的迟暮 | `add_prowess_skill = -4` |
| `curse.048` | 48 | 普通 | 生活方式 | 席间的冷羹 | `add_diplomacy_lifestyle_xp = -350` |
| `curse.049` | 49 | 普通 | 生活方式 | 唇舌的石蜡 | `add_diplomacy_lifestyle_xp = -650` |
| `curse.050` | 50 | 普通 | 生活方式 | 万言的失声 | `add_diplomacy_lifestyle_xp = -1000` |
| `curse.051` | 51 | 普通 | 生活方式 | 沙盘的塌角 | `add_martial_lifestyle_xp = -350` |
| `curse.052` | 52 | 普通 | 生活方式 | 兵棋的乱局 | `add_martial_lifestyle_xp = -650` |
| `curse.053` | 53 | 普通 | 生活方式 | 烽火的湿薪 | `add_martial_lifestyle_xp = -1000` |
| `curse.054` | 54 | 普通 | 生活方式 | 账册的墨渍 | `add_stewardship_lifestyle_xp = -350` |
| `curse.055` | 55 | 普通 | 生活方式 | 仓廪的鼠患 | `add_stewardship_lifestyle_xp = -650` |
| `curse.056` | 56 | 普通 | 生活方式 | 国帑的空算 | `add_stewardship_lifestyle_xp = -1000` |
| `curse.057` | 57 | 普通 | 生活方式 | 暗巷的迷灯 | `add_intrigue_lifestyle_xp = -350` |
| `curse.058` | 58 | 普通 | 生活方式 | 罗网的断丝 | `add_intrigue_lifestyle_xp = -650` |
| `curse.059` | 59 | 普通 | 生活方式 | 千面的哑剧 | `add_intrigue_lifestyle_xp = -1000` |
| `curse.060` | 60 | 普通 | 生活方式 | 书库的蠹痕 | `add_learning_lifestyle_xp = -350` |
| `curse.061` | 61 | 普通 | 生活方式 | 青灯的泪尽 | `add_learning_lifestyle_xp = -650` |
| `curse.062` | 62 | 普通 | 生活方式 | 智海的搁滩 | `add_learning_lifestyle_xp = -1000` |
| `curse.063` | 63 | 普通 | 特质 | 抽骨的酸软 | `add_trait = weak` |
| `curse.064` | 64 | 普通 | 特质 | 盘根的绊足 | `add_trait = clubfooted` |
| `curse.065` | 65 | 普通 | 特质 | 琉璃的脆纹 | `add_trait = physique_bad_1` |
| `curse.066` | 66 | 普通 | 特质 | 蒙灰的铜镜 | `add_trait = beauty_bad_1` |
| `curse.067` | 67 | 普通 | 特质 | 膝软的阴影 | `add_trait = craven` |
| `curse.068` | 68 | 普通 | 特质 | 席地的沉疴 | `add_trait = lazy` |
| `curse.069` | 69 | 稀有 | 特质 | 缠身的病影 | `add_trait = sickly` |
| `curse.070` | 70 | 稀有 | 特质 | 负山的佝偻 | `add_trait = hunchbacked` |
| `curse.071` | 71 | 稀有 | 特质 | 雾锁的灵台 | `add_trait = intellect_bad_1` |
| `curse.072` | 72 | 稀有 | 特质 | 熄焰的空颅 | `add_trait = intellect_bad_2` |
| `curse.073` | 73 | 稀有 | 特质 | 碎面的铜镜 | `add_trait = beauty_bad_2` |
| `curse.074` | 74 | 稀有 | 特质 | 窥隙的疑目 | `add_trait = paranoid` |
| `curse.075` | 75 | 普通 | 修正 | 蚀骨的寒痕 | `add_character_modifier = { modifier = xar_pc_health_s days = 3650 }` |
| `curse.076` | 76 | 稀有 | 修正 | 寒焰的蚀体 | `add_character_modifier = { modifier = xar_pc_health_m days = 3650 }` |
| `curse.077` | 77 | 稀有 | 修正 | 余命的漏刻 | `add_character_modifier = { modifier = xar_pc_health_l days = 3650 }` |
| `curse.078` | 78 | 普通 | 修正 | 薪火的湿薪 | `add_character_modifier = { modifier = xar_pc_fert_s days = 3650 }` |
| `curse.079` | 79 | 稀有 | 修正 | 嗣线的霜结 | `add_character_modifier = { modifier = xar_pc_fert_m days = 3650 }` |
| `curse.080` | 80 | 普通 | 修正 | 阶下的窃议 | `add_character_modifier = { modifier = xar_pc_vassal_s days = 3650 }` |
| `curse.081` | 81 | 稀有 | 修正 | 俯首的假面 | `add_character_modifier = { modifier = xar_pc_vassal_m days = 3650 }` |
| `curse.082` | 82 | 普通 | 修正 | 心弦的绷响 | `add_character_modifier = { modifier = xar_pc_stress_s days = 3650 }` |
| `curse.083` | 83 | 稀有 | 修正 | 梦魇的常客 | `add_character_modifier = { modifier = xar_pc_stress_m days = 3650 }` |
| `curse.084` | 84 | 普通 | 修正 | 名望的漏勺 | `add_character_modifier = { modifier = xar_pc_mprestige days = 3650 }` |
| `curse.085` | 85 | 普通 | 修正 | 龛火的断供 | `add_character_modifier = { modifier = xar_pc_mpiety days = 3650 }` |
| `curse.086` | 86 | 普通 | 宗族 | 族徽的蒙尘 | `dynasty ?= { add_dynasty_prestige = -65 }` |
| `curse.087` | 87 | 普通 | 宗族 | 黯淡的族徽 | `dynasty ?= { add_dynasty_prestige = -200 }` |
| `curse.088` | 88 | 稀有 | 宗族 | 族焰的萎灭 | `dynasty ?= { add_dynasty_prestige = -400 }` |
| `curse.089` | 89 | 稀有 | 宗族 | 谱系的断页 | `dynasty ?= { add_dynasty_prestige = -650 }` |
| `curse.090` | 90 | 普通 | 压力 | 压舱的石契 | `add_stress = 65` |
| `curse.091` | 91 | 普通 | 压力 | 账契的枷锁 | `add_stress = 100` |
| `curse.092` | 92 | 普通 | 压力 | 梦魇的加演 | `add_stress = 135` |
| `curse.093` | 93 | 稀有 | 压力 | 心渊的坠石 | `add_stress = 200` |
| `curse.094` | 94 | 稀有 | 秘契 | 灯芯的焦痕 | `add_character_modifier = { modifier = xar_pc_life }` |
| `curse.095` | 95 | 传说 | 秘契 | 蚀魂的寒斑 | `add_character_modifier = { modifier = xar_leg_cold days = 3650 }` |
| `curse.096` | 96 | 传说 | 秘契 | 琉焰的抽成 | `add_character_modifier = { modifier = xar_leg_tax days = 3650 }` |
| `curse.097` | 97 | 传说 | 秘契 | 众叛的耳语 | `add_character_modifier = { modifier = xar_leg_vassal days = 3650 }` |
| `curse.098` | 98 | 传说 | 秘契 | 褪色的馈赠 | `add_diplomacy_skill = -1 + 	add_martial_skill = -1 + 	add_stewardship_skill = -1 + 	add_intrigue_skill = -1 + 	add_learning_skill = -1 + 	add_prowess_skill = -1` |
| `curse.099` | 99 | 传说 | 秘契 | 重压的账契 | `add_stress = 150 + 	add_character_modifier = { modifier = xar_leg_stress days = 3650 }` |

## 实现位置

- 数据表：`tools/pools_data.py`（改条目改这里，再跑 `py tools/gen_pools.py`）
- 抽取/发放：`common/scripted_effects/xar_generated_pools_effects.txt`（GENERATED）
- 选项槽文本：`common/customizable_localization/xar_generated_pool_loc.txt`（GENERATED）
- 修正：`common/modifiers/xar_generated_pool_modifiers.txt`（GENERATED）
- loc：`localization/<lang>/xar_generated_pools_l_<lang>.yml`（GENERATED，9 语言；含动态 wrapper + 池条目名 + 修正名）
- 事件：`events/xar_events.txt`（xar.0004 / xar.0005 / xar.0006，手写不变）
- 拒绝扣分：`xar_compute_score_effect` 末尾 ×max(0, 1 - 0.01 × xa_bless_reject_count)
- 稳定 ID 语义契约：`tools/pool_semantic_contract.sha256`。普通生成不会改它；只有人工审阅本表与 dispatcher diff 后，才用 `py tools/validate_static.py --print-pool-contract` 输出的新值更新。
