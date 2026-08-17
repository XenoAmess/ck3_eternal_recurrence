# 祝福 / 诅咒奖池（权威表）

**本文件是奖池的唯一权威定义。代码（events / scripted_effects / loc）改动必须与本表同步，反之亦然。**

## 规则框架

- 商店「开始此生」后琉焰卿开启**垂青会**（`xar.0004`）：展示祝福池随机 3 项（无放回）+ 「什么都不要」
- 选中祝福 → 立即发放 → 必须再从诅咒池随机 3 项中选 1（`xar.0005`，无退路）→ 回到祝福事件
- 每场垂青会**上限 3 祝福 + 3 诅咒**；选「不要」或领满即散场，**3 年后**（1095 天）琉焰卿再度现身（`xar.0006` 重置会话）
- 每完成一对祝福/诅咒，**最终结算总分 +1%**（加算，N 对 = +N%），结算明细单列一行
- 角色死亡 → 结算后进入观察者模式，计时自然作废

## 数值原则

**同类型奖励：祝福量级 = 诅咒量级 × 0.75**（诅咒更强，这是代价感的来源）。
整数类凑整到最接近 0.75 的比值（属性 +3/−4）。无数值量级的（特质）按同类型配对。

## 祝福池（10 项，等权重）

| id | loc key | 名称 | 效果 |
|---|---|---|---|
| 0 | xar_bless_0 | 余烬遗金 | `add_gold = 150` |
| 1 | xar_bless_1 | 众口的颂歌 | `add_prestige = 225` |
| 2 | xar_bless_2 | 静焰的祷声 | `add_piety = 225` |
| 3 | xar_bless_3 | 耳语之网 | `change_influence = 75` |
| 4 | xar_bless_4 | 琉璃色的体温 | modifier `xar_bless_health`（health +0.6，10 年） |
| 5 | xar_bless_5 | 巧言的馈赠 | `add_diplomacy_skill = 3` |
| 6 | xar_bless_6 | 戎光的馈赠 | `add_martial_skill = 3` |
| 7 | xar_bless_7 | 书库的残页 | `add_learning_lifestyle_xp = 750` |
| 8 | xar_bless_8 | 不败之躯 | `add_trait = physique_good_1`（健壮） |
| 9 | xar_bless_9 | 宗门的余晖 | `dynasty ?= { add_dynasty_prestige = 150 }` |

## 诅咒池（10 项，等权重）

| id | loc key | 名称 | 效果 |
|---|---|---|---|
| 0 | xar_curse_0 | 漏底的荷包 | modifier `xar_curse_gold_drain`（monthly_income −1，10 年；1.19 无合规的一次性扣金币手段：add_gold 负值运行期被拒，remove_gold 已移除） |
| 1 | xar_curse_1 | 暗处的嗤笑 | `add_prestige = -300` |
| 2 | xar_curse_2 | 圣像的沉默 | `add_piety = -300` |
| 3 | xar_curse_3 | 断线的傀儡 | `change_influence = -100` |
| 4 | xar_curse_4 | 蚀骨的寒痕 | modifier `xar_curse_health`（health −0.8，10 年） |
| 5 | xar_curse_5 | 褪色的心眼 | `add_intrigue_skill = -4` |
| 6 | xar_curse_6 | 蒙尘的经卷 | `add_learning_skill = -4` |
| 7 | xar_curse_7 | 锈死的门环 | `add_diplomacy_lifestyle_xp = -1000` |
| 8 | xar_curse_8 | 缠身的病影 | `add_trait = sickly`（体弱多病） |
| 9 | xar_curse_9 | 黯淡的族徽 | `dynasty ?= { add_dynasty_prestige = -200 }` |

## 实现位置

- 抽取/发放：`common/scripted_effects/xar_bless_curse_effects.txt`（`xar_draw_blessings_effect` / `xar_apply_blessing_effect` 等，无放回用 `random_list` 条目 `trigger` 排除）
- 选项槽文本：`common/customizable_localization/xar_loc.txt`（`xar_bless_slot_a/b/c`、`xar_curse_slot_a/b/c`）
- 事件：`events/xar_events.txt`（xar.0004 / xar.0005 / xar.0006）
- 修正：`common/modifiers/xar_modifiers.txt`
- 结算加算：`xar_compute_score_effect` 末尾 ×(1 + 0.01 × xa_bless_count)
- 新增/删除条目 = 改本表 + 抽签名额 + apply 分支 + 槽位 loc + 9 语言 yml，五处同步
