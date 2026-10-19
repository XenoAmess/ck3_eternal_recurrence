# 入站联盟邀请：下一只读观察叶已锁定原生入口

`machine_id: xenoamess-full-tower-eb9d2c1186`；实际UTC、文件SHA和源预算见[来源锁定记录](research-plans/g2-m2-inbound-alliance-12004-20261019/source-lock.json)。本包不改上一批联盟closure、冻结C5或策略。采用现有[research-plan](research-plans/g2-m2-inbound-alliance-12004-20261019/plan.json)流程，已生成[图与证据表](research-plans/g2-m2-inbound-alliance-12004-20261019/graph.md)，[检查](research-plans/g2-m2-inbound-alliance-12004-20261019/check.json)仅证明记录与文件一致，不授实机资格。

**当前`.4` recipient raw score getter与ABI已有完整保留来源，可直接进入一个窄只读叶施工；无需重新扫描AI或读取EXE。** 本次复用235B getter、678B实际caller及既有pending构造、上下文复制和数值生产器证据。新EXE读取、Game／RPC、构建与原生调用均为0。旧缓存未附机器身份的仍为`machine_id: unknown`；复用其代码证据不继承来源机器安装或运行资格。

[缓存字节核对](research-plans/g2-m2-inbound-alliance-12004-20261019/cached-byte-check.json)实际读取既有913B缓存，逐字节等于两份完整decoder指令拼接；新跟踪包合计小于24KiB。

## 唯一getter、实际caller和消费位置

| 层 | exact CK3 1.20.0.4来源结论 |
| --- | --- |
| 现成绑定 | `BindInteractionContext12004`严格匹配EXE SHA `98702F88…19DD518`；recipient getter=`307C440`，outer answer=`307BC60` |
| 实际调用 | 已保存的`307BD70` mode1分支在`307BEF4`唯一调用`307C440`，随后`307BEF9`读取返回指针指向的QWORD |
| ABI | `int64_t* (void* context, int64_t* out)`；Win64 RCX=context、RDX=out，RAX必须返回原out；raw为signed Q64，scale100000，不能截成int32 |
| root与分支 | 读取context DWORD `+2D8` actor与`+2DC` recipient。相等时直接写10000000；否则复制context`+8` scope，改root WORD为4、payload为完整recipient DWORD的零扩展值 |
| 评分来源 | `307C4A3`以definition`+1918`、原out及复制scope调用`3761680`；其继续到既有726B完整数值生产器`3761780` |
| 数值消费 | base在score block`+28`，modifier指针序列`+30`、signed count`+3C`。每个vtable`+30` occurrence更新同一个out，不能把回调地址当结果、把未知填0或任意相加 |

原pending内部已经持有完整interaction context。实际`2A32770`构造器将RCX设为pending`+18`后调用`3076B60`复制context；现有collector也从pending`+18`读definition、`+20`读原scope。因此**传给getter的是pending+18，不是pending对象起始地址，也不是scope+20**。borrowed context不能refresh、finalize、destroy；getter自身的临时scope复制／清理沿既有原生路径，由现成受管invoker执行，而非自行拼scope内存。

## 最小实现边界

下一叶只接现有owning-thread pending query：绑定原生revision、当前full pending ID、definition及双方完整角色，调用已adopt的`.4` getter一次，核返回原out，再读回同一pending／角色／帧。复用现有guarded调用通道；本包没有创建独立运行器、连接或新增动作。

当前`InitializeUnavailableTerms`把两项AI terms设为unavailable，native serializer与Python合同也限定此形状。不能只在一个collector里填raw就宣布接口可用。应同时增加明确的**counterfactual recipient raw**表示及对应serializer／contract；保留原生reply legality和auto-accept各自来源。

本次玩家31254是**human recipient**。即便未来实际getter返回raw，它也是“把玩家当AI评估”的反事实参考，不能叫opponent-would-accept、玩家实际final decision、联盟边际价值或战略最优值。outer`307BC60`的intermediary／recipient组合与raw分开；human responder的actual AI final应标为不适用，不能用raw正负伪造。下一叶不调用outer去替玩家做决定，也不移植1.19的地址。

## sender战事可复用，current／max军力需要两项窄来源

现有`.4` World binding已锁`contains-participant=2494B40`与完整war storage／participant ID规则。`ReadActiveWars12004`底层按传入角色筛选；下一叶可在同一次有界存储遍历中分别投影sender与player的战争、主参战方和相互冲突，保留partial／unavailable。不能把player战争列表当sender列表，不能为每个sender重复扫全军队。它解决“sender现在卷入哪些战争”，不证明未来参战意愿、到场时间或所有互惠义务。

原版联盟评分使用actor **current** 与recipient **max** military strength。已审旧1.19 military-preparation fixture保留两项canonical leaf：`current_military_strength`旧`2849550`／129B、`max_military_strength`旧`28494C0`／129B。本次有界资料未提供它们的`.4`唯一registration／callback锚点；旧地址与offset不迁移为`.4`事实，军队subtotal也不冒充这两个stock scalar。

给下一来源owner的**最小请求**已经冻结：先检索现有cache，只取上述两个canonical getter的exact`.4` registration／callback身份和各完整leaf body，单叶上限256B；已有缓存不再读EXE。若没有named`.4`锚点，先回报这两项locator缺口，不按image delta猜地址、不展开整棵AI。recipient raw与pending scope本身的新EXE需求为0，这个军力缺口不阻碍先实现诚实的counterfactual raw观察叶。

本包readiness为**source链已锁定、下一叶可实现，尚未编写／部署／实测该collector**。没有新增业务或G2信用；旧本批拒绝及其来源闭包保持原样。
