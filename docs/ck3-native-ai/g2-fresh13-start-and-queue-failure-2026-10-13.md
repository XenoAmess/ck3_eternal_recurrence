# G2 fresh13：开局验证与队列异常（2026-10-13）

fresh13 已实际通过固定 1066 罗贝尔 Start，最后 campaign-root 状态为 `campaign_root_frame_verified`。随后队列在镜头请求前退出，历史 helper 只保存了单叶 `ExceptionGroup` 摘要，真实内层原因仍为 UNKNOWN。**普通回合、日期推进、选定战争目标、胜战仍为 0；B12 完整地图 owner-tree 仍未验收。**

## 实际输入和结果

本机外置根 `R = D:/codex-ck3-background-spill/g2-remediation-20261013`，attempt 为 `R/fresh-robert13`。冻结源码 `c4e1450bf51e177738478ba22a06fdf4b82f09f7`，复用 B12，DLL SHA-256 `28c01334e474a712180c94782d72c0880d7360e49296dbc82e73e23e9416b648`；没有 Native 修改或重编。完整实机编号 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0007`，Game PID265560、creation `20261013111959.877935+000`。

Root 亲审本场 `ROOT-ARMED-REVIEW-003` 的 Game/scene 主菜单帧后，唯一启动录制，再启动配对的 SDK。route1 为 0.091 秒，New Game2 verified 为 0.479 秒，Robert Start3 verified 为 171.669891 秒。这里的 171.67 秒是整个 Start 工具耗时，不能写成最后根查询耗时。

`state/native-session/frontend-start-root-queries/frontend-start-root-e74f6d3d032747cf845e0ffc9b19ecec.json` 实际记录共享 deadline、原请求不重放、剩余 429.691 秒及独立根帧 `native:2` / revision2 / date_raw53144328。最后根查询约一秒返回 verified，证明共享 deadline 修复在本场可用，不证明后续普通回合通过。

Root 发布了 73 字节 camera4 请求；没有 INFLIGHT4、response4，NEXT 仍为 4，不能声称 camera RPC 已提交。队列于 11:31:11.727227Z 保存 `ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)` 后退出。当前证据排除已到 deadline、128MiB artifact cap 或录像字节上限；录像在异常前后仍增长。历史守卫内存值、瞬态文件读取和原始叶异常未记录，不能据推测补写原因。

## 闭场与原件

`R/fresh-robert13/ROOT-ACTUAL-CLOSED-EVIDENCE.json` 为实际闭场摘要：queue 原句柄 PID142140 / FILETIME134363644923416774 exit1；application 原句柄 PID154344 / FILETIME134363644942557635 exit0。Game 为 owned forced cleanup exit1/tree_gone；keeper 停止，屏幕由 CAS4011→4012 释放，登记为 waiting/unresolved_red，不是业务完成。

独立录像 `R/custody-recorder01/recordings/679cd172-f01c-4669-88dd-a59aca5d31f2.mkv` 实际 COMPLETED，111,588,263B、185.666 秒、2560×1440/30fps，SHA-256 `f5aadd33be27eca66ee82ab5a85e7134f4c45501aab4c62b8aa4008b72604a84`。输入已解除，独立 OBS 实际正常 exit0。没有初始 SAVE、普通回合或日期推进。

原 response、根查询状态、闭场摘要、亲审帧及录像仍可读，作为下一场对照保留；owner `/root`，下一步是有完整异常诊断的 fresh14，复核仍为原 `2026-10-13T16:58:39.018273Z`，不自动续期。沿用用户的 Steam 离线保证，没有取得新鲜 Steam 离线像素，也没有切在线。

## 外置修复候选

`R/resume08/m_harness/queue-error01/DELIVERY.json`（SHA-256 `e75716348b392ff1bc844ff7816eda9bd6f37ce2e2f00d79fe2f830ef1844487`）绑定外置单文件候选 `root_fresh_sdk_queue.py`，61,570B / SHA-256 `859b86d00ed62108dc48213b818566e8e0d5f43fb2e14733f5663153ff1cc7cf`。

单次离线对比复现了一个明确机制：原 `halt_request` 再调用守卫，使最初失败被第二次异常遮蔽。候选只登记一次失败序号，零 RPC、零重放；在异步上下文退出前保留首次完整 traceback/异常树和 ≤16KiB 守卫事实，最终分组异常另存。夹具 GREEN 证明该机制及候选行为，**不识别 fresh13 的真实叶异常**。历史 helper 未改，旧测试矩阵未重复。

下一场使用新目录、pipe、state、profile 和 live ID，冻结当前 clean master；容量不足时先按通用策略精确回收合格对象，不增原 8GiB 共享预算、1200秒/1GiB录像上限或复核期限。候选只有 fresh14 实际执行后才取得实机信用。
