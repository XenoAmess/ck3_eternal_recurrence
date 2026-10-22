# NPC 连续场次验收（第一阶段）

当前实机状态为 **NOT_RUN**。正式入口、保存观察器和离线回归已接入；本文件不授予 NPC AI 实机、GUI、完整产品或发布通过。离线结果、命令、原工具输出位置和源码摘要见 [验证回执](evidence/npc-continuous-offline-validation.json)。记录机器为 `pc-20260924rtuf-f11af23c08`，记录时间为 `2026-10-22T12:46:55Z`；其他机器须重新核实本机环境与实机结果。

## 正式入口与执行方式

共享产品清单 [ck3_mod_acceptance_products.json](../../tools/ck3_mod_acceptance_products.json) 注册产品 `living-artifacts` 的 `npc_continuous` case，加载 [npc_acceptance_adapter.py](../tools/npc_acceptance_adapter.py) 和 [npc_continuous.contract.json](../tools/npc_continuous.contract.json)。清单中的 `ready` 只表示入口已实现，不表示已经运行或验收通过。

`prepare_case` 调用现有 NPC 输入生成器和共享 `materialize_fixture_profile`，部署正式 product staging 与外置 fixture，检查完整部署文件集合、来源摘要、外层 `.mod` 和 `dlc_load.json`。fixture 使用 `NpcFixtureSpec(0)`，不生成 51 件队列。它从真实现存 AI 候选中选择 landed、baron、courtier、fragile；三个健康角色获得初始资源、目标活武器和原版四种稀有度的材料。候选不存在时保留缺候选标记，不伪造角色。

运行沿用共享 `Session` 的原生快照、逐日推进、弹窗处理、Save 与 `CasePort.root_checkpoint`，没有另一套 attempt 状态机，也不主动调用 NPC 的装备、训练、喂养或 AI 处理 effect。上限为 47 个自然日、320 次预算内公共调用、4 次保存；正常关闭属于共享入口，须另留实机截图、保留的 OS 退出码 0 与 native 退出结果 0，不以本 case 的返回或静态 profile 作为退出成功。

| 保存 | 自然日 | 目标日期 | 用途 |
| --- | ---: | --- | --- |
| 初始 | 0 | 1066.9.15 | 绑定真实角色、目标和四材料，建立完整初值 |
| 次日 | 1 | 1066.9.16 | 观察第一次自然 AI 行为 |
| 第一月锚点 | 16 | 1066.10.1 | 保存装备和已结算成长状态 |
| 第二月锚点 | 47 | 1066.11.1 | 与第一月锚点比较成长，保留最终状态 |

运行与复核都绑定同一机器、玩家、PID、连接代次和四个日期。初始来源还须通过原版罗贝尔开局绑定；fixture 输入属于人为构造初始条件，因此不验收随机自然觉醒率或无输入辅助的自然获取。

## 独立检查与准确范围

每个健康角色分别保留 `BIND`、`EQUIP`、`GROW`、`TRAIN`、`FEED`，共 15 项；fragile 另有一项 `BIND`，总计 16 项。

| 检查 | 必需证据 | 不授予的结论 |
| --- | --- | --- |
| `NPC-BIND-<healthy role>` | 玩家保存变量中的真实角色引用、真实角色记录、完整库存、目标与四材料引用、物品 owner 与角色 inventory 双向一致 | 不单凭候选名称证明实时 AI、健康、费用或秘密状态 |
| `NPC-BIND-fragile` | 真实角色引用与对应角色记录存在；缺标记、缺引用和缺记录分别诊断 | 只验绑定，不验其培养、健康、秘密或费用行为 |
| `NPC-EQUIP-<role>` | 目标初始确实未装备，后续仍由同角色持有且真实保存装备槽引用目标 | 初始已装备不算新装备；私有变量不算装备真值 |
| `NPC-GROW-<role>` | 10月1日和11月1日目标仍归同角色、两个保存时点都装备，已结算累计经验增加 | 不证明两时点之间始终装备，也不把经验全归因于被动月成长 |
| `NPC-TRAIN-<role>` | 初始无训练冷却标记，后续出现真实训练标记且目标成长；实际部署脚本中该标记仅有训练成功分支写入，并存在原 AI 调用链 | 不单凭经验上涨判断训练，不验实际声望付款 |
| `NPC-FEED-<role>` | 初始无喂养印记，后续新增真实 `primary_armament` 印记、同角色初始材料确实不存在、目标成长；实际部署脚本的独占写入位于销毁成功后的经验结算分支，并存在原 AI 调用链 | 材料转移、引用缺失或物品消失本身都不算喂养，不验费用或所有喂养类型 |

