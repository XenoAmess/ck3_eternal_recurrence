# `textured_emblem` 原生验收 R32（启动超时 RED）

R32 是第一次用单样例入口启动的受管 CK3 验收。120 秒内没有观察到 `main_menu` 路由，因而没有进入家徽页，也没有生成像素结论。该结果只说明冷启动上界不足，不是 renderer 或 `textured_emblem` 失败。

- 完整报告：188,074 bytes，SHA-256 `8AE2E0E0E985C7DE77AED5EA65A505AC9E4590A3D33DF04E35CEFD4E9177FCBE`。
- 总耗时：122.921 秒。
- 失败：`main_menu route was not observed`；picture corpus 没有执行。
- 清理：受管进程树归零，锁已释放。
- 后继：R33 将启动上界扩大至 300 秒；最终通过结果是 R35。

完整返回保存在 [`report.json`](report.json)，并按 binary 跟踪以维持精确哈希。
