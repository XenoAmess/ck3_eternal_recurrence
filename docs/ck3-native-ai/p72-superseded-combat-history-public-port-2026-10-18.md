# P72：新有效查询后摘要过期战斗研究历史

公共实现把旧 V2/V3 假设战斗查询的全文改为明确有损的历史摘要，避免每次规划与持久化继续复制已失效的大正文。触发条件是新查询已经通过原 typed normalizer、同帧检查、完整 canonical cache 发布及成功记录；当前最新 history 行、API 返回值和模型输入保留完整。该修改没有部署到当前 R8。

来源是 [P67 实际巨大回执和归档上限分析](p67-p68-combat-query-payload-and-archive-compression-2026-10-18.md)。本次没有重新读取 Driver、AUTO77 或旧 archive。机器 `xenoamess-full-tower-eb9d2c1186`；观察时间、外置 P72 来源和公共源码 pin 见[证据](evidence/p72-superseded-combat-history-public-port-2026-10-18.json)。它不能证明实际吞吐或 Driver 缩小比例，首30节点也尚未完成。

`combat_history_superseded_v1.py` 只处理同版本、更早 native revision、query sequence 更小的旧成功 available 记录，保留所有行、位置、index、command、ok、query frame 和其他结果字段。partial、unavailable、错误、同帧、其他版本和 battle-control 正文保持。general/siege 的完整预测输入来自当前帧 cache；active battle tracking 所需的 battle-control 历史、真实日进的 war progress、决策和 pending ledger 不改。冷恢复保留原行合同，过期缓存仍按原机制失效。

摘要保留场景、completeness、计数、规范 JSON SHA/字节和原查询帧，明确旧全文未保留、不可由摘要重建；本模块没有新 archive writer。没有已绑定原 MCP 路径时明确记为未知，不能声称原件已归档或能完整复原。已有闭场 Driver 和 MCP 原件不变。

每次最多摘要8行，单正文哈希上限64MiB，批次128MiB。哈希在原 history lock 外计算，提交前核对象身份，再显式失效增量 JSON 缓存。超预算或编码错误保留完整历史并返回原成功查询，不重发 Native；因此这不是无条件的尺寸上限。V2/V3 内部帧读取和 primitive 校验沿已有不携带 history 的路径，直接 snapshot 默认仍包含历史。

一次必要验证通过：21 tests、30 subtests，包含公共 Native 原 execute/primitive/normalizer/cache/record、Service typed API、合成持久化和恢复，以及 partial/unavailable、跨帧、digest 失败、缺缓存与重复摘要。端点是内存夹具，没有启动 SDK daemon、Native 或 Game；有限消费者源码审核沿已封 P72 记录，第三方历史正文消费者不在本次资格范围。未来 SDK 冻结和实机采用仍须独立绑定来源。

2026-10-18 16:18 UTC追加（`machine_id: xenoamess-full-tower-eb9d2c1186`）：公共 `NativeHeadlessGameplayDriver._execute_war_termination_step` 的投降一次性守卫及白和一次性／30日冷却守卫仍先调用 `_history_snapshot()`。该API在锁内深拷贝全部历史；三个原守卫仅逆序读取命令和终战元数据，调用方只判断是否存在。现改为在同一历史锁内执行原纯读取函数，仅带出布尔值；不改变匹配、拒绝消息、读取顺序、Native提交或后验，也不摘要或删除历史。纯函数没有Native、I/O、等待或外部回调，未把这些工作带进历史锁。对N行、正文总量B的历史，取消白和分支最多两次O(B)复制及其分配，原有最坏O(N)元数据搜索保留。

