# 事件恢复的连接角色与真实 READ 原件（2026-11-05）

原事件 `event-8131…916af` 的 `select-event-option-1` 已有真实 ACK，原命令与期限保持不变。33 次恢复已取得独立后态：Native383/public316，旧事件与 pending interaction 均为 null；原期望的连接代次是19，真实 READ 后态的代次是25。`NativeEventPostconditionPort` 与 `ActionEffects` 两次普通比较都据此拒绝，最终525仍为 UNKNOWN。后态事件消失不能单独替代完整效果证明。

本单元为已绑定原动作的只读 EVENT 恢复增加显式比较入口。原 expected19继续绑定原 Attempt guard；after25保留真实 READ 的当前连接。其余 actor、事件、来源、机器/Game、episode、日期、版本与具体材料字段继续完整比较。普通 `project` 和通用 `ProposalLifecycle.compare` 保持原行为；恢复入口还必须绑定完整 canonical command/body、原 Attempt、原 receipt、实际 reconciliation identity 与 after 原件。

实时观察从现有 `ActionReconciliationScope.requireProvenance` 取得真实 `FreshSnapshotQuery.ColdAfterAcknowledgement`。新 effect-basis/v4 保存明确 profile、完整 Root guard 和原 provenance codec 表示。冷读取用原 READ ACK、snapshot chronology、原控制 ACK/custody及实际 frame loader 重验，再重放 NativeEventEffects 与完整 compatible result。Root 的冷消费者复用同一规则；事件 family 与公开结果读取均安装已有的真实 READ verifier wrapper。旧 v2/v3 与 `.unsettled/v2` 的 false 诊断记录保留原语义。

| 软件切点 | 实际结果与范围 |
| --- | --- |
| 最终生产 | 8TU首次0、56类、12.4138633秒；随后仅Journal03增编14类0、5.9939238秒，其他42类复用。正常新 loader 所需，不授原地重定义 |
| 必要旧契约 | 只RUN原 v3 全文 after/捕获时窗/拒绝哨兵方法，真实1P、6.2944315秒；旧Test和生产均未重编，其他旧3方法未RUN |
| 新Hosted DATA | 1新Test TU/3类首编0、4.8652138秒；3方法3P、4.2689929秒，0失败/错误/跳过。含原19/actual25不变、12个实际消费者拒例、v4严格字段与真实Factory拒非READ/缺原件 |
| 首次失败保留 | 原Test01编译0，三方法共同在fixture canonical预算参数检查处3E，尚未到业务断言；02只把两个helper三处64MiB RawJson常量换为合法1MiB ActionCodec预算。未改生产、断言、堆或期限 |
| 运行层 | 本文软件资格不授34实际装载、私Root发行、真实READ custody正例、原事件SETTLED、新游戏日或SAVE。由唯一Runtime在原动作受控只读scope验收 |

Hosted正例是明确未发行的结构DATA。它保留真实原命令/ACK与后态材料，但缺真实READ ACK正例，不能充当Root issuer；错误READ原件和缺档由真实verifier拒绝。测试源码及现场JSON留D执行机，未放入通用Maven套件或公开仓库。最终三方法和唯一受影响旧方法的原XML、原3E、source/actor/fence/close各自可追溯。

03额外收窄了Journal的新解析门：只有v4执行新增严格provenance解析，旧v3最低DATA契约沿旧路径到mandatory Root consumer。这个必要保持由上述旧方法实际1P验证。原936f `.unsettled/v2` 已经通过真实Scope、完整原件与mandatory Root诊断校验并持久化；empty supports仍不执行效果重放、不获得Applied信用。

模型54首次完整200/DONE，29.4264123秒、有效TTFT3.7900284秒、27733+4530 tokens；两新完整方法与整patch均源审拒绝，owner接管八叶。独立Test55首次length8000，62.9255541秒、TTFT18.9818611秒、148320+8000 tokens；整份正文/SSE未读未hash、0采用、无R2，三方法由owner完成。源码审阅错误、fixture实际3E、生产类型0、软件3P、正式投影与实际运行分层记录。

正式八叶仅移植对应owned spans，全部outside逆还原精确；其中四叶与实测actual全体相同，另四叶保留各自既有formal outside，不授整个formal reactor软件通过。原SHA/hash/parser与冻结Guard主题未改，原期限01:55:03.894579600Z不刷新，连接19/25均未伪写。首版仍限定当前Game/EXACT，跨Game及新历史关系不扩张。

实际最后已持33切点为原525 UNKNOWN、C22、169 eligible/8 saved；本单元不新增确认保存日，不报告有限秒/保存日或达成10秒目标。后到34装载和原动作结果另据真实回执补记。机器来源与精确SHA见[源码与证据索引](../maintenance/2026-11-05-event-reconciled-read-postcondition-sources.json)。


??34?????after/v3?v4 proof??526?UNKNOWN????checked IO???Assembler??????[????](2026-11-05-reconciliation-source-io-diagnostic.md)????????postwrite?Scope???canonical???
