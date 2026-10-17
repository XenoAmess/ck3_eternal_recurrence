# 移动ACK未知后的独立路线观察

`machine_id: xenoamess-full-tower-eb9d2c1186`。本批只移植SDK45的四处公共生产叶增量，保留公共主线额外功能；上批已入库的战果窗口两叶不重复应用。没有复制完整SDK、场次queue、Driver状态、SAVE、媒体或Game DLL。

## 原错误与后续观察分别保留

SDK44窗口11实际在143日后失败：FULL416／AUTO453于2026-10-17T14:06:15.252605Z报告 `move-army-167772577-to-2621`、expected Native6285、`CK3 move-army state is unavailable`，cycles4365、raw53297328。原生把多个提交前错误与提交返回未知共用这一错误文本，因此不能据此断言“没有提交”，也不能重新发送原Move。

实际437的该军路线为空，后续454／457独立暂停帧出现完整目标路线 `[2621]`。Root采用456原位观察核对，保留原失败行与原始请求，明确ACK未知；0新Move、0重放、0日期／业务／周期信用。后续461普通规划仍缺少“已接受Move”历史而阻塞，本次Strategy补上对独立路线观察的消费。路线已存在不等于原生命令被接受，更不证明安全、接敌结果、围城成功或战争胜利。

## Driver等候晚到快照，Strategy消费完整路线

Driver只针对上述精确Native错误，在即时读回仍为同暂停地图、actor／episode／Game／connection／日期和同Native版本时，使用现有 `_wait_for_snapshot` 等候已发送命令之后的独立新帧，最多2秒且不超过原command timeout。后续原有raw request／reply、public／Native版本、owner、目标和完整路线守卫保留。新帧缺失、错误scope或其他错误继续报告原错误；只发送原来的一笔Native请求。

返回DTO仍为 `accepted:false`、`native_ack_status:unknown_after_error`、`native_ack_verified:false`，同时明确 `business_submission_may_have_applied:true`；历史 `ok:false`。这是独立观察，不是“确定未提交”或成功ACK。原raw request使用Native版本，普通planner使用public版本，两者不能互换。

Strategy只消费该typed DTO，或与原最新失败Move严格对应、有独立audit／原响应SHA的 `reconcile-observed-move-intent` 历史。当前暂停帧必须实际持有目标、完整非空路线且无战斗／撤退；actor、episode、Game、Native版本及日期均受既有界限约束。SDK同Game换代后public版本可重置，当前原生路线仍须重新观察；不把旧public版本当跨代全局时钟。新的失败Move会遮住更早接受的Move，不能借旧成功掩盖新结果未知。

独立新帧实际到达目标、清空移动目标和路线后，可以识别 `arrived_sieging` 的路线意图终点，ACK仍false。是否围城、接敌、contact-free和可推进时长，继续由当前普通完整规划与独立Native接触范围／时钟证据决定。

## 测试入口与限制

公共正常导入测试分别执行真实Service、Driver constructor、`execute_step`、`_execute_primitive_step`、ProtocolState命令回执、`_record_command`与 `_wait_for_snapshot`。只替换Native endpoint／snapshot输入与预选的起始规划输入；`public256/native3207→public257/native3208`刻意不同。一笔原请求、晚到快照、connection／actor／路线漂移、等候超时、其他错误及未知ACK零信用均有定向验证。这不证明实际原版提交结果，也不冒充起始普通planner选择由本测试完成。

独立Strategy测试使用94KB已完成响应／audit字段投影与原SHA，不依赖外置SDK或完整Driver历史。合成到达、未来horizon及clock选择明确只验证消费者路径。原外置 `21fb162f` 测试替换primitive、record和snapshot的事实已纠正；它是typed分支到正式queue classifier的消费测试，不能称“仅Native I/O为替身”的完整生产入口。完整生产入口测试与消费者测试分别留回执，不把旧绿色扩大成它没有执行的路径。

## 可选写入分段诊断

`environment.write_bytes_atomic` 的默认 `timing_step=None` 分支保持原字节逻辑。仅已有可选诊断路径增加temp文件open、stream write、close三段时间及payload字节数；旧总write和replace段保留。不开启 `XAR_CK3_ARMY_TIMING_JSONL` 时不发布诊断文件。没有增加fsync，没有改变临时文件／原子replace语义、SAVE绑定或失败后dirty历史保留。