软件来源为 `fc091e9a724e5b7c048ac5a834ec5174a8992083` 上的窄修改；修改后 `native_driver.py` 为1,595,864 B／SHA256 `d4cf1cda71e3f042803cddba98d3b2e931e9742f4c09b7bb141f3a33f3590d99`（读回工具 `3de299`）。新增 `test_war_termination_history_read_guard.py` 加原显式投降和白和原生协议夹具，共16项测试通过（`6f35cd`，测试体0.205s，单进程BELOW_NORMAL、禁字节码）；合成无关正文经原历史API复制2次，经新实际守卫复制0次。测试保留pending／applied、错WarID／episode、冷却精确边界、畸形日期和先行readiness拒绝，并验证扫描持锁、到primitive前已经释放锁。首次新夹具因其列表子类附带RLock而不能深拷贝，已仅将旧路径计数夹具改回真实普通列表。冻结运行源未改；这些是调用与分配次数证据，没有游戏实测墙钟收益。

2026-10-18 17:16 UTC追加（同一 `machine_id: xenoamess-full-tower-eb9d2c1186`）：在 `91c570484452a915dcc24024de5ce166e48e1c85` 上，start／stop-assault仍各额外复制一次末128条历史，仅用于同帧holding siege投影。现持原历史锁执行原投影，再只深拷贝投影状态，避免无关正文复制；原128条范围、成功restore隔断、最新失败查询阻止旧查询、同帧身份和资格条件保持，选中的active_siege仍独立于历史。复制成本由该尾部全部正文B降为投影状态S，128条扫描不变；没有取消起始公开snapshot的历史导出，也未改变独立后读或实际查询次数。源码读回 `native_driver.py` 1,596,131 B／SHA256 `4bf357b97b7339a1979a26ee23fdb28945cdd7e890f6b4e9695797ca0bc8a28e`（`5febb4`）。6项新增测试与原注册Client／Service／Driver的holding-only start-stop测试首轮7 PASS（`d1310f`，BELOW_NORMAL、禁字节码，总5.03s）；合成无关正文复制1→0、alias隔离、拒绝、ACK及独立后验均保持。每次start／stop一次是源码调用频率，实际长局频率和墙钟收益未测；未部署冻结SDK或触碰影片。

Root 独立复核（同一机器，结果复核时钟 `2026-10-18T17:19:40Z`）：完整审阅新测试、原投影和restore隔断纯函数后，再跑相同7项，实际外层0（`c4b7c8`，测试体1.222秒／进程4.084739秒，单进程BELOW_NORMAL、禁字节码）。验证保持独立后读，Native primitive不在历史锁内；没有操作实际Game或当前编码会话。

2026-10-18T18:38:40Z 源码候选补注（`machine_id: xenoamess-full-tower-eb9d2c1186`）：研究时实际HEAD为 `ae1a97e742c982ea381102e223fabe57b2ca6834`（`a41906`）。已核预测、会合和起点的按需展开专题：已实现的是不适用时跳过展开，各消费者仍使用独立列表。下列完整source pins于18:40:30.374998Z仅从仓库读回（`664c36`；path相对仓库根），没有读取冻结SDK或运行证据：

- `ck3_autonomous_player/src/xar_autoplayer/strategy.py`，1,031,722 B，SHA256 `38b4d445646b4e501c8f9ce98649c25fdcb7469f20320ecc2bf11b55c429e7ae`。
- `ck3_autonomous_player/src/xar_autoplayer/war_safe_rendezvous_v1.py`，17,001 B，SHA256 `6df6bc79cfcc902766e27f4fffa367d12fb241245c7569de4d75764a19c32281`。
- `ck3_autonomous_player/src/xar_autoplayer/war_route_origin_exposure_v1.py`，19,945 B，SHA256 `119bba068a45cd81819f9264de9f641e20fbca2be3011c77d75ae6e34a248d60`。
- `ck3_autonomous_player/src/xar_autoplayer/raiktor_formal_exit.py`，16,262 B，SHA256 `e83e8373c3fafd4b857ab4c1a6828af7197868474f859eadfb9f6f46cf2cadd8`。

