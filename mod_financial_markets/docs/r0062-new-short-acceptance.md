# R0062：正常GUI新SHORT真实成交，累计5/6

2026-11-22，machine_id: 4-8e1c2f1861。本机CK3 1.21.0／build26622941，scene21s／R0062，运行源码 `d4255f6845c0f46c13aaae50dc48eb63154cb80b`；Q44实际编译来源仍为 `7e19220153d6c6dcf25b8bf4cdcb96234a708e4a`、DLL SHA以 `307a3cb5` 开头，不改写原产物来源。

本场沿已保存R61终档继续，两份真实物理SAVE同为raw53150688／financial day261，零新增自然日。基线19,137条完整记录与来源相等；没有observer、补日、注资或重放旧UNKNOWN动作。

## 新SHORT与真实双边保证金

正常GUI提交新SHORT374／native16795348，一手2倍，在军事模型指数62、永续合约6／native1163，以120分与原独立BUY372实际成交，生成新仓191／native16795353。买方账户1839／native6795、受益人31915，与玩家PRIMARY2／native54、受益人31254独立；不是临时虚构对手或只有回调ACK。

空方实际保证金60分，长方120分，双方本次手续费各1分。PRIMARY可用8132→8071、冻结335→395分；对向账户可用278→302、冻结585→560分。6308个账户加手续费总账始终1065677分，费用44852→44854分。43项只读独立核算条件全true，它们不是43项新增软件测试。

新仓191携带P1版本1的十项公共数值，直接关联原BUY372／SELL374及永久账户1839／2；三个仅减仓时适用的条件字段缺失，保持缺失，不补0或回填190个旧仓。P1不提供出生fee／受益人／现金快照；本次保证金和费用由两档真实账户、预留及订单累计差额核实。完整图恰新增5个金融对象，旧记录无缺失，旧仓及不相关义务保持；已允许的索引／链尾变化经Root逐项审阅，未拿总数相等代替身份对账。

## 原metadata失败与有限通过

基线父pipeline因actor输出顺序假设退出1，后继suffix因summary漏checkpoint局部绑定退出1，原失败保持。原归档／audit／whole／Raw及三项比较共12个子操作均实际退出0；Root依据已完成的比较先接受基线并走正常GUI。seal04退出0／16.0485237秒只封metadata，没有重SAVE、重parse或重compare，不能将旧父pipeline写成0。正常short02 pipeline退出0／115.2539541秒。

Root最终仅授本场新SHORT格OBSERVED；2倍选择是setup，不另加杠杆格。期货零日GUI累计5/6，剩余reduce本场NOT_OBSERVED：没有新减仓动作／对应SAVE，当前缺SELL，不能制造流动性或保证旧151可以成交。

最终Root响应已在原预留前发布。公共run退出0／2053.2681033秒、verify退出0／0.9037848秒，case_acceptance_pass及qualified_boundary_pass为true，仅授该有限case。NativeGame11352于20:51:04.468132 UTC正常退出0，Host／retainedOS／Job均0，keeper5768退出0，allocator退出0；CAS16042→16043、done/resources[]。autosave_verified=false不等于已独立证实退出自动保存行为。原closure通用note还残留旧run/verify2-PARTIAL句子，原件不改；本场按typed字段、released及原wait的0／0结果记账。

## 已完成的存储操作与后继范围

此前compression22 old／recent两原动作均实际2，候选耗尽且目标未授通过：合计3份新NTFS压缩保持逻辑字节、身份、时间及完整hash，另1份already-compressed SKIP不冒称新body验证或收益。R61的restored单副本后继实际退役214168174逻辑字节，旧私有路径不可读，独立R60 PAID外档全hash保持；此前六副本清单的SKIP历史不改。新3520MiB准入另据实际容量通过，不因压缩／删除退款旧spent或自动授未来场。

唯一前进来源为本场short物理档：214169416字节、SHA-256 `bf55de02608f0915cfa79bf8e543daf12664527b87c6ff2eca420a45aaded0bb`。本场不新增日结算、正额资金费、到期／强平／债务、容量、通知或性能信用；426／631／411及Q44不重复加总，完整Mod及Workshop首发仍待。

[43项核算、P1、原失败、实际闭场和资源原件](../../docs/maintenance/evidence/2026-11-22-financial-markets-r0062-new-short.json)。文档作者仅消费已成元数据，不重读物理SAVE。
