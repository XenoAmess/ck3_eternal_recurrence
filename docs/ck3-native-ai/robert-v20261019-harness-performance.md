# Robert v20261019：Queue / feeder 性能审查

阶段目标为实际完整游玩窗口不高于 **1 秒/游戏日**，后继目标仍为 0.5 秒/游戏日。这里只审查 Queue、feeder、MCP 结果包装与显示握手；没有操作 Game、调用 Native/MCP、读取大 Driver 或改变正在运行的冻结源码。

`machine_id: xenoamess-full-tower-eb9d2c1186`；实际源码观察与软件资格时间为 2026-10-19T03:24:41Z 至 03:26Z。证据为 [精确源码审查清单](evidence/robert-v20261019-harness-performance-source-audit01.json) 和 [当前实际 Queue 源资格](evidence/robert-v20261019-queue-encoding-source-qualification01.json)。前者固定实际 entry、Queue、feeder、relay、provider API，以及资格工具和两个公共 helper 的 SHA。后者输入 Queue 262,759 字节、SHA `3773af1c2beb0d66d800371012826e42d973d16cac855c4786212d45b28b9f20`。

历史 [P49 封存窗口](evidence/p49-settled-performance.json) 的 machine_id 缺失，所属机器为 unknown，不能当作当前机器结果。其 settled 窗口为 118 游戏日、134.924610 秒，即 1.143429 秒/日。其中 RPC busy union 为 130.511249 秒，全部间隙合计只有 4.413361 秒。即使把所有间隙都消掉，也只是理论上限 0.037401 秒/日，仍有 1.106028 秒/日；这不是可实现收益，更不能把所有间隙归因给轮询。达到目标需要减少 RPC 内的真实开销，并用当前自然闭合窗口验证。

实际源码证实：

- `full_loop` 内最多 30 turn 连续执行，逐 turn 没有固定的 0.25 秒 sleep。0.25 秒出现在控制请求 dispatch 完成后；feeder 的 0.2 秒等待针对批次结果。SDK pair 的 0.25 秒只用于启动保管握手。
- 每 RPC 的容量检查已使用四个平坦目录的新鲜 `scandir`，没有每 turn 全量源码核对或 Driver 大文件 SHA。大文件 SHA 在启动、冷迁移等边界；不能删除边界核对来宣称加速。
- 每个普通 AUTO 后仍取得实际 `take_internal_semantic_snapshot` 形成 paired METRICS，核对日期、角色、episode 与原回执。此审查保留它。
- 当前 Queue 对完整 MCP result 执行两次 JSON 编码：第一次算字节数，第二次写完整权威 response。已有公共 `owner_response_json_once_v1.py` 可以把第一次编码直接用于第二次写出，保留整个原始 result、外层字段顺序和字节。
- 显示 relay 的 before-submit 与结果握手仍检查精确输入、TEXT_PUBLISHED ACK、source 与进程代次；20ms 的 publisher 轮询不能在没有计时证据时说成秒级瓶颈。

本次新增 [资格 CLI](../../tools/g2_saved_campaign/qualify_queue_response_encoding_v1.py)，输入精确 Queue 文件与 SHA 后，仅 AST 提取其实际 `call`、`atomic`、`decoded`，使用假 Session 和小型临时本地回执运行。整个 owner 模块不 import，所有其他函数 AST 与 post-result 尾部 AST 必须一致。成功、调用结果未知、后验拒绝、原件已存在四个分支均通过：完整 response 字节相同，前后验和 relay 顺序相同，假 RPC 次数相同；unknown 不获得 credit 或重放权限，原件已存在时零次 RPC。临时小文件已清理。

| 纯合成编码输入 | 原实现中位数 | 单次编码中位数 | 节省 |
| --- | ---: | ---: | ---: |
| 约 4 MiB | 50.080 ms | 28.871 ms | 21.209 ms |
| 约 16 MiB | 229.430 ms | 109.288 ms | 120.142 ms |

每项为五轮交替测量，完整输出逐字节一致；没有大文件落盘。这是编码组件收益，实际响应大小与出现频率尚待当前闭合窗口核实，不能据此声称达到 1 秒/日。候选由现有严格转换器生成，SHA `cae7a895ea1307fec08f81ce3b2e735c9853470ca2784d4fe1b24297c76f65d5`，263,109 字节；[实际源最小补丁](../../tools/g2_saved_campaign/patches/robert-v20261019-owner-json-once.patch) 为 2,581 字节，SHA `57e1bdeef52ee544f3f3cbafdbd98270d37749c2ce6f94850b633262a9db159b`。当前未采用，不能热换活跃 owner。下一次实际 SDK owner 交接时，由唯一 runtime owner 从精确原源生成候选，把公共 `owner_response_json_once_v1.py` 连同 Queue 纳入原 source pins、保管与开局合同后采用；补丁不能代替精确输入 SHA 核对。

所有新增源码、证据与临时小回执均计入已获准研究共享预算，未新设容量预留。紧凑证据保留至 2027-04-17 复核；原因是可重建的精确来源与行为等价证明，不保留额外合成大输入。
