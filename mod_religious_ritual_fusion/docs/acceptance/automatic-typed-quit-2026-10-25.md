# 公共客户端自动 typed 退出

`machine_id: 4-8e1c2f1861`，实际验证截至 `2026-10-25T01:10:54.665806Z`。[R0008](R0008-2026-10-25.md) 的 core14 已被接受，但正常退出依赖 Root 多轮操作而错过原截止。本修复不修改旧场次，也不延长任何 hold。

既有 `CaseClient.normal_close` 现在对显式选齐三项 normal-exit 工具、实际 allocated profile、源索引和宿主参数均绑定的场次自动接管退出。它读取实际当前上下文，逐步执行原版准备，关闭退出自动保存，最终确认仅一次，再以只读观察取得原生事实。阶段间核对原进程／出生身份、角色、连接、revision、源和暂停日期；UNKNOWN 不重新确认。其余无资格路径保留原流程，没有新增 Python 生产模块、私有 runner、鼠标或模板代替原生动作。

公共 queue 和 client 只允许同一个 canonical 单步退出意图使用原剩余 Quit reserve；普通业务仍保留原90秒守卫。失败宿主也仅允许该退出意图，原错误保持。正常通过仍要求原 retained OS0、原生0、finish_hold、线程与 cleanup，退出 ACK 不授业务信用。

实际受影响完整组 **124 tests／0 skip／各命令原 wait=0**，覆盖 normal-close 四模块50、manual13、failed-host61及对应严格／queue静态。完整 client 默认 mypy 仍有原两个 pywin32 缺 stub 环境错误；新增函数完整范围严格检查通过，不外推旧大模块全绿。未改 driver／SDK／native，未重跑其115项或 Maven。

R8 原证据只到 query_context。其后测试响应明确为 authored，不冒充 R8 发生过准备或退出。另有 R8 实际 allocation/profile/index 到新入口的无分派消费，及 R6 原单场完整 durable claim/fact/observer 消费；没有打开旧 PID、修改旧输入或拼接两场事实。

原证据 `C:/workspace/rrf-development-20261024/public-chain-a01/r8-auto-quit-a02/VALIDATION.full-scope.actual.json`，7271 bytes，SHA-256 `b71b3182c642084d73ce410a43b5d1f13fb57bb474d0b970ec6fa9e74636e3a4`。client 102638 bytes／SHA-256 `f8685bd09b3ab5ee73ab920a626896d868dda5814729c26d930e49919e18db8b`；queue 25017 bytes／`e15fa52a8634d4199c9753113915d6e6ee92ecc478f9f74e823b2079a6c1df5f`。

后继 cold-rite 将实机验证自动协调和真实正常退出。这份离线验证不授新的 OS 或产品实机通过。

远端 allocator 的独立来源索引修复已线性合回，随后本机实际完成相关四条原命令：25／13／12／20，共70 tests、0 skip、各原wait0，包含新增 typed helper／完整消费者 strict 与 strict-equality。仅把测试的显式 mypy 缓存位置改回 `nul`，避免额外大缓存；不改生产校验。回执 `public-chain-a01/r8-allocator-remote-a01/VALIDATION.actual.json`，2960 bytes／SHA-256 `734ccb635b99ae1c17a2f01567a947d1a71d4b1e1ccbb52ce0e7b00d8f062872`。前述124受测生产及fixture原字节完全相同，没有重跑或继承其他机器的实际环境事实。
# R0010 实机后继

机器 `4-8e1c2f1861`，源码 `3836e7db1d2d4bfda5faf2ffdb8b2e1634107ad0`、runtime-a13：自动 typed Quit 已实际完成 query、准备、关闭退出自动保存、重新确认、一次确认及只读退出观察，保留 OS handle 退出0、native0、host0、cleanup完成，keeper0／CAS13805。`normal_close_qualified=true`。它在保留 Root 原阶段超时错误的同时正常退出，公共 run／verify 仍2，不授业务通过。精确原件与边界见[R0010](R0010-2026-10-25.md)。此前“实机待验证”文字保留其当时语义，不再代表最新状态。
