# 宗族化密教：2026-10-29 休假交接

> 本文保留10月29日闭场历史。用户10月30日已改为“立即发布，发布后继续测试”；**0.2.0已于10月30日发布**。当前状态以[恢复执行记录](2026-10-29-dynastic-esotericism-resume-progress.md)最新条目为准，下文“未发布”、Source97和旧容量期限不能用作当前状态。

观察基准：2026-10-29T14:14Z（北京时间22:14），`machine_id: desktop-3fevhd2-1c74096080`。用户最新指令：“你要去度假了。温和地收尾手上的工作，梳理交接文档到docs中。”本文件接续[10月26日交接](2026-10-26-dynastic-esotericism-vacation-handover.md)，以本文件与配套[机器快照](2026-10-29-dynastic-esotericism-vacation-snapshot.json)记录的实际状态为准。旧文档中的R0018、fe6049、未运行生产链及旧容量期限不能代表当前状态。未改写旧五个用户文件。

## 当前结论

- **0.2.0尚未完整验收、未发布。** 仍更新同一Workshop **3826991345**；公开0.1.0基线保持。不能把局部通过或正常退出当整轮业务通过。
- 最新冻结源码为 **97e6e45d6b2ec45a301cbfe2f3f1024c7ba65a20**，Main12干净；F15正式56文件、13个case及配套运行图已实际生成。当前不是旧52文件包。
- 最新实际场次 **R0033**：原六阶段中 **P1—P4签核，P5明确未完成并拒签，P6未到达**。最后实际日期53145384；从readiness53144328起新增44个完整游戏日。最后独立保留Save为 `r33-founder-cross`。
- R33实际正常资源闭场：**Game原handle0、host原wait0、public run2、keeper0、allocator0、native Job0、tree gone、cleanup true、SCREEN已释放**。`normal_close_qualified=true`、`business_pass=false`、`failure_lifecycle_completed=false`。public2与Root拒签保留，不能改为通过。
- 本轮暂停前的问题是Root将大量操作卡复核与等待串行放入固定9000秒窗口，留给完整出生、继承与赦免链的时间不足。已主动拒签并正常退出，未延长原hold。没有观察到本轮产品 `DESAF: TEST FAIL`；这不证明未执行部分通过。
- 收尾后台Steam探针 **14:11:10Z，offline / offline_mode=true**；无截图、抢焦点或切在线。下次启动必须重新探测。
- **不再发起UAC，禁止PowerShell。** 当前精确EXE登记沿用已有实际回执；不能把旧路径资格外推到新EXE。用户要求鼠标角落问题自行移开，无需再询问；游戏业务仍优先原生接口。
- 已停止新验收、发布、GC与容量采用；主任务总线改为waiting。C32只完成离线候选，**未采用**，不能据此启动新场。

## 路径与固定身份

以下路径仅属于上述machine_id，不能照搬到其他机器。这台机器是desktop机，不能套用xeno机器的D盘规则；继续使用已经资格化的本机根映射，不自动迁移或回退系统卷。

| 简称 | 实际位置 |
| --- | --- |
| Base | `C:/ck3-dynastic-esotericism-20261024` |
| Main12 | `Base/main12`；分支 `work/dynastic-heir-stock-input-20261025`；HEAD 97e6e45… |
| A20 | `Base/resume-product-a20` |
| Admin | `A20/core-a30-administration` |
| PROD31 | `A20/operations-core-a41/f14-a01/retest-f15-a01` |
| RT31 / HOST31 | `A20/runtime-a20/retest-f15-a01` / `A20/canonical-host-a20/retest-f15-a01` |
| LIVE33 | `RT31/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0033` |
| STATE33 | `A20/attempt-core-a30/retest-r33-a01/state` |
| PREP33 | `A20/prepared-core-a30/retest-r33-a01/prepared` |
| KEEP33 | `A20/keeper-core-a41/retest-r33-a01` |
| 用户工作区 | `D:/workspace/ck3_eternal_recurrence`；HEAD仍3c0b5ec8fb5d5ba12724dfdc1a26222b9b768e26 |
| 统一容量账本 | `D:/workspace/.codex-task-bus/e04-capacity-reservations.json` |

Main12与RT31均不得热改。D树五个原脏/未跟踪文件保持原字节，本次只新增本交接、快照及通知离线知识文件，没有commit、push、切分支或整合master。接手者不要将旧unpushed patch直接套回当前源。

