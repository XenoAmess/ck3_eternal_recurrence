# M4：借款观察接入既有军费只读查询

`machine_id: xenoamess-full-tower-eb9d2c1186`。机器身份由本活动 MSVC producer 的 `tools/ck3_live_run_id.py:current_machine_id` 实际读回；观察、命令、全部变更前后 SHA、实际项目 headers、测试与外置完整编译记录来源见[资格记录](evidence/holy-order-loan-war-cash-integration-2026-10-19.json)。本次按[已冻结采用方案](holy-order-loan-war-cash-collector-object-2026-10-19.md)实施，没有覆盖旧 source-only/object/九例合成历史。

既有 `.4` `query-war-cash-current-resources-v1` 的同一 application-main executor 在 `ReadActor` 后调用一次已编译的 collector；它复用已进入的 envelope、完整 snapshot 和 execution stamp，再沿原 `FinishQueryMailbox`、worker 后验 snapshot 比较和回收流程返回。没有新增 query、权限、action 或重复读取机制。

`ActorResources` 末尾新增 optional `holy_order_loan`；serializer 为其输出 `holy_order_loan_observation_v1` 子叶，保留原生 ticket/revision/actor/date/local-player 与 execution stamp 的全部成员。发布可用值须满足完整 snapshot owner 保留、暂停地图、原外层同帧及 provider actor/date/epoch 一致；本金还须已确认临时 root/scratch 清理。十槽费用沿用原 provider serializer，数值不折算成钱包。

原 Python cash normalizer 保留钱包、净收入和军费的既有合同及总体 status，只对新增 loan 子叶独立降级。决议子项复用已有 cost-only projector；`principal_quote_raw`、原生 `borrow_eligible`、费用分别保留。原生 `can_take=false` 可保持 false；无法观察或格式不完整时资格为 null。本金零是有效报价，不能当作缺失。未知债务仍为 null，完整条款未资格，到账 false、funding credit 为 0。子项失败不能使有效的原 cash 查询整体不可用。

普通战争 consumer 新增默认空的 `cash_resources`/`cash_source_frame` 参数，只合并融资观察。输入须与当前完整 planning source frame 的 snapshot/public/native revision、角色、日期、episode、bridge PID 和 connection generation 严格一致，且匹配实际 query metadata。没有数据时沿用原行为；输入失配只留下未知贷款观察，不改变战争、建设或雇佣决策。Service、driver、strategy 未改，真实普通 planner 的实际查询与完整帧交接仍由 Root 后续协调；这里不制造 Driver 缓存或将局部 monthly packets 当作普通 planner 输入。

CMake 在现有 runtime 明确增加 decision-costs、principal、collector 三个 cpp，并把 research include 需求传给其公共头文件消费者。没有新 target、glob、生产 archive 副本或 EXE。`ActorResources` 布局已改变，未来采用必须按实际 Ninja 依赖一致重编相关 TU/archive；本次没有 configure、大 Native 构建、生产链接或当前 SDK 热换。

验证分两段保留原件：首次 focused Python file 的 27 个合成 case 全通过；随后源审补齐 supplied current snapshot 必须 paused/map_ready 的两个谓词，仅运行新增 node 的两个参数 case，亦通过。没有把两段测试写成“最终 29 case 全量重跑”，失败 attempt 为 0。覆盖费用全部十槽、已知 false 与未知资格、零本金、错误成本与错误本金彼此隔离、错误 Native frame/stamp、禁止资金/完整条款断言，以及跨 episode/PID/connection 的输入拒绝。

`2026-10-19T06:15:24.335189Z` 至 `06:15:28.406880Z` 对实际 serializer cpp 做一次独立 `/c /W4 /WX /MD /O2 /std:c++20` 编译，首次返回 0，用时 4.0717 秒，实际依赖 485 份 header。object 为 277,949 B，SHA `ea366df1d4696640d7472cfaae03482eac16dca7e925e1174a68a862f2e90e50`。没有链接或执行；该资格证明新 serializer/公共类型可编译，不证明整个 bridge 已构建、Native RVA/ABI 正确或实际贷款金额可用。

所有 Game、RPC、SAVE、活 Driver、当前 Native26/C5 与 SDK 均未接触。无已到账贷款、借款提交或新增资金信用。本次源与测试只为下一次确需维护时采用及自然现场资格准备输入，不使当前实局等待。

存储归原 other-research 128 MiB，源/测试/小记录 repo 净增硬上限 128 KiB，pytest 新 child 硬 1 MiB，serializer object 新 child 硬 8 MiB；exact 路径、含自身 manifest 的最终 logical、原复核期限见各 `CLOSE01.json`。编译 25 ms logical 采样高水位为 342,866 B，仅为观测下界，最终写入量另计；allocated 未核为 null，不声明精确瞬时/physical 峰，不返还父预算或物理信用。两类 producer 均关闭，遗留进程与未来写入均为 0，旧 closed child 不重开。
