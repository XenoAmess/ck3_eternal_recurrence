# Saved 准入后的性能与功能切点

本文现场时间均为 2026-11-06 UTC。旧切点文档保持原样，本文追加后到事实，不把源码、软件测试或 Git 提交当成运行收益。

## 已完成的运行边界

P08503 后 r57 从 START 到 LOOP 实耗 873.4317432 秒，完整历史恢复已过；这段冷恢复成本没有从性能分母中剔除。public SAVE1475 确认了此前未存的38日，SAVE1323→1475完整窗口17685.8439599秒，平均465.4169463秒/新增确认保存日，目标10秒尚未达到。

M7 新 Game102152 的严格 preentry 路线在19:03:27.586962实际报告 SavedEntry/head20，随后进入普通 LOOP。START→Entry为262.525278秒，custody→Entry为220.0321708秒，包含两次 READ、校验和采用，不能称为纯 RPC 时间。19:02:48.7526968的event20已含 Entry marker，到采用状态日志仍有38.8342652秒，因此这段至少包含 marker 写入后的初始化/返回成本。这里尚未授新增 Goal/fullplan、游戏日或 SAVE。

## 当前成本排序

| 窗口 | 已测事实 | 下一步的安全范围 |
| --- | --- | --- |
| 冷恢复 | 873.4317432秒完整恢复；历史 CAS 有大量身份校验调用 | 避免不必要重载；细分历史读取、物理校验、纯解析和重建，保留全部历史与当前校验 |
| source qualification | 被动入口从 actor START 到 SOURCE_QUALIFIED为45.963秒，尚无排他内部时间 | 同 writer 锁内重复 qualification/readMaterial 是实际源码链，先消除相同输入的纯解码，保留每次文件读取、哈希、ACK、owner/current 检查 |
| 普通业务 OBS/PLAN | 下表四窗口已有实际命中和阶段墙钟 | 先用既有计数观察当前候选覆盖面，不把不同输入、不同 return 次数当成对照实验 |
| public SAVE | HTTP完整耗时1033.1095352秒；实际 Native写入完成→ACK仅25.2846毫秒 | 分开 Java排队、前置校验、文件/Driver处理和发布；未证明整个HTTP耗时来自游戏 SAVE 或 fsync |

SAVE1475 的原 custody 显示写入完成15:45:48.9781682、ACK接收15:45:49.0034528。其前 guard 观察时间为15:44:36.6594861，Submitted为15:45:32.7633313；后态snapshot为15:46:42.0997211，pair观察为15:47:11.3045541，确认事件为15:49:08.1922044。这些锚点说明需要细分 Java pipeline；尚不能把前置整段都归入锁等待或纯磁盘耗时。

旧45秒混合 JFR 的 replay223、rebuild161、EvidenceReader158 为包容采样，不能相加。FileForce合计2.122秒和 GC暂停1.970秒也不能外推为上述恢复或保存窗口的主因。一个后到 P088 数据测试在真实 Windows 文件身份读取前沿超出其10秒等待，只能作为该测试样本，不能据此认定主程序死锁或全部文件系统成本。

## P087 已采用后的四个业务窗口

| scope秒 | OBS秒 | PLAN秒 | nominal calls/hits/parse |
| ---: | ---: | ---: | --- |
| 69.9589509 | 46.6490354 | 17.2179816 | 8 / 6 / 2 |
| 67.5765534 | 45.9652377 | 15.7258079 | 8 / 4 / 4 |
| 150.3991124 | 69.1650843 | 79.8819801 | 18 / 6 / 12 |
| 118.7105154 | 46.3373321 | 72.3055184 | 12 / 4 / 8 |

第三窗口有三次 OBS/PLAN return，其他表中窗口为两次。nominal 计数只覆盖该纯历史投影路径；v4 fresh 校验及其他解析、文件读取和权限校验没有全部计入。因此已证的是 P087 在业务中实际命中，尚未证明完整窗口差值由它单独造成，更没有新增保存日的达标结果。

P097 候选针对同一次 checkpoint binding 中先 readVerifiedOriginal、随后 verifyOriginal 的重复严格解码。第一次严格读取后，只在局部保存不超过8 MiB的原字节副本；第二次仍按原顺序执行文件verify、ACK检查、Driver读取和verify。相同字节及相同捕获参数才省纯解码/anchor重算，变化、超限、非 plain BigInteger 或再次调用走原严格路径，IO前清除可复用字节。没有 Complete/global/ThreadLocal 缓存。两生产TU首编通过，真实1475 Driver DATA测试取得1P，证明解码计数、读取顺序、变化与错误回退；实际采用和墙钟收益仍待后续真实回执。

## 当前功能故障

ordinary-sway 的原 HTTP400 已取得服务端原body：上下文上限1048576，而请求至少1048577 input tokens，参数为input_tokens。一次原请求中history约2,847,000字节、root facts712,937字节、current snapshot45,909字节、proposal2,800字节；字节数不直接等于token数。专属任务投影及有限客户端输入预算修复由功能线继续验证，不调整服务上下文、不盲截断必需字段、不重放 Native动作。它与已完成的 SavedEntry、P087命中和P097软件测试分别记录。

机器证据导航：`D:/ck3-state/resume91-runtime/resume-after-user-play-20261105/m7-loaded-preentry97/first-metrics97/FIRST-FOUR-METRICS-AND-HTTP97.json`；`D:/ck3-state/resume91-root/newgame-loaded-saved-entry-independent97/`；P097源码、软件与DATA资格在`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/saved-driver-same-call-recheck97/`。上述路径用于核对原件，不是新的恢复审批门。
