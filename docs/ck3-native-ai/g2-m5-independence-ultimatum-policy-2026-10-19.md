# M5：独立派系最后通牒的普通规划消费

本轮补上普通规划器会主动接受独立派系要求的一个确定接缝：`faction_demand.0001` 第一显示项接受后，原版会逐一改变派系成员的隶属关系。源码已提前学入独立窄策略；当前原生窗口确认为这份已审事件、接受是原 fallback 选择，而且显示合法拒绝项时，改选拒绝并接受派系战争风险。没有把拒绝、调用 ACK 或窗口消失写成战争胜利、保地成功或实机资格。

机器身份：`machine_id: xenoamess-full-tower-eb9d2c1186`，身份读回出处为 `python -B tools/ck3_live_run_id.py machine`，本轮读回记录时间为 `2026-10-19T04:46:02Z`。来源逐文件 SHA、完整定义与实际读取 UTC 见[小型来源证据](evidence/g2-m5-independence-ultimatum-policy-2026-10-19.json)。这些是该机器当时的安装源码事实；当前运行 SDK 的加载字节和实际游戏结果未在本轮观察。

## 已有能力与真实缺口

`strategy.choose_one_life_turn` 在普通 `_choose_one_life_turn_core` 返回未覆盖事件捕获后，先调用 `annotate_source_reviewed_event_plan_v1`，再调用已有 `choose_source_reviewed_populist_refusal_v1`。这是此次唯一挂接点；增加后者开头的两行窄 dispatch，没有改 Service、Driver、普通战争、军费、采购、建设、投降或外交权限。

`.1001` 已有 source-reviewed refusal，AUTO193/本轮 frozen lessons 不必再造修复。本轮没有修改它的原识别与选项策略。`.0001` 没有专用策略，原生语义接到用户 unknown first-displayed fallback 后，会选接受；通用离线来源审阅即便标为 known，也继续选择第一显示项。这正是保地经验尚未被消费的接缝。此前独立战争领土后果纯事实叶仍不接普通消费者，不能因此宣称这条事件已避免割地。

## 来源闭合