五项生产持久化测试覆盖完整字节、SAVE绑定、错误后dirty／旧文件保护、open／write／close／replace错误与原pathlib顺序等价、默认路径不启动诊断以及诊断目标不可写不改变已完成写入。该增量是诊断，未实施盘符迁移、写入hint或新的性能优化，不授实机速度收益。

## M7与当前采用边界

[M7有限报告](research/m7-natural-readonly-reconciliation-v1/REPORT.md)、[plan副作用审计](research/m7-natural-readonly-reconciliation-v1/PLAN-SIDE-EFFECT-AUDIT.json)及[已闭living帧投影](research/m7-natural-readonly-reconciliation-v1/CLOSED-LIVING-PROJECTION.json)只保存一个已识别的私有harness接缝：sentinel内死亡后，新继承人已发布但reconciliation尚未生成时，原SEM不能代替普通planner的既有Root读取。候选仅在严格expected heir／同Game／EP／goal守卫后执行一次现有只读plan和一次fresh SEM，再回到原完整分产qualifier与原Continue／Close／SAVE事务。plan会保留读取观察及更新内存reconciliation，不能称无副作用纯函数；不执行规划动作、不安排镜头、不推进日期。

该M7候选为六项离线研究，继承人发布与事务接缝明确为替身；没有新SDK API，也没有当前自然继承实机通过。G2仍6/8。稳定30年优先，其后<1秒／日，再0.5秒／日，均未达成。

上批精确提交 `87b64c8579ac3e0232c72ec3774918b23da1caaf` 的[Official39041657167](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39041657167)与[Linear39041657081](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39041657081)均SUCCESS；44ff原RED及外部测试更正历史保留。本批新的提交、CI与实机采用各自另计。

### 后续实际SDK45接续截点

[首批健康小投影](evidence/sdk45-observed-route-health-2026-10-17.json)核对八个已完成小原件：SDK44 queue／application均正常exit0，Game和录像未停；SDK45 SEM1为同Game51028、Robert31254、Native6287／public2、connection7、raw53297328，当前路线仍为 `[2621]`。FULL6真实10轮完成、共6日，首个正向AUTO17后的MET18为raw53297400，即从起点+72；批末cycles4376／raw53297472。Root的 `a7ea7033` 准入据此开启新窗口12，旧窗口11失败不改写。

这证明本次已有路线观察续接、完整普通新horizon及后续实际进日。永久Driver“未来移动报错后有界等新帧”的分支尚未复遇，旧453的ACK仍未知；实际首批健康不替代该分支实机验收，也不证明连续稳定30年或速度达标。本段是固定交付截点，不是实时运行指针。

M7完整最小[零上下文研究补丁](research/m7-natural-readonly-reconciliation-v1/terminal-readonly-reconciliation-zero.patch)与[来源pins](research/m7-natural-readonly-reconciliation-v1/SOURCE-PINS.json)保留44冻结base到候选的可重建差量；45的namespace／source-epoch重绑由Root／fresh另行完成。补丁不作为公共运行API直接应用，未授自然继承信用。


### 最终公共连接测试

本地合并运行26项／11子例通过，另4项既有accepted route／restore／clear／contact回归通过，共30项。新增一项将真实Service→Driver→wire／history输出直接交公共零信用classifier，再进入普通 `choose_one_life_turn`，选择新Native horizon查询；明确合成的同帧未来horizon才使普通planner选择既有clock step，测试不执行clock。正式P45 queue canonical AST另用真实六字段startup baseline消费该生产输出，public256／Native3207分开，三项wire／public／ACK篡改均拒绝。

便携history只保实际7211–7222十二行。前置7210条 `history-elided-offline-fixture` 是明确非证据占位，仅保持原flattened索引；不算实际业务、周期或历史覆盖。测试中的未来typed DTO替换原failed行只存在于反事实输入，原错误／独立audit投影不改写。完整Driver正文没有读取或入库。具体公开文件、源包、语义差异及测试边界见[精确来源清单](evidence/sdk45-move-observation-public-transplant.json)。
