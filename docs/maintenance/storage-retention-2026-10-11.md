# 2026-10-11 LYD 容量与到期复核

执行统一 [存储保留策略](../storage-retention-policy.md) 1.0.0。00:11 CST，Root 在既有卷独占锁内重新核验任务总线、进程、实际可用空间及原配额，创建独立预约 003；前一预约 002 已实际 CLOSED/0，没有并存的旧未用峰值预约。

| 项目 | bytes |
| --- | ---: |
| 上一保守已有使用量 | 131233343898 |
| R51 已观测新增保留逻辑量 | 838105040 |
| 本轮小源码与审计预计入 | 134217728 |
| 本轮保守已有使用量 | 132205666666 |
| 新峰值预约 | 4294967296 |
| 已有量加新峰值 | 136500633962 |
| 原配额 | 137438953472 |
| 计入后配额余量 | 938319510 |
| 准入时 C 盘可用 | 622757015552 |

本轮预算含 Source11 导出上限 192 MiB、native build 0、新缓存 seed 快照/复制 0。仅允许已有缓存与当前精确 key 一致时使用，否则冷启动；不放宽 key。存档输入与必要输出仍计入 4 GiB 总峰值。

预约实际截止为 `2026-10-10T22:11:10.391492Z`，原配额截止 `2026-10-12T05:19:51.814083Z` 不变。Source11 继承 Source10 的 `2026-10-17T08:45:50.800231Z` 复核时间；缓存/profile 原复核时间保持。这里记录有限保留，不将复制、访问、续跑或入库视为续期。

本轮对已有分类、复核集合的结论为 **NO_ELIGIBLE_CANDIDATE**。先前重复 payload 已退役，当前 v2 缓存、B3/D2a、Source09/O10 与未解代表失败仍有用途且未到原期限；没有新增删除，没有重复全树扫描，也没有将过去的删除量再次累计。此结论只覆盖已有已复核集合，不能外推全盘没有过期文件。

[原始准入与协调回执](../li-yu-dao/acceptance/2026-10-11-i4-source11-preflight/INDEX.actual.json) 已保留。当前预约仍开放；实际场次结束后须核验独立进程退出、keeper/CAS 及限定新增资产元数据，再将未来写入预约归零。释放 4 GiB 预约不是物理删除 4 GiB；实际保留量、全项目占用、历史峰值分别报告。

01:00 CST 追加实际闭账：R52 公共 readiness RED 保留；正常 GUI 行政退出取得实际 OS0/native0/原 host wait0，keeper 线程及 allocator 原等待0，最后 owned4551 已完成 CAS release、done/resources=[]。预约 003 于 00:59:18 实际 CLOSED，剩余未来写入预约 **0 B**；限定新增目录的保留逻辑量 **441327935 B**，闭账时可用 **622230110208 B**。[原闭账](../li-yu-dao/acceptance/2026-10-11-i4-natural-r52/reservation-closed.actual.json)与[限定元数据测量](../li-yu-dao/acceptance/2026-10-11-i4-natural-r52/reservation-measure.actual.json)仅覆盖新 CASE3/run/a14/Source11/O11 及指定小回执，不代表项目全量占用或历史峰值。后写的闭账与发布文件不在该次测量小计内；并行小源码仍由原 128 MiB 预计入覆盖。

缓存/profile 原截止、Source11/O11 继承复核上限与原配额 2026-10-12T05:19:51.814083Z 均未延长。有限新证据按原策略登记复核；本轮实际物理删除 **0 B**，不把 4 GiB 预约释放或过去的清理再次累计。自动预约/自动 GC 尚未实现。


## 2026-10-11 03:03:23 CST：R53 原生完成绑定拒绝、正常闭场与重复缓存回收

[实际闭场与清理记录](../li-yu-dao/2026-10-11-i4-r53-native-binding-refusal.md)及[最终可用性回执](../li-yu-dao/acceptance/2026-10-11-i4-natural-r53/cache-retirement-final.actual.json)：只删除已闭场R52原shadercache的3740个同字节重复文件，逻辑量146942031B，API分配量之和155353904B。每批≤1000，原件与保留seed均以实际持有句柄核SHA后删除，最终原manifest路径全部缺失且目标剩余文件0；未递归删除目录。旧mutable payload现在不可读，保留immutable seed及R53输入，不改写R52业务RED。两个preclaim新鲜租约拒绝原样保留，四个实际批次均成功。当前seed仍按原Oct17期限复核，大ledger最晚Nov9复核、精简回执180天复核，没有自动续期。

