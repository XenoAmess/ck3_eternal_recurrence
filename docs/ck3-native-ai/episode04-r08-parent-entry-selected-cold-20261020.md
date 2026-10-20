# R08 parent-entry：独立有限冷验已接受（2026-10-20）

machine_id: `desktop-3fevhd2-1c74096080`。实际观察与 Root 验收时间、来源 SHA 见本专题证据包中的原始回执。

Root 已接受这次独立组件的有限结果：真实 MSVC 静态库和 surrogate EXE 编译成功；新精确 EXE 路径的普通 SYSTEM Defender 排除得到实际设置读回；四个本机模式各执行一次并以原始 Popen wait 0 完成。ABI/默认 OFF/foreign 257、状态/并发 OFF 两组各通过 2 项检查；Windows `RtlVirtualUnwind` 在实际生成的 90 个合成 CONTEXT 指令 PC 上全部通过。当前正式进度为 5/11；本次不增加游戏内 R08 业务资格。

实际 own-image 解码只读 6 段，thunk 403 B / 80 条指令、prefix 42 B / 10 条指令。完整两 span SHA、生成器来源、registered EXE SHA、1026 B case 文件 SHA 和原 `--unwind` argv 在执行前绑定。没有 CK3 EXE 读取或实际 CPU 每 PC 单步。

第一次真实构建因 fixture ASM 的 BYTE extern 内存 operand 缺少显式宽度而返回 1。原 10 个源码、源清单、失败 report/log/wait 均保留；新 fixture-a03 只增加 XMMWORD/QWORD operand 标注及引用旧 C++ 的 CMake，小修后在新 build-a03 真实配置和编译。核心 a04 未改字节，不能称为整个 bc638 或当前 master 的重新编译。

Root 的有限验收原件是 `ROOT-LIMITED-COLD-ACCEPTANCE.actual.json`。较早的 selected qualification 保留其生成时“待 Root 接受”状态；后继 Root 原件完成该接受。两份记录均不覆盖重写。完整 273331 B SYSTEM 设置原件只保留外部 path/size/SHA 引用；Git 小包纳入 Root 亲读后的 selected review、manifest 和 exact gate，不声称完整系统原件已经便携入库。

真实 Install/Restore、VirtualProtect/Flush/rollback 故障夹具、受管 all-peer-thread 停止安装窗口、AVX upper-state 哨兵、entry FullID/clock 及 same-owner 现场仍未验收。现有 public managed 安装时序缺口继续阻止游戏接入。付款、payer、军事 producer、cadence、c/d writer、live/full R08 结论均为未取得。

证据：[`episode04-r08-parent-entry-selected-cold-20261020`](evidence/episode04-r08-parent-entry-selected-cold-20261020/ROOT-LIMITED-COLD-ACCEPTANCE.actual.json)。原始失败和有限冷验材料由该目录精确小清单绑定；不包含 EXE/lib/PDB。
