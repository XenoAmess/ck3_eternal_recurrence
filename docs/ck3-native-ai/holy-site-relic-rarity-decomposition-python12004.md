# 圣物稀有度贡献拆解：既有 MCP 的只读解释

`ck3_query_player_holy_site_relic_context_v1` 在收到既有 `recognition_matrix`
扩展时，增加可选结果 `rarity_decomposition`；工具名、参数、权限和原生调用次数不变。
旧 reader 没有矩阵字段时，响应形状保持原样。动作查询、预览 canonical 与 SHA 不变。

该字段用于向玩家及规划器解释已采集的稀有度输入。它的
`method=independent_matrix_projection`，`same_native_evaluation_as_total=false`：
原版总数读取和认可矩阵是两次独立求值，不能说矩阵就是总数函数当时的逐槽调用轨迹。
即使两者数值一致或 `capture_epoch` 相同，也不证明求值原子性、脚本无随机副作用或缓存已刷新。

按实际 `inventory.slots` 顺序逐槽输出，重复宝物 ID 保留重复贡献；仅拥有、未放入槽的宝物不相加。
已观察的空槽为 0；原始拥有引用计数明确为 0 时，记录 `inventory_count_zero`；
当地持有者的信仰明确未关联此圣地时，记录 `holder_faith_not_associated`，贡献为 0。
普通求和分支中，宝物对象与稀有度已知、该信仰关联圣地、对应认可矩阵单元明确为真，才贡献该宝物的稀有度。
明确不认可时为 0；缺计数、缺对象、缺稀有度、缺关联状态或缺相关认可单元时保留 null。

父响应和矩阵必须通过现有 exact-build、身份与形状校验；额外核对实际槽序列、玩家信仰、
当地持有者信仰和关联信仰来源数组。矩阵不可用、达到既有上限、来源不稳定或身份不符时，
拆解不可用，不影响独立有效的原生总数。无关候选宝物缺结果时，只要矩阵仍可用且实际槽所需输入完整，
允许 `complete_for_equipped_slots=true`；这不将整个矩阵提升为完整。

`reported_native_sum` 保留原版读取值；`projected_sum` 仅在所需槽输入完整且结果在 int32 范围内给出。
`numerically_matches_reported_total` 仅比较这两个标量，不替换原版总数、Active、缓存或收益读回。
现有原版总数继续是 `current_relic_evaluation`，不能依据拆解结果授动作合法性或全部信仰收益。

本轮另已闭合缩放脚本值的消费者：`holy_site_total_artifact_rarity` 最终读取圣地对象的缓存总数，
不是每次重跑当前求和函数。因此当前重评与 `cached_world_state` 不一致时须分别呈现；
不能用本投影的 0 宣告已应用的缩放修正全部归零。具体效果门与缓存来源见
[等级、参数与容量](holy-site-grade-effects-and-limits-12004.md)。

验证来源：machine_id `4-8e1c2f1861`，2026-10-18；基线代码 `d1c2bc7eb568a4eab3f55c065adb645a9dbace6f`。
本次为冻结的、由 C++ reader/serializer 生成的自有 fixture 包重放，以及明确标注的 Python 输入变体；
实际经过生产 Driver → Service → MCP ClientSession，public/native 序号分别为 2 / 9。
没有启动游戏、编译原生、额外执行 getter 或重新授予实机资格。

新验证入口：`tools/.venv/Scripts/python.exe -B -X utf8 ck3_autonomous_player/tests/unit/test_holy_site_relic_rarity_decomposition.py`。
同时运行既有 `test_holy_site_relic_recognition_matrix.py`，保留原矩阵上限、来源顺序和动作预览 SHA 回归。
