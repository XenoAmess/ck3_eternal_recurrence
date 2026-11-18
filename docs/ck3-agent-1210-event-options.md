# CK3 1.21 普通事件选项后台通道

本通道服务金融 Mod 的正常事件操作验收，不调用控制台 effect，也不恢复旧自动游玩。窗口必须保持最小化；通道不激活窗口、不读取屏幕、不模拟鼠标。

本机 `machine_id: 4-8e1c2f1861` 的安装版为 CK3 `1.21.0`、Steam build `26622941`，EXE SHA-256 为 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。以下布局来自这份 EXE 的离线 RTTI、构造器、原生按钮查询和命令路径，未沿用旧版地址。来源跨度与 SHA 见 [ABI 原件索引](../ck3_autonomous_player/native_bridge/research/ck3_1_21_0_event_options.json)。

## 正常界面语义

原先的基本事件快照只观察 authored 总数。隐藏选项没有实际 GUI item，显示次序也不等于 authored native index。本通道从精确类型的实际窗口读出 materialized item，返回其 native index，再调用本版本原生 `CanSelect`。该查询包含 fallback、原始 enabled、界面等待和自定义控件有效性；只看 enabled 字节会漏掉这些条件。

| 路径 | 1.21 本机静态证据 |
| --- | --- |
| Jomini owner → in-game idler | `+0x10`，idler vtable RVA `0x4B24758` |
| idler → event window manager | `+0x28` |
| manager → window vector | pointer `+0x18`、capacity `+0x20`、count `+0x24` |
| CEventWindow 类型与 data | vtable RVA `0x4C5D430`，data `+0xB8` |
| data → materialized options | pointer `+0x10`、capacity `+0x18`、count `+0x1C` |
| item | stride `0x1B8`，owner `+0x160`，native index `+0x1B0` |
| 原生 CanSelect | RVA `0x1B6C810` → data validity `0x1B697A0` |
| 原生 option command | size `0x28`，instance `+0x20`、native index `+0x24` |

所有列表有界、身份重复读，item owner 必须等于所属 data；索引须唯一且在本事件 authored 范围内。最多 32 个窗口、512 个 authored/显示选项是桥接器工作界限，不声称是引擎极限。带 `data+0x7C0` 自定义选择处理器的窗口明确拒绝，不能绕过其处理器直接排队。

## 单一请求与生产消费

`query-current-event-options-v1` 和 `select-event-option-N` 都使用 `execute_step` 外壳，携带真实 `expected_revision`、唯一 `event_option_control` claim，以及仅含正 int32 `event_instance_id` 的 `arguments`。claim schema 是 `ck3_1210_event_option_control_v1`，其 build tuple、`snapshot_id: native:N`、`native_revision`、原始 deadline 与 Full 一致；重复字段、未知字段、布尔数值、浮点和字符串 ID 一律拒绝。

查询能力为 `game.query.current-event-options.v1`，选择能力沿用 `game.command.select-event-option-N`。新能力受 `XAR_CK3_ENABLE_1210_EVENT_OPTIONS_V1` 控制，要求精确 paused Full。旧 adapter 的 worker 虚函数保持关闭；真正操作走 application-main mailbox，校验真实线程、TLS、pump、Full、当前 occurrence 和实际显示选项。

沿用公共 MCP 的索引语义：step 的 `N` 为 1-based authored identity；查询与结果中明确命名的 `native_option_index`、CK3 command payload 为 0-based。生产者只在编码 step 时加一，Native parser 只在解析 step 时减一；显示行顺序不参与转换。

选择先用引擎自己的 clone 得到 owned command，再在入队前重新核验同一 Full、occurrence 和原生可选性，通过原生 manager 的 channel 7 排队。未知结果不得重发。`submitted` 只证明 native queue 接受，业务结果还须由新的独立 Full、日志或存档确认。

结果 schema 为 `ck3_1210_event_option_control_result_v1`，固定回传请求的 revision、event id 和 index，不借当前另一个事件冒充关联。query 的 index 为 null。结果含完整 build tuple、step、accepted、application-main/full-before/effect-attempted 三项事实及实际 options；失败不保留旧 options。

## 当前验证边界

2026-11-18，本机共同 DLL 已在唯一增量目录 `C:/workspace/ck3-market-task-20261118/native-event-build01` 真实链接，原构建退出码 0，`-j2` 从 10:15:22Z 到 10:50:31Z 确认结束，端到端 35 分 09 秒。产物为 13,364,224 bytes，SHA-256 `22da249e8de425ad605693d062cd691e7b2dd3a334f21a7a090fc98e06111b4e`。实际 File API 的生产闭包为 bridge 268、runtime 522、protocol 1 个 TU，没有 fixture 依赖；这是配置图计数，不代表全部重新编译。

两个事件夹具覆盖隐藏索引、disabled、fallback、错误 owner、重复索引、边界、列表变化、自定义处理器拒绝、严格 claim、原始期限、零派发拒绝与真正 C++ serializer 输出。共同 profile 的 19 个 1.21 既有／新增有限夹具各自原始 `Popen.wait` 均为 0，CTest 19/19 通过，实际耗时 0.31 秒。首次扩展资格因生产 `SOURCE` 宏泄漏到默认 identity 而产生 LNK2019/1120；修复仅用两个 test-only 薄 wrapper 在各自宏环境 include 真正 adapter／Full reader，保留原 RED。随后同一缓存 `-j6` 只重编四个受影响 wrapper 对象及必要链接，未改变生产能力或重建第二份 DLL。

精确 19 个测试 EXE 已通过既有工具完成 Defender 注册，另一个 WMI client 的独立只读三设置读回为 verified；行政令牌实际为 true，扩展与进程排除未改变。此为机器设置事实，不授运行期信任。

首编发生于 dirty 源码状态，不补写为编前冻结。正式资格仍须绑定最终 clean commit、编前 source freeze、同缓存 production no-work 验证与公共 runtime；当前实机正常事件选择、业务后验及 SAVE 仍待 Root 独占验收。不得依据本文或软件通过声称金融业务已经实机通过。
