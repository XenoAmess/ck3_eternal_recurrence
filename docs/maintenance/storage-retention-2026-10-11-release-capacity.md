# 2026-10-11 本机发布验收容量回收

用户要求按仓库最新规则自主清理足够空间，不再将普通项目容量处理交回用户。本次按[通用存储策略](../storage-retention-policy.md) 1.0.0 执行；只处理当前获准机器，不代表其他机器已清理。机器路径、精确清单与资格依据留在外置工作包，仓库只保留[精简实际回执](storage-retention-2026-10-11-release-capacity.actual.json)。

## 实际结果

2026-10-11 09:52:05Z 完成17批、15,936个精确文件删除，实际 native AllocationSize 合计 **2,910,665,920 B**（约2.91GB），执行126.63秒。原进程由221实际wait确认exit0；09:52:38Z关闭预约也实际exit0，children0、unspent0。未删除目录、未递归删树、未动源码/Git/游戏/依赖/个人或其他任务文件。

回收包括：已消费闭场profile的15,116份生成着色器缓存；15份有保留原件的已证明重复存档/对象；被正式TED后继验收替代的2份旧R6 checkpoint；1份被有界分析替代的旧失败巨型JSON；14个已闭场QOL attempts中的230张旧截图、572份纯LIST stdout。最后两类保留全部小结、原失败判定、native/debug、keeper与命令sidecars；不以场次失败本身作为删除理由。

Source19控制中出现profile祖先路径，并不表示其每个shadercache是未来输入：逐项复核确认R77/R78已消费，未消费的RMTM/core、threshold及QOL输入为独立profiles。本次仅显式提前回收生成缓存，不删除这些祖先路径内的非缓存输入。R76/R68/R71/R78等各问题代表证据与原R14/R17 checkpoint、AUB验证原件、正式TED Save25继续保护，owner为/root，2026-10-18T09:20Z复核，不自动续期。

所有精确删除路径现已不可读取；摘要与哈希不是替代原件。已证明副本可从保留原件恢复，旧PNG、LIST、失败导出及R6历史字节不承诺恢复或同字节重建。原失败/UNKNOWN/RED不改写。

## 容量与后继

执行前全卷free为28,559,601,664 B，执行后31,474,786,304 B，闭场后再次读回31,473,754,112 B。全卷差额含系统并发变化，不全部归因于本次删除；回收量来自逐文件实际native身份/分配量与不可读回执。

默认2GiB场次要求30,071,062,528 B，读回已高出1,402,691,584 B。6GiB系统增长、6MiB其他预约及20GiB安全余量均未降低；本清理包16MiB上限由后续52准入自动保守计入一次，不从usage减去回收信用。真正实机仍需在新鲜容量/任务状态及同卷锁内完成原子准入，不把此快照当作已启动。

首次admit在入口变量重名处exit1，未建立预约、未删文件；保留原wait及冻结plan01。修正入口与未启动失败闭账分支后冻结plan02（gzip、43,228 B），独立代码审阅通过，再实际admit/execute/close。旧producer版本精确字节未另存，不能把现版本当作旧失败源码。

精确计划与压缩逐文件可用性ledger于2026-11-10复核归纳；精简回执于2027-04-09复核。不新增大库存或无限保留审计副本。

闭场后只读校验实际PASS：永久回执的全部精确pins与计数匹配，计划删除路径均不存在，保留证明及原件仍可读；清理回执包实际native allocation为580,720 B，低于16MiB预算。校验时free为31,471,820,800 B，默认容量门槛仍满足。

本轮只解除容量阻挡，业务验收仍QOL 2/6、RMTM 0/2，两项未发布；下一步优先原RMTM core默认2GiB场次，再推进QOL余项，不涉及361迁移。

## 2026-10-11 21:18 CST：R14/R79 生成缓存提前退役，下一场仍未准入

