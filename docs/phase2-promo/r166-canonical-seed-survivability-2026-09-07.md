# R166：三次角色死亡后的 canonical seed 存活保护

## 触发证据

R162、R164、R166 三次 promotion/full-tree 实机推进均由同一类 one-life
终止条件结束：验收绑定的玩家角色在业务树闭合前死亡或被继承人替换。R166 的原生快照在
`date_raw=53160984` 精确记录 `actual_player_character_id=36354`、
`expected_player_character_id=32904`、`one_life_terminal=true` 和
`one_life_terminal_reason=played_character_changed`；当时产品 runtime blocking
diagnostics 仍为 0。因此这是场景寿命不足，不是产品脚本 RED。

项目所有者已明确授权：因角色病死连续三次验收失败后，可以给验收角色添加健康值与 buff。
该阈值在 R166 达到。

## 最小处理

manager-seed fixture 在最终可见 `zga_phase2_manager_seed.1` 选项中仍先移除
fixture-only `zga_phase2_manager_seed_survivability_modifier`，避免 product-only
加载时出现缺失 modifier key。随后把 CK3 1.19.0.6 原版可解析状态写入新的
canonical save：

- `add_trait = immortal`；原版 `common/traits/00_traits.txt` 定义
  `immortal = yes`，阻止再次因自然死亡终止长周期验收；
- `feast_good_food_modifier` 持续 1100 天；原版
  `common/modifiers/00_activity_feast_modifiers.txt` 只提供 `health = 1`，没有战争、
  经济或 AI 决策副作用。

正式天朝二期产品树不新增验收专用 modifier，也不修改任何产品机制。保护只存在于重新物化的
验收 seed 存档；健康保护本身不构成业务树 GREEN，仍必须在 product-only full-tree 中按默认
5 速完成真实动作与后置状态验收。
