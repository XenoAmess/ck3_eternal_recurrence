# `textured_emblem` 原生验收 R34（验收器误判 RED）

R34 首次完整走通受管 MCP 的路由、Apply、Copy、重新 Apply 与两轮 framebuffer 比较。所有语义和像素门禁都通过，但旧 runner 无条件要求每个样例都超过旧 v1 的 128 KiB 单请求界限；本标定样例仅 172 wire bytes，因而被错误记为 overall RED。

这项假阴性不改变像素结果，也不能把 R34 称为整体 GREEN。代码 `e7100297` 将“大载荷超界要求”和“小型标定样例”分开，R35 随后在修复后的合同下完整通过。

- 完整报告：4,722,086 bytes，SHA-256 `E4A1F52F5D4FCDB265862A05BF499969B4890C4567455BFFEEF35D0F12C4F98A`。
- 浏览器→原生：MAE `0.0067262757`、color MSE `0.0002362251`、edge loss `0.0236444268`、最差 8×8 空间 MAE `0.0279777106`；全部低于预声明阈值。
- Copy→重新 Apply：MAE `0.0000176776`、color MSE `0.0000000693`、edge loss `0.0001509101`、最差空间 MAE `0.0001413178`；全部低于更严格阈值。
- 唯一失败键：两轮各自的 `input_exceeds_v1_bound` 与 `native_copy_exceeds_v1_bound`。
- 清理：GREEN，受管进程树归零，锁已释放。

机器可读精简回执见 [`summary.json`](summary.json)，完整报告见 [`report.json`](report.json)，对齐后的两张原生图见 [`crops/`](crops/)。