13:17:17Z 原精确删除器实际完成两场已闭场 profile 的 8 批删除：7,560 个文件，native AllocationSize 合计 **315,999,840 B**，48.967 秒，未删除目录。对象仅为 `rmtm-source12-core-01/state/profile/shadercache` 和 `qol-pam-delayed-boundary-20261011-01/state/profile/shadercache` 内冻结的 dx11 两个分支。两场原公开 session/native cleanup/lease 均已闭合；它们不属于原 prepared 不可变输入，新 RMTM prepare 明确未复制旧 state、未使用 shader cache seed。按用途提前退役，不以失败、目录名或年龄单独推断过期。非缓存 profile、存档、日志、原始报告、代表失败、正式源及当前 Source19 均未动，owner `/root`，2026-10-18 复核、不自动续期。历史缓存字节现已不可读取；保留的游戏、Source19 与 mod 输入只能重新编译新缓存，不保证恢复历史字节。

首次 admit 因 R79 prepared 的 profile 字段路径不同实际 exit1，发生在预约和删除前；01 源码、计划及失败原件保留。02 只修正这层字段选择，未替换删除循环或降低预算。随后 admit、execute、close 均由原 221 等待得实际 exit0，children0、unspent0；16MiB 清理包整额继续由原52计入一次，RMTM prepare 4MiB 计一次、既有 PAM prepare 不重复计费，不从 usage 扣除回收信用。

小型原件位于 `C:/workspace/ck3-upgrade-20261010/r14-r79-cache-retirement-20261011-01/ACTUAL-SUMMARY.json`（2,684B，SHA `3ee967b1bfe274f5ee804960ff61d68d254cc322a86dfffbd1d3a7e8ca3b2366`）；原 execute wait（990B，SHA `0c3721ab92f45be04982fdcf7233cb0a426934ada9db0f5cfe8bcf5c38b11946`）在同级 `r14-r79-cache-retirement-controls-20261011-01/r14r79-execute-01-process-exit.json`。标准237闭账为 `C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/post-r76-r14-r79-cache-retirement-01-reservation-237-closed.json`，实际 close wait（985B，SHA `86178749708ec3cc1ab6c1ad57e404b271c82a1113f41ae244865bf6cf1f2f73`）留在控制包。小型清理记录复核期限为2027-04-09，不代表自动GC。

累计两轮实际 native 回收 **3,226,665,760 B**，不把卷空闲变化全部归因于本次删除。卷上其他增长使 13:18Z 新 RMTM/core/a184 原52实际仍 **BLOCKED**：available 29,885,378,560B，required 30,071,062,528B，差185,683,968B。blocked 原件6,630B / SHA `588910864f6721f7b16877a150df84fcffe8fc80bdb5819afe4ef8e743198578`；admission命令exit0仅代表完成检查，不等于准入。此时尚未 allocate、启动观察或游戏。继续核查有替代证据的项目派生资产，不降低2GiB场次、6GiB系统增长、20GiB安全量及6MiB其他预约门槛；业务进度仍2/8，无发布完成声明。

## 2026-10-11 21:49 CST：旧只读监控中间/派生退役，RMTM/core a184 已准入

13:48:44Z 实际完成一个精确批次，删除29件旧只读监控中间报告副本/派生JSON，native AllocationSize 合计 **231,346,176 B**，1.601261秒、failures0、bodyhash0，未删除目录。范围仅 C05 的 `xqol-religion06-live-monitor-agent-01`（10件）、`xqol-defense07-live-monitor-agent-01`（7件）和 `xqol-payment-live-monitor-agent-01`（12件）。保留各组最后完整代表 raw：religion006、defense008、payment007，以及原source/debug/error/小结/控制记录；特别是 R8/R9 原 LIVE native report 路径已经不可读，不能把薄JSON或旧source绑定说成仍存的完整原件。用途结束的早期capture/派生投影按明确授权提前退役，不声称相同SHA去重、历史字节可恢复，也不改写 R8有限D0/whole-root缺口、R9 setup failure、R6 NO_ACTUAL_D1 的原判定。

原221的 admit/execute/close 均 actor `/root`、实际wait0；13:49:16Z标准237闭账 COMPLETE，原child0、unspent0。新包后继usage按16MiB整额计一次，RMTM262的4MiB计一次、既有PAM262不重复计费；不从usage扣回收信用，不降低2GiB场次、6GiB增长、20GiB安全或6MiB其他预约。代表原件 owner `/root`、2026-10-18复核，不自动续期；小闭账记录2027-04-09复核。

