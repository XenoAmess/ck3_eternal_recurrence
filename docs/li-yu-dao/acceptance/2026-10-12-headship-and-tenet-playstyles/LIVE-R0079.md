# R0079：原版儒家宗主制度发起，代表与表决仍待完成

2026-10-13 的原生场次 `bf-202609141645-5434332d4d--li-yu-dao--R0079` 加载源码 `aa41b8c446f2d8cbd7bd9ea5a51af466f8f1105b` 的83文件正式构建；CK3为1.20.0.4，EXE SHA-256 为 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`。本页只记录实际得到的信用。整体仍是 **NOT_GREEN**，0.1.2未上传，公开版仍为0.1.1 Alpha内部测试。

外置原件简称：`A42=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-first-storage-admission-20261013-042`，`RUN79=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0079`，`CASE030=C:/workspace/ck3-common-runtime/cases/lyd-release012-keypaths-20261013-030`，`A43=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-expired-settlement-20261013-043`。

玩家31254从原版 `confucian_faith`（Faith31、宗教9、原主礼仪道学33）出发，经生产入门和择师入口成为白沙之学礼仪174的唯一成员。原Faith和主礼仪未变。T35与T08各使用真实付费选项一次：威望2200→2050、金币247→147、虔诚150→350；实际学识5→16，达到自提名门槛。两项决议使用后再次打开时，4年冷却条件均未满足。T08付费选项当帧要求既存成年廷臣，实际选项可用并被选择；具体哪位廷臣获得500经验未独立读回。

同场新鲜完整名册显示：原主礼仪道学33有4676名成员、25郡、279名合格选举人，建议候选 NPC 31763 学识28；白沙174有1名成员、1名选举人，即玩家31254、学识16。两派均有合格候选，**候选资格不是代表接受或选票**。

ROOT先取得原始制度前存档 `CASE030/state/profile/save games/xar_checkpoint.ck3`，69411120字节，SHA-256 `f91795ad026e42ca5c958a5c50af949bb103381073d1ccb34fc51d05dab24e9d`，date_raw53144328。一次受限RAM读取核对角色领地的7项完整政治头衔 `[2230,2231,2262,2232,2263,2235,2264]` 以及四项实际领地法；没有在磁盘生成完整文本导出。该存档在生产发起前，因而只构成实施前政治基线。

随后经原版决议界面实际确认一次 `lyd_i3b_begin_decision`，`lyd.430` 随之出现。条款进度的实际悬停提示显示两派代表均未就位，包括道学的279人派别与玩家所在的白沙之学；事件此时没有可执行的实施 native0。ROOT仅选择一次“待诸方答复”以结束本轮检查。封定名单决议的实际详情也显示因名册与代表条件不满足而禁用，未确认。没有真实代表接受、法定票数、所有玩家同意、签署、实施、宗主头衔或实施后SAVE信用；`RUN79/case-output/release012-institution-0004-root-result.json` 的结果为 partial。

正常退出已独立核验：ROOT亲审未勾选自动存档，只在实际正常退出窗口提交一次最终Quit；延迟新鲜桌面画面显示 CK3 已消失，原进程 PID2800 的 retained handle 返回 OS0，native cleanup 成功。public run0、verify2、allocator0，verify2保留上述业务未完成状态。最终Steam离线截图经窗口位移和新像素复核，显示恢复1024×768，SCREEN 5436→5437 由原CAS释放。资源正常关闭不构成宗主业务通过。

原 AD042 的2GiB/120分钟预约于 `2026-10-13T04:51:23.300819Z` 到期。虽然资源关闭发生于此前，原存储关闭入口在到期后拒绝执行；**A42保持过期且没有 `CLOSED-RESERVATION.actual.json`**。A43于07:05:36Z在新的独立1MiB/20分钟元数据预约下核对进程、总线、原始正常退出和四个输出根，记录 `EXPIRED_SETTLED_NO_FURTHER_WRITES`。原四根实际保守计费845434840字节，原未用预约1302048808字节只归还预约余额；加上新元数据的完整1MiB计费后，保守项目carry为139609553562字节，有效cap仍为141327031211字节。GC信用0，物理回收量未知，旧A42不补写按时关闭；后续重型写入须另行准入。

精确 `aa41b8c4` 的原始CI有文档用语校验失败；之后只修正交接文档措辞的 `c8dfa3c7` 得到 Official 与 Linear attempt1 SUCCESS，LYD工作流未触发。新CI结果不倒授R0079的宗主业务通过。后继应从真实已保存资格或新鲜原版开局，先让两派合格代表接受提名，再核对封定、各派三分之二投票、全部在世玩家同意、代表签署与实施前后政治保护；不得用休眠、虚构选票或夹具授位代替。

| 关键原件 | 字节 | SHA-256 |
| --- | ---: | --- |
| `A42/initial-political-ram-001.actual.json` | 20721 | `f36b84c655dd1351118f80c5faa18163ea0b5d28e7b00886eecba2ffabcbb974` |
| `RUN79/case-output/release012-institution-0004-root-result.json` | 1649 | `c5dbdd5964c7ee0fb1deec369e6fb4fe692fc8e93ed47cc07402369e9b1f54ab` |
| `RUN79/case-output/normal-quit-root-result.json` | 3572 | `c3fe8524af54432fcca07b33b166af18e4a19c301ae4cec2c8213092d17e776e` |
| `A42/RESOURCE-CLOSE.actual.json` | 23205 | `153aed48dc76517efb3e716a9df74155ff9a7af2aa84acce1d8b21f31764b5fd` |
| `A43/EXPIRED-SETTLEMENT.actual.json` | 2215 | `5b3c3a0bf5acb3c08075639d2b78ea8fed2545206a7f558f86dd1a20c04ef409` |

原始证据按[全机器存储策略](../../../storage-retention-policy.md)分级保留；本页不延长整个场次的原件期限。

2026-10-13 可用性更正：本场隔离 profile 的着色器缓存已按[精确清理回执](STORAGE-R79-R81-CACHE-RECLAIM.md)回收，原缓存文件现不可读；上述69,411,120字节真实资格存档、运行证据及原结论保留。
