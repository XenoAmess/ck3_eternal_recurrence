# P112：和平建造 finalizer 的临时 SDK 角色

本地 2026-11-08 04:46，UTC 11 月 7 日 20:46；持续性能目标保持 active。完整 PlanningRequest 含大历史时，旧和平 finalizer 把 starting／ending 两份全文都送入原 262144 B SDK lane，合法的无候选来源也会先因体积失败。现在只在计算副本中投影两个 snapshot 的 13 个实际消费字段，diagnostics 仅 hello，hello 保四个 expected／fallback build 键；原顺序、missing、null、错误父类型和完整业务数组保留。

原 query、完整 native_envelope、PlanningRequest、Complete、read receipts、stableReceipt／SEM 及原件守卫不变。未扩大 codec cap，也未裁持久 query_observation。和平计算可用不代表完整 Construction quote／action／material 可用；后者仍需后继 P113 的完整原件引用闭环。

生产只改 OrdinaryConstructionCollector.finalizePeacetime 和一个私有 copy-present helper，29941 B／SHA256 `f7cbd02be9a7bc17bf00c408712d79945df99bed81f4747dec3ce1f7c49de4d2`。必要 1 TU／22 class exit0，4.4718553 秒。新 Test/main 14422 B／`9562ef119b93c41bb2448dd8a0f12dc8c090321ec0e06cc051dff18388842a5d`，1 TU／1 class exit0，5.2698124 秒；仅三个新方法 3P／0F／0E／0skip，5.0974169 秒，无旧测试重跑。

真实 DATA 使用既有 authored peaceful input 加未消费的同源前 139 行历史：原 query 6805700 B，旧 SDK 拒绝，新 finalizer／assembly 的完整 742 B 输出与原小输入固定 codec 结果逐 byte 相同，完整原 query 和 native envelope 字节不变。测试还覆盖 build expected 键 presence／null 优先级、错误父类型、原模式／schema／episode／request ID 拒绝，以及完整 native envelope／消费数组自身过 cap 仍拒绝。该大 DATA 是大小与正确性反例，不进入性能分母，也不构造真实 intent 或 Runtime 许可。

有限 ABBA 使用已有具名缓存 Collector binary 与本次新编 Collector，其他 classpath、同一 Test/main 和 DATA 相同。基线来源记录在 EXISTING-BINARY-BASELINE.json；只授这两份具名 binary 的 static-finalizer 组件对照，不声称旧缓存等于当前全量源码或当前 Runtime。共同输入 198482 B／SHA256 `78c89b02d505075d21b3c9acfc475e9a8ef3b1c28afb25ba50c1f5efb204971a`，在旧 262K 内；共同输出 689 B／`017c81c921f6dcf907e316192d27e494e25efa3a1f02c8d1262d24cd66edc9e3`，四 JVM 的全部 warm／sample 均相同。

四个独立 JVM 固定 A0/B0/B1/A1、CPU1／384 MiB／45 秒，各 2 warm＋4 measured，每模式 8 实际测量全保。完整 static-finalizer 中位 3.7886→2.83575 ms，均值 6.0843375→3.64805025 ms；主线程实际分配均值 1984696→64936 B。无 force GC、速度断言或慢样本删除。两进程合计实际 4.7575663→4.7378597 秒；main（含 setup、warm、sample、校验，写出前）合计 3.3759619→3.3797185 秒，完整 main 未变快。setup 合计 3.1754384→3.2021271 秒，独立 outer／OS 峰值原件完整保留。组件差异不授 HTTP／TTFT、完整规划、游玩或保存日速度。

两轮真实本地模型均拒收后由 owner 接管。首轮 Value 误调 Obj API、缺 import、重排成员；第二轮仍丢 null／scalar 父和擅裁 played_character。两轮 1 POST，TTFT／total 分别 3336.159／10898.194 ms 和 815.112／10836.678 ms，prompt/output 23854/1183 与 24035/1651，cached tokens 均未报告。未编译错误候选，不把 owner 实现记为模型原样采用。

具名软件资格：`D:/ck3-state/resume91-native-integration/p112-peacetime-finalizer-test03/QUALIFIED-P112-PEACETIME-FINALIZER-AND-ALL-ABBA.json`，26946 B／`eca779cf1622cf23ce44628c4c0b38ee54f35b4c0aac2bcab06bb446fe51cb63`。全部 8 warm／16 measured 为 ALL-ABBA-SAMPLES.json，11362 B／`a8402fee3b3b30116244066e09a6ed4315057e6cc696ab6668f7f16ed1994a25`。末实际 close 为 20:46:39.667224Z，资源已释放。

P111 完整 Finance v2/v3 集成仍独立推进；其旧 Faction 消费者缓存与当前源码差异正同步，不混入本提交或改合法 0 来绕过。P113 完整 Construction 原件引用继续。未进行部署、Game／Native live／GET、原 UNKNOWN 重放或 SAVE；10 秒／新增确认保存日目标尚未达到。
