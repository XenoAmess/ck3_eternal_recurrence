# Faction pending：已到达新暂停帧时只重规划一次

AUTO515 的失败发生在规划阶段。513 已提交一次赠礼，ACK 仍为 pending；515 只等待到了合法的新暂停帧，随后抛出旧 `PreSubmissionRevisionMismatchError`。普通 Service 已有一次只读重规划器，但其 classifier 不认识这条 faction 条件，异常因此越过 `plan_turn` 返回为工具错误。**515 没有进入选定步骤的提交、before-submit callback 或原生赠礼/回执发送。** 这不撤销 513 的不确定提交，不允许重发赠礼。

`machine_id: xenoamess-full-tower-eb9d2c1186`。实际时间、冻结来源与 SHA 见[小型证据](evidence/faction-pending-paused-replan-2026-10-19.json)。本轮只读 runtime 已封小投影和 `13eb02ce80249921b1ac1313507793c382e08448` 的冻结 Python 源码；无 Game/RPC、活 Driver/state、SAVE 或现场 metadata 写入。

## 真实来源与边界

runtime 的 `c6-faction515-failure73/FROZEN.json`、`context/CONTEXT.json` 及后来精确封存的 `faction-gift-pending-v1.json` 记录：513 请求 `faction-gift-d29a273508614be4aa0fdfaba560667c`，玩家31254、faction52、recipient34973、native418、date53153472。Native ACK 为 `submitted_verification_pending`、`executor_invocations=1`。514 仍是 native418、public351、同一 episode，Game PID153556。根目录没有 faction 文件不能证明没有 pending；真实 ledger 路径是 `state/native-session/faction-gift-pending-v1.json`，这份原件已单独封存且字节稳定。

冻结 `faction_gift_formal_route_v1.py` 的同进程 pending 分支在 planning 调用 `_wait_for_pending_paused_revision_v1`。它只调用 Driver 的有界 snapshot wait；底层等待 public state 并读取 semantic 缓存、附本地观察，没有 native `endpoint.send`，也不修改赠礼 ledger。成功守卫要求同 actor/episode/date、暂停地图、无事件/交互，以及 public 和 native revision 的真实前进，然后在原171行抛出515所见精确错误。

冻结 Service 的 `auto_turn` 原4771行尚在 `self.plan_turn()`；未返回时原4779行 `_execute_planned_turn` 和 before-submit hook 均不可达。回执 `_send` 又在独立的执行函数中。因此这个特定错误的**515 业务提交边界可由来源证明**，不能将其泛化为所有错误都可重放。实际 fresh revision 没有包含在515错误返回中；能从精确抛出点推得 native>418/public>351，不能把 harness 合成419/352写成该帧实测值。

当前新 PLAN 若仍是同一 CK3 process、同 episode/actor 的已前进暂停帧，旧冻结策略的 pending 分支会直接选择 `private-query-faction-gift-receipt-v1`，而非再次提交赠礼。harness 另有它负责的 queue220 有限0RPC清理合同；本修复不改 queue，不重放515，不读现场确认回执应用。

后续只读核对实际517的已完成 response（78,782B，SHA `7df0fe8ccb389f387b37d0aa409b9dfd9187182902c61caff0b285c5bdcaa184`）：正常 PLAN 已到 native419/public352，但实际选择的是 `private-query-faction-gift-cold-recovery-v1`。这是精确步骤差异，不是参数或显示名差异；runtime 因此在 NEXT518 停住，没有执行冷查询。此前“可直接选receipt”的结论明确以同 process 身份判断正确为条件，不能用来替换517真实计划。

冻结来源另闭合一个确定缺口：`runtime._process_identity` 的 WMI 路径返回原 CreationDate（可为 local `+480`）；access-denied/moniker-syntax fallback 的 Toolhelp 生产器在 `environment.py:1407` 返回 UTC `+000`。旧 faction route 的计划、同进程 receipt、冷恢复三处都用 raw string equality。这足以让同一个 birth 因合法编码变化误走 cold，但截至本包记录时，517分支当时的新 raw creation 字符串没有回显，**不能把这个来源解释写成517实际已核原因**。runtime 已有的物理 PID/birth、pending 原 raw 与517步骤各自保留，新的只读 OS 身份核对由 runtime 负责。