实际summary：`C:/workspace/ck3-upgrade-20261010/old-monitor-retirement-20261011-01/ACTUAL-SUMMARY.json`，1,317B，SHA `2eb399073ffb9b7c425a555dadebebddb40b47fb1e694f5976e7f742dcd11a39`。execute wait：控制包下 `monitor-execute-01-process-exit.json`，987B，SHA `87f8fecd6c00914e5b316429d1e8025b988e8833bef2e83a3e36e885e55edc70`。标准237闭账：`C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/post-r76-old-monitor-retirement-01-reservation-237-closed.json`，2,540B，SHA `5c81aef8b376bfdbb7987854a7aa61b13a215d4ddc090dfc7329ea80c8c2ee1e`。

执行前free 29,847,240,704B，执行后30,078,582,784B、闭账30,078,496,768B；全卷变化不全归因于删除。本文三轮实际native回收累计 **3,458,011,936 B**。此前 a184 BLOCKED 原件保留；随后root实际完成原52重新准入（42,749B，SHA `961e60ec435eebad561e7b3d3e2ca35dbe84e7aa69006586bac30c27581d0cb6`），RMTM core R0015/a184 已启动，业务结果仍待实际验收，不能把清理、准入或启动写成PASS/发布完成。

## 2026-10-12 追加：Source20 中间库、R16 缓存及过期过程输出实际退役

以下均已实际执行并按标准237闭账，不是候选量；admit/execute/close实际0，未删除目录，未以整卷free差额代替逐项native AllocationSize。外根前缀 `C10` 为 `C:/workspace/ck3-upgrade-20261010`，`coord` 为 `C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator`。

| 已结束用途的精确资产 | 实际删除 | 小摘要（路径、bytes、SHA-256） | 标准237 CLOSED（路径、bytes、SHA-256） |
| --- | --- | --- | --- |
| Source20 已完成链接的 `build-01/xar_ck3_12002_runtime.lib` | 1 file / **108,007,424B**；0.7598035s | `C10/source20-runtime-archive-retirement-20261011-01/ACTUAL-SUMMARY.json`；1428B；`a3b433382efdd834c5d4e85a968b4f12e48d018daba14094abed32f85d91d850` | `coord/post-r76-source20-runtime-archive-retirement-01-reservation-237-closed.json`；3717B；`dc3dd1f6f2b9174ebe38d60c88a125e2b93f169dbca3643ece2bcf6f2e00246f` |
| R0016/a185 已闭场 profile 的 shadercache | 3820 files / 4 batches / **160,604,976B**；22.4564087s | `C10/r16-cache-retirement-20261012-01/ACTUAL-SUMMARY.json`；1879B；`88db77a7ef7ee247633b48aeeb8461f18e632092f1ae7d2d8fc2fe5e5380ce57` | `coord/post-r76-r16-cache-retirement-01-reservation-237-closed.json`；2867B；`43f444351353e6567dfc99418103990bf5a951140299b2e3655a4a1294acdd79` |
| 已明确提前解除用途保护的旧 transport/poll streams | 53 files / **954,867,712B**；1 batch / 1.2016206s | `C10/obsolete-transport-retirement-20261012-01/ACTUAL-SUMMARY.json`；1361B；`aac2b7f4d6b0f1230f8020c91a2eb6b35931105d06b6091ed1534000f32b6b44` | `coord/post-r76-obsolete-transport-retirement-01-reservation-237-closed.json`；2883B；`64d16fefcc9a90aedc7d4fa5a9010b014bc1fd201e15eaa0d50b10f56e67899b` |
| 已完成行政用途的 pure LIST stdout | 900 files / **313,344,000B**；11.5201828s | `C10/obsolete-admin-list-retirement-20261012-01/ACTUAL-SUMMARY.json`；1371B；`3571a1b8f733f7276d573b672b12149d728e384719b5bdae0bfd3b3efb6d48a9` | `coord/post-r76-obsolete-admin-list-retirement-01-reservation-237-closed.json`；2390B；`ee0f61b89779cf45061cbf32c359fe94469c56cbe8cea6a1f149ce614e6118b1` |

