# R0047：双启动标记对照

R46 的首次 campaign 查询在进入执行器前取消，owner pump 停滞原因仍 UNKNOWN。本轮只验证已采用的启动顺序候选：本场完整 history-loaded completion 与 In Game 两行均出现后才注入，先后不限；原生双 owner 帧、单次注入、900 秒绝对期限及业务输入保持。准备或单测通过不等于实机修复。

## 新预算与实际 Source08

R46 的 4 GiB 预留已按实际闭场核销，剩余预留为0；已知保留逻辑量924,798,428 B，历史峰值和精确物理占用未测。R47 于06:28:12 UTC在原卷锁下登记新的4 GiB峰值预留。保守已用120,604,915,355 B，加本场峰值124,899,882,651 B，小于既有128 GiB限额；现场空闲626,470,379,520 B。配额例外仍到2026-10-12T05:19:51.814083Z，不因续跑延期。

- [实际准入](C:/workspace/ck3_lyd_runtime_20261004/r47-root-storage-admission-20261010-001/ADMISSION.actual.json)：4,775 B / SHA-256 `6276902ee2150dd757a774f085c49d4d68d6cf880e095cefe12cbdb5db4f8db4`。
- [原预算核销](C:/workspace/ck3_lyd_runtime_20261004/r46-root-storage-admission-20261010-001/CLOSED-RESERVATION.actual.json)：3,042 B / `2166ecf90af0736dacfde648de96000106ecb368d01918fbff0e0adc3dfcf322`。

Source08实际于06:29:24至06:29:37 UTC单次生产，12.965秒、exit0。冻结提交 `86214a2b770ba16ff79ff0c8f8953df988afe67a` 的唯一父是Source07 `e8562cc04fae188f73c59ed33215126bb8bca7ac`；四路径取自已发布 `cfc17e346e5b017dbe8b57eeca1fdaaef31a4eaa`，包括runtime、专属延后注入测试、graphics helper及其测试。7,902继承文件仅copy/stat并继承已验证SHA，四个变化文件重新hash。未生成全树ZIP、未重编native、未改变MAIN分支或index。

实际选择为 `C:/csr8` 与 `C:/workspace/ck3-common-runtime/20261010-007`；[SOURCE08-BIND](C:/workspace/ck3-common-runtime/20261010-007/SOURCE08-BIND.actual.json)绑定manifest 5,221 B / `255fd41ba7d5156660054ccbeb03ebded8b2e6978e838d94968797a5ddf15b3e`，runtime 2,011 B / `993e19f335efadbac6232373f211707371bc02c8c3625e9700ca1b80fe87aa75`。host、DLL、injector及完整native输入沿用Source07精确pins；Source08是本机运行输入，不是新业务验收或产品release。

源码提交cfc17e346的[Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38030611652)与[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38030611518)已终态success，实际一次查询06:29:26 UTC；LYD专题未触发。采用后的16项启动测试及17项缓存测试见[R46报告](2026-10-10-r46-startup-query-red.md)，不重复运行同一套检查。

冻结时计划从实际闭场R44重新派生新key的缓存，再走公共prepare/plan/preflight/allocate/run/verify；旧seed不改写、不绕过key校验。原D2a存档、71正式文件加6 overlay、actor31254、日期53144712、事件instance121与native option0均保持。以下补记实际执行结果。

## 07:12 UTC 实际闭场：对照断言通过，公共结果仍未通过

完整编号为 `bf-202609141645-5434332d4d--li-yu-dao--R0047`。新seed实际生成3,687文件、143,124,020 B，key `5ac74c96b2bc266b557ccb599d88da3978d9276b7823f629c1bb01e4183aecdb`，仍继承R44的Oct17期限。公共prepare/plan/无context preflight各一次exit0；重新亲审Steam离线、nonce与实际窗口移动后，reviewed preflight exit0。原MAIN冻结655da780a的[Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38031468951)和[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38031468969)均success；LYD专题未触发。