预约004已在原卷协调锁内按实际host/keeper等待和CAS释放闭账，未来写入预约剩余0。限定CASE4/R53/a15、新seed与指定小回执范围保留逻辑量1056211427B；额外未枚举小增量actual=null，保守上界32MiB，不冒充整个项目总占用。物理分配量与历史峰值未知，闭账时卷空闲621170180096B；并发空闲变化不全部归因于清理。Source11/O11/native/原campaign seed未重计；缓存Oct17及配额Oct12原期限未续。通用策略仍1.0.0，其他机器未运行的清理没有被标为已执行。

03:22 CST，[focused预约005](../li-yu-dao/acceptance/2026-10-11-i4-native-completion-diagnostics/storage-closed005.actual.json)实际闭账。峰值预约128MiB仅供3TU定向编译、EXE和回执，无source export或完整DLL复制；限定build和3个命令目录保留逻辑量17421872B、1792项metadata，未来预约0、物理清理0。基数沿用004保守占用+实际保留+32MiB未知小增量上界，没有抵扣缓存删除；原缓存和配额期限不续。新build按策略Oct24复核。编译及测试通过，Defender设置失败独立保留；自动预约/GC仍未实现。

## 2026-10-11 04:30 CST：Source12完整构建预约006闭账

公共Source12的712步编译/链接、必要离线检查和运行时绑定已进入终态；构建资源已实际释放。006在原卷协调范围内实际CLOSED，未来写入预约 **0 B**。限定新增保留逻辑量 **516918142 B**，闭账时卷空闲 **620593745920 B**。源8735项沿用原索引与文件大小，构建及指定小回执只测元数据；没有重新扫描整个项目或读取旧PE、SAVE正文。

未枚举小增量的实际量为null，上界32MiB；闭账后输出的实际量为null，上界1MiB，后续准入继续保守计入。物理分配量、项目总实际占用和历史峰值仍未知。释放3GiB峰值预约不等于释放3GiB磁盘空间；本包物理删除 **0 B**，不重复累计先前缓存清理。

精确闭账位于 `C:/workspace/ck3_lyd_runtime_20261004/common-storage-admission-20261011-006/CLOSED-RESERVATION.actual.json`（6960B / SHA-256 `3710e6570a23e4d0c37f0deee1a9891020f619402f51952cfc1b60335ac13f8c`）；元数据测量 `MEASURE.actual.json` 为6571B / `21a1b029ead2ff8ac32297ded8ce5e471f03137ac9085ec54e470844446ec0d3`。新source/metadata按7天、build按14天、raw按30天、compact准入按180天复核，以原准入时刻锚定；已消费的2天资格准备包解除pending保护，原到期不续。缓存Oct17及原配额 `2026-10-12T05:19:51.814083Z` 均不变。

下一公共Python后继只需192MiB独立新预约，不能沿用已关闭006；后续实机另计容量。全机自动预约/自动GC仍未实现，规则已入库，当前执行为人工协调。

本轮精简[闭账原件](../li-yu-dao/acceptance/2026-10-11-common-source12-native-runtime/storage-CLOSED-RESERVATION.original.json)与[测量原件](../li-yu-dao/acceptance/2026-10-11-common-source12-native-runtime/storage-MEASURE.original.json)已随[Source12实绩](../li-yu-dao/2026-10-11-common-source12-native-runtime.md)入库；完整大索引和构建输出继续外置限期保留。

## 04:54 CST：Python后继007闭账、独立实机008准入

