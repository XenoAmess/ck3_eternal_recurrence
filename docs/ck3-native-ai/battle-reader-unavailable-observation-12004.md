# 战斗读取未完成时继续观察

2026-10-16，`machine_id=xenoamess-full-tower-eb9d2c1186`。
本条整理当前罗贝尔长局 P17/P18 的实际故障及已采用的 SDK 修复。
主线集成不修改正在运行的 Game、Native DLL、SDK 或录制进程。

P17 AUTO222 的 `query-battle-control-snapshot-v1-285213008` 在应用主线程执行后返回
`typed_result=false`，执行完成、外层帧稳定且无异常。当前 Native adapter 把多个内部
不满足条件的结果折叠为同一种错误，故具体失败谓词仍未查明。公共 CUnit ID 到 CArmy
再到 Combat 的转换路径没有发现本次 ID 错误；不能据这个错误宣称 CombatID 尚未物化。
既有原生控制读口与身份物化合同保持不变。

Driver 只针对这一精确终态失败，独立读取一次当前暂停语义帧，核对同一玩家、episode、
Game、连接、日期、局面版本、战斗地点与参战军队集合，然后返回明确的
`xar.battle-control-readonly-unavailable.v1`。回执保存实际原始 request/result，
history `ok=false`；它没有可用 battle snapshot，不授权预测、撤退或重放查询。
其他错误和变化的帧仍保留原始失败。

普通规划器可选择已有的 speed1 精确一日原生时钟，逐日回读战斗。首次失败在下一游戏日
重查；同一战斗范围连续两日失败后冷却 30 游戏日，期间使用便宜的日级语义回读。
退出战斗、参战集合或地点变化、玩家/连接变化、逐日连续性中断都会使旧范围失效。
这降低重复慢查询成本，不改变宣战、议和或战争结果偏好，也不把不可用读口伪装成完整观测。

同包补入的路线 Halt 策略只消费已有原生动作：同帧完整路线证明即将发生未经合格策略允许的
接敌时，选择现有 `halt-army-*`；收到提交 ACK 后等待新的路线和目标读回，不重复提交。
Halt 的源码与离线夹具通过，本场尚未取得它的实际游戏动作验收。公共主线原本已无
“敌军 CArmy 不可读且我军移动时直接推进一天”的捷径，本次没有重复加入或删除它。

P18 AUTO10 已真实返回上述不可用 DTO。随后队列因使用较旧 SDK namespace，导入应用侧
新 helper 失败。外置分类器改为自包含 `classify_*` 函数和字面量大写常量，通过现有 AST
安装与原回执重消费，在同一 SDK 内恢复；没有重放 AUTO10。可复用分支见
[`battle_reader_unavailable_classifier_v1.py`](../../tools/g2_saved_campaign/battle_reader_unavailable_classifier_v1.py)。
它只提供新分支，`None` 交回原分类器；部署者仍保留全部已有 material/available 分类。

当前实机已持续续行，战斗实际失利，防御战争尚未结束；之前两场主动战争胜利保持各自原证据。
本修复不授胜利、完整战斗读口或 30 年目标完成信用。

原件索引（本机外置工作包，非代码发布路径）：

- `continuation42-cold-prep/p17-responses/0222-1-result.json`：原生 battle typed failure。
- `continuation42-cold-prep/p18-responses/0001-1-result.json`：实际同帧语义范围。
- `continuation42-cold-prep/p18-responses/0010-1-result.json`：实际不可用 DTO，SHA-256
  `6b20f93eaf4ad272044be14191490e1a33d885e718879694346ee493af9cc558`。
- `ROOT-P18-SELF-CONTAINED-CLASSIFIER-VERIFICATION.json`：原件回放、真实队列方法离线验证。
  SDK 内实际安装和重消费另由 Root 的控制回执证明。

仓库保留小型字段投影夹具，明确标为 projection，源 SHA 保存在夹具中，不能替代原件。
原件按通用存储策略管理；本故障最小证据下一次复核为 2026-10-23，禁止无限保留派生副本。
本轮为 Python DTO/调度修复，`open_kaishek` 脚本语义预验不适用；无 CK3/native 调用。