日志history completion为本机14:50:04、In Game为14:50:14，分别在3955/3961行；公共启动器于06:51:23.970442 UTC观察到的466,445 B原始前缀已同时包含两行。该前缀SHA为 `eafa1bd6175ef45c9a43754b3b1746cf11ca074e4efac74c009ce1a2058dc91e`；注入进程随后于06:51:24.002创建，单次exit0。引擎日志时间与文件可见时间分列，日志缓冲原因未知。双owner帧pump2→4后，唯一campaign query于06:52:23.850092至06:52:24.620484成功；这证明本次共同路径可以工作，不单凭一次正例认定R46停泵根因已经查明。

八个原业务步骤全部ok：snapshot、初始event、cache-before、唯一select、terminal snapshot/event、cache-after、SAVE。公开option1对应native0；终点为 `lyd_factory_diag.2` instance122。前、后及保存后的45项有序继承缓存完全相同；七个政治头衔AST相同；完成变量为1，新宗教头衔18373仍无holder。保存原件91,711,704 B / SHA `c8dd0c7a47f181e3ebc2e2c50cde09220dd29d5c11738eb2db6f174fe13a14cf`，原检查器只读取一次SAVE正文。对照 `transaction_control_pass=true`，无推进日期；formal I3b/C3/I4及whole product不授信用。

ROOT在原图中亲审并取消退出autosave，07:05:43 UTC通过统一坐标映射单次点击“退出到桌面”。首次菜单点击曾因误传仅适用于move的reviewed-region参数，在输入前exit2；纠正后菜单与退出点击各一次，失败收据保留。独立观察器于07:05:54.518713 UTC从原句柄得到CK3 exit0，公共client保留的原CK3句柄亦为OS0。ROOT未在07:07:26.083315原hold截止前写入人工退出确认，因此原public run实际exit2、verify exit2，`normal_close_qualified=false`、native-zero proof为NULL、case acceptance=false。原host随后exit0，managed thread finished/cleanup true与Job最终0另列，不能覆盖缺失确认。晚写的 `ROOT-LATE-MANUAL-QUIT-REVIEW.actual.json` 明确不是向client补交的响应，不改写旧结果；下轮须在点击后立即提交实际确认，或使用公共已支持的自动正常退出配置。

当前CK3/本case进程及控制文件均为空。ROOT亲审15:11新鲜Steam原图“离线模式”，显示恢复1024×768×32@60；allocator、keeper、observer实际exit0，keeper线程退出后CAS4395→4396、done/resources[]。旧R46与本轮失败边界保持。

## 容量与后续正式路线

原4 GiB预留已于07:12:05 UTC核销，剩余0；六组有界metadata测量的已知留存为1,022,796,752 B，闭场卷空闲625,264,418,816 B，物理占用和历史峰值未知。[核销回执](C:/workspace/ck3_lyd_runtime_20261004/r47-root-storage-admission-20261010-001/CLOSED-RESERVATION.actual.json)为2,989 B / SHA `d297ee3a5506ca7e162978d8c47021a313b7a18fe0126a0f78f0c671eddba83f`。后续小型整理产物另计，不把闭场测量外推为未来总量。

并行清理只增量复用已有索引：新增可回收对象0项。Source06/07约282 MB旧导出和143 MB旧seed列为用途退役待评估，未因相同SHA或closed自动删除；七个旧attempt约21.2 GB仍缺替代/退役证明。此前实际删除11,190,757,265 B全文导出不重复计。缓存仍Oct17复核、Source08构建Oct24、raw Nov9、代表问题证据七天复核；复制、使用或失败均不自动续期，其他机器不冒写清理回执。

下一工作包是公共I3b正式B4 adapter：使用R29合法B3签署存档，重新取得当场事件、完整45项继承缓存与七政治头衔基线，单次正式430提交并独立验证B4保存/政治保护，再做B5冷载。R29失败B4头衔不能作为通过基线；C3必须等同一真实新T与冷载合格后，才交同Faith NPC65865。缺席的升级目录不参与依赖。当前一期仍NOT_GREEN，75%仅为工作量估计。
