# 战争第4期 B：休整数字通过，合军后冻结条件失败

R0175-a02 实际完成两支军队的供给休整观测，随后在第38日合法合军。合军后新增一个1/1军团，当前将领也发生变化，触发既有冻结条件。Root 正式停止本臂，状态为 `STOPPED_GATE_INCOMPLETE`；没有继续赴 London，也没有修正将领、排除新增军团或挑选重跑结果。

本包包含原始 JSON、相对路径索引和仅用 Python 标准库的消费者，无需本机 C 盘目录、游戏或 SDK 即可读回结论。共同入口由 [INDEX.json](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/INDEX.json) 定位。源包的历史 pending 字段保留原样；后来完成的停止、闭合及媒体审阅使用独立增量。

## 共同输入及真实主体

本臂来源是纯原版1.20.0.3、冻结源码 `7f1db1a773e647b9f31378d4a9ccf57a60cf9e73` / a08；实际 episode 为 `native-33388-23726fbd8a80`，actor33388。共同 whole checkpoint 为73795635 B，SHA256 `d052a2e412109a28247b8844567100a272998c536711d75f0fbc29ee6a286f6a`。T0为raw53148432，绝对终点为53150592，共90实际日；本臂没有重置预算。

合法平分读回 Main public/native0 与 child public204/native199。Main15团3337/3371、25条 DATA；child12团3342/3376、12条 DATA。两组互斥，完整并集为原27团、37条 DATA，当前人数6679守恒。实际将领分别为27357和33388，不能从其他 run 借用人物、public/native映射或健康数据。

Root 接受的首次休整锚点在本臂第6日raw53148576：Main停在2174，child停在2327，均为 `regular`、完整空路线、月供给getter为+2000000。局部31日截止raw53149320固定不变；每次 driver 继续运行没有替换锚点。

## 实际休整和整数人数变化

以下供给数值均为原始整数，scale100000。每个观测窗口独立保留完整主体、将领和时钟来源。

| 窗口 | 实际变化 | 能支持的结论 |
| --- | --- | --- |
| 第20→21日 | child stock11037716→10000000；capacity10000000，月getter+2000000；`+188`写入日期53147760→53148936 | 真实超容量库存收敛到当前容量；此窗口的库存差为负值，不能叫正库存增长。Main库存未变。 |
| 第26→27日 | Main3337→3344，child3342→3345，总人数6679→6689；六条 DATA 的整数current/effective增长 | 原27团/37条 DATA身份和maximum保留。整数变化与prepared_fraction、补员权限字段变化分别列出；没有应用账本或兵员变化原因证明。 |
| 第31→32日 | Main stock10613988→12613988；capacity30000000，月getter+2000000；`+188`写入日期53148480→53149200 | 真实低于容量的库存增加+2000000；完整27团/37条 DATA整行在此窗口无变化。 |

两个供给分支落在同一固定休整窗口内，Root 实际资格收据为 `ROOT_ACTUAL_B_REST_QUALIFIED`。月getter为正、补员许可或位置到达不能单独替代这两个实际库存写入窗口。数字详见 [B-qualified-rest-values.json](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/merge-exception/qualified-rest/B-qualified-rest-values.json)，其引用的原始观测和消费者随包保存；R0173 的资格研究没有替代本臂实测。

## 合军实际接受，冻结队伍和将领条件失败

第38日raw53149344，typed `merge-armies-0-with-204` 原回执accepted、`merge_applied`。新鲜玩家roster从[0,204]变为[0]，Main public/native0存续；child从roster消失不能推导为死亡。

合军前Main3344/3371、child3345/3376，总6689/6747。合军后Main实际28团6690/6748：原27团整行没有变化，原37条 DATA整行差分为空，另外新增FullID16778273的current/maximum为1/1。该团的 `maa_type_status` 为absent、key为null；完整 `native_all_data_records` 容器为available、record_count0、records[]。这些字段没有证明它是骑士、永久不可补员或某种兵员producer，新增类型和原因保持UNKNOWN。

新鲜typed commander查询读到Main当前将领33388，原Main将领为27357，所以 `commander_preserved=false`。实际post stock/capacity均为10000000，月getter−423728；这组端点本身没有证明库存加权、clamp算法或将领选择机制。

[B-merge-exception-values.json](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/merge-exception/B-merge-exception-values.json) 与原始body保留完整异常。其验证器的PASS只表示失败证据的来源、字节和对照可以重算，不能解释为冻结合军条件通过。

## 正式停止及运行闭合

Root正式terminal为 `STOPPED_GATE_INCOMPLETE`，实际使用38日、剩余52日，`deadline_reached=false`。这不是到90日仍未到达的截尾结果，也不是B的London终点；London指标和winner均为NULL。Root直接审阅合军后原图见Apr12暂停、6690、stock100/100，原图收据与numeric source分别保存。

之后SDK及keeper退出、GameJob0、全部所属游戏/录制进程树为空；受管supervisor实际exit0。屏幕任务CAS5113→5115、DONE、resources[]。supervisor exit0不能外推为游戏进程exit0。

S02实际 `NORMAL_TREE_EMPTY`、FFmpeg returncode0、Job active0。原片3363279647 B、SHA256 `de8f9c72f64e62bc14461ee6611a301d1dc765599f138b015cacaf54dcd7f468` 来自原录制worker终端收据，本数据包不携带或重新读取原片。闭合细节见 [B-closed-terminal-values.json](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/closed-terminal/B-closed-terminal-values.json)。原terminal的 `raw_closure_pending=true` 与原closure的 `media_audit_pending=true` 保持历史原样，不以新事实覆盖。

本专题记录休整数字资格和门禁停止，不授予B到达完成、整体ABC胜负、连续clean span、精确原生事件PTS或人工1×完整签核信用。NPC和驻军变化、补员应用账本、新增军团类型/原因、合军供给和将领producer等未闭合项分别保留，不能用净人数或现金差shortcut归因。

## B S02 后续机器审计及单帧审阅

独立 [B-S02-media-review-values.json](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-b-gate-stop/media-review/B-S02-media-review-values.json) 增量保留原始审计、media delivery及Root三张实际encoded原图的后续审阅收据。机器报告PASS：2080秒、1920×1080、30fps、62400完整解码帧和video packets、无音轨，strict decode无stderr错误；完整PTS/DTS严格递增。这里的stdlib消费者只核相对小JSON及这些报告之间的pin关系，不重复媒体探测、读取原片或PNG。

Root直接看本段ordinal6000/PTS200000见Apr6 Main3344/S126of300；31200/1040000见Apr12 child3345/S100of100；43980/1466000见Apr12 whole6690/S100of100。它们是本段媒体真实decoded位置，不能推为原生事件精确PTS。Sea hover ETA仍非已提交actual route。原media delivery里的Root review pending字段保留，新收据单独记录后续审阅；S01与S02独立PTS、段间间隔没有连续clean信用。B的STOP、第38日、London/winner NULL和人工1×完整签核未完成等边界不变。