补充实际 OS 证据：runtime 在 `2026-10-19T06:59:37.172210Z` 通过冻结 `src05/runtime._process_identity` 仅调用一次，回 `creation_date=20261019131054.525692+480`；独立 retained kernel handle 证明 PID153556、birth134368602545256920、alive 与实际 launch 一致。该独立 Base313 probe 未仿运行 App 的 `-S` 依赖注入，原函数也不回显 WMI/fallback 分支，故它证明物理 Game 未更换，**不证明517当时用了哪个字符串或分支**。原件 `C6-GAME-OS-IDENTITY74.json` 及 SHA 已入本包索引，没有修改 pending。

## 永久最小修复

仅修改两个 SDK 叶：

- `bridge/faction_gift_formal_route_v1.py`：成功 wait 后生成专用 `FactionGiftPendingFrameReadyError` 与小型 typed proof。proof 含原 pending ID、process 身份、两帧各自 public/native revision、同 actor/episode/date/PID/connection generation、暂停地图和无窗口状态，并明确本次未提交赠礼、未查回执、未重放赠礼。先检查 pending 玩家身份与 session，再生成 proof。
- `bridge/readonly_planning_retry_v1.py`：只识别此异常类及完整、相互一致的 proof，复用已有 `retry_readonly_planning_once_v1` 的最多一次完整 fresh plan。拒绝未分类 mismatch、仅同样错误文本、字段不全或声明业务已提交的 proof；不执行旧计划、不改旧 revision、不吞超时或 material unknown。

另将 pending native 前进比较统一到 `pre_native_snapshot_revision`。本场两个 pre revision 都是418，所以这项身份纠正不是515根因。保留原 ledger 格式和 `pre_snapshot_revision`、原计划真实 public351，测试用 public413/native13 证明没有将两个 revision 域互换。

同一 faction 叶还统一三处 process 比较，复用已有 `environment.same_process_creation_time`，保留原 raw 字节。相同 PID 加同一严格 UTC birth 不因 `+480/+000` 拼写误判；1微秒不同 birth 仍是不同 process；不可解析的不同 birth、缺失值及字面 `None/null` 保留 unknown，不能宣称 `new_process_confirmed`。原 raw 完全一致的历史非空标记保持兼容，未按 PID 单独放宽。真正执行冷恢复仍须原 process 分支与后验守卫通过。

暖换 SDK 后 public revision 可以重置，本修复不将其与旧 App 的 public351相比较。proof 只比较一次 wait 起止的当前 App public 域，并核相同 PID/connection generation；pending 的进度只用原 native418。原 `pre_snapshot_revision=418` 与 `pre_native_snapshot_revision=418` 两字段不作迁移，public351留在原 planning-source-frame。

只读 wait 的成功 proof 不清 pending，也不授赠礼效果信用。完整 fresh plan 仍要走原独立 receipt 查询和原材料后验；只有其证明钱包、gift opinion 等匹配后，原 ledger consumer 才能完成该请求。foreign owner、日期改变、regressed native/public、事件、超时或第二次 race 继续保留原错误与 pending。

## 一次定向验证

全部测试 frame、ACK、process 标识与独立 receipt 均为 **SYNTHETIC**。首先执行三文件：`test_faction_gift_formal_route_v1.py`、`test_readonly_planning_retry_v1.py`、`test_faction_gift_pending_v1.py`，结果 **30 passed，2.63s**，runner chunk `6fe425`。后来实际517暴露 identity 分支后，追加新行为并必要重跑同三文件，最终 **36 passed，2.69s**，runner chunk `0a687a`。没有重复无变化矩阵。

新增覆盖实际 Service planning wrapper 的一次完整 fresh plan→原请求 receipt；规划期间 ledger 字节不变、赠礼发送0次，后续仅发送一次 synthetic receipt 查询。另覆盖9种异主/日期/episode/PID/generation/native/public/timeout/event拒绝、同文本非 typed error/已提交或未知 proof拒绝，以及重复 race 共享一次重规划预算。identity 追加覆盖两种 DMTF 等价 birth、同birth拒冷/走receipt、1微秒不同birth、原raw同值兼容和 malformed/None。旧 pending、ACK、冷恢复、未知不重发测试一并通过。whole-Service 历史夹具仅两处 process marker 改为有效 DMTF，不扩展或重跑该大矩阵。Service、Driver、冻结 SDK、现场包均未修改。

代码和回归由 Root 合批提交；必要 Windows CI 命令见证据。本包为小型 record/source 产物，无重型写入，遵守存储策略1.0.0和当前共享研究池；复核期 `2027-04-17T06:55:00Z`，替代证据出现后按统一策略重评。旧515错误与513不确定 ACK保留；没有新增实机结果或 G2 信用。