本机实际文件 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/events/factions/faction_demands.txt` 的 SHA-256 为 `eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd`。事件 `.0001` 完整定义在 124–365 行，三个 authored options 顺序如下。

| native authored index | source name key | 来源效果与边界 |
|---|---|---|
| 0 | `FACTION_DEMAND_ACCEPT` | `on_faction_demand_accepted`；root dread/legitimacy 损失；建立 independency title change，`add_claim_on_loss=no`；`every_faction_member` 调用 `change_liege_or_become_independent`，双向 1825 天休战、条件 struggle catalyst、`.0002` 通知，然后 resolve title change 与 prestige 损失。|
| 1 | `FACTION_DEMAND_BRIBE_CO_EMPEROR` | 条件显示/可用的共同皇帝反提案；tooltip 展示接受/拒绝分支，实际发 `.0006` 给派系首领。本策略不估计其概率，也不把这个 authored row 当作必定显示项。|
| 2 | `FACTION_DEMAND_REFUSE` | 调用 `faction_demand_independence_rejected_effect`，向首领发 `.0003`；后者唯一选项在 385–404 行执行 `scope:faction.faction_start_war={}`。拒绝进入明确的开战链，实际 WarID 与开战时点仍需后验。|

拒绝 helper 在 91–120 行：先触发 `on_faction_demand_rejected`，显示派系开战 tooltip；independence faction 另有 clan unity 效果。原版 `common/scripted_effects/00_war_effects.txt` SHA 为 `f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b`，1271–1296 行的 `change_liege_or_become_independent` 在当前宗主独立时使成员独立，否则改属当前宗主的宗主。不能把所有接受结果都描述为离开最高层帝国，也不能把 target 命中集当实际失地列表。

来源证据保留四个完整定义和三个完整 option body，包括条件、隐藏 effect、AI weights；并未在摘要中将条件当作当前已满足事实。计入已有来源审阅器所有 option 字段的 catalogue SHA 为 `6237b0c9f4e27ba6f1197d8cad68d41b58bfd64112cdb8705d80b626759f9192`。保留的完整 block SHA 按已有 `block` parser 结果计算，包含其抓取的前导空白并保留原始 CRLF，不混用“从 key token 起”的其他历史 hash 约定。

## 认识、选择与后验边界

M2 审过现有持久知识合同：`event-source-registry` exact entry 必须绑定实际观察到的 calculated definition ID 和真实 incident 来源；不能为提前学习伪造一份。新独立叶的静态 `REVIEW` 只含 build/EXE/source/catalogue、选项语义、依赖和来源链接；`readiness=static-ready`、`new_live_evidence=False`、`observations=[]`，没有 instance、calculated ID 或虚构实机 incident。

当前选择前，专用 recognizer 要求 `.4` 原生 backend、三项 authored count、唯一窗口、完整 readiness、当前 pause/map/frame/date/episode/PID/connection/actor/instance 绑定，以及 root/faction_target 为玩家、真实 typed faction 与不同玩家的 faction_leader。拒绝项必须实际 `shown=True`、`enabled=True`，并具有当前 advertised native selection step。它从已审 catalogue 的拒绝 key 找 native index，再从当前显示 row 取 rendered index；共帝项隐藏时拒绝在 rendered 1，共帝项显示时可在 rendered 2，不能将第三 authored 项误作固定第三显示项。

既有 durable exact source 知识如存在，必须仍为当前 fingerprint 和 known 决策；source/facts 验证拒绝记录、其他 binding mode、catalogue 漂移、未审 source、未知 key、失效帧、缺失或禁用拒绝项，均保留原 first-displayed 计划。静态知识不覆盖现有 source validation 的失败。新 audit 使用独立名称 `independence0001_source_reviewed_current_binding`，当前 ID 来自本次原生窗口，不冒充旧 generic exact registry entry。

Native event DTO 没有加载中定义的 SHA；静态原版来源与当前 key/count/typed shape 绑定不等于验证了加载字节，audit 明确 `loaded_definition_bytes_verified=False`。这与静态源码认知不同：本轮提前学习的是已审原版语义，运行资格、mod 覆盖、战争触发和实质领土变化仍需各自证据。本轮没有热换当前冻结 SDK。

提交继续沿既有 Service 的 generic unhandled before/after capture。捕获绑定改选后的 native row；ACK 与 `event_instance_advanced_verified` 分开保存，错误 native index 的 ACK 不获窗口前进信用，不重放。新策略输出保留 `exact_lost_titles=None`、`war_started_verified=False`、`victory_verified=False`、`title_retention_verified=False`；不以兵数推胜率，也不改变后继全战争处理。

## 一次离线验证与存储

全部 frame/actor/definition IDs、options 展示与 ACK 测试均标为 **SYNTHETIC**，不是新存档或实际窗口资格。

一次 runner 执行新策略测试和 `.1001` 已有 focused/source-binding/cold-rebind 四个文件：**54 passed / 1 failed，3.76s**。其中新 `.0001` **17 项全部通过**：源码完整选项/依赖、普通公开 hook 的两种显示布局、当前 exact-known 路径、11 个 source/unknown/合法性/帧拒绝条件、2 个正确/错误 native ACK 捕获。

唯一失败属于既有 `.1001` 冷恢复测试 `test_enabled_restore_hook_intercepts_unresolved_target_before_native`：该测试 `object.__new__(GameplayBridgeService)` 未初始化 `driver`，公共 Service 在 `service.py:5036` 的新 `getattr(self.driver, ...)` 先于 before-submit hook 读取它而抛出 `AttributeError`。已交 Root/公共叶负责人；本包没有修改其源码或旧测试掩盖失败。原始 runner 回包为 `functions.exec` command chunk `275ae7`。最终父任务如修复公共叶，可独立追加其真实回归结果，本记录保留首次失败。

遵守通用存储策略 `1.0.0`。仅小型源码、测试、来源记录；无 Game/RPC/桌面/活 Driver/SAVE 读取，无构建或 C++/规则 hash 更改；临时来源导出脚本已经精确移除。新包按共享研究小池计费，预计峰值低于 1 MiB；文档/来源记录按 record 类复核 `2027-04-17T04:51:51Z`，代码、测试与必要来源链接随现行策略保留，替代后按通用策略重评。Root 统一 commit/push，本子任务不 stage。
