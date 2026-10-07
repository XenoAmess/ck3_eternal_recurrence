# R0021 operational 闭场后记：原业务与 typed-exit RED 保留

截止 **2026-10-07T10:17:02.896526+00:00**，ROOT 原最终文件 `ROOT-AFTER-RELEASE-CENSUS-001/RESULT.actual.json`（4845 B / SHA-256 **7210aed9ab1858abe9ee1976387b1bd35977d71d36b8f223319dc5f28885537c**）为 **`RED_UI_NORMAL_CLOSE_OPERATIONAL_ABSENCE_CONFIRMED`**。完整 run ID `bf-202609141645-5434332d4d--li-yu-dao--R0021`，本场加载来源仍 **9b068c8fc9bb45d69417bf6857dddd65abece7d6**。

ROOT 使用正常窗口 X → ExitDesktop，回报 autosave 选中；原坐标换算 exec exit0及原 UI REQUEST/stdio 均保留，像素原件按原路径/SHA 外置回链。后续实际 census 证明游戏、Client/server 以及 helper 均不再存在；最终 `actual_process_census=[]`、`fresh_screen_owners=[]`。原 keeper 最后序号3603，实际 CAS **3604** 为 `done/resources=[]`，序号取自原 release stdout。

| 层次 | 实际结论 |
| --- | --- |
| Client 原 HANDLE | wait0 / exit0，原 retained observation；原 exec0 |
| keeper 原 HANDLE | wait0 / exit0，原 retained observation；原 exec0 |
| holder 原 exec | exit0，原完成回执 |
| 游戏原 HANDLE | **exit_code=NULL / exit0_observed=false** |
| typed normal-exit | **false**；0007 context RED，0008 observe RED |
| 场地与进程回收 | 原最终 census/owner 空，CAS3604 已释放，`forced_exit=false` |

0008 的官方 SDK 原文是 **`no backend-owned pending original-process observer is available`**（SHA `b4214c5e4e9636876ef33be9f16b20b00000b152f007d6a6c048131908daded3`）。进程消失与正常 GUI 路由不替代原游戏 HANDLE 的退出观测，本次 operational 闭场不能写成 typed normal-exit GREEN。Clientclose0009 的原 control response 与三份原 exec 完成也分层归档，不能补造游戏/native ACK。

首个 stop/preserve source 在记录 absence001 后因 `native_ack` checkpoint key 缺失失败，**没有发 STOP**；原 source 与原 absence001 不改。新 successor002 采用实际 `result.checkpoint`，完成 exact copy/STOP。原错误按002的 `previous_partial_error` 保存；独立外置首轮 tool stderr 文件为 **NULL**，不制造 wrapper。checkpoint 原件与外置 copy 均 **91669783 B / SHA-256 aa57de8382eae22d94e55091c8d370405748d39fa0917c04d313f2d555618849**，原 preservation JSON 明记 `AST_read=false`。本包只归档505 B的原 descriptor，不读取或复制91MB正文。

[10:02:23 原 partial](../PARTIAL-20261007-100223.md) 及其四个文件保持原字节：SAVE 成功、G2/G3 exact build/schema RED、0007 unsupported step 仍属原事实。新关闭后记只追加生命周期与回收结论，业务状态仍 **G2_G3_SCHEMA_RED / whole mod NOT_GREEN**；formal approval、new T、C3、I4 均 **NULL**。后继源码/冷载 intake 正在独立任务准备，本截止其新 PID、业务 GREEN 或修复 live 信用均不填。

[事实投影](FACTS.closed.actual.json)、[原件清单](INDEX.closed.json)、[原字节 ZIP](raw-closed-evidence.zip) 保存 77 个新来源引用/63 组原字节，并按原 partial INDEX 复用 1 个既存来源。original stdout、错误、原 HANDLE、source successor 和 release/list 均按来源 exact SHA 保留；文档作者没有 SDK/游戏/屏幕/总线/进程/CI/build/tests 动作，没有移动主树。