Source20 只退役 `C10/source20-complete-timeline-native-build-01/build-01/xar_ck3_12002_runtime.lib`（logical108,004,896B）；保留349个父objects、精确LIB argv/RSP、source/index和冻结DLL，可以重新构建新archive，不声称恢复历史archive字节。R16仅退役其已闭场准备根 `C10/rmtm-core-source20-current-formal-publicprepare-20261011-01/state/profile` 内指定shadercache；不是R17当前profile，未授R16业务PASS。

53个旧过程流由QOL精确12 files/328,515,584B及C7精确41 files/626,352,128B组成；不含 `g2-player-claims-stock` R0001，也不涉及361。900份LIST stdout在2026-10-11T19:08:47.857Z实际退役；其对应CONTROL下实际221 wait `admin-execute-01-process-exit.json`，1005B/SHA `0487c4b71345729f01a6582e0baaa121183b54090d94d55055afecd82ab4796b`。以上执行bodyhash=0；被删除的旧transport及LIST stdout正文现已不可读取，不能由摘要恢复历史raw字节，也未制造同名替代。

原argv/result/stderr、keeper、native报告、关键typed/pools、debug/error、GUI、SAVE及source inputs继续按具体用途保护至 **2026-10-18复核**；尤其保留a184/R15原生异常及typed/wire关键代表，R20原RED及OS未知也不改写。保护不是无限续存，届时重新核对未解决问题及后续引用。

沿[此前四轮已闭账累计3,616,011,856B](storage-retention-2026-10-10.md)，本次四项新增1,536,824,112B，实际native回收累计 **5,152,835,968B**；不重复累计早先回收项。整卷free变化包含其他写入/释放，不能全额归因；每个16MiB reservation full-cap后继仅计一次，不产生usage负信用或新的启动授权。LIST闭账后实际free **29,321,334,784B**，距当时默认2GiB准入门槛仍差 **749,727,744B**，未据此准入下一场。

## 2026-10-12 追加：R17 业务进展与失败资源闭账分离

VALUE占位符九语言修复的实际输入commit为 `42e32cf310bb91bfcea272e08ce2f213ed7dbcb9`。12个相关测试、static、builder check及36文件formal各actual0；01父导入失败保留为FAILED_PARTIAL，不能把四个child0写成prepare成功。02 fresh publicprepare/plan实际0，之后用于R0017/a186；旧R16 GUI RED与正常OS0历史不被追认PASS。

R17实际A/B GUI均明确显示新近脱离旧朝 **−50**，C1–C5通过，Continue仅一次，真实死亡GUI已资格；D5切到37989，D6实际stock `realm_maintenance.2001` 的ROOT37989/prev34422/same title18371，D7原snapshot仍37989。但原执行时独立engine heir及hidden `rmtm.2001` fullTitle回调因果仍为GAP；stock事件不能冒充产品hidden回调。**2026-10-11T18:32:08.887Z是原normal Quit reserve截止，不是52预约到期。** run02/verify01实际2，verdict缺失；native GREEN仅证明清理完成，实际native shutdown CK3 exit1，原host wait未知、旧retained snapshot exit=null、observer child wait=None，normalOS0=false。详见[R17继承缺口专题](../reclaim-the-motherland-r17-succession-gap-2026-10-12.md)。

A186失败资源闭账现已实际完成：`coord/rmtm-core-a186-valuefix-default2gib-01-reservation-52-closed.json`，10828B/SHA `e9668e4639a332e51bd22f3a9d0187ec322a4533090c14764d3485e2d47105af`，状态CLOSED_STORAGE_RESERVATION_RELEASED；实际221 wait `C:/workspace/ck3-upgrade-20261006/resume-root-01/a186-failure-storage-close-02-process-exit.json`，931B/SHA `462d9617664f5ba036f5728e1027f70e939ae719f579025ebcb35ea36de5aea4`，exit0。keeper/allocator实际0，CAS8987 done/resources[]；这仅释放失败场资源，不授正常退出或业务PASS。

