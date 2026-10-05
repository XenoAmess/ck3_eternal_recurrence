# R9 实机结果：NOT_GREEN

R9 已取得首次 JOIN 与随后 DETACH 的真实保存和独立 AST 回读，完整 JOIN→DETACH→JOIN2 周期没有执行完成。0053、0056、0057、0058 四次 SDK 调用均超时，消费者保存 ERROR_NO_RETRY，没有 SDK 返回，ROOT 未重发。实际 native 后验与保存证据保留，不能将其改写成 SDK 成功。源码冻结来源为 `54457b371e947edb86903c2ebd578034f02695db`；本说明与原始 closure、native FACTS 的精确绑定见同目录 JSON。

首次 JOIN 由 0028 独立存档回读证明：Rite169 的 parent105→104，actor31254/NPC65865 为 Faith104/Rite169，recipient65866 保持 Faith104/Rite159；旧 Faith105 保留，实际动态读出的 backup main Rite186 保留。钱包为 1743 金币、6650 虔诚、2200 威望，正式收费为 300 金币/1500 虔诚。0033 RESET 人为缩短冷却，不能证明自然五年已过。

0058 的真实 DETACH 存档为 91,530,739 字节，SHA `2abd208d9387b33aff5bb41fb5ea8f2cbe843b1b48df37a5f9a5bb4d87642539`。独立 native 分支回读确认 Rite169 的 parent104→106，新增 Faith106 采用 Rite169 的朱子三教义；source Faith104 保持汉学三教义及 main Rite159，旧 Faith105/main Rite186 保留。actor31254/NPC65865 随 Rite169 移至 Faith106，recipient65866 保持原状态；detaches1→2，joins1 保持，正式费用为 200 金币/1000 虔诚，钱包1543/5650/2200。七个实际政治头衔完整 AST 及有值的选定保护分支一致；缺失 family/stress 等字段不授予 NULL 相等信用。只读属性首拒绝、ROOT 的属性32→33修正及错误 expectation 测试原样保留；存档内容 hash 没有改变。

最终退出由 0064 正式 MCP 确认一次完成，0065 使用保留的原始进程 HANDLE 独立观察 PID20264/creation FILETIME134356529492116987，验证正常退出、exit0、signaled、typed terminal，native submission0，观察 HANDLE 随后释放。前置 MCP prepare 消耗0且后状态未知，晚到 query 返回 menu/modal=false；维护 WM_CLOSE 唯一一次 posted 只打开确认窗，0063 新 query 返回 modal=true，随后才执行0064。因此正常终局退出已获证，完整 MCP 前置准备仍为 false，autosave 未授通过信用。

SDK client 留下 session-closed，ROOT 执行回执 exit0；keeper FINAL 为 thread_exited=true、failure/entry_error=null、last_sequence2980。FINAL 中 screen_released=false 如实保留，实际资源释放由另一份 CAS2980→2981/resources[] 回执证明。首 CAS 因 lowercase CLI SHA 格式拒绝且未 mutation，002 exact uppercase 修正保留。task 仍为 waiting，retirement business_status 为 unresolved_red，不得写 done。

最终 whole-log 已实际完成并逐件复核 INDEX bytes/SHA：16 文件两次完整读取稳定，结果 ACTUAL_R9_WHOLE_LOGS_RED。primary error.log 30891598字节，SHA 2603033cd62be7676a86213c9b27dd8bd357f18e71f2b5a9370bebacc4224158；100000E中578 fixture、99422产品错误，含1 native dynamic-localization。debug/game镜像不重计；日志上限未证，后段零增长不授通过信用。ROOT OS census实际ck3_processes[]、original_pid_matches[]，未重新打开个别进程HANDLE；ROOT policy note实际解除source-freeze逻辑政策门禁，没有单独物理source-lock字段，原冻结输入记录仍保留。原闭合/失败/准备包不修改。大原存档永久外置，最终封存仅作无损证据保存，整体NOT_GREEN，JOIN2/fullcycle NOT_RUN。
