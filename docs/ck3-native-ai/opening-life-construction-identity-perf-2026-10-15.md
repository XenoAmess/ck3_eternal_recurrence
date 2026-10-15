# Opening LIFE 与建设身份检查的复制/元数据优化

2026-10-15，候选基于 continuation40 的冻结 SDK；只把已审小补丁合入开发树，未覆盖完整运行时文件。

Opening LIFE 提前返回时，原规划器仍携带 faction/construction/council/M5 的私有快照与历史，受保护规划视图会复制这些未消费数据。现在只在该分支移除非 LIFE 私有字段，严格保留 lifestyle scope、原 pending action 与 war-frame；三个只用于当前帧资格检查的快照显式省略 Native 命令历史。正常普通规划器、M5 与 LIFE 下游消费者所需历史保留。

建设 `_identity` 原来在每次普通规划时重新访问 WMI。新 helper 仅在原 WMI 与前后两次内核读取一致后建立每 Driver 身份 pin；每次命中仍重新打开只读 HANDLE，核 PID、完整 100ns FILETIME、映像及非退出状态。输出保留首次实际 WMI 创建时间字符串的原字节。证明同 PID 的出生或映像变化时拒绝；权限/平台/读取未知、无 pin 或不可解析时间仍回退原 WMI 路径。全局 `runtime._process_identity`、启动命令行/映像资格和建设业务守卫不变。

本场实际只读元数据基准：PID 226540、FILETIME `134365126565203982`；WMI `20261015123736.520398+480` 与冻结 UTC `20261015043736.520398+000` 为同一瞬间。`+480` 是分钟偏移，FILETIME 最后一位 `2` 只在初次与微秒 WMI 配对时不参与时间格式比较，此后完整保存在 pin 中并逐次精确比较。

| 测量 | 结果 |
| --- | --- |
| 原 WMI，3 次中位 | 1.3395651 秒 |
| 候选首次 WMI 配对 | 1.3111034 秒 |
| 已配对后内核重核，31 次中位 | 0.0000763 秒 |
| 已配对后内核重核最大值 | 0.0005208 秒 |

来源为外置 `construction-identity-kernel-fix01/ACTUAL-PROCESS-BENCHMARK.json` 与 `DELIVERY.json`，运行叶 helper SHA `31f0f776d5b9790f4c4b2c972ddb696d186e53e09a63b1c943c979cd48473da9`；opening 候选在 `opening-life-plan-copy-fix01`。测试不依赖这些本机路径，使用完整合成 Windows metadata、真实 Service/Driver 方法与现有 LIFE protocol fixture，覆盖原 ID/三 LIFE 字段、时区、100ns 出生差异、映像变化、观察竞争、权限未知及原异常。

这是进程元数据与离线消费者验证，不是完整 MCP/游戏日吞吐实测。首次 WMI 成本仍在，其他规划、Native 查询、保存和真实游戏处理成本未由此消除；目标 0.5 秒/游戏日尚未验收。部署只需下一次 SDK 热接，游戏与录制不需重启。
