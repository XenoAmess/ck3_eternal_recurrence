# 技能边界与实机读回参考

《超人强》的角色经验计数与技能转移使用独立生产脚本。技能读取的通用原生研究已富化到主仓：[CK3 1.20.0.3 角色技能 trigger 与属性转移读回](../../docs/ck3-native-ai/character-skill-trigger-readback-1.20.0.3-2026-10-04.md)，原始证据及 SHA 见该页的永久 JSON 索引。

已解析的普通六技能 getter 读取角色总技能缓存，不是基础属性。当前未证实 `base_diplomacy`、`base = yes`、`source = base` 或其他基础技能 scripted value 接口；本研究没有证明所有原生参数都不存在。原生 `add_diplomacy_skill` 写基础 `+0xC0`，没有同步写条件读取的总缓存 `+0xD8`。原版支持 `force_character_skill_recalculation = yes`，其已闭合调用链实际同步更新六项总技能字段。

## 当前转移合同：signed 账本与缩放修正

六项角色变量保存各自净转移点数，未设置时按 0，每项限制在 **-1,000,000 至 +1,000,000** 原始属性修正点。每次成功转移同一项接收者账本 +1、来源者账本 -1，原生基础数组保持，其他五项账本保持。来源者当前有效技能为 0 的项不进入候选；接收者有效技能为 0 仍可接收。本次 +1/-1 会越过任一方向边界的项跳过，剩余候选等权；没有候选仍双方经验各 +1。经验上限沿用 [产品规则](product-contract.md)，不由技能账本上限替代。

每项账本投影为 character modifier。静态定义中的 `scale.value` 读取接受角色的变量，在赋予 modifier 时计算一次。正式更新必须删除旧投影，再按新账本添加对应正或负投影；只改账本不能刷新既有 scale，0 则两种投影均删除。使用正属性 +1 与负属性 -1 两种静态 modifier、非负 scale，避免依赖未确证的负 scale 行为；不把缩放键写进 `add_character_modifier` 参数。

原版百分比修正、整数运算和总技能边界继续生效。原始转移点数严格 +1/-1，不承诺双方有效技能也严格 +1/-1：面板变化可能为 0、2 或其他原版计算结果。因此总值不变不能判定转移没发生，也不能触发再试扣或补点。零经验查看及 trait hover 只读角色计数；当前转移路径不使用破坏性基础技能 probe。

## 原版缩放定义与调用依据

只读核对目标安装 `C:/SteamLibrary/steamapps/common/Crusader Kings III/game/`，版本 **1.20.0.3 / build 25652598**。下表绑定实际原版完整文件字节；没有复制游戏源码入仓。

| 原版来源（相对 `game/`） | 确证内容 | 完整文件 SHA-256 |
| --- | --- | --- |
| `common/modifiers/_modifiers.info:12–23` | scale 位于静态定义；接受者为 root；赋予时一次计算，有效期保持；支持 named script value 和 inline math。 | `530ffc0e27d061c716d417d6f726d6227a7ea573f1c0073d61c71eaf6e090800` |
| `common/modifiers/00_story_cycle_pet_animal_modifiers.txt:127–145` | `loyal_eagle_story_modifier` 的 `diplomacy = 1` 按接受角色的 `var:eagle_personality_level` 缩放。 | `6f3d644d32b890dcc0dd3248e5a19b6c2eae393af38eccad96f3e35436c01e71` |
| `common/scripted_effects/00_animal_effects.txt:1429–1431、1548` | 按名称删除旧 modifier；普通 `add_character_modifier = loyal_eagle_story_modifier` 消费静态定义的 scale。 | `bfa1aac3780c9c0822ba1e2abc0a8c7bea885b89d8cd2e808651eef2351dd5e2` |
| `common/modifiers/07_ep3_modifiers.txt:1356–1359` | 静态 `personal_schemes_distracted_modifier` 使用 `diplomacy = -1`。 | `c4a7815e1d5f787699ffc4705a6f39ab742796e3493fce979e348f90147c4a9b` |

最小形状是 `diplomacy = 1` 搭配 `scale = { value = <正账本 script value> desc = <loc key> }`，负投影使用 `diplomacy = -1` 搭配负账本绝对值的非负 scale；其他五项相同。这是原版源级可行依据，**新模组实现及其 fresh live 验收仍 pending**，不把源级语法、离线 parser 通过或既有宠物 modifier 的调用外推成本产品通过。

新方案必须核对六项生产 helper 和真实随机入口、正负翻转及回到 0、单项百万边界、更新后重建读取新账本、重复重建不叠加、百分比取整、原生基础数组不变和保存重载。实际门槛见 [测试方案](test-plan.md)；需要强制刷新时仍使用已证实的 effect，但刷新不改变原版百分比及取整语义。

## 历史 R0006 RED 与 A0002 静态修复

本产品 [R0006](live-R0006.md) 已从原生存档确认旧探测方案 RED：确定性分支来源者漏扣一点、接收者没有加点，随机探测甚至漏扣来源者全部六项。原始存档读回、角色数组摘要和 SHA 继续保存在上述 [通用原生专题](../../docs/ck3-native-ai/character-skill-trigger-readback-1.20.0.3-2026-10-04.md) 及其永久 JSON 索引，原始 attempt 不改写。

[A0002 缓存修复静态记录](build-validation-2026-10-04-R0006-cache-fix.md) 对旧 generator 增加了 probe 正值 guard／基线前刷新、每次试探和恢复后刷新、最终双方提交后刷新。它针对已定位的缓存读取问题增加刷新，保留旧正显示候选限制与临时探测；静态及 parser 结果没有证明百分比取整下“总值没变即基础值没变”。当前账本方案已经替代这些破坏性探测，不沿用其通过数或候选规则。R0006 RED、A0002 静态事实和新方案 pending 分开记录，不把历史来源覆盖成新验收。