007原192MiB预算内实际完成Source13冻结与公共绑定，限定新增保留 **159672946 B**，未来预约 **0 B**；原8MiB Git分项失败及3文件partial保留并复用，只计一次，总峰值与原期限不增。无重复native编译/复制或新cache seed。007闭账原件5549B / SHA-256 `4abebb315e92354795b2afb251478568bc525f44151d27097b1b31fa6e2f5bdc`；测量3344B / `b061f1607e6609abf2ffe4e0cf9a1416fb6c8362d64668d455c8e19ff718fe27`，位于 `C:/workspace/ck3_lyd_runtime_20261004/common-storage-admission-20261011-007/`。物理删除0B；未知小增量32MiB和闭账输出1MiB继续保守计入。

下一I4公共CASE5已单独获得008 **2GiB**峰值准入，保守已有量加峰值 **136815235244 B**，低于原配额137438953472B，余623718228B；实际卷空闲620397649920B。008只覆盖本场inputs/prepared/state、新分配的run/keeper/profile和必要输出，不授source/native重建或第二份immutable seed。原始存档与metadata只引用，不新建源seed副本。公共prepare/plan/preflight实际exit0，尚未allocate/launch。

008原件 `C:/workspace/ck3_lyd_runtime_20261004/i4-root-storage-admission-20261011-008/ADMISSION.actual.json` 为6834B / `f3f1a8a67dfea35f5dbcac1333e9bea05708f7ef63af484891adbadf24236940`。原配额Oct12、Source12/13与native/cache复核期限均不续。实机结束后再按实际进程/keeper/CAS及有限新资产闭账；没有将预留额度当作物理回收。


### 2026-10-11 R54 预约008实际闭账与有限清理复核

实际追加时间：2026-10-10T22:02:37.164748+00:00。008于2026-10-10T21:56:59.867165Z CLOSED，已知新增保留逻辑量775397888B，未来预留0，physical delete0；当时卷free619456413696B。原准入、CLOSURE-MEASURE29116B、ASSET-GROUPS88462B及其SHA均由[永久R54小包](../li-yu-dao/2026-10-11-i4-r54-pause-frame-refusal.md)回链，未重复复制大native/SAVE/PE/source。原配额2026-10-12T05:19:51.814083Z及缓存2026-10-17T13:06:29.278808Z不续，行政清理不授normal0或业务通过。

B内closed006/007小台账有限复核未取得新增大对象的替代/可重建、无当前引用及保护依据，因此无新增已证可回收候选；未全B扫描或读取旧大body。该结论不表示全B没有垃圾，亦不重复计入先前已删146942031B。外置复核INDEX978B SHA727a0882e56440ec3bd129be430b1898ce6ace9457e87275ffe19e737b3aa5cc，路径C:/workspace/ck3_lyd_runtime_20261004/storage-b-closed-ledger-review-20261011-001/INDEX.json。Source14后继只读准备继续，任何新重型写入另作串行准入。


### 06:21 CST：五份已闭场 SAVE 重复副本实际回收

ROOT 原命令实际 exit0：3 个保留源与 5 个目标共读 733357860 B，全部持有句柄 SHA/身份匹配后，精确删除 CASE3/4/5 的 restored_campaign 与 CASE4/5 的 xar_checkpoint。5 个旧副本现不可读；逻辑回收458348713 B、API分配量458362880 B。原0240基线与R53/R54两份独立实际初始SAVE均在执行时可读并保留，其他SAVE、shadercache与失败证据不动，原期限不续。卷free增加458354688 B不独占归因；旧R52缓存146942031 B不重计，下一预约只扣本次逻辑量一次。没有业务重验或新增通过。[小原件与可用性索引](../li-yu-dao/acceptance/2026-10-11-five-save-duplicates-reclaimed/README.md)。


06:36 CST追加：009在Source14/O14与materialize commandroot均不存在时实际取消，未来预约0，原192MiB释放属于预约释放而非磁盘回收。五副本458348713B仅在下一容量台账按同一事件扣一次。共享v2现在可按显式review收据核准Python-only runtime delta复用缓存，但没有实际复制/命中；原cacheTTL与quota截止不续。[合同与取消回执](../ck3-native-ai/2026-10-11-reviewed-python-cache-compatibility.md)。


### Source14 预约010闭账与CASE6预约011实际准入