运行绑定：CK3 **1.20.0.4 / build25734779**，EXE `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101040248B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。R33 PID34980，出生FILETIME规范字符串 `134377483362782153`，现已退出。
Native DLL `Base/native-repair-r27-a01/build/xar_ck3_bridge.dll`，16629760B，SHA `771ab21eb1a68e63d1fe1268a98d5da593811988daa42d67848ce577431ff647`。Native tree `41d4bd5d597cac291e0f5b8c2778fe1dc2e9b88f`；SDK tree `8fddf06d43bb4d23d20f89b94cc0e8312959d5ca`。机器快照保存当前小型Pin索引。
Java继续使用Java+Maven+Quarkus；默认mvn3.10.0已满足最低版本。安装home目录名仍含3.9.16只是本机事实，不把绝对路径写成构建规范。

## R33实际业务证据

所有证明在LIVE33/operator-evidence及Admin，原输入、原退出码、失败结果和UNKNOWN不得重写或重放。R33已结束，不能接着向其发动作，也不能把R32部分结果拼入新的完整Core。

| 部分 | 本轮实际范围 |
| --- | --- |
| P1 | 原生取消前后完整AST/CoA/数量不变；实际创建一次，纯产品D0先Save后capture；D1、D2各全量Native+独立Save；原Dynasty174/House174复用，未新造宗族/家族/首领。正式56 mounted profile逐字节一致，不声称全VFS逐文件加载trace |
| P2 | H0/H1/H2真实逐日队列与采用；多成员和单人成立新宗族分支；全部当前信徒独立Save核对；其他合法家族/纹章保留。P2原12个独立Java观察均0，Root已审原事实并签核 |
| P3 | 同Faith离开主Rite，目标保留House174，产品背离状态、−100好感及三种原版犯罪理由验证；监禁控制对象与execute/banish只读合法性核验，没有实际执行刑罚 |
| P4 | 跨Faith进入Rite6/Faith14，来源仍主Rite152；好感modifier完整AST与P3相同，没有刷新；外人无产品污染。悔改输入只提交一次，控制器进入P5 |
| P5部分 | 独立悔改Save确认产品背离/trait306/三组产品好感消失；真实生成角色、合法cadet和儿童归属修正；第二礼仪宗族绑定；创始人死亡后的新首领与加入者；双向交叉背离来源及六组好感隔离 |
| 未完成 | 本轮跨礼仪迁移、独立原版罪行与悔改保留、timer61/founder31；真正自然出生及精确B+24；成熟原继承人/原主头衔自然继承；旧首领None与新首领Dynastic原生编辑；实际普通赦免及精确+31；最终cold anchor；原P5/P6完整断言 |

重要动态ID，**只供R33证据阅读，未来必须重新取值**：

- Root31254；主Rite152 / Dynasty174 / House174；原主头衔2230。
- T65845、peer65846、child65847、outsider65848、prison65849、father65850、mother65851、oldDesc65852。外人实际Faith13/Rite0/H12759，不能复用R32的Faith14或死者状态。
- H2多成员头A65866/B65867→Rite153/D12158/H12762；单人C65868→Rite154/D12159/H12763。中间NPC65870仍在世，不能误认最终首领。
- generated65968，实际出生1040.6.28，为成人生成对象，**不计自然出生**；合法cadet peer65846/H12772，child65847被修回House174。
- 第二Rite155 / D12167 / H12773；创始人33946（不是R32的34973），observer65972、target65973。
- FounderCross Save实际dead_data：33946死于1066.10.28，reason=death_natural_causes；新D/H首领均41497且在世；新加入者66409。原第二Rite/D/H互相绑定保持；两个目标各只受对应来源礼仪的好感惩罚。

日期锚点：B0=53144352；H0=53144424、H1=53144448、H2=53144472；P3 same/prison=53144520；P4 cross=53144544；repent/G=53144568；generated=53144592；第二礼仪stock首次实际S=53144616；cadet G+31=53145312；second-bound S+31=53145360；founder/cross=53145384。F为实际输入日53145360，不猜固定偏移。

最后完整独立观察操作 `Admin/R33-P5-FOUNDER-CROSS-INDEPENDENT-SAVE-READ-a01.original-wait.actual.json`：1215B / `13bea4f16b937b575a28c7bbb6aaeb1a957c87592e177873d08f9ea174d3d5ac`，原0。
最后Save `LIVE33/operator-evidence/retained-saves/r33-founder-cross.ck3`：69689628B / `b4a0503bd592668980fd3b1ea58cfe5baf2f178f8a1cd2d5674e3079dec80eb7`；SDK pin与custody同目录。NTFS压缩后的分配量与逻辑长度不同，不能用69MB逻辑大小冒称物理占用。

## 收尾原件与已纠正的操作失误

权威小闭场：`Admin/R33-PARTIAL-BUSINESS-RESOURCE-CLOSURE-a01.actual.json`，**5090B / 5080764cb1d244e4dd4f3651ed138eef00ae420c02543eca51098db93e7d8469**。含原Native报告、normal-close、host、public、allocator、keeper及SCREEN证明Pin。
SCREEN任务 `ck3-common-12004-20261023-a53`；实际CAS9790→9791，state=done/resources=[]。Root任务 `ck3-des-resume-20261026` 为waiting，无资源占用。

P4签核后，Root私有等待器误等旧P5文件名；P4实际签核和悔改输入已经生效，真正P5是 `actual-repentance-disable-and-reenable-ui`。已凭精确PID/出生/argv终止**仅私有等待器**，原exit15保留；没有重发悔改、没有终止Game/host/keeper。纠正回执：
`Admin/R33-P4-PRIVATE-POSTSIGN-WAITER-CORRECTION-a01.actual.json`，1513B / `e19fec7ba3b2126d50287fa5b3939824943721bbc0e89076b234e685e5aca73b`。不能把该私有等待器原失败改写成0。

两次容量Source资格曾拒绝sharedindex身份/分配变化；失败均在相应Save前，静置重验后通过。只证明两次当前扫描不一致，未查明具体字段/写者，不能归因为产品、Defender或已证实mtime。

## 已退役优化与下一轮执行方式

R32仅推进266日、4/6，因Root的host-after复用遗漏同暂停日异步通知，SDK正确拒绝旧revision。不要再执行 `finite-native-days-host-after-candidate-a01.txt` 或旧R32 donor内的此路由。
保留R32整条Native wire和两条精确fault slice容器；故障不归因GC或产品。共享真实fresh-before CaseClient路由的回归已实际正常14项、-O14项及完整严格mypy均0，夹具环境也已同步：
`Admin/r32-public-fresh-day-regression-a01/ACTUAL-a02.json`，1590B / `49d885813beae9f4d0cf0db5522003defc575d38b90f341073d8508a1cacca71`。

最终 `FINAL-TEST-ONLY-a01.patch`、`FINAL-PERSISTENCE-a01.actual.json` **仍未应用Main12**，须在冻结全部实机结束后落持久测试并完整执行原CI step三命令。两行operator_sequence的实际callback日期措辞更正也待最终源维护，不热改RT31。

下一完整Core要先把已验证操作链准备充分，再开9000秒hold；暂停窗口中不能再次逐张设计所有操作卡。沿 `Admin/R33-existing-public-days-prefix-a01.operation.txt` 的现有CaseClient，每次真正 fresh-before、每次严格1日、全局400日cap、单一writer和UNKNOWN不重放。该Root helper的1380秒额外规划余量不等于原case的180秒Quit reserve；不要为赶进度改冻结SDK/hold/原业务预算。

共享Save合同：每次selected request同一kind和path都唯一；不能放多个ACTOR table。按living、dead_unprunable、characters.dead_prunable分别独立请求并只收FULL_RECORD，缺失不等于死亡。Root/角色变量均取当次Saved真实refs，严禁复制R32旧ID。F15共享Save JAR SHA `c9ec777f59b9406b4cd87dca9646851b1689c7c5a2da2921c11de3fa65c15545`；代码证明 `Admin/retained-save-operator-f13-a01/CODE-PROOF-F15-a01.actual.json` SHA `d1451149ffcb9820790f77f4271597955ce5601c810ddb98510d8c1f7804cb9d`。
已修正静态操作片段在 `Admin/r33-p5-early-preparation-a01/SCHEMA-ERRATUM-a02.actual.json`，旧片段标STATIC_SCHEMA_INCOMPATIBLE，不能复跑。尾链清单在 `Admin/r33-tail-preparation-a01/CHECKLIST.actual.json`，33466B；它是操作准备，不是尾链已验。

原顺序不可缩减：自然on_birth_child的B及精确B+24各Native+Save先验；真正primary heir准备只在全部前置标记后才合法，不能先强制继承并与怀孕重叠。旧首领Native None完成后独立Save，死亡日允许actual actor change，由原头衔自然继承；新首领再Native Dynastic；普通赦免必须合法预览→一次initiate→原窗口/后态→精确+31不刷新；最终cold anchor后才P5/P6原全部断言。

## 剩余13-case矩阵准备状态

Core尚未完整通过，Core cold无合格最终输入。另6个不依赖Save的case已走公共plan+prepare，各原0，**没有对应preflight、allocate或Game业务资格**：

`empire_heads_procreation`、`empire_heads_vivhite`、`initial_reform`、`sect_presets`、`native_binding_transfer`、`pre_product_seed`。

实际prepared：`A20/prepared-core-a30/post-r33-<case>-a01/prepared/prepared-case.json`；state与keeper分别在现有attempt-core-a30、keeper-core-a41同名子目录。CLI与依赖卡：
`Admin/r33-remaining-cases-preparation-a01/FINAL-INDEX-a01.actual.json` 6744B / `f860aaa10793e233341fbd38db730ea89dfebd92fad88a27c99b7c00ea6f8d59`；
`STATIC-SIX-ACTUAL-a01.actual.json` 6807B / `a3212a64092608d03231b4e7b4af4530d0814993e3bf9b846e8d277287d9800c`；
`CASE-CLI-DEPENDENCIES-a01.actual.json` 28599B / `c027a029578f2d38624a3e7a2a53afe610d657dc5a9df96cd580c8924b886466`。

尚未prepare的6个Save依赖case：core cold、old-save bootstrap、两Empire cold、两Empire restore。bootstrap需真实pre_product_seed；Empire cold需实际继承人最终Save；restore必须各自付费取得头衔的S0→普通stock UI生成并资格化的S1，不能用继承后的Save冒充。

原完整窗口：Core10800+9000+120=19920秒；五long case各5400+3600+120=9120；bootstrap3600+1800+120=5520；六short各3600+900+120=4620。旧CLI卡顶层说明中“4520”属算术笔误，行内与原catalog为4620，实际B01按catalog计算。新窗口必须逐case严格准入，不能以总时长估算保证全部完成。

## 容量、GC及C32未采用边界

统一策略1.0.0，按本机原根映射、实际allocation、所有并发预留、OS未知历史上界与shrink hold计算；不要取消安全预留或把负增长重发信用。

当前仍为 **C31F15T18**：`Admin/C31F15T18.json`，20268B / `063722a0c859bac52a6e733e7338ed68433499a170e40d6bb96aaded6862cf1c`；**硬截止2026-10-29T18:00Z**。Core8GiB、Native512MiB、PNG256MiB、Source16MiB、Git32MiB及原其他边界不变。账本最后rev1332/storage220，7860B / `9ef38e1ecb54f5e00cac875c2c305d0ba83541e83b733407f2276428f0e3f59a`。本次收尾没有容量CAS或新authority。

闭场完整双卷collector原0，观察14:13:21Z：
`Admin/VACATION-20261029-CLOSING-CAPACITY-CHECK-a01.fresh.json`，9376B / `3d28aba89d5378bd02cb5dba38ac304501b2425f9e9cc5d47247c10ca2d4d85b`。
仅核1MiB小交接峰值；Game_execution_admitted=false。scope charged=7,269,405,408B，remaining=1,320,529,184B；相对新完整Core caller2,133,425,404B仍缺 **812,896,220B**，后续小文档写入未含。C物理裕量1,197,159,136B、D仅31,068,160B；这是公式扣预留后的裕量，不是磁盘free。新重型写入须重新完整准入，不用历史fresh。

GC9已实际回收26份被替代的R29/30/31中间Save，731,664,384分配字节，保留小证据、SDK/custody/AST；原件已不可读，不制造同名替代。两次CAS已完成，不能再次累计。精确计划 `Admin/G9A.json` 19612B / `0c09547f2cf3776bd4b8a0e6253f64c3f293d5906c12f63ee12a354833d10a57`。没有GC10。本轮最后用途复核仅定位≤11个旧raw叶方向，SHA/allocation/当前用途闭环未完成，**没有可回收量或删除资格**。保留R32关键fault/UNKNOWN、当前冷输入及全部R33必要Save。按统一期限复核，不默认永久保留；接手复核点2026-10-30T06Z不延长任何写入authority，到期也不自动删除。

C32候选Own：`Admin/case-window-c31-time-successor-c32-a01`，只为未来尚未启动case拟延至2026-10-30T06Z，旧R33 hold不延长：
- `C31TimeSuccessor20261029A01.java` 43769B / `d8fa3873816b82eadb3f613eaccff522850b890117f7e349edc84e6bb228bb11`。
- `QUALIFICATION-a01.actual.json` 123228B / `27cafb0ba234948237212fdff4fb3efca0ea21eef8d6ba5ae91a7e1733474782`。
- `CLASSES-FINAL-a01.actual.json` 114288B / `8df8b85691278af91ac2ef3ab3e2a6c37bc6c9b8f932330026b35feba463de4d`。
- `MECHANICAL-PROOF-a01.json` 1939B / `d1f68e8a4d652f7085e2e083392d5b5796f03559e7734a786c04a04dc0c8d376`，含最终三源full diff Pin。

严格编译/语法/四模式各26项数学+27项合同/独立合成producer→consumer原0。独立审查没有新增阻断，但**真实R33闭场尚未由候选读回；inputs/draft/propose/adopt、collector、CAS、目标C32卡均未执行/创建**。Own保守790528B+子预留1179648B=1970176B≤2MiB，只余126976B，不能再任意加日志或复制依赖。

未来需读最终Q/源码，先真实Inputs与R33 closure消费，再Root审完整typed Review和新有限OS窗口理由、全双卷fresh0、完整next，才允许adopt；不能改卡日期或机械签名。若恢复时已过拟06Z，必须重新设计有限期限，不回填审批时间。旧B01消费者精确绑定C31，**不因C32测试0自动接受C32**；新消费者仍PENDING，未物化。Core19920窗口与各case原预算继续保留，不能以普通--check代case资格。

## 宣传、发布及最终集成仍待办

PROD31/formal为当前Source97正式56文件，manifest9954B / `8474a21ccfa0c0f3c1594919e3fd4241c59d3e1f8a5a3f8b4eecff75c7d2a214`。旧f13 HEAD差异已纠正，不因此重建整套图。descriptor无内层remote_file_id。

用户要求实机截图放商店。已有8张旧raw共14,014,518B继续保留；**R33没有新增PNG**。原总上限16张/48MiB，含拒绝/旧图，不另开额度。后续计划自然继承、繁育/白绮正常取得和交接等5类；每张必须当次实际业务+独立Save、实际Native UI subject/visible、SCREEN/PID+出生绑定、新鲜容量及看过实际PNG质量，不以AI图或fixture ACK冒充实拍。
Root已审的单帧候选在 `Admin/promo-r33-rebind-a01`，截图仍未执行；R33身份/scene admission现已过期且进程结束，下一场必须重新绑定，不能直接执行旧输入。

发布准备在 `Admin/r33-publish-preparation-a01`，只是事实/动作卡。0.2描述候选仍缺完整两预置与Empire说明，未形成最终发布描述；旧说明不完整，不直接上传。
完整验收后再正式构建/tag→更新同一3826991345→公开标题/描述/Notes/标签/media全文回读→真实Steam下载cache逐文件exact56→CK3实际mounted/loaded及正常退出；cache只验证加载，不重复业务。必要联网结束立即恢复offline；online启动前仍检查跨机占用。
永久0.2 changelog、最终持久测试、线性master整合/普通push与exact官方CI均未完成，不报告源码已有即交付。

最终用户需求继续保留：两教派独立Faith+同名main Rite、指定三信条/普通及特殊教义、帝国级领袖头衔及对应纹章、正常取得/恢复。**政府转换/绑定已被用户取消，不得恢复**；不为迎合原版选择器擅改用户教义。

## 通知离线知识与恢复起点

R33在53144736遇到普通婚姻通知16777244：actor34232→Root31254，secondary33234/38924；实际auto_accept=false，原生reject允许，特殊婚姻条款仍opaque。先记录Root决策，再原生一次accept=false，原实例消失、日期不变后继续。原版婚姻GUI与普通通知GUI均为左拒绝/右接受。已离线读原定义与on_decline；来源SHA、范围及真实后态归入[来源绑定知识](../ck3-native-ai/evidence/2026-10-29-arrange-marriage-notification-r33.json)。这不是已实现婚姻策略或未知条款自动求值，也未热改冻结registry。
faith_creation.1021的12-scope变体沿既有R19来源分析执行用户规定第一显示项；不扩写自动7/8-scope registry资格。

恢复时先：
1. 阅读本交接和快照，核机器/根映射、现时Source97与原证据可读性；R33已闭，不能重放任何已提交动作。
2. 解决有效期限和实际容量缺口，再采用正确的未来case消费者；禁止UAC、PowerShell、冻结图热改。
3. 新Core完整操作链预备到可直接执行，再公共plan/prepare/preflight/allocate/run/verify；前置原非0/timeout立即停依赖动作。保存预算、身份、原生后态、独立Save与完整墙钟。
4. 完成全部13个case及实拍素材后，落实同物品发布、公开回读、cache加载、master与exact CI。休假收尾期间不继续这些动作。