实际生产脚本的源码检查会拒绝额外标记写入者、重复 effect、缺 AI 调用链，以及把唯一喂养标记移出销毁成功分支。它与保存变化共同支持本阶段的动作判断，源码存在本身不等于 AI 已执行。单个健康角色的初值缺失会保留该角色的阻断结果，完整角色仍可形成自己的基线；fragile 缺候选只使其 `BIND` 为 `BLOCKED`，不抹掉三个健康角色的结果。只要有必需项阻断，case 总状态仍为 `BLOCKED`。

## 保存来源与装备观察

Save 实际回执 → Root 原请求 → [checkpoint_producer.py](../tools/checkpoint_producer.py) 复制原保存并严格 melt → 公开 `CaseClient.root_checkpoint` 文件消费者 → 唯一 [verify_checkpoint](../tools/checkpoint_callback.py) → [npc_saved_observer.py](../tools/npc_saved_observer.py)。原玩家 `verify_readback` 也委托同一文件验证，不复制或放宽来源守卫。

装备来源是 `living.<character id>.alive_data.inventory` 的原生保存字段 `owner`、`artifacts`、`equipped`，并与实际 artifact 的 `owner` 交叉核对。区分整个 inventory 缺失、装备字段缺失、空装备集合、物品不存在、物品转移和引用缺失；不把 mod 的 `xalw_*` 装备变量当原生真值。角色与物品 ID 使用规范十进制字符串，保留原变量编码，入口执行严格类型与 JSON 往返校验。

R8 同日期的实际玩家 weapon 查询与两份真实保存已校准“完整 inventory 中 equipped 字段缺失表示当时未装备”及 `equipped.weapon=<id>` 的表示。外置对照 `comparison.v2.json` 的 SHA-256 为 `4611a3312ada1ad11bafdaad548bc7b2c5ab2449da76b41090731d2dca94c279`；新观察器手工校准回执 SHA-256 为 `6b644ad1f4d3344028dde5ab170e1394a58b21a61c24151524ca7add33c36cc6`，机器同上。此校准仅涉及该版本、玩家 weapon 与历史时点，不外推其他装备槽或 NPC AI 通过。

早期实际 live 保存路径可能被后续 Save 覆盖。离线复核保留原预期 pin，经原 Root 请求及留存 raw 文件精确核验，不要求被覆盖的 live 路径仍含旧内容。复核重新消费四份保存、重建基线、重新计算检查，不能仅凭结果 JSON 形状追认通过。它还核对完整结果字段、机器、严格整数计数、检查状态/原因/范围和所需证据摘要。

这些结果始终属于**保存的历史时点**，不是 current native NPC 装备查询。只凭保存字段或离线构造数据，不能追认当前游戏、连续区间行为或 AI 实机结果。

## 已完成与尚待执行

离线实际结果为：产品完整测试 151 项通过；相关共享三个完整测试模块共 38 项通过；产品全部 37 个 Python 文件 strict mypy 通过。新增 adapter 的构造场次覆盖实际 producer 到两个真实消费者、完整共享 Session 的 47 日/四保存、部署闭包、独立 Python 进程中的正式包导入，以及错误字段、类型、场景、来源和动作标记的拒绝路径。外部 melt、原生帧和游戏推进输入在这些回归中明确为 authored stand-in，不是实际 CK3 执行。

测试 UTC 未单独留存，回执中保留 `null`；原输出只存在本次工具 transcript，以 chunk ID 引用，没有补造独立日志或测试时源码快照。回执的源码 pins 是记录时读取的精确字节，不代表冻结了全部测试时生成/加载图。共享整个 SDK、完整部署图的所有间接依赖及真实 AI 通过均不由这些局部结果自动获得资格。

下一次 fresh 场次须实际消费该正式入口，取得四份来源完整的保存并运行复核，逐项记录 `PASS` / `BLOCKED` / 真实失败，保留实机截图和正常退出后验。fragile 健康/秘密/费用、51 件队列、自然随机觉醒、其他槽位原生校准和完整发布验收继续延期。

玩家正常 feed preview 的 `[SCOPE.ScriptValue...]` 显示修复另设短玩家场次验证，并提供真实玩家材料；本 NPC fixture 只准备 NPC 资源，该 UI 结果不计入 NPC 自主行为事实。
