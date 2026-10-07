# R0018 CLOSED 追加后记：原 HANDLE 退出、实际缺席与释放

本后记覆盖原件截止 `2026-10-07T03:17:47.829692+00:00`，运行来源仍是冻结的 `dbaf5f8db2067419838b814e278d962f428dc33c`。原游戏 PID `5920`、creation FILETIME `134358115483546531`、native generation `1`、session `9cdca47579f54d3191efdecdb7400374`。**本轮正常退出现已取得实际信用**：`TYPED_NORMAL_EXIT_AND_ORIGINAL_PROCESS_HANDLE_EXIT0`；ROOT 的实际闭合边界状态为 `ACTUAL_R18_CLOSED_RELEASED_BOUNDARY_VERIFIED`。整体业务仍 **NOT_GREEN**，没有 formal、新 T、C3 或 I4 信用，autosave 仍未验。

FIRST430 与 03:04 两轮 PARTIAL 是各自截止点的原快照，保持原样。它们当时的退出 `UNVALIDATED` 不再代表本轮最终退出状态；后续判断须同时读取本后记。两轮 STATE 原 mismatch、NPC 自然 NO、两 cancel、首次 materializer 失败、SDK80 native 派发前拒绝和 SDK84/88 Python 未决锁都保留。

SDK96 原记录为 `process_exit_observed_zero`，`typed_normal_exit_observed=true`；预确认原 retained HANDLE 的初始 wait `258`，最终 wait `0`、exit `0`，并核对原 PID 和创建身份。原 SDK SHA-256 为 `45cff8feb685cd9b65cd2853fa0b714d9df9889cea537058afb763dc43ee7063`，对应 native receipt SHA-256 为 `d461504832780fff672bb3b6a2d7091a5b22984beb219ad21488735ad452d202`。其嵌套 `native_observation` 保留中间 `dispatch_pending`、`orderly_exit_verified=false`，不把这些旧阶段字段重写；最终实际信用来自 typed 退出与独立原 HANDLE 的 exit 0。ROOT 已有的 VERIFIED 原件另记录 terminal native ACK 和 normal-exit callback 核验成功。

Client PID `16100` 与 keeper PID `11024` 的关闭前保留原 HANDLE 均实际 wait `0`、exit `0`；原创建身份分别保留。Client 正常 close 的 response 与 `session-closed.json` 已归档；keeper 实际 FINAL 的 `thread_exited=true`，last sequence `3535`。原 holder 执行 session 是 **37726**，原 keeper 执行 session 是 `55834`，两原执行 completion 的 exit 均为 `0`。keeper completion 的 stdout **只保全实际回调中的首个完整行投影**，其原件明确写出完整回调仍在工具 transcript；不能把该投影宣称为完整 stdout。原 helper HANDLE exit 0 提供独立证明。

实际 screen CAS release 的 event sequence 为 `3536`，task state `done`，resources 为空，原 RELEASE SHA-256 为 `fc835cd90a5c12f88345c7298ffcc9c5d70580a48700f521e0ad37c3f04f1030`。这来自已保存的实际回执，本报告没有再调用任务总线。keeper FINAL 自身的 `screen_released=false` 保留；实际 release 属于后续 ROOT CAS 阶段。

ROOT 于 `03:17:36.669198Z` 的实际 post-release census 记录 game/client/keeper/holder 四个原 PID/创建身份均缺席，且 `no_current_managed_game_or_native_services=true`；该原件 SHA-256 为 `3f8c41a29657e3b955118da084070fa021c6a4b895bc9e677fe2d370c4b0784a`。Steam 明确在此 census 的闭合范围之外。ROOT 的闭合边界作者原 execution RESULT 于 `03:17:47.829692Z` 完成，actual exit `0`，SHA-256 为 `410d8fa89f0938d42b3604e7c8e66e5f9a74e7cd0c543ebc21d6aaa47627c780`，automatic retry 为 false。作者产生的 INDEX、PREVIOUS-BOUNDARY、VERIFIED 与原 verifier/author inputs 分层保存；本报告代理没有重复执行作者或 verifier。

R1/R2 自然 NO 的解释有冻结源码支持：setup 原第 65 行把 vote 初始化为 `-1`，response 原第 4 行仅在实际 vote effect 回调中设为 `$YES$`，event 411 原第 4 行给 YES/NO 分别传 `1/0`，AI base 分别为 `60/40`。所以本轮保存的 NPC `65865 vote=0` 已是 NO 回调值，不能当成未处理的初始值。精确源码原文件 SHA 和所引原行见 [NATURAL-NO.source-provenance.json](NATURAL-NO.source-provenance.json)。这一解释只用于已保存的 R1/R2，不预测 R3，也不预填任何 YES。

选定的实际原 JSON、execution stdio、闭合 verifier/author 和必要依赖源码以原 bytes 保存在 [CLOSED-0317.original-evidence.zip](CLOSED-0317.original-evidence.zip)。完整来源与 SHA 见 [CLOSED-0317.inventory.json](CLOSED-0317.inventory.json)，分层原事实见 [CLOSED-0317.facts.json](CLOSED-0317.facts.json)。没有可执行文件、存档正文或整份 runtime/source 树。

本后记 create-only 写入独立 worktree 的新目录。报告代理主树写入、SDK/游戏调用、进程查询/操作、任务总线调用、CI、重复 checks、commit/push 均为零。原运行和失败证据没有移动、删除或改写。
