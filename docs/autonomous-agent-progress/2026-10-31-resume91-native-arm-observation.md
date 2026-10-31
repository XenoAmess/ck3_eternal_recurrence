# Native63 ARM / STATUS 与快照发布合同

2026-10-31 08:07Z，针对实际 ARM child384 收到成功 ACK、随后观察失败的任务，只读复用了既持 Native63 源码。没有新 PE 读取、Native 查询、编测、DLL 部署或游戏动作；本页不确定该次 IOException 的内层原因，也不授日期推进信用。

`bridge.cpp:19902–19942` 的 ARM 分支调用 `ArmTacticalDailySentinelV1`；`.4` 成功走 `SerializeTacticalDailySentinelArmResult12004`，旧路径走 `TacticalDailySentinelResultFrame`。分支内没有调用普通快照或 timeline 发布器，也没有清空 `previous_snapshot`。`.4` serializer 在 `ck3_12004_default_routes_mailbox.cpp:148–167` 成功委托 `109–145` 的状态 serializer，帧类型为 `command_result`。

STATUS 字面值为 `research-query-tactical-daily-sentinel-v1`，`bridge.cpp:19973–19980` 直接读取 sentinel 并返回同类 `command_result`。`tactical_daily_sentinel_v1.cpp:749–792` 读取哨兵原子状态并计算结果字段，不发布完整普通 Game snapshot。ARM producer `594–712` 验证并写入哨兵槽及 generation；这两个完整函数不调用恢复游戏或设置速度。

外层 `RunConnectedSession` 仍会独立尝试发布：`bridge.cpp:15364–15376` 处理 date/pause publication-due，`15418–15427` 在心跳路径调用 `PublishSnapshot`。调用不保证发送：`PublishSnapshot:12711–12812` 的 unsupported、read_failed 及相同 snapshot/checkpoint（编译期开启时还要求 modal hint 未变）的去重分支均可返回 true 而不写 state frame。只有通过这些分支后才递增 revision 并写出状态帧。

因此，成功 ARM ACK 没有承诺随后必定产生一个新的普通快照；也不能据此声称之后绝无快照。`PublishTimelineSnapshotWithDiagnostics:12814–12834` 在普通发布器外写 begin/end，wrapper 返回 true 本身仍不证明状态帧已写出。独立 STATUS 原件、实际普通快照和动作前缓存应按各自合同消费；本页不提出使用旧缓存冒充动作后态的修复。

先交原文再派本地模型：首请求实际 08:02:58Z，完整 stop/12.706 秒；外层循环的新原件到达后精化请求实际 08:05:08Z，完整 stop/9.256 秒。两答仅部分源分析采用。首答误把命令内发布称为 background 并过度推断故障；第二答正确识别去重，但 mailbox 行号虚构为 12729，owner 按原件修为 109–154，未采用其 Java 接收时序猜测。没有整答原样采用或模型代码信用。

原件与审阅在本机 `D:/ck3-state/resume91-root/native-arm150/REVIEW150.json`；M1 独立核读在 `D:/ck3-state/resume91-m1-native/arm-status150-source-map/INDEPENDENT-MAP150.json`。这些路径只标识本执行机，不是其它机器使用本地模型的前置。
