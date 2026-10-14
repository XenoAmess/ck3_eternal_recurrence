# R90 宿主修复的静态绑定准备

2026-10-14。R89 的实际失败点是宿主 `RecordingEndpoint.send` 录制包装器缺少 `packet_evidence_path` 参数。修复提交 `8ee983df04bc51fabeab534d2059be8deaca678a` 后，进一步审阅 R89 的共享运行时发现，入口 host 与 `source_root` 各有独立的 manifest pin。原 Source19 索引和 native 二进制无需修改；复制整棵约148 MB源码会造成无意义的盘占用。这里冻结唯一改变的宿主文件，创建新包装器和 manifest，保留 Source19 作为其余 Python 模块的固定来源。

外置准备根为 `C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-r90-host-fix-20261014-001`。`PREPARATION.actual.json` 记录文件大小及 SHA-256：修复宿主快照285,497 B / `e9bfb8123ba6d1b1779dc8f79969de21b4ed1928f3f2a963db43b67f07f46d95`，新 host 包装器14,136 B / `033dcc3cb21bfd8819cfa23c261e8878d8da24cf33621b3a2e702a33533d8c4e`，新 manifest159,093 B / `6bf294965fd04b9ba2aebc02c37ca5f7a15e12ac14bd942afb40ab02650d5914`，新 `runtime.local.json` 3,906 B / `91b72e5933fb00c1095d3c56ae4acc099858744079506f3d39a01c424034bcbe`。包装器从新快照执行，并沿用已验收的 normal-exit profile helper；新配置不重复应用已经进入修复源码的五处旧 overlay 编辑。旧 `C:/csr19` 文件仍为282,507 B / `206f41a189cad449059fb2802c039d2239e0e567a4ede805ce6c4a4c14befd97`，未改写。

静态检查解析冻结宿主的 AST，读回 `RecordingEndpoint.send` 的 keyword-only `packet_evidence_path`。新包装器的 `--help` 实际退出0，并读取配置及修复宿主；公共 `ck3_mod_acceptance.py preflight` 精确核对新 manifest、host、配置、Source19 两份索引、原生 DLL/注入器和已装 CK3。预检最终状态仍是 `BLOCKED`，仅因本场新保存的存档/准备计划尚未绑定；这不能当作业务验收。包装器源码中的 Windows 路径字面量在 Python 3.13 产生一条 `invalid escape sequence` 警告，实际路径和哈希读回成功；此警告不影响当前静态执行，但后续通用生成器应改用正斜杠路径。

下一步先按通用存储策略建立新的有限容量准入，再创建本场存档副本、profile 与准备计划；实机前另取新鲜 Steam 离线画面并领取屏幕独占。只有原生一次性道学提名实际发送、后验 NPC 接受、封定、两派表决、签署、头衔及正常退出逐项成立，才能计入相应验收。此准备没有启动 CK3、没有 Steam 发布，也没有补授 R89 的 RED 信用。
