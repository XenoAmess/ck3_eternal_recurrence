# R0081：75/25 候选已装载，首节点答复超时

2026-10-13 原生场次 `bf-202609141645-5434332d4d--li-yu-dao--R0081` 使用源码 `dc6c990930c47f645df9d72e46d8093c39785fbe`，其中 NPC 中性提名、投票和签署的赞成／反对权重为75／25。正式候选为83文件，manifest SHA-256 `e56ed03fc8922c17fb9492fe8876acf0c041248de9363ba9387cf64e57d4e884`，ZIP SHA-256 `89a46e81149c6619628ca61025a9bdb9da94cd91976efb6e89e35d82a390636b`。实际 profile 与候选逐字节一致；启动标记一次，LYD范围解析错误为零。原生基线读回玩家31254、原版 `confucian_faith` Faith31、当前礼仪32、主礼仪33；不能由此推断提名权重的业务效果。

本场业务 **RED**。首个 ROOT 基线检查点的固定截止为 `2026-10-13T10:14:09.828350Z`。ROOT已取得候选装载及宗教原生读回，但在补充 GUI 核对时再次超过原截止，未写入检查点答复。原 host 保存 `TimeoutError: Original normal Quit reserve reached; pending Root phase remains GAP`，run返回2。没有执行入门、提名、代表接受、封定、学者投票、签署、实施或实施后的政治继承保护；75/25 改动仍未获实机业务信用。下一场首节点应先根据已核实的最小证据及时答复，其他画面观察放在后续阶段。若必要事实仍缺失，应按时提交 partial，不能静默让时限耗尽。

退出链路独立通过：ROOT直接审阅未勾选 autosave 的正常 Quit，CK3 PID13496 retained handle OS0、原生清理与进程树消失均成立，keeper正常 STOP 并退出0，屏幕 CAS 5508→5509 释放。桌面分辨率恢复为原先1024×768；ROOT直接审阅最终 Steam 离线画面。退出成功不改变业务RED。

外置原件：`A46=C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-nomination-storage-admission-20261013-046`；`RUN81=C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0081`；`CASE032=C:/workspace/ck3-common-runtime/cases/lyd-release012-keypaths-20261013-032`。A46在原期限 `2026-10-13T11:39:51.431827Z` 前完成结算：四根逻辑量343207643字节，扣除已预计源10426字节，保守加计总线/Git与收尾34603008字节，本次计费377800225字节，未用峰值695941599字节归还预约。保守项目carry为140438485214字节；GC信用为0，物理回收量未知。原始证据按[全机器存储策略](../../../storage-retention-policy.md)分级到期，不因本报告而无限续期。

| 关键原件 | SHA-256 |
| --- | --- |
| `A46/BASELINE-PROFILE.actual.json` | `f2d4a392907d7615b4e844dcc446a7536d6778252b4a9a7b9e36e92cd032962d` |
| `RUN81/case-output/case-error-preserved.json` | `2cf736ddad600998af8b0849e8c897ba72308432b470f15ae4c877af4d2bf6a9` |
| `RUN81/case-output/normal-close-result.json` | `c4abdbd2497d515ce2f338063ee5463a3020b9be6ff2e63bf4b11867ff59cc7d` |
| `A46/CLOSED-RESERVATION.actual.json` | `bc3b92add72b55cd5528bb6e70b379e4c64750cc95cd2493447d018a99d730f4` |

0.1.2未发布，Steam公开版仍为0.1.1 Alpha内部测试。