真实追加时间：2026-10-10T23:08:46.175750+00:00。010实际CLOSED，限定known-retained161111254B、future0、physical delete0；原件6191B / SHA-256 `774c1af5a9bf6339985d444116c23143c710b5043f6ac0ff3c3fbd4eea1b0ab8` 位于 `C:/workspace/ck3_lyd_runtime_20261004/common-storage-admission-20261011-010/CLOSED-RESERVATION.actual.json`。释放192MiB预约不等于磁盘回收。限定索引及Git只计一次，没有全B或旧PE/SAVE正文重扫。

独立011实际准入2GiB，ADMISSION8775B / `afbbf05faad65cb09c5980dd9d059515d2b59184a5c229b1e4b38ff995280ebb` 位于 `C:/workspace/ck3_lyd_runtime_20261004/i4-root-storage-admission-20261011-011/ADMISSION.actual.json`。基数135510258348B +010实际161111254B +闭账1MiB +新小增量32MiB -五副本458348713B +本场2147483648B =137395107545B，低于原配额137438953472B，余43845927B。原008/009已含的小上界未再加；五副本claim1460B / `ca3b0324e41daaa27b1a0d6acc67dbb4ddaf77c000b5a8da4f5c2c41d989d5ea` 已实际唯一创建，不能再抵扣。准入卷free619678306304B不代表项目实际占用。

本轮CASE6 prepare/plan/preflight实际0，新v2 seed3740文件/146942067B及profile复制已纳入011。大prepared-case/2MB stdout保持外置，原[小准备证据](../li-yu-dao/2026-10-11-i4-case6-cache-preparation.md)入库，不声称cache engine命中或业务通过。011仍ACTIVE，实际run结束和keeper/CAS释放后再按限定新资产metadata闭账；未知全量与历史峰值继续null。原配额2026-10-12T05:19:51.814083Z、cache复核2026-10-17T13:06:29.278808Z不续，策略仍1.0.0，自动GC/自动预约尚未部署。


### R55 预约011实际闭账

真实追加时间：2026-10-10T23:48:42.406614+00:00。011已于2026-10-10T23:42:56.387502Z实际CLOSED_NO_FURTHER_WRITES_RESERVED。新保留逻辑量1004823890B，未来预约0，物理删除0；结束2GiB预约不等于释放2GiB硬盘。闭账回执7496B/SHA`698328e9cef1661e3f26fe4f2bf6540adb6907e54a8d445af3a198d991cc7ae3`、限定measurement16672B/SHA`2da9f1fc5ee169e73fe09ae611068e904a97c23206b66dad0d86dfff61950a02`在`C:/workspace/ck3_lyd_runtime_20261004/i4-root-storage-admission-20261011-011/`；原小闭账及RESULT已收入[R55永久小证据](../li-yu-dao/2026-10-11-r55-i4-natural-expiry-red.md)。free618612236288B仅是当次卷读数。

闭账002仅处理public-run-command receipts嵌套在actual_run下的真实重复测量，原public2/host1/normalfalse及所有范围/partition门槛保留。旧001未执行；没有全项目扫描或重读旧PE/SAVE/cache正文。五副本458348713B既有credit不再次扣减，旧R52 cache也不再计入。新source/runtime与下一场仍须独立准入；原配额Oct12、cache Oct17截止与通用策略1.0.0不续期，自动GC尚未部署。

### Source15 012闭账及新重复副本回收

2026-10-11 08:15 CST：012已实际CLOSED，新保留159991748B、未来预约0、物理删除0；[Source15小事实与闭账引用](../ck3-native-ai/acceptance/2026-10-11-common-source15-pause-ready-convergence/ADDENDUM.md)固定闭账6200B/SHA`c7251842d864f0b84199ad7578ba3434a0ac14957d05ce2a742ca4ff5e2fc0e3`。保守carry变为136412439535B；结束预约不作为物理回收。

[R54可变缓存实际回收](../li-yu-dao/acceptance/2026-10-11-r54-mutable-cache-reclaimed/README.md)：四批0，3740文件/146942067B logical，allocation API155353904B。新唯一event尚未claim。随后四SAVE实际0回收366678829B，两保留锚+四目标共550018294B均以持有句柄核SHA，原0240及R55独立初始SAVE不删。RUN55重复输入缓存四批0回收3740文件/146942067B；原不可变seed和CASE6可变缓存不删。[两类小型永久索引](../li-yu-dao/acceptance/2026-10-11-r55-duplicate-inputs-reclaimed/README.md)已实际采用，保存原五份小回执；executor/identity/ledger只回链外置原件，避免再复制审计正文。