同次四根metadata占用 **630,610,040B**，闭账current project usage **39,296,503,096B**、free **29,010,063,360B**；第四个F控制根119,864B已计入本次占用，只计一次，后继不得再次加收其cap。旧receipt中budget charge文字保留其历史原貌，不改原件或追溯造信用。失败adapter02路径绑定actual1及后继成功闭账均保留。当前业务仍 **QOL2/6、RMTM0/2，总2/8=25%；release0/2**，存储闭账不是发布完成。

## 2026-10-12 追加：R17 已闭场 shadercache 实际退役，admin 仅完成公共准备检查

R17/a186失败资源52已实际关闭后，精确退役其准备根 `C10/rmtm-value-fix-fresh-publicprepare-20261012-02/state/profile` 的指定shadercache：**3820 files / 4 batches / 160,604,976B**，22.6299558s；admit/execute/close实际0，bodyhash0、无目录删除。旧shader字节现已不可读取；后续重新编译不保证相同历史字节。非cache原件、当前DLL及输入、R17独立heir/hidden回调缺口的关键native/typed/GUI/SAVE证据继续保护至2026-10-18复核，不改业务GAP或nativeOS1。

实际小摘要 `C10/r17-cache-retirement-20261012-01/ACTUAL-SUMMARY.json`，1879B/SHA `efaa24f68602c193ef44fe7cc23fdffdd9eefd8f2db55ed3de1af4414826d5e0`；对应CONTROL下221 wait `r17-cache-execute-01-process-exit.json`，987B/SHA `04a32cee8d16bce15c70b6a05e5081fc1a390a77fb5f4486cdb594b604e1c140`。标准237闭账 `coord/post-r76-r17-cache-retirement-01-reservation-237-closed.json`，2267B/SHA `ba9c01a992df99d2886270fc06af9377613d15af73e0742ac1ad371e9045ecd4`，actual0；原16MiB full-cap后继仅计一次，不从usage扣回收信用。

实际native回收累计 **5,313,440,944B**；此轮后实际free **29,472,485,376B**，距当时默认2GiB准入仍差 **598,577,152B**，未准入下一场。整卷free差额不全归因于本轮回收。

下一QOL `administrative_appointments` 的公共plan/preflight已各actual0、blockers=[]；preflight状态 `READY_FOR_EXISTING_REVIEWED_LAUNCH`，runtime_status=NOT_RUN、business_acceptance=NOT_ASSESSED，尚未allocate/run。小型实际wait位于 `C10/qol-next-admin-controls-20261012-01/`：`admin-public-plan-01-process-exit.json`970B/SHA `f89503ec796dcda31febbec13f581a456b2333c24491c0936c64399fe489d3d0`；`admin-public-preflight-01-process-exit.json`986B/SHA `375aae3be0d407044150b5d9a0e3ae4f3c126559ea19c11f9ad7335468e41fcc`。准备检查不授存储准入、GUI资格或业务PASS，业务仍2/8=25%、release0/2。

## 2026-10-12 追加：596项实际回收及A187/R80日志拒绝后的正常资源闭账

此前批准的596个精确旧派生文件已实际退役：admit/execute/close均0，释放native AllocationSize **656,019,456B**，8.9860608s，无目录删除、bodyhash0；累计实际回收 **5,969,460,400B**。小摘要 `C10/rmtm-r16-navigation-retirement-20261012-01/ACTUAL-SUMMARY.json`1770B/SHA `1859942e5ac6b798173d03736fe7f4e0d36a1f4d17d70214575090872c5a69c3`；execute221为981B/SHA `27cebf9d999e104c13a88651be87da1035c9322e531813460c205fe3aeac9562`。标准237实际CLOSED/COMPLETE、children0/unspent0，16MiB full-cap后继仅计一次。该阶段实际free30,263,693,312B，不把全卷差额全部归因于本轮删除。

A187原默认2GiB预约随后实际ADMITTED：required30,071,062,528B、当时free30,263,758,848B、headroom192,696,320B、usage39,346,834,744B；三个新增16MiB包各计一次，非回收负信用。原keeper READY并不等于allocator已terminal；以下为此后实际运行及闭场结果，保留此前准备阶段NOT_RUN的历史身份。

