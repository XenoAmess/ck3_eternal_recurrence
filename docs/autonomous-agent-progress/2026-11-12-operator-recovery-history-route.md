# 原操作员恢复事件的跨批历史读取修复

本轮普通游玩在 UTC 2026-11-11 17:16:07 出现新的 Life UNKNOWN，独立于旧 Sway 事故。parent346 保留两个真实 children：ARM339 已结算；resume345 已有提交与正 ACK，后续 fresh READ 负 ACK 为 `fresh_full_state_native_read_unavailable`。原执行期限 17:41:30.687424200Z 不变，不能重发 ARM、resume 或 cleanup。head347 为 repair_required；最近结算推进100日，确认保存仍为先前8日，不把 observed 当作 saved。

既有同 ID 只读恢复随后读取历史时，在旧事件39落入普通 SETTLE 的 active-batch 门，抛出 `settled cycle crossed its real active batch or original retained control`。事件39实际上是已归档的 OPERATOR_QUARANTINE_RECOVERY：原 batch0 已消费，next1，零周期 credit，并非普通 SETTLE。这是确定的历史事件路由缺支，与首个 fresh READ 失败分开。

单生产叶 ContinuityBatchJournal 只增加一个局部防重标记及75行显式历史分支。分支核对原 session/batch0/next1/唯一 consumed batch、归档终态及观察原件、完整 ACTION 前驱与首次 child reservation、原 request/head、Controller 零 credit、保留 Driver、原 reducer 边及原观察时间窗，随后继续原周期回放。不新增恢复 admission，不改普通 RETAIN/SETTLE、年度保存、Guard、parser、hash 或旧编码；不增加保存或推进 credit。移除两处插入可逐字得到原整叶。

实际 active 变体从393104B/e60937fe…变为402585B/2ed13f43…；正式源保留其既有 Saved 等差异，只机械移植相同两处，397237B/04df8af4…。本轮正式变体未另运行 JVM，不把 active 资格说成整正式源码图验收。

必要 active 1TU 首编 exit0/accepted/CLOSE，21类455610B。独立完整474程序比较中473程序的 resolved Code、BSM、flags、locals、分支和异常目标不变；唯一 readSameGameHistory 生成方法7099→8655B、2837→3467指令，方法/字段/API保，无 LDC 宽度变化。Native另核完整 BSM 内容及逐索引映射，不强称嵌套原 raw SHA 或 BSM 顺序相同。完整 frozen0..347 动态 reader 尚未执行；软件与代码核通过不预授实际采用、当前地图或 child 结算。

原件为 `D:/ck3-state/resume91-runtime/life-postcondition-p0-20261112-01/NEW-LIFE-ORIGINALS-INDEX01.json`（20071B，SHA04ba78b7…）。源码/whole inverse 与 owner code 位于 `D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01/`：`source01-owner/SOURCE-READY01.json`（2134/4f8f4d1e…）、`OWNER-ACTUAL21-CODE-PEER02.json`（10281/1ab73bce…）、`formal-transplant01/FORMAL-SOURCE-DRAFT01.json`（1737/4d475b11…）。Native编译及 Code 原件位于对应 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/`，ACTUAL1524/023657d0…、OUTPUTS157803/6a42014c…、CLOSE204/46c38250…，窄 Code119072/f06312ce…均保留。

Journal阶段成本切点 `JOURNAL21-SOURCE-CODE-ONEJVM-ALLCOST-DELIVERY-CUT01.json`（6847/b54bfdee…）为17:44:51.232660Z。actor13.006098300102167秒嵌套于 operator14.863608499988914秒，不能相加或代整轮。原事件→切点1723.293062秒，SourceReady→切点984.056136秒，所有准备、错误、等待及更早真实开始 UNKNOWN_NOT_ZERO 保留。Native原rawNested/BSM顺序误门、owner写前薄件cap、JS封包/解释器路径错误均为0JVM工具原件，不覆写为无错误。三根当时2588862B低于本次4MiB；后继现场与诊断增量另按实际切点记账。上一操作员单元后到日志已超旧32MiB的失败切点保留，不靠换名、删除或搬移补绿。后到新增HB编译后，本单元 Native 实为2次编译，actor17.995061100111343秒嵌operator21.796717999968678秒；官方原心跳纯DATA解码由Runtime接棒执行，不加入Native actor总和，Runtime现场HB缺JNA失败/成功捕获分列。后到fresh三根4206709B超过4194304B预算12405B，metadata-budget=FAILED；功能编译/Code通过与预算失败并列，保全部原件、不删除搬移或抬旧cap。6MiB为新前瞻quote，不回改原4MiB配置或追认旧预算。Runtime另在18:00:15、第三次被动观察之前选择新8MiB前瞻范围，非Root已批准或旧预算补绿。

17:23标准 Core READ 实际 UNAVAILABLE，不能据 Game/keeper 存活推地图状态或 UI 原因。后到有限被动心跳诊断沿公开 attach/observe，单5秒窗口/32帧，零 Native 请求、动作、focus 或 flags写；原心跳8947B/SHA84d4d6ee…已保存，snapshot返回布尔不冒未归档的 snapshot 或 map ready。第一次缺 existing jna.tmpdir 的真实退出保留；补参数后通过，心跳官方离线解码与后继恢复另记。新诊断窗不是原命令期限续签。官方 NativeWire.decode 后原 payload8943B/SHA68934cbe…显示 installed=true/stop=false/failure=0/executor_exception=0、submission_enabled=true，但 paused_main_thread_observed=false/ready=false/date53170560/paused=false。它只能说明该原心跳分项，不证明地图或 source 故障已恢复；当时距离原 target53170608 尚有48ticks，不能先补 pause/cleanup 或授未来 sentinel 已触发。

既有 ActionObservationWindow 的同 ID reconcile 使用独立最多2分钟只读窗，嵌套取较早期限；Coordinator 只递归 reconcile 既有 children 并调用 observe，不执行子命令。Life 后态继续要求 canonical 原 command/Attempt、实际同 Game/actor/source/connection、原 ACK/outbound 与真实新观察，原 deadline 字节不改。Runtime唯一负责正常 resume 采用与这些实际回执；本次未取得新 SAVE，窗口不报告有限秒/日，未宣称10秒目标或 primary provider 故障已修。

后到18:00:39–42的第三次有限被动HB（0请求）仍date53170560/paused=false/ready=false；owner_verified pump增加但10分钟未推进日期，不承诺 sentinel 会自然完成。原packet8947B/SHA368fcd1c…及官方payload8943B/SHAc5895be7…保留。当前没有新的 pause/cleanup/盲resume；有限可见UI排查与后继实际恢复仍归Runtime按真实结果另记，源修复发表不预授 primary 问题已解。
