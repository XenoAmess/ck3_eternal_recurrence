# 二期原版 1.19.0.6 合同

本文件冻结二期实现依赖的原版入口，升级 CK3 时必须逐项重审。

| 功能 | 原版入口 | 本 Mod 的使用方式 |
|---|---|---|
| 防御召集 | `on_war_started`、`call_ally_interaction`、`call_house_member_to_war_interaction` | 用完整互动 validity 过滤，随后调用原版防御加入 effect；排除一切付费调用 |
| 改信筛选 | `ask_for_conversion_courtier_interaction`、`demand_conversion_vassal_ruler_interaction` | 用 `is_character_interaction_potentially_accepted` 和 literal `ai_accept=0..100` 过滤 |
| 改信答复 | `religion_demand_conversion_default_modifier`、`demand_conversion_interaction_effect`、`demand_conversion_vassal_ruler_interaction_effect` | 内部异步互动镜像接受率，二元累计接受/拒绝 |
| 牵制索款 | `demand_payment_interaction`、`golden_obligation_value` | `run_interaction execute_threshold=accept`，由原版 effect 扣款和消耗牵制 |
| 赎囚 | `ransom_interaction`、`ransom_interaction_effect` | 保留原版付款人 redirect、价格、劫掠传承加价与付款释放后果 |
| 条件释放 | `release_from_prison_interaction` | 七个隐藏互动镜像 H/R/C 可用条件、接受分及接受后果 |

已知必须实机验证的边界：滑条点击与拖动在 0、1、49、50、51、99、100 的精度；异步批量改信最后一条答复是否只产生一次汇总；战争开始 scope alias 与全部免费候选去重；连续共享付款人的赎金余额重验；七种释放组合的原版等价后果。
