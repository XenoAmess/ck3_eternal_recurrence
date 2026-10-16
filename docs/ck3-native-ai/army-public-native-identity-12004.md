# 公共单位 ID 与原生军队 ID 的同帧绑定

公共 `CUnit` 标识与原生 `CArmy` 标识属于不同空间。先从当前实际基线中唯一的 `army_id` 行读取 `native_carmy_id`，再与同一份基线的 `current_refill_classification` 交叉核对；不能要求两者数值相等，也不能把 R192 的 `93→85` 固定到下一场或下一军。

复用顺序：

1. 核机器、场次、源码、PID/create-time、generation、episode、actor、日期及暂停状态。来源机器的成功不代替目标机器读回。
2. 从实际 F0 的 `frozen_observable.armies[*].army` 选择唯一、available、`army_id == public_id` 的行。原生 ID 必须是实际正整数；缺失或多行即拒收。
3. 同帧 `current_refill_classification[str(public_id)]` 的两个 ID 必须分别匹配公共 ID 和该行原生 ID。不要补值或借旧帧映射。
4. Select 以公共 ID 提交一次。独立 UI 查询核 `current_subject_id == public_id`，另核 `native_army_id == native_id`；同时要求实际 army 窗口 accepted/available/effective_visible、owner/played actor 一致。
5. before/after snapshot、revision、native revision 及 UI 的 queried 字段必须同帧；generation/episode/date/paused 也分别匹配。ACK 不能代替窗口已显示。
6. 需要视频画面时，另外取得当前 owned foreground/client 原图，并由 Root 审图。语义 UI 成功、截图审阅、连续片段及人工签核分别记录。

R192 原件记录于 machine_id `desktop-3fevhd2-1c74096080`，源码 `60de49f61d23b9c3437af4544c3f12bb28445429`/a31，2026-10-16T22:18:26Z 至 22:18:56Z。已保存的组装回执给出公共93、原生85；随后独立截图回执与 Root 审阅回执引用同一 UI 记录和身份。Root 报告一次 native Select 后独立查询已可见、无 counter-click。这不是纯静态候选，也不授 R09 全卡、连续 clean 或 human approval。

旧 helper 错把两种 ID 要求相等，旧失败记录保持。兼容字段 `native_army93_visible_subject_verified` 的历史名称表示公共 Army93 的 UI 检查，不能据名称推出原生 ID 为93。

[来源索引](evidence/episode04-army-public-native-identity-12004/source-index.json)及[便携检查](evidence/episode04-army-public-native-identity-12004/verify.py)保留两个 helper、原交付与四份小实际回执的原字节。helper 含该场机器路径及 live capture/review 入口，作为已执行过程源码保存；不应在新 clone 直接运行。便携检查只核归档与小回执的引用关系，不重新读取原 UI 大包、基线、截图、存档或视频，也不重演 SDK。
