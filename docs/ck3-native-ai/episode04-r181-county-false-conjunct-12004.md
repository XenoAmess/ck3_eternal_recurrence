# R181：多终点false不等于多条县边失败

R181 Army18实际到2644/date53147712后，Root报告12个有限只读preview均false。本包直接读取并用生产 `normalize_county_entry_condition_in_route_preview` 严格消费其中**具名6份**：050→1034、053→2643/2642/2641/2640/2635；另读本scene较早的024直边2645→2644，共7份。没有把未读6份当前候选冒充独立核验。来源机器 `desktop-3fevhd2-1c74096080`、当前源码 `09b83be4b46dc1938d05ccca65023905c99a8431`；观察时间、原envelope/proof与源合同pins见 `ROOT-DELIVERY.actual-a14.json` 和 `PREVIEWS.actual-a14.json`。

七份均是available原生false，actor31254、public/native Army18、mode1/Army1D4raw0，同R181实际runtime proof的episode/generation；其中六份source2644，较早一份source2645。它们不是unavailable补false。无SDK、游戏、桌面、新EXE/save/大raw读取或构建；没有R04 positive。

| 实际请求终点 | 实际原生route | child实际first hop | 已发布门 | 可说的结论 |
|---|---|---:|---|---|
|1034|[1034]|1034|1B=1/0；县指针不同且nonnull；target magic=`0x4E756C6C` (Null)|24E2230首先因target definition byte0走false；目标pointer非null不等于有效CoDa。不是缺少某个“敌我”条件才false。|
|2643|[2637,2642,2643]|2637|1B=1/1；两pointer非null且不同；target magic=`0x436F4461`；nativefalse|共同raw门通过，仍有未发布条件失败。|
|2642|[2637,2642]|2637|同上|再次测试同一first edge。|
|2641|[2637,2641]|2637|同上|再次测试同一first edge。|
|2640|[2637,2640]|2637|同上|再次测试同一first edge。|
|2635|[2645,2635]|2645|1B=1/1；源/目标县pointer相等；CoDa；nativefalse|共同县对象差异门直接不通过；未进入P链。|
|较早024→2644|[2644]，source2645|2644|1B=1/1；源/目标县pointer相等；CoDa；nativefalse|正向也在相等门旁路。不是县边阳性测试。|

六份当前候选只覆盖三种first edge，其中只有2644→2637通过已发布共同门：1034被byte0排除，2645被县对象相等排除。264x终点变化没有进入本次native predicate的target参数；它始终2637。不能把四个远端false当成四个不同县/不同邻接链失败，继续同frame请求同first hop没有新的条件信息。

## exact mode1还缺哪个合取项

已闭 `24E2230` 的mode1顺序是：两definition byte非0、源/目标县pointer不同且源非null，然后依次要求：

1. `P(actor, sourceCounty)` true（CALL24E22AE→2C09DF0）；
2. targetCounty非null，`P(actor,targetCounty)`第一次true（CALL24E22EC）；
3. targetCounty+3E0为CoDa；
4. `P(actor,targetCounty)`第二次true（CALL24E2343）；
5. 对targetCounty+40/+4C数组中的每个非null N，`Q(actor,24D4ED0(N))`都false；Q为2C097F0。

因此2644→2637的false只能收窄到上述**尚未观测的Psource、Ptarget两次、邻接Q**中至少一处未通过；不能据现有child分配唯一原因。raw gates调用前后稳定并不代表内部关系/数组已经被逐项采样。mode1的target+88/+8A不形成独立false门；本次也不能用mode0的额外比较来解释。

规划模型容易漏掉的合取项是**离开源县的P也必须true**，而不只是目标县条件。它若false，会先于所有目标P短路，使同一2644起点的全部终点false。应把它列为首个诊断对象；这是一项信息优先级，**不是已经查明R181就是Psource失败，也不证明源县友方/己方**。本次四个有效raw目标还共享2637，所以Ptarget和2637邻接Q仍是同等可行解释。

### P内部已闭到哪里

`2C09DF0(actor,County)`先核County+3E0 CoDa、County+18 FullID经实际Land registry5D1DAF8/fallback5D1DAE0解析且Land magic/ID有效，再用 `24D4ED0(County)` 的实际返回作为receiver，尾跳 `2C09620(receiver,actor,nullptr)`。preview child没有发布这些Land admission、receiver或P返回值。

完整192B `24D4ED0`有原生helper24D4D20返回Char的快路，以及County+18→Land+128→Character/fallback解析路。快路helper仍未知，不能把返回receiver换成公开legal_holder、occupier/controller或county_title_id。

