# 机制合同

## 支持范围

功能仅对 `is_ai = no`、`top_liege = this` 且政府恰为行政制、贤能制或天朝制的玩家开放。日本律令制与草原行政制不在 1.0.1 范围内。两个开关默认关闭并彼此独立。

## 自动选择继任

原版五套省级任命继承类型为：

| 政府 | 原版 appointment type |
|---|---|
| 行政制 | `admin_governor` |
| 贤能制（文） | `meritocratic_civic_governor` |
| 贤能制（武） | `meritocratic_military_governor` |
| 天朝制（文） | `celestial_civic_governor` |
| 天朝制（武） | `celestial_military_governor` |

本 Mod 以相同相对路径覆盖三份原版定义文件，保留每套候选池、等级要求和评分正文；仅在原版把独立君主分数归零之后，追加条件扣分：候选人是独立君主本人、该君主为人类且持有 `xqol_auto_appoint_successors_enabled` 时再减 `1,000,000`。因此死亡继承与原版 `force_step_down_landed_titles` 卸任链都会选择其余合资格候选人中的原版最高分者。关闭时追加分支不命中，行为与原版逐字等价。

若原版候选池确实没有第二位合资格人选，游戏仍可能使用自身的最终兜底；本 Mod 不生成凭空候选人，也不改写候选资格。

## 别把封臣给我

原版 `grant_vassal_interaction` 的 AI 路径会拒绝带 `ai_should_not_transfer` 标志的待转移封臣。本 Mod 只处理“待转移角色的直属领主采用 administrative 类政府，且其最高领主是已开启功能的受支持玩家”的角色，并按需设置：

- `xqol_no_vassal_transfer_guard`：所有权标志，说明 `ai_should_not_transfer` 是本 Mod 设置的；
- `ai_should_not_transfer`：原版实际消费的 AI 禁转标志。

若角色原先已经带 `ai_should_not_transfer`，本 Mod 不声明所有权；关闭时只清理同时带有本 Mod 所有权标志的角色，从而保留其他内容设置的原版保护。`on_vassal_change` 负责新进入或离开受保护层级的角色；`yearly_playable_pulse` 是低频自愈。玩家手动转封不受原版 AI 专用检查影响。
