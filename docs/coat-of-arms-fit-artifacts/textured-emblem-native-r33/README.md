# `textured_emblem` 原生验收 R33（内容加载超时 RED）

R33 将受管 CK3 上界扩大到 300 秒，但 exact build 仍在数据库/事件内容初始化阶段，未及时观察到 `main_menu`，因此同样没有进入家徽页或产生像素结论。日志已证明 frontend GUI 开始加载，失败仍属于启动预算而非 renderer。

- 完整报告：149,463 bytes，SHA-256 `A0E23C6E1570C94F7DB450C6F9E993F61561A47E418F8ADA6EE738099DD545E4`。
- 总耗时：305.895 秒。
- 失败：`main_menu route was not observed`；picture corpus 没有执行。
- 清理：受管进程树归零，锁已释放。
- 后继：R34 复用此轮预热 profile 并把上界扩大到 600 秒；最终通过结果是 R35。

完整返回保存在 [`report.json`](report.json)，并按 binary 跟踪以维持精确哈希。