完整191B `2C09620`先比较receiver+18与actor+18，**同FullID立即false**。其后28BC250返回对象+20为FullWarID；resolved/fallback War+358raw byte0且aux为空/同War时true，否则测试2C09580或2C09780。县wrapper的R8D0只是64位nullable aux pointer的null，绝不是本次county mode1。现active War、target敌人标签及公开holder都不能替代这些具体源输入。两个fallback predicate、pair lookup及Q未由本包新增展开。

### 反向证据边界

24E2230不是已证的无向边函数：它区别source、target，并只遍历**target**县的邻接链。正反向即使两byte均1、同mode，也不能互相推导true/false。现在有两份实际same-scene证据：024的2645→2644以及053请求2635的firsthop2644→2645，**各自child内部**都直接观察到源/目标县pointer相等，故双向false都有独立共同门解释，不需要跨query拼地址。它们不能检验Psource或邻接Q，也不证明2637反向会怎样。R180历史2635→2645 false属于另一scene/process，不能用其opaque地址或revision绑定R181。

## 下一次有限只读实验

1. 先复用已经保留的12份响应，按 `(actual source, actual first hop, actor, mode, same runtime/frame)` 看是否还有未审的**不同first edge**；这不需要重发preview。来源不同的snapshot/process不混为一帧，不以opaque pointer跨scene join。
2. 上一轮建议的反向2644→2645其实已由053请求2635覆盖，且县pointer相等；**取消追加请求，本轮新增preview数为0**。不重复024或053，不再Move。Root已接受保存/闭场停止规则。
3. 同origin、同actual firsthop、同actor/mode的结果归并，不加刷其它远端终点。将来新scene确有新first hop时，按实际1B/CoDa/raw gates和最终bool记录；只有available/true才进入原R04一次Move recipe。当前false条件下不自然推进或改军队来“试出”阳性。
4. 这不能证明世界上没有可行县损耗边，只说明本场这批现接口候选没有阳性。另一个controllable Army若实为combat/deferred，也不冒充一个可用的跨source对照。下轮有来源的readonly对照应改变**源县/actual firsthop**，而非只换远端终点；当前不指定一个未观察的新ProvinceID。
5. 要解释具体false，应转为有限源码/输入缺口：优先实际callee Q=`2C097F0`（24E2230邻接链直接调用）与helper=`24D4D20`（24D4ED0实际CALL24D4EFD），再区分关系链28BC250/2C09580/2C09780。它们需要单独获准精确body范围和来源计划；本包不读EXE、不发新SDK、不加重复predicate调用或branch hook。当前公开数据不足以从legalholder推断Psource。

当前最准确口播是：“这条2644→2637边的两项definition原值和县对象差异已通过，原生最终条件仍为false；尚未取得县来源物理扣兵正证据。” 不说“敌县必扣”、不把B100当实际损耗，也不说全县损耗0。

## 源引用

- `newcounty-condition24E2230-source-a01/SOURCE-CONTRACT.actual-a01.json` SHA `3e43b5d98b9e13c497c8437818c3fd24c028dd4a60f41814aae7f7d6ae8ab544`；420B body `d011c6bb38172950e99324f1fa7157d0083cbe5316587b7945ed5b168f80370c`。
- `county-actor-condition2C09DF0-source-a02/SOURCE-CONTRACT.actual-a02.json` SHA `7f0340e0228bb885cd4ccd70bae86cf6574762406e81709fa57e51ab4bfa5a21`；131B body `344dc31069a905f0615c45fd59967f35530a14f75e496cda079841c897a3652b`。
- `county-receiver24D4ED0-source-a03/SOURCE-CONTRACT.actual-a03.json`；192B body `e6b73ab9e779bc7d856d61731fc73366caf63f1ec5adbababa3580c357e67d38`。本包回执附完整合同pin。
- `county-relation2C09620-source-a03/SOURCE-CONTRACT.actual-a01.json` SHA `ca8f09e272b4774e24c9aaa5d084610453ac74baa1da77a92f705b3066d4d6d5`；191B body `701c63b6a5f7ed78ce75d6a591fcc4dc0ae2464267a05a23f5b5feb3a3cd8edb`。

实际七份完整child原值和机器/process-proof引用保留于[紧凑原值证据](acceptance/2026-10-16-r181-county-false/PREVIEWS.actual-a14.json)；不复制游戏raw/save，也不重跑旧矩阵或新增实机结果。