三项新logical回收合计660562963B，尚未从任何新reservation重复扣减。卷free差额不全部归因于清理；旧458348713B SAVE与146942031B R52 credit不再累计。Source08—11当前仅有metadata plan0，恢复CAS、删除及其credit均未执行。下一实机维持完整2GiB预算，等待实际回收与独立准入，不扩大配额或延长Oct12/Oct17期限。大型identity/detail留外置30日，小回执180日复核，策略1.0.0不变。

### Source08–11 可恢复退役实际补记（实际原件已绑定）

保留 08:15 历史计划原文；本段只记录其后真实终态。Source08–11永久摘要 INDEX.actual.json 2670 B / SHA9990d26bd5b9a1c8ddbb1bb68258824a2e11275a53c21869a3ea0d1032a80cf1 绑定非 host 31624 文件/gross 563263222 B，以及恢复 CAS 141 项/10721390 B。恢复 CAS 为最小唯一旧字节集合，不能从 gross 删除量中推断 free 的排他归因。

保留四旧 host 原路径、全部旧 O metadata/Git objects、Cbr2/Cbr3、当前 Source13–15、全部 cache/SAVE；旧源 payload 需要已审恢复入口，原 frozen index/commit 历史保持。48 MiB 预约闭账=source08-11-recovery-admission-20261011-001/CLOSED-RESERVATION.actual.json 14061 B / SHAef58855e080f176151557f3946622a0bf8a94812b5f824dace4267a8d19ebf56；其未来0不代表物理删除。四清理事件 gross 合计1223826185 B 仅供 013 一次实际 claim（PENDING（未执行/claim=NULL）），不在本补记重复扣减。原到期/保护期限不自动续期。

精确0abb双CI成功原 REPORT2905 B/SHA9c9c067ea5b4511d90c6f0e8db0acb3aea2c54a05d058950bc2ff80ad0419b83、INDEX11806 B/SHA8e8c2c34c36fafc4a6b658f5b7001dca07a0fe3f98ba5159695827a984438aff 仅引用，不复制大 logs。

### LYD CASE7 容量准入及公共预检（08:46 CST 实际补记）

013 原容量命令实际 exit0，四份回收记录各创建一次 claim，gross 合计 1,223,826,185 B。独立恢复作业的 retained 加 closing bound 20,681,865 B 先计回，再扣四份新逻辑回收；usage=135,209,295,215 B，完整 2 GiB 峰值后为 137,356,778,863 B，距原 quota 余 82,174,609 B。实际 free=619,700,330,496 B，required=34,359,738,368 B。原截止、缓存/源码复核期限不续，未来预约不是物理删除。原 ADMISSION、四 claims、输入与命令原件见 [013 小型永久证据](../ck3-native-ai/acceptance/2026-10-11-i4-case7-admission/INDEX.actual.json).

公共 CASE7 prepare、plan、preflight 原命令均 exit0：50.388 s、0.423 s、29.392 s；预检 READY_FOR_EXISTING_REVIEWED_LAUNCH，blockers=[]。实际 prepared-case 1,338,827 B / SHA256 6e69150792193fd925b5d7af143951e5e447859f5c3c5f409ab70ed7c5291bde，仅引用外置原件，不将完整缓存索引搬上库。绑定 Source15/O15、原0240 SAVE和现有R54种子，未新增 native build/SDK重验/immutable seed；源码与实际启动、缓存命中、业务通过分别记录。尚未 allocate/启动，下一步是冻结干净主线、取得当次新鲜离线图并执行 I4 现有冷却自然到期；全一期仍75% / NOT_GREEN。

并行拓扑：旧 Source08–11 可恢复退役及容量入账完成；B4 handler 研究继续，实际发现 FH4 collided unwind 的 ScopeIndex 保全缺口，安装保持阻断；013 实机闭账源码在外置准备，终态字段保持待填。未新建分支；同步只用 fetch/rebase/普通 push。