具体重复链为 `choose_one_life_turn:7869`→`_choose_one_life_turn_core:8399`先展开全部历史；同次choose的7928／7958又向围城／普通预测传入新的展开工厂，适用消费者在18092–18093／17592–17593再次调用。453–477的展开函数为每个有效行新建含index的外层dict，并不深拷贝其正文。核心加一个适用审查因此至少物化2N个行dict；非适用路径仍只需核心的一次。这是源码条件频率，不是实机采样，也不是重复Native查询的证明。

最小候选是在单次choose内惰性物化一次，让核心的可选工厂及现有审查工厂消费该结果；直接调用核心仍保原默认行为，不跨轮缓存，不改变早退、调用顺序、原帧与Native守卫。可把k次O(N)展开降至一次。**尚未资格的阻点**是独立可变列表合同：AST只见核心对rows的初始赋值，尚未证明所有下游都不修改list、外层row或index；不能直接共享，更不能假称已有只读资格。

必要资格应先有限追踪这些变更，再用真实核心到适用预测的生产路径比较完整plan、selected_step及拒绝，并计展开2→1；无关／terminal早退保持原0或1，混合AUTO-run／restore／错误行次序不变。同帧两轮间追加history必须重新展开；陈旧帧、参与者或风险变化仍选原查询／拒绝。另在首消费者主动尝试list／row修改，证明拒绝或隔离不会污染后续消费者。若隔离需要改写整条消费链则停止此候选。本补注没有实现、测试、现场操作或性能收益测量，也没有重复assault投影优化。

2026-10-18T19:38:24Z 隔离资格补注（`machine_id: xenoamess-full-tower-eb9d2c1186`；控制源码补核19:39:39Z）：新[有限所有权检查](../../ck3_autonomous_player/tests/unit/test_command_row_cache_isolation_audit.py)首轮6 PASS，单进程BELOW_NORMAL、禁字节码，测试体0.004s／进程2.73s（`fe9f87`）。这是写入探针与对象身份检查，不是性能基准；使用可拒绝调用方dict/list写入、但允许deepcopy成私有可变副本的容器。完整源码pins、各域判定与边界在[小证据](evidence/p72-command-row-isolation-audit-2026-10-19.json)，没有Git查询、实现修改或现场操作。

检查确认：两次原展开的list及外层row各自独立，nested result原本就共享。battle-control读取只读history后产生私有规范化frame，两次规范化结果互不污染；同次current与records则刻意共享一个规范化record。adapter在162–302的入口先deepcopy原frame，clear用replace创建新数值状态；selected-owner撤出在原正向资格夹具中复制backing映射并构造新side／condition；normal finalizer的daily-row投影也不写调用方condition／manager／backing。这四域的输入读取通过，但不代表其输出深不可变：clear新condition仍与旧私有condition共享source_snapshot／source_entry映射，frozen dataclass不足以允许跨消费者缓存模型输出。可复用原始只读观察的判断不能扩张为取消adapter的复制屏障；可选分支、所有事件registry及其余post-review仍未全部资格。

另核真实控制边界：NativeDriver的retreat preview在13272清旧token、13406写新token；order在13521先清token再做新鲜观察／提交。`finalize_projected_one_life_settlement:23501–23527`调用终端并记录成功或失败。这些会改变状态的控制不在纯规划行缓存内，不能跳过。battle-control在9345–9369过滤history后递归choose；Council在14872–14883改变capability集合后递归，同帧并不等于相同输入。

结论是**不启用全规划共享cache，也不缓存规范化或模型返回值**。本轮仅排除所查四域主动修改输入的疑点，未抹去外层容器的独立合同。最小后继实现边界仍只在strategy的单次choose创建惰性展开工厂、核心保留直接调用默认路径；每个递归子调用必须建立自己的新作用域。剩余资格应只追踪未审的事件registry／post-review外层list、row、index写入，再比较完整plan、拒绝及混合AUTO／restore和变帧路径；没有这项证明就保留现实现。现有原生读取、normalizer、adapter隔离和提交后验均不应因该候选减少。
