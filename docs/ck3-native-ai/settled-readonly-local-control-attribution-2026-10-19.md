# 本地控制错误不再归到已完成 MET

machine_id: `xenoamess-full-tower-eb9d2c1186`。2026-10-19 的来源为实际 C3 Queue、保全的153/154/148及58周期状态、原错误 proof，以及原 C3 clean installer。资格全为离线源码组合，0现场 RPC。

153 MET 已完成，`call()` 将其留在 `current_attempt`。随后154本地 classifier install 使用错误的初始 pin 模板，原 clean guard 正确拒绝；`halt_request()` 却从残留的 current_attempt 取了153，导致本地控制错误被归到成功 MET。旧重消费仅允许 AUTO/SAVE，又不能合法处理该伪 MET halt。

[源 transform](../../tools/g2_saved_campaign/settled_readonly_dispatch_source_v1.py)只在下一 bootstrap 的 `run_request_loop` 加一个调用上下文守卫：请求是本地 command、无已有 halt、所有 pending/terminal 都为空，且 current_attempt 为完整成功、无 transport error 的 SEM/MET 时，先清旧 current_attempt。之后154若仍拒绝，就由原 halt_request 记录154本身。它不改变 classifier 或业务结算，不清 unknown、不动真实 pending/既有 halt，也不增加任何本地控制的准入或自动恢复。

[资格工具](../../tools/g2_saved_campaign/qualify_settled_readonly_dispatch_source_v1.py)执行真实 `run_request_loop`、`install_result_classifier`、C3 clean qualifier 与 `halt_request`，回放原154错误 proof。原源错误指153，新源正确指154，两者仍报同一真实 guard 拒绝。unknown transport、真实 pending、已有 halt 三种实际风险边界逐值保持，counts/state不变，未调用 MCP。测试写入被捕获到内存，生成候选及小资格文件位于独立 review，没有改现场树。[完整资格](evidence/settled-readonly-dispatch-source-qualification01.json)保留 pins。

输入 C3 Queue SHA256 `18bfcbe93b17c625b80fa2701a29e44229f2a554b5daee75c32544c677e9c2b6`；输出264841B，SHA256 `633dee176ad0a182179793b09d1da0b137dca61dfeeacf36338bb90df9bc0b5e`。AST 只增加这一守卫，原 Queue 其他 AST 逐项不变。先应用该 transform，再由唯一 runtime owner 做下一代 bootstrap 字面和 factory 变换；不热改当前已加载 Queue/App。源修复解决错误归因，不保证本地控制本身一定成功，也不授权重放任何原动作。