QOL `administrative_appointments` R0080/a187在D0 paused完成全部原任命业务观察：当场新鲜读回 `d_optimatoi` 对象1861、holder30599；AI37981 score81；player29912开关off时−945、on时−1000945、恢复off后−945，raw精确delta **−100000000000**。实际GetHeir GUI及Source20 character读回均绑定37981；没有通过死亡或转封制造结果。原root结果25150B/SHA `4826b7c15157b29b09e04e118b3f48cf33eade954b9efbebf3c3dc9c429670f3`保留。

但canonical fixture的 `events/zqagov_events.txt` 与 `common/on_action/zqagov_start.txt` 发出两项BOM warning，原classifier按原门槛严格拒绝；原error17670B/SHA `48734b6752e2c4e599294c4bf9352c6f1d0398132e624504bf2ef50f4ef2f09a`保留。run/verify实际2，verify为NOT_RUN/businessfalse，不能把已取得业务观察补成旧场GREEN。实际run wait在 `C10/qol-scene-resume-03/administrative_appointments--a187/run-01-process-exit.json`987B/SHA `3962ba73e481470e446f395b0300cff8d45964cef6d8480a517de3c1d5905b29`；verify wait同根 `verify-01-process-exit.json`996B/SHA `a3e2aad8ec6dc163cdd8e4ae7ad23614452831c25ad2f10bd20e8863afee4dee`。

本场实际正常GUI Quit、retained CK3 OS0、native GREEN；observer原parent实际15，redirect child wait=None仍未知，不能推为0。keeper/allocator实际0，CAS9037 done/resources[]。`C10/qol-scene-resume-03/administrative_appointments--a187/POST-RUN-CLOSE-01.json`39732B/SHA `076b6d1ca727556adacea8c58b246a584fea179b81e251d6df957e68109dbed1`绑定三项公共closure=true、normal_close_qualified=true、businessfalse。post-close-01旧checker pin拒绝原件保留；03仅纠正checker绑定到frozen `02a6244d` 的实际版本，未改变业务判定；post-close-02实际0，不追认失败尝试。

标准51 `storage-close-01`实际wait0，receipt1014B/SHA `2e534527394940d3bf85835b7aac87edb45e04e8b4f8e07ff997e27ae41ab6ca`。`coord/qol-admin-a187-source20-default2gib-01-reservation-52-closed.json`7901B/SHA `b1d969f952d3f2b95f16e3e281a1058e02e39a1749674003ec74fb8fd498baa9`于2026-10-11T20:43:32.221955Z实际CLOSED_STORAGE_RESERVATION_RELEASED：同次三个闭场根新增保守占用 **477,995,152B**、current project usage **39,824,829,896B**、free **28,852,498,432B**，释放原2GiB活动预约，unspent0/future credit=false。全根保守加计并未按删除量回扣usage，也不自动授下一场准入。

原native/typed/完整候选及GUI、BOM错误、正常退出和失败闭场尝试按具体用途保护至 **2026-10-18复核**，不改外置原件。下一计划仅补七个canonical fixture文件BOM及三项支持pins，再fresh publicprepare；**本记录不声明该修复或新prepare已经完成**，不放宽classifier。业务仍 **QOL2/6、RMTM0/2、合计2/8=25%；release0/2**。

随后完成最小编码修复：七个canonical脚本仅增加首部`EF BB BF`、三份case合同同步精确pins；删除新增三字节后，全部正文与原SHA一致，含stock observer的232个CRLF/237个LF。classifier/common/host/Source20与正式产品字节未改。定向回归仅实际运行一次，1 test/0.015s/OK/exit0；`C10/qol-fixture-encoding-controls-20261012-01/fixture-bom-unit-01-process-exit.json`984B/SHA `4dea4475db26c8dbf52d743f649932026fbc8d6545d9171dcce4a446f21b994e`，stderr103B/SHA `869abd0e2b84452f4b1d9e29207b48a28b92e272d1df9ca35a154860fce6d539`。控制包限64KiB，纳入原OTHER6MiB且下次保守usage全额计一次，无新profile或实机；新prepare及实机仍待执行，不追认R80。
