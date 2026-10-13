# R0080：原版儒家基线通过，宗主业务检查点超时

2026-10-13 的原生场次 `bf-202609141645-5434332d4d--li-yu-dao--R0080` 使用源码 `31f96a50df8a1be4cba9d3c95a2016e6ed87445f` 的83文件正式构建。候选构建的 manifest SHA-256 为 `5b37fbf608bc6cd677782dd367c6aca145d7772ada83c91ad20bf60119e7133e`，ZIP SHA-256 为 `6bb87f23dc326177de4a96011a6c71ce1c0b09fd798affe31dc4cc4ea04215cc`。实际装入 profile 的产品文件与构建逐字节一致，启动标记出现一次，未发现 LYD 范围引擎解析错误。CK3 为1.20.0.4；玩家31254仍属于原版 `confucian_faith`（Faith31、当前礼仪32、信仰主礼仪33）。

本场业务状态为 **RED**。在首个原版基线检查点，ROOT延迟到该阶段固定截止后才完成候选字节与日志审阅；原 host 保存 `TimeoutError: Original normal Quit reserve reached; pending Root phase remains GAP`。因此未向本场提交基线答复，也未进行入门、提名、代表接受、封定、投票、签署、实施或实施后政治保护验证。实际原版基线和加载证据不能倒授这些玩法信用。public run2、verify2，0.1.2仍未上传，Steam公开版仍为0.1.1 Alpha内部测试。

退出链路独立完成：ROOT在实际暂停菜单审阅未勾选自动存档后，仅提交一次正常 Quit；原进程 PID9912 的 retained handle 报 OS0，native cleanup 与进程树消失均通过，原 host 返回0。keeper和allocator退出0，SCREEN CAS 5480→5481释放。ROOT直接审阅新鲜的 Steam 离线画面，显示模式恢复到原来的1024×768。正常退出不改变业务RED。

外置原件：`A44=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-nomination-storage-admission-20261013-044`；`RUN80=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0080`；`CASE031=C:/workspace/ck3-common-runtime/cases/lyd-release012-keypaths-20261013-031`；`A45=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-expired-settlement-20261013-045`。A44的1.5GiB/120分钟预约于 `2026-10-13T09:15:24.695895Z` 到期，原目录保持过期且未补写 `CLOSED-RESERVATION.actual.json`。A45以独立1MiB/20分钟元数据预约核查原退出回执、总线、四根实际占用和无重型写入；四根合计414441692字节，扣除原已预计脚本10425字节，再保守加计 Git/总线33554432字节和收尾1048576字节，原场实际计费449034275字节。未用预约1161578461字节仅归还预约余额；计入A45整笔1MiB后，保守项目carry为140060160701字节，cap仍为141327031211字节。GC信用0，物理回收量未知。

| 关键原件 | SHA-256 |
| --- | --- |
| `A44/BASELINE-PROFILE.actual.json` | `c46119972a285051fe31ca4f6610a37c320714056333f77dd53a5b62d37cbc34` |
| `RUN80/case-output/case-error-preserved.json` | `43f577af9afe0b6fc961a6c5efd4edda46d58255336daf62aee54e6f3159965a` |
| `RUN80/case-output/normal-quit-root-result.json` | `5cab325692fb9997f9ff03464b3f80fa77ed2a4d4f02715829337014386b2e8f` |
| `A45/EXPIRED-SETTLEMENT.actual.json` | `8a9906f5bc91ac6f2b3aa146b7f8743a7f78d05e2953b1774001a49536d9806c` |

后继必须在新场首个检查点出现后先立即提交基于已审阅原始 profile 的最小基线答复，把耗时的额外审阅放到后续阶段；无答复的R80不得复用为业务通过。新场须重新取得有限存储准入和新鲜 Steam 离线证据。原件按[全机器存储策略](../../../storage-retention-policy.md)分级保留，本页不延长其期限。

2026-10-13 可用性更正：本场隔离 profile 的着色器缓存已按[精确清理回执](STORAGE-R79-R81-CACHE-RECLAIM.md)回收，原缓存文件现不可读；其余运行证据与业务RED结论保留。
