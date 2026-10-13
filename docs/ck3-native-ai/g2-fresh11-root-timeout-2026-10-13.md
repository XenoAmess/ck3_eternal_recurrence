# G2 fresh11：开局根查询超时与接续修复

接续[第二次休假交接](../handover/2026-10-13-g2-continuation-vacation-handoff.md)。用户要求继续从头以1066罗贝尔使用完整普通规划器。旧受限场次不计入本轮成绩。

## 实际结果

外置根 `R = D:/codex-ck3-background-spill/g2-remediation-20261013`，本场 `R/fresh-robert11`，新回执 `R/resume08`。正式实机编号为 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0005`，并非旧 attempt 名替代全编号。源码固定 `ad61be99bb6a8ae9d7c436164b123e8873ccea38`；1277个不可变SDK文件复用硬链接，新增物理源码字节0。

CK3实际EXE重新核为1.20.0.4／Steam25734779，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。无Native改动，复用B12，SHA-256 `28c01334e474a712180c94782d72c0880d7360e49296dbc82e73e23e9416b648`。Game273532／creation `20261013101030.217309+000` 实际启动；Desktop1放置完成，未切用户Desktop2或抢前台。Steam沿用交接中用户明确的离线保证，未切在线，也不声称取得新离线像素。

Root亲审实际独立录像sample006的主菜单后，route1、New Game2、固定Robert Start3各发送一次。前两项实际通过。Start3于10:18:17.145133Z开始，10:20:39.427455Z返回错误，耗时142.282326秒：

```text
native command_result timed out for gameplay step query-campaign-root-context-v1
```

Root随后亲审sample010：地图已出现罗贝尔头像、暂停HUD、1066-09-15和阿普利亚。实际Driver保存actor31254、episode `native-31254-0679e22d39f5`、ordinary／xar_off／no-pact绑定。这些事实不追认原Start为完整verified：没有camera4、semantic5、初始SAVE6或普通回合。

**有效普通回合0、日期推进0、已选战争目标0、胜战0；B12地图内完整owner-tree结果仍未取得。**

## 故障定位与Python修复

生产Start流程依次提交Start primitive、等待暂停玩家快照、等待post-ready pump、再读取campaign root。具体错误来自最后一步，不能仅因录制中仍显示载入0%就断言Start没有提交。此次没有重送Start。

原map/pump共用frontend transition deadline，但最后root查询仍落到primitive默认120秒等待。新修复将同一绝对deadline继续透传到root查询：发送前没有剩余预算则不发送，发送耗时也扣除，始终只等待同一个native request ID，不重新enqueue或延长原600秒总预算。root的角色、日期、版本、完整性与环境资格判断保持原样。

为避免再次丢失超时来源，Start root query的真实ID及prepared／pending／received／verified状态写入小型 `state/native-session/frontend-start-root-queries/<id>.json`，并通过既有diagnostics读回。当前没有新增通用root collector；fresh11旧ID未保留，不能事后编造或声称已收回其迟到结果。

定向验证12项通过，另有2项确受新增deadline参数影响的旧fake调用检查通过，`git diff --check`通过。覆盖超出旧120秒但仍在总预算内的迟到结果、单次发送、发送耗时扣减、零剩余预算、真实超时ID、日期不一致与到期后拒绝采用。初次fixture误计startup ping的失败保留；更正后结果见 `R/resume08/m_harness/DELIVERY.json` 和 `root-start-deadline-tests02.{json,log}`。这些是Python定向结果，尚不授fresh12实机通过。

只读Native路径分析发现root collector含两次character/province扫描，以及root callback周围的完整Snapshot；它们是潜在成本来源，尚无本场分段测时，不能指定为已证120秒根因。未发现root直接调用B12私有owner-tree helper；普通Driver文件大小也不是history复制成本。

## 录像、退出与未执行的观察候选

独立录像session `712b85be-11aa-46eb-a4e4-dae86e9fb027`，原片在 `R/custody-recorder01/recordings/<session>.mkv`：369,369,136 B、614.266秒，SHA-256 `21de68b90894aa24e22f83d7943d57842e3a0ba00f3507806fe66697c95c3fe0`。实际状态FAILED，错误 `actual output reached the reserved stop margin`；500MB是配置总上限，不能写成原片实际大小。Root最初1.5秒增长探测没有观察到增长，在没有启动SDK的条件下改为有界20秒观察，随后实际观察到2,961,408 B增长并只启动了一次SDK。

queue222952与application65156由supervisor持有原代际句柄；实际exit分别1／0。原queue保留Start错误后，外层TaskGroup仍于10:22:07.527634Z结束；小型ExceptionGroup摘要没有内层原因，不能把录像错误未经证明写成其精确异常链。Game一次正常关闭未退出，随后owned Job force清理实际exit1／tree_gone。OBS输入解除、独立engine实际exit0。个人OBS未控制。

keeper线程退出、failure=null，最后3994；Root以该序号CAS释放为3995。业务未完成。原closed、cleanup、failed、response和Driver均保留，汇总为本场 `ROOT-ACTUAL-CLOSED-EVIDENCE.json`。

Root在闭场后准备了仅接受当前错误全文的外置观察适配候选，但publish因 `EXIT-SDK` 已存在而拒绝，零观察RPC，没有清HALT、推进frontend或重放Start。该候选未运行，不能列为热恢复通过。

## 存储与下一场

沿用统一策略1.0.0、全组8GiB和原16:58:39.018273Z复核期限；没有加领预算或延长期限。启动前在任务总线锁内登记1.28GB峰值，并精确回收fresh06/07/08各last_save／autosave共6份相同副本413,653,532 B。各自canonical checkpoint、seed、Driver、响应和录像保留；原6路径现已删除，不重建同名证据。计划、实际删除和后续保留用途见 `R/resume08/ROOT-PRECISE-RECLAMATION-RECEIPT.json`。

fresh12须冻结修复后的clean HEAD，复用未变B12，先把原生主菜单加载与正式录像起点分开，再尽快完成camera／SAVE／首个普通回合。新的存储准入及完整录制额度在重型写入前另核，不能以本页的候选释放量当作实际已释放或已准入。

### 录制起点控制与第二批实际回收

公共录制器新增可选 `--start-signal`。它先绑定本场Game与decision、写入 `record-armed.json`；等待时每15秒只覆盖两张 `armed-latest` PNG和明确标为mutable的索引。Root必须复制并亲审实际主菜单帧，再写新signal；worker随后只通过原有路径调用一次StartRecord。未传signal的行为不变，原1200秒／1GiB及Game／存储时限不延长。28项离线定向检查通过，含默认、延迟、未知StartRecord超时不重放、等待到期零开始及覆盖帧不进入immutable回执；尚待fresh12实机。回执为 `R/resume08/m_recording/fixture-result.json`。

10:45:05Z第二批回收实际完成：5份已被后继替代的旧Native archive和fresh06／07各1000个shader副本，共2005个精确对象、1,095,563,830 B逻辑量。旧archive全部成员与622份保留OBJ逐项匹配；保留旧配方／OBJ／DLL，但未授容器时间戳字节可完全重现。shader逐文件匹配保留fresh08，游戏build身份相同；后续可变profile只允许独立复制。B12实际链接依赖、B9的612成员archive、319个direct object及canonical源保持可读。

各批在任务总线锁内核进程／用途，再用禁止并发写删的Win32句柄绑定身份和SHA，逐项删除并读回2005路径消失。首次在DELETE句柄期间再次CRT open产生兼容错误，实际删除0，原RED保留；后续从同一句柄读取并成功。实际去重逻辑占用6,614,496,574 B，组余额1,975,438,018 B；physical allocation未测、卷free并发差额不全部归因于GC。这是回收读回，不是fresh12空间预留。精确可用性及原manifest哈希见 `R/resume08/m_storage/GC-ACTUAL-SUMMARY-RETRY04-20261013.json`。原已删路径不再可读，未制造同名替代证据；原期限没有延长。
