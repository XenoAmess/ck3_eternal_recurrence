# 战争结果关闭引发的暂停迁移与邮箱故障

2026-10-16，`machine_id=xenoamess-full-tower-eb9d2c1186`。本文区分原始故障、已实际恢复
的旧 Native worker 与尚未载入的 B18 修复，不把编译通过当作实机通过。

P18 AUTO696 在 native1095/public567、日期53338704 正常读到战争结果窗口 visible，
独立 owner ticket2680 已进入并完成。AUTO698 的实际 before-submit plan 随后选择
`close-war-results-window-v1`，返回
`Native war results refused: war_declared_owner_submission_or_completion_failed`。
这里的 `war_declared` 是宣战通知与战争结果共用 Native owner 分支的历史错误名；本次实际
能力是战争结果窗口。原错误、计划与未知关闭结果全部保留，不改写为成功或零副作用。

SEM699 读到 Game 仍在同一 PID249712/FILETIME134365503082970177 运行，日期已到
53339880、paused=false、事件71。主线程邮箱 failure=1024，published、executor_started、
completed sequence 都为2681。705 在单次 MCP pause 后独立读到 paused=true，邮箱仍为1024。
原生 enum 的1024精确对应 `main_thread_query_failure_post_execution_drift`。这证明关闭请求
的 owner executor 已进入并完成；原 GUI callback 的进入/返回 trace 被旧错误路径丢失，
因此不能单凭这些记录宣称 Dismiss 已成功。

旧 mailbox 在 callback 后要求 `SameExecutionBoundary(before, after)`，包含日期和暂停。
不相同时设置永久 failure bit；reclaim 只清 executor exception，不清 post-execution drift。
后续 TrySubmit 见任何 failure flag 都直接拒绝。因此706虽在实际暂停后查询，仍在0.111秒
返回同一泛化错误，且 ticket未变；事件71不是这次查询拒绝的原因。单SDK重连不重建
WorkerMain 生命周期中的邮箱，不能清除这个位。

Root 随后通过绑定原 DLL/PID/FILETIME/exports 的既有 Stop/StartWithPipe 生命周期恢复
同 Game worker。Stop 的 void线程结束不单独授成功，须 Start返回与新 heartbeat互证。
实际707读到 failure=0、native revision1/public628，同一日期53339880、paused=true；
独立710 query读到 war_results hidden。原698仍为未知关闭结果，恢复没有重复关闭；
正常事件处理随后继续。此实际恢复用旧 Native SHA `29768ab0…0ac0c7d`，不是 B18 验收。

B18 窄修复仅针对固定 war_results close、实际同一 owner/ticket、零异常且 callback_returned：
允许暂停释放与日期单调增加，其他 pump、线程、TLS、Jomini/Game身份保持严格。它强制返回
`verification_pending`，不授 closure 或动作信用，并在既有 reason记录真实 begin/end日期、
暂停及 owner边界判定。正常 reclaim继续验证终态与ticket所有权；没有盲清任何既存failure
flag。普通查询及其他不明身份变化维持原拒绝规则，旧故障需由正常 worker重装处理。

SDK transport同时保留这类独立 owner证明的 typed pending，不再因关闭本身释放暂停把它
抛成丢失上下文的纯文本错误；查询的同帧守卫保持不变。下一普通规划应暂停/读回，再查询
窗口；收到 pending从不授权重新关闭。外置队列分类器须对应接受这一零信用新类型，不能
把它当作已关闭窗口或普通可用查询。

便携队列分支位于 `tools/g2_saved_campaign/war_results_scope_transition_classifier_v1.py`，
只由 `classify_` 函数组成并使用标准库，可被现有 AST installer选入；它不依赖运行中的
应用SDK命名空间。synthetic Native packet与5项正负验证随工具保存，原始游戏请求没有
被重写成这个新合同。当前外置 future classifier以实际5e520建设worker重绑叶为基，
完整保留旧分支；它尚未作为 B18实机结果验收。

外置 B18 实际只重编 mailbox与bridge两个对象，341项其他链接输入保持原摘要；AMD64 PE、
五项exports与14项直接调用生产helper的 Native检查通过。SDK transport两项定向验证通过，
仓库在现有 mailbox测试入口加入同一组检查，没有新增EXE目标。B18 DLL SHA-256为
`36ca467b19f99b2ac6551286c6f647923b155a02950f70f3521d3b51333d6de6`；尚未载入实机。
正常关闭 popup的完整业务、战争胜利与30年目标不由此授予。

同Game升级到另一路径的B18 DLL不能沿用同DLL Stop/Start的验收：现有injector仅以
basename查找首个模块，旧pinned DLL驻留时可能用旧基址加新export RVA；ordinary Stop
还保留部分sway/activity观察器hook，新的module-static journals无迁移合同；DllMain也
可能先沿旧环境pipe自动启动。只改文件名不能解决这些独立问题。当前选择同Game保留
原DLL恢复SDK，B18后续需要符合正常冷载合同，不执行未经验证的双DLL热替换。

本机原件索引位于外置 `continuation42-cold-prep/p18-responses/` 的0696、0698（含0-plan）、
0699、0705、0706、0707与0710回执；1024确认摘要在
`p18-war-results-partial-recovery-candidate01/POST-FAILURE-MAILBOX-1024-CONFIRMATION.json`。
构建与源码摘要见 `native-war-results-b18-ui-scope01/DELIVERY.json`、`SOURCE-PINS.json`、
`BUILD-RESULT.json`、`FINAL-PE-VERIFICATION.json`、`FOCUSED-NATIVE-RESULT.json`。
这些是来源索引，不是跨机器固定运行路径；按通用存储策略复核，当前最小证据下一复核日
为2026-10-23。本轮是 Native边界与Python DTO逻辑，无 `open_kaishek` 游戏脚本语义子集。
