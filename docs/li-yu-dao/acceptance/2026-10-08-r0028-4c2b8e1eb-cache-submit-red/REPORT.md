# R0028：原0240基线通过，新增继承缓存查询提交失败

2026-10-08 12:39（Asia/Shanghai）。实际运行来源为 `4c2b8e1eb496ae9167dd23b88fbff3ec9a84b60c`，clean export `C:/lr28s1`；CK3 1.20.0.4/build25734779，Steam始终离线。外置永久材料根目录 `BASE=C:/workspace/ck3_lyd_runtime_20261004`。本次不授完整缓存读取、正式提交、B4/B5、有效newT、C3或I4通过信用。

原0240冷载后，同一official MCP Client核对29项工具，仅附加一次。原进程PID18372/create_time1791431112.077351、原FILETIME134359047120773513、native session `4a85c5060cef448bac18496cb537db54`、connection_generation1、actor31254/date53144712始终绑定。SAVE004及其after-frame的G2/G3正常；保存副本SHA `04c3d6086a1a6553b45230699c446821648fc4fdef1d46d3532ba79aaf31097d`。

SDK007实际返回 `isError=true`、`structuredContent=null`：`cached-succession native error: actor_cached_succession_mailbox_submit_unavailable`。没有native receipt，也没有候选数组。原SDK结果497字节，SHA `cfc54754d78fbe30bd288fa62941ea7a8399d33ba234f378cf20e4bbab6a229d`，路径 `BASE/live-attempt-028/persistent-client-001/0007-r28-007-baseline-actor-cache.sdk-result.json`。失败未重试；缓存与存档比较未执行。

有限源码定位发现新executor只登记在1.20.0.3分支，实际1.20.0.4的 `InstallCoreFrame12004` 没有登记。mailbox的allowed/copy/submit名单已有该查询；实际原生枚举结果未被记录，不能把源码推导写成实机枚举证据。最小补丁仅在既有assembly compile gate内新增两行executor登记，不改reader、29项schema、12项开关、业务文件或87项保护。补丁源包 `BASE/r28-actor-cache-submit-blocker-sourceonly-20261008-001/INDEX.json` SHA `8093f8ff80e3dd2022c1224cb49643f318d8f976ae67a66345e0aa6820a1309c`；修正后bridge SHA `4225750a18c486b108ca459723983ba652e429f697ac0ce207cd76691c7c4efa`。新DLL编译及实际查询另由后继运行验收，本次不给修复通过信用。

baseline author第一次在读取正文前失败，`save_body_reads=0`：源投影把已审阅inverse首行docstring的R27改为R28，破坏原强SHA绑定。CP003恢复原inverse全部字节 `e8e4c79d6328b4ba5d9641968d1605e93ebc98d0637f2d439101142efa0bad13`，不刷新或放松consumer/policy/9键AST。原失败001、CP002和CAP004保留；恢复002沿用原SAVE副本、原G2/G3，仅改新输出目录。实际正文读取唯一1次，author RESULT为 `ACTUAL_COMPACT_NATIVE_SAVED_OBSERVATIONS_JOINED`，87项保护全部TRUE；control SHA `ea88f89bb685d9dc07dece39d4d35d4a4e9fe45d213ab7ee8ad1391fe4e85ed5`。没有第二copy、SAVE或正文读取。

退出通过原生正常流程：SDK009、011、013分别一次消费prepare/continue/confirm，SDK014只读原先保留的native HANDLE，确认 `process_exit_observed_zero`、`typed_normal_exit_observed=true`、exit0。SDK014原件12813字节，SHA `5cac5d3f4ed4cc086419ce370522422ea6d1246d98cd0b2622435884b8ea2686`。autosave_verified仍FALSE，外置被动HANDLE不替代native typed信用；其原有效第三holder执行、Client和keeper原执行也均0。此前两个holder精确时间比较失败已闭合并永久保留，不声称历史总共只OpenProcess一次。

keeper停止后使用实际FINAL3871做CAS3872释放，任务done/resources[]。04:36:38Z后置清场：processes[]、errors[]，PID6592/18372均不存在，四个精确受管marker为空；随后bus screen_owners[]。最终新鲜1920×1080原图由ROOT直接审阅，Steam底部“离线模式”、桌面12:33/date2026/10/8；窗口80→100→80、像素边缘变化。图SHA `8229488e6b2691de8f6549234348a4c8429ac649c4bb533085881436224180d8`，freshness SHA `225e1884a277e3924b0e8fb8946babf740d7bdfc3aaa155900fd6f824ed68dbe`。无强退、重连、再注入或Steam模式切换。

typed closure check/create随后均由ROOT实际执行0，最终 `BASE/r28-root-actual-typed-closed-boundary-20261008-001/PREVIOUS-BOUNDARY.actual.json` 3089字节，SHA `f81bced6100fb70f3ab21bb379d0e017d778fb37da2372190620260a3e8bffdb`。原pure contract、SDK/native/text、保留HANDLE、原执行0、真实CAS与清场均严格核验；业务FALSE和autosaveFALSE保持。finaloffline审阅实际发生于原执行和keeper FINAL之后、同一保留lease的CAS之前，没有伪造释放之后的截图时序。

本次native编译与六项focused实际通过，但原build外层因Defender设置失败返回1。既有SYSTEM broker在本机未安装；后续一次精确7个EXE的管理员COM请求仍失败，实际before/after三项数组及missing7保留。不把编译通过写成环境门禁全通过，也不声称新增EXE已永久排除。

已逐字节入库的伴随证据见[实际import记录](source-evidence/ROOT-IMPORT.actual.json)：[精确4c官方CI](source-evidence/ci/REPORT.md)、[本机broker缺失](source-evidence/defender-broker/REPORT.md)、[一次管理员COM真实失败](source-evidence/defender-com/REPORT.md)。各包原INDEX与原件ZIP永久保留；CI的Official Runner/Linear成功，Li Yu未触发。Official完整job log读取仍NULL，原实际超时/403记录保留，不能称全量日志已取得。

完整本轮[258原件归档](../2026-10-08-r0028-4c2b8e1eb-cache-mailbox-red-typed-closed/INDEX.json)由ROOT一次CREATE及逐字节import实际0入库，ZIP SHA `82223f23eb1ab07a7dd6ff1dc85fb9ac41cae7a53aaa64b5ebbc1cd882ebc2d9`。14个存档、二进制、图像及既有ZIP引用只保存metadata，原件永久保留在外置路径；没有再次读取存档正文或二进制。归档覆盖失败与修正、原SDK/native、typed闭合和最终离线，不授业务通过。
